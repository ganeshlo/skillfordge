from django.conf import settings
from django.db import models

from core.models import SoftDeleteModel, TimestampedModel


class CodingProject(SoftDeleteModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="coding_projects", on_delete=models.CASCADE)
    organization = models.ForeignKey("organizations.Organization", related_name="coding_projects", null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    primary_language = models.CharField(max_length=30, default="python")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["owner", "status", "-updated_at"])]


class ProjectFile(TimestampedModel):
    project = models.ForeignKey(CodingProject, related_name="files", on_delete=models.CASCADE)
    path = models.CharField(max_length=500)
    content = models.TextField(blank=True)
    language = models.CharField(max_length=30, default="plaintext")
    version = models.PositiveIntegerField(default=1)
    checksum = models.CharField(max_length=64)
    size_bytes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["path"]
        constraints = [models.UniqueConstraint(fields=["project", "path"], name="unique_project_file_path")]
        indexes = [models.Index(fields=["project", "path"])]


class ProjectFileRevision(TimestampedModel):
    file = models.ForeignKey(ProjectFile, related_name="revisions", on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="code_revisions")
    version = models.PositiveIntegerField()
    content = models.TextField(blank=True)
    checksum = models.CharField(max_length=64)

    class Meta:
        ordering = ["-version"]
        constraints = [models.UniqueConstraint(fields=["file", "version"], name="unique_file_revision_version")]


class ExecutionJob(TimestampedModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        DISPATCHING = "dispatching", "Dispatching"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        TIMED_OUT = "timed_out", "Timed out"

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="execution_jobs", on_delete=models.CASCADE)
    project = models.ForeignKey(CodingProject, related_name="execution_jobs", on_delete=models.CASCADE)
    source_file = models.ForeignKey(ProjectFile, related_name="execution_jobs", null=True, on_delete=models.SET_NULL)
    language = models.CharField(max_length=30)
    source_snapshot = models.TextField()
    stdin = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    idempotency_key = models.CharField(max_length=128)
    controller_job_id = models.CharField(max_length=160, blank=True, db_index=True)
    limits = models.JSONField(default=dict)
    stdout = models.TextField(blank=True)
    stderr = models.TextField(blank=True)
    exit_code = models.IntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=80, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    runtime_ms = models.PositiveIntegerField(null=True, blank=True)
    memory_bytes = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["requested_by", "idempotency_key"], name="unique_execution_idempotency_key")]
        indexes = [
            models.Index(fields=["requested_by", "status", "-created_at"]),
            models.Index(fields=["project", "-created_at"]),
        ]
