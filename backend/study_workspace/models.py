from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimestampedModel


class StudyResource(TimestampedModel):
    class Type(models.TextChoices):
        YOUTUBE = "youtube", "YouTube"

    topic = models.ForeignKey(
        "roadmaps.Topic",
        related_name="study_resources",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_study_resources",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=240)
    resource_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.YOUTUBE
    )
    external_url = models.URLField(max_length=1000)
    youtube_video_id = models.CharField(max_length=20, db_index=True)
    channel_name = models.CharField(max_length=180, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "youtube_video_id"],
                name="unique_user_youtube_video",
            )
        ]
        indexes = [models.Index(fields=["created_by", "display_order"])]


class VideoProgress(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="video_progress",
        on_delete=models.CASCADE,
    )
    resource = models.ForeignKey(
        StudyResource, related_name="progress_records", on_delete=models.CASCADE
    )
    last_position_seconds = models.PositiveIntegerField(default=0)
    unique_watched_seconds = models.PositiveIntegerField(default=0)
    completion_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    playback_speed = models.DecimalField(max_digits=3, decimal_places=2, default=1)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "resource"], name="unique_user_video_progress"
            )
        ]
        indexes = [models.Index(fields=["user", "-last_watched_at"])]


class WatchedInterval(TimestampedModel):
    video_progress = models.ForeignKey(
        VideoProgress, related_name="watched_intervals", on_delete=models.CASCADE
    )
    start_seconds = models.PositiveIntegerField()
    end_seconds = models.PositiveIntegerField()
    client_event_id = models.CharField(max_length=128)

    class Meta:
        ordering = ["start_seconds", "end_seconds"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_seconds__gt=models.F("start_seconds")),
                name="watched_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["video_progress", "client_event_id"],
                name="unique_progress_client_event",
            ),
        ]


class StudyNote(TimestampedModel):
    class Format(models.TextChoices):
        MARKDOWN = "markdown", "Markdown"
        TEXT = "text", "Plain text"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        AI = "ai", "AI generated"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="study_notes", on_delete=models.CASCADE
    )
    resource = models.ForeignKey(
        StudyResource, related_name="notes", on_delete=models.CASCADE
    )
    timestamp_seconds = models.PositiveIntegerField(default=0)
    range_end_seconds = models.PositiveIntegerField(null=True, blank=True)
    content = models.TextField()
    content_format = models.CharField(
        max_length=20, choices=Format.choices, default=Format.MARKDOWN
    )
    is_pinned = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    tags = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.MANUAL)

    class Meta:
        ordering = ["-is_pinned", "timestamp_seconds", "created_at"]
        indexes = [models.Index(fields=["user", "resource", "timestamp_seconds"])]


class VideoTranscript(TimestampedModel):
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual import"
        YOUTUBE_AUTHORIZED = "youtube_authorized", "Authorized YouTube captions"
        PROVIDER = "provider", "Transcript provider"

    resource = models.OneToOneField(
        StudyResource, related_name="transcript", on_delete=models.CASCADE
    )
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="imported_video_transcripts", on_delete=models.CASCADE
    )
    language = models.CharField(max_length=16, default="en")
    source = models.CharField(max_length=30, choices=Source.choices, default=Source.MANUAL)
    full_text = models.TextField()
    segments = models.JSONField(default=list, blank=True)
    checksum = models.CharField(max_length=64)


class AINoteGeneration(TimestampedModel):
    class Mode(models.TextChoices):
        FULL = "full", "Full video"
        RANGE = "range", "Timestamp range"

    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="ai_note_generations", on_delete=models.CASCADE
    )
    resource = models.ForeignKey(
        StudyResource, related_name="ai_note_generations", on_delete=models.CASCADE
    )
    note = models.OneToOneField(
        StudyNote, related_name="ai_generation", null=True, blank=True, on_delete=models.SET_NULL
    )
    mode = models.CharField(max_length=20, choices=Mode.choices)
    start_seconds = models.PositiveIntegerField(default=0)
    end_seconds = models.PositiveIntegerField(null=True, blank=True)
    provider = models.CharField(max_length=30, default="openai")
    model = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    error_code = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "resource", "-created_at"],
                name="study_ai_user_resource_idx",
            )
        ]


class StudyBookmark(TimestampedModel):
    class Type(models.TextChoices):
        IMPORTANT = "important", "Important"
        DIFFICULT = "difficult", "Difficult"
        REVIEW = "review_later", "Review later"
        EXAMPLE = "example", "Example"
        INTERVIEW = "interview_point", "Interview point"
        CUSTOM = "custom", "Custom"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="study_bookmarks",
        on_delete=models.CASCADE,
    )
    resource = models.ForeignKey(
        StudyResource, related_name="bookmarks", on_delete=models.CASCADE
    )
    timestamp_seconds = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    bookmark_type = models.CharField(
        max_length=30, choices=Type.choices, default=Type.IMPORTANT
    )

    class Meta:
        ordering = ["timestamp_seconds", "created_at"]
        indexes = [models.Index(fields=["user", "resource", "timestamp_seconds"])]


class StudySession(TimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        ENDED = "ended", "Ended"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="study_sessions",
        on_delete=models.CASCADE,
    )
    topic = models.ForeignKey(
        "roadmaps.Topic",
        related_name="study_sessions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    resource = models.ForeignKey(
        StudyResource,
        related_name="study_sessions",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    last_transition_at = models.DateTimeField()
    active_seconds = models.PositiveIntegerField(default=0)
    paused_seconds = models.PositiveIntegerField(default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    session_goal = models.CharField(max_length=240, blank=True)
    session_summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [models.Index(fields=["user", "status", "-started_at"])]


class TopicStudyProgress(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="topic_study_progress",
        on_delete=models.CASCADE,
    )
    topic = models.ForeignKey(
        "roadmaps.Topic",
        related_name="study_progress_records",
        on_delete=models.CASCADE,
    )
    completion_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    confidence_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    difficulty_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    personal_summary = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic"], name="unique_user_topic_study_progress"
            )
        ]
        indexes = [models.Index(fields=["user", "completed", "-updated_at"])]
