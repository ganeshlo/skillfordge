from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import SoftDeleteModel


class LearningGoal(SoftDeleteModel):
    class Category(models.TextChoices):
        CAREER = "career", "Career"
        SKILL = "skill", "Skill"
        PROJECT = "project", "Project"
        CERTIFICATION = "certification", "Certification"
        HABIT = "habit", "Habit"

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        PAUSED = "paused", "Paused"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="learning_goals", on_delete=models.CASCADE)
    roadmap = models.ForeignKey("roadmaps.Roadmap", related_name="goals", null=True, blank=True, on_delete=models.SET_NULL)
    project = models.ForeignKey("coding.CodingProject", related_name="goals", null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=24, choices=Category.choices, default=Category.SKILL)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NOT_STARTED)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.MEDIUM)
    target_value = models.PositiveIntegerField(default=100, validators=[MinValueValidator(1)])
    current_value = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=40, default="percent")
    target_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "-priority", "target_date", "-updated_at"]
        indexes = [models.Index(fields=["owner", "status", "target_date"])]

