from datetime import timedelta

import httpx
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .controller import signed_headers
from .models import ExecutionJob


FINAL_STATUSES = {
    ExecutionJob.Status.SUCCEEDED,
    ExecutionJob.Status.FAILED,
    ExecutionJob.Status.CANCELLED,
    ExecutionJob.Status.TIMED_OUT,
}


def _fail(job, code, message):
    job.status = ExecutionJob.Status.FAILED
    job.error_code = code
    job.stderr = message[: settings.EXECUTION_OUTPUT_BYTES]
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error_code", "stderr", "finished_at", "updated_at"])


@shared_task(ignore_result=True)
def dispatch_execution_job(job_id):
    job = ExecutionJob.objects.select_related("source_file").filter(id=job_id).first()
    if not job or job.status != ExecutionJob.Status.QUEUED:
        return
    job.status = ExecutionJob.Status.DISPATCHING
    job.save(update_fields=["status", "updated_at"])
    path = "/v1/executions"
    payload = {
        "request_id": str(job.id),
        "language": job.language,
        "source": job.source_snapshot,
        "stdin": job.stdin,
        "limits": job.limits,
    }
    headers, body = signed_headers(method="POST", path=path, body=payload)
    try:
        response = httpx.post(f"{settings.EXECUTION_CONTROLLER_URL}{path}", content=body, headers=headers, timeout=5.0)
        response.raise_for_status()
        result = response.json()
        controller_job_id = str(result["id"])
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        _fail(job, "controller_unavailable", f"The isolated execution controller could not accept this job: {type(exc).__name__}")
        return
    job.refresh_from_db(fields=["status"])
    if job.status == ExecutionJob.Status.CANCELLED:
        return
    job.controller_job_id = controller_job_id
    job.status = ExecutionJob.Status.RUNNING
    job.started_at = timezone.now()
    job.save(update_fields=["controller_job_id", "status", "started_at", "updated_at"])
    poll_execution_job.apply_async(args=[str(job.id)], countdown=1)


@shared_task(ignore_result=True)
def poll_execution_job(job_id):
    job = ExecutionJob.objects.filter(id=job_id).first()
    if not job or job.status in FINAL_STATUSES or not job.controller_job_id:
        return
    deadline = job.created_at + timedelta(seconds=job.limits["timeout_seconds"] + 20)
    if timezone.now() > deadline:
        job.status = ExecutionJob.Status.TIMED_OUT
        job.error_code = "controller_timeout"
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_code", "finished_at", "updated_at"])
        return
    path = f"/v1/executions/{job.controller_job_id}"
    headers, _ = signed_headers(method="GET", path=path)
    try:
        response = httpx.get(f"{settings.EXECUTION_CONTROLLER_URL}{path}", headers=headers, timeout=5.0)
        response.raise_for_status()
        result = response.json()
    except (httpx.HTTPError, ValueError):
        poll_execution_job.apply_async(args=[str(job.id)], countdown=2)
        return
    controller_status = result.get("status")
    status_map = {
        "running": ExecutionJob.Status.RUNNING,
        "succeeded": ExecutionJob.Status.SUCCEEDED,
        "failed": ExecutionJob.Status.FAILED,
        "cancelled": ExecutionJob.Status.CANCELLED,
        "timed_out": ExecutionJob.Status.TIMED_OUT,
    }
    job.status = status_map.get(controller_status, ExecutionJob.Status.RUNNING)
    output_limit = settings.EXECUTION_OUTPUT_BYTES
    job.stdout = str(result.get("stdout", ""))[:output_limit]
    remaining_output = max(0, output_limit - len(job.stdout.encode("utf-8")))
    job.stderr = str(result.get("stderr", "")).encode("utf-8")[:remaining_output].decode("utf-8", errors="replace")
    job.exit_code = result.get("exit_code")
    job.runtime_ms = result.get("runtime_ms")
    job.memory_bytes = result.get("memory_bytes")
    if job.status in FINAL_STATUSES:
        job.finished_at = timezone.now()
    job.save()
    if job.status not in FINAL_STATUSES:
        poll_execution_job.apply_async(args=[str(job.id)], countdown=1)


@shared_task(ignore_result=True)
def cancel_controller_job(job_id):
    job = ExecutionJob.objects.filter(id=job_id).first()
    if not job or not job.controller_job_id:
        return
    path = f"/v1/executions/{job.controller_job_id}/cancel"
    headers, body = signed_headers(method="POST", path=path, body={})
    try:
        httpx.post(f"{settings.EXECUTION_CONTROLLER_URL}{path}", content=body, headers=headers, timeout=5.0)
    except httpx.HTTPError:
        return
