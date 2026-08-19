import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from core.models import SoftDeleteModel, TimestampedModel


def knowledge_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"knowledge/{instance.owner_id}/{uuid.uuid4().hex}{suffix}"


class KnowledgeFolder(TimestampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_folders", on_delete=models.CASCADE
    )
    parent = models.ForeignKey(
        "self", related_name="children", null=True, blank=True, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=7, default="#4F46E5")
    is_favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["owner", "parent", "name"])]


class KnowledgeTag(TimestampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_tags", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=60)
    color = models.CharField(max_length=7, default="#7C3AED")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="unique_knowledge_tag_per_user"
            )
        ]


class KnowledgeNote(SoftDeleteModel):
    class Context(models.TextChoices):
        GENERAL = "general", "General"
        SUBJECT = "subject", "Subject"
        TOPIC = "topic", "Topic"
        PROJECT = "project", "Project"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_notes", on_delete=models.CASCADE
    )
    folder = models.ForeignKey(
        KnowledgeFolder, related_name="notes", null=True, blank=True, on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=240)
    content = models.TextField(blank=True)
    content_format = models.CharField(max_length=20, default="markdown")
    tags = models.ManyToManyField(KnowledgeTag, related_name="notes", blank=True)
    context_type = models.CharField(
        max_length=20, choices=Context.choices, default=Context.GENERAL
    )
    context_label = models.CharField(max_length=160, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    current_version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "is_archived", "-updated_at"]),
            models.Index(fields=["owner", "folder", "-updated_at"]),
        ]


class KnowledgeNoteVersion(TimestampedModel):
    note = models.ForeignKey(
        KnowledgeNote, related_name="versions", on_delete=models.CASCADE
    )
    version = models.PositiveIntegerField()
    title = models.CharField(max_length=240)
    content = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_note_versions", on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["note", "version"], name="unique_knowledge_note_version"
            )
        ]


class KnowledgeDocument(SoftDeleteModel):
    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_documents", on_delete=models.CASCADE
    )
    folder = models.ForeignKey(
        KnowledgeFolder,
        related_name="documents",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tags = models.ManyToManyField(KnowledgeTag, related_name="documents", blank=True)
    title = models.CharField(max_length=240)
    file = models.FileField(upload_to=knowledge_upload_path, max_length=500)
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120)
    size_bytes = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=64, db_index=True)
    extracted_text = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PROCESSING, db_index=True
    )
    error_code = models.CharField(max_length=80, blank=True)
    page_count = models.PositiveIntegerField(default=0)
    is_favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "status", "-updated_at"]),
            models.Index(fields=["owner", "folder", "-updated_at"]),
        ]


class DocumentHighlight(TimestampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="document_highlights", on_delete=models.CASCADE
    )
    document = models.ForeignKey(
        KnowledgeDocument, related_name="highlights", on_delete=models.CASCADE
    )
    page_number = models.PositiveIntegerField(default=1)
    start_offset = models.PositiveIntegerField(null=True, blank=True)
    end_offset = models.PositiveIntegerField(null=True, blank=True)
    quote = models.TextField()
    annotation = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#FDE68A")

    class Meta:
        ordering = ["page_number", "created_at"]
        indexes = [models.Index(fields=["owner", "document", "page_number"])]


class CodeSnippet(SoftDeleteModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_snippets", on_delete=models.CASCADE
    )
    folder = models.ForeignKey(
        KnowledgeFolder,
        related_name="snippets",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tags = models.ManyToManyField(KnowledgeTag, related_name="snippets", blank=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=40)
    code = models.TextField()
    is_favorite = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["owner", "language", "-updated_at"])]


class KnowledgeChunk(TimestampedModel):
    class Source(models.TextChoices):
        NOTE = "note", "Note"
        DOCUMENT = "document", "Document"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="knowledge_chunks", on_delete=models.CASCADE
    )
    note = models.ForeignKey(
        KnowledgeNote,
        related_name="chunks",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    document = models.ForeignKey(
        KnowledgeDocument,
        related_name="chunks",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    source_type = models.CharField(max_length=20, choices=Source.choices)
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["source_type", "chunk_index"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(note__isnull=False, document__isnull=True)
                    | models.Q(note__isnull=True, document__isnull=False)
                ),
                name="knowledge_chunk_has_one_source",
            )
        ]
        indexes = [
            models.Index(fields=["owner", "source_type"]),
            models.Index(fields=["note", "chunk_index"]),
            models.Index(fields=["document", "chunk_index"]),
        ]


class KnowledgeAIInteraction(TimestampedModel):
    class Action(models.TextChoices):
        ASK = "ask", "Ask knowledge base"
        SUMMARY = "summary", "Summary"
        FLASHCARDS = "flashcards", "Flashcards"
        INTERVIEW = "interview", "Interview questions"
        REVISION = "revision", "Revision plan"
        EXPLAIN = "explain", "Explanation"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="knowledge_ai_interactions",
        on_delete=models.CASCADE,
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    model = models.CharField(max_length=120)
    source_ids = models.JSONField(default=list)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    succeeded = models.BooleanField(default=False)
    error_code = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "action", "-created_at"])]
