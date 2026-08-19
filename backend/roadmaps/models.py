from django.conf import settings
from django.db import models

from core.models import SoftDeleteModel, TimestampedModel


class Roadmap(SoftDeleteModel):
    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        ORGANIZATION = "organization", "Organization"
        PUBLIC = "public", "Public"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ARCHIVED = "archived", "Archived"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="roadmaps", on_delete=models.CASCADE)
    organization = models.ForeignKey("organizations.Organization", related_name="roadmaps", null=True, blank=True, on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    career_goal = models.CharField(max_length=160, blank=True)
    visibility = models.CharField(max_length=20, choices=Visibility.choices, default=Visibility.PRIVATE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    target_deadline = models.DateField(null=True, blank=True)
    estimated_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["owner", "status", "-updated_at"]), models.Index(fields=["organization", "visibility"])]


class RoadmapPhase(TimestampedModel):
    roadmap = models.ForeignKey(Roadmap, related_name="phases", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [models.UniqueConstraint(fields=["roadmap", "position"], name="unique_phase_position")]


class RoadmapModule(TimestampedModel):
    phase = models.ForeignKey(RoadmapPhase, related_name="modules", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    estimated_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [models.UniqueConstraint(fields=["phase", "position"], name="unique_module_position")]


class Topic(TimestampedModel):
    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    module = models.ForeignKey(RoadmapModule, related_name="topics", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    objective = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.BEGINNER)
    position = models.PositiveSmallIntegerField(default=0)
    estimated_minutes = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["position", "created_at"]
        constraints = [models.UniqueConstraint(fields=["module", "position"], name="unique_topic_position")]


class Resource(TimestampedModel):
    class Type(models.TextChoices):
        LINK = "link", "Link"
        VIDEO = "video", "Video"
        ARTICLE = "article", "Article"
        DOCUMENT = "document", "Document"
        BOOK = "book", "Book"

    topic = models.ForeignKey(Topic, related_name="resources", on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    url = models.URLField(max_length=1000)
    resource_type = models.CharField(max_length=20, choices=Type.choices, default=Type.LINK)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "created_at"]


class Milestone(TimestampedModel):
    roadmap = models.ForeignKey(Roadmap, related_name="milestones", on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "due_date"]


class TopicProgress(TimestampedModel):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="topic_progress", on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name="progress_records", on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    confidence = models.PositiveSmallIntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_studied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "topic"], name="unique_user_topic_progress")]
        indexes = [models.Index(fields=["user", "status", "-updated_at"])]

