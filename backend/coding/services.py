import hashlib
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from audit.services import record_audit_event
from billing.entitlements import coding_project_limit_for_user
from .exceptions import ExecutionUnavailable, ProjectLimitExceeded
from .models import CodingProject, ExecutionJob, ProjectFile, ProjectFileRevision
from .validation import MAX_FILES_PER_PROJECT, RUNNABLE_LANGUAGES, validate_content, validate_project_path, validate_stdin


def owned_projects(*, user):
    return CodingProject.objects.filter(owner=user, deleted_at__isnull=True).prefetch_related("files")


def _checksum(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@transaction.atomic
def create_project(*, user, name, description="", primary_language="python", request=None):
    # Serialize project creation per user so concurrent requests cannot bypass the plan limit.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    project_limit = coding_project_limit_for_user(user=user)
    active_project_count = CodingProject.objects.filter(owner=user, deleted_at__isnull=True).count()
    if project_limit is not None and active_project_count >= project_limit:
        raise ProjectLimitExceeded()
    project = CodingProject.objects.create(owner=user, name=name.strip(), description=description, primary_language=primary_language)
    record_audit_event(action="coding.project_created", actor=user, target=project, request=request)
    return project


@transaction.atomic
def create_file(*, user, project, path, content="", language="plaintext", request=None):
    if project.owner_id != user.id:
        raise PermissionDenied("Only the project owner can add files.")
    if project.files.count() >= MAX_FILES_PER_PROJECT:
        raise ValidationError({"path": f"A project can contain at most {MAX_FILES_PER_PROJECT} files."})
    path = validate_project_path(path)
    content = validate_content(content)
    digest = _checksum(content)
    try:
        file = ProjectFile.objects.create(
            project=project, path=path, content=content, language=language,
            checksum=digest, size_bytes=len(content.encode("utf-8")),
        )
    except IntegrityError:
        raise ValidationError({"path": "A file already exists at this path."})
    ProjectFileRevision.objects.create(file=file, created_by=user, version=1, content=content, checksum=digest)
    project.save(update_fields=["updated_at"])
    record_audit_event(action="coding.file_created", actor=user, target=file, request=request, metadata={"path": path})
    return file


@transaction.atomic
def update_file(*, user, file, content=None, path=None, language=None, request=None):
    if file.project.owner_id != user.id:
        raise PermissionDenied("Only the project owner can update files.")
    changed_content = content is not None and content != file.content
    if path is not None:
        file.path = validate_project_path(path)
    if language is not None:
        file.language = language
    if changed_content:
        file.content = validate_content(content)
        file.version += 1
        file.checksum = _checksum(file.content)
        file.size_bytes = len(file.content.encode("utf-8"))
    try:
        file.save()
    except IntegrityError:
        raise ValidationError({"path": "A file already exists at this path."})
    if changed_content:
        ProjectFileRevision.objects.create(
            file=file, created_by=user, version=file.version, content=file.content, checksum=file.checksum,
        )
    file.project.save(update_fields=["updated_at"])
    return file


@transaction.atomic
def soft_delete_project(*, user, project, request=None):
    if project.owner_id != user.id:
        raise PermissionDenied("Only the project owner can delete it.")
    project.deleted_at = timezone.now()
    project.save(update_fields=["deleted_at", "updated_at"])
    record_audit_event(action="coding.project_deleted", actor=user, target=project, request=request)


@transaction.atomic
def create_execution_job(*, user, file, stdin, idempotency_key, request=None):
    if not settings.EXECUTION_ENABLED:
        raise ExecutionUnavailable()
    if file.project.owner_id != user.id:
        raise PermissionDenied("Only the project owner can execute this file.")
    if file.language not in RUNNABLE_LANGUAGES:
        raise ValidationError({"language": "This file type is not supported by the isolated execution service."})
    stdin = validate_stdin(stdin)
    existing = ExecutionJob.objects.filter(requested_by=user, idempotency_key=idempotency_key).first()
    if existing:
        return existing, False
    job = ExecutionJob.objects.create(
        requested_by=user,
        project=file.project,
        source_file=file,
        language=file.language,
        source_snapshot=file.content,
        stdin=stdin,
        idempotency_key=idempotency_key,
        limits={
            "timeout_seconds": settings.EXECUTION_TIMEOUT_SECONDS,
            "memory_mb": settings.EXECUTION_MEMORY_MB,
            "cpu_millis": settings.EXECUTION_CPU_MILLIS,
            "output_bytes": settings.EXECUTION_OUTPUT_BYTES,
            "network": False,
        },
    )
    record_audit_event(action="coding.execution_requested", actor=user, target=job, request=request, metadata={"language": file.language})
    return job, True


@transaction.atomic
def cancel_execution_job(*, user, job, request=None):
    if job.requested_by_id != user.id:
        raise PermissionDenied("You cannot cancel this execution job.")
    if job.status in {ExecutionJob.Status.SUCCEEDED, ExecutionJob.Status.FAILED, ExecutionJob.Status.CANCELLED, ExecutionJob.Status.TIMED_OUT}:
        return job, False
    job.status = ExecutionJob.Status.CANCELLED
    job.cancelled_at = timezone.now()
    job.finished_at = job.cancelled_at
    job.save(update_fields=["status", "cancelled_at", "finished_at", "updated_at"])
    record_audit_event(action="coding.execution_cancelled", actor=user, target=job, request=request)
    return job, True
