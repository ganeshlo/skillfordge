from django.utils import timezone
from rest_framework import serializers

from .models import LearningGoal


class LearningGoalSerializer(serializers.ModelSerializer):
    roadmap_title = serializers.CharField(source="roadmap.title", read_only=True, allow_null=True)
    project_name = serializers.CharField(source="project.name", read_only=True, allow_null=True)
    progress_percentage = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = LearningGoal
        fields = [
            "id", "title", "description", "category", "status", "priority", "target_value",
            "current_value", "unit", "target_date", "completed_at", "roadmap", "roadmap_title",
            "project", "project_name", "progress_percentage", "is_overdue", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "completed_at", "progress_percentage", "is_overdue", "created_at", "updated_at"]

    def get_progress_percentage(self, obj):
        return min(100, round(obj.current_value / obj.target_value * 100)) if obj.target_value else 0

    def get_is_overdue(self, obj):
        return bool(obj.target_date and obj.target_date < timezone.localdate() and obj.status != LearningGoal.Status.COMPLETED)

    def validate_roadmap(self, value):
        request = self.context["request"]
        if value and (value.owner_id != request.user.id or value.deleted_at):
            raise serializers.ValidationError("Select one of your active roadmaps.")
        return value

    def validate_project(self, value):
        request = self.context["request"]
        if value and (value.owner_id != request.user.id or value.deleted_at):
            raise serializers.ValidationError("Select one of your active projects.")
        return value

    def validate(self, attrs):
        status = attrs.get("status", getattr(self.instance, "status", LearningGoal.Status.NOT_STARTED))
        target = attrs.get("target_value", getattr(self.instance, "target_value", 100))
        current = attrs.get("current_value", getattr(self.instance, "current_value", 0))
        if status == LearningGoal.Status.COMPLETED and current < target:
            attrs["current_value"] = target
        return attrs
