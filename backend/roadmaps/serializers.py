from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    Milestone,
    Resource,
    Roadmap,
    RoadmapModule,
    RoadmapPhase,
    Topic,
    TopicProgress,
)


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ["id", "title", "url", "resource_type", "position"]
        read_only_fields = ["id"]


class TopicProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicProgress
        fields = ["status", "confidence", "completed_at", "last_studied_at"]
        read_only_fields = ["completed_at", "last_studied_at"]


class TopicSerializer(serializers.ModelSerializer):
    resources = ResourceSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ["id", "title", "objective", "difficulty", "position", "estimated_minutes", "progress", "resources"]
        read_only_fields = ["id", "progress", "resources"]
        extra_kwargs = {"position": {"required": False}}

    @extend_schema_field(TopicProgressSerializer(allow_null=True))
    def get_progress(self, obj):
        request = self.context.get("request")
        record = next((item for item in obj.progress_records.all() if request and item.user_id == request.user.id), None)
        return TopicProgressSerializer(record).data if record else None


class RoadmapModuleSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)

    class Meta:
        model = RoadmapModule
        fields = ["id", "title", "description", "position", "estimated_minutes", "topics"]
        read_only_fields = ["id", "topics"]
        extra_kwargs = {"position": {"required": False}}


class RoadmapPhaseSerializer(serializers.ModelSerializer):
    modules = RoadmapModuleSerializer(many=True, read_only=True)

    class Meta:
        model = RoadmapPhase
        fields = ["id", "title", "description", "position", "modules"]
        read_only_fields = ["id", "modules"]
        extra_kwargs = {"position": {"required": False}}


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = ["id", "title", "due_date", "completed_at", "position"]
        read_only_fields = ["id", "completed_at"]
        extra_kwargs = {"position": {"required": False}}


class RoadmapListSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    organization_name = serializers.CharField(source="organization.name", allow_null=True, read_only=True)
    topic_count = serializers.IntegerField(read_only=True, default=0)
    completed_topic_count = serializers.IntegerField(read_only=True, default=0)
    progress_percentage = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Roadmap
        fields = [
            "id", "title", "description", "career_goal", "visibility", "status", "target_deadline",
            "estimated_minutes", "owner_name", "organization_name", "topic_count", "completed_topic_count",
            "progress_percentage", "is_owner", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner_name", "organization_name", "topic_count", "completed_topic_count", "progress_percentage", "is_owner", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_progress_percentage(self, obj):
        total = getattr(obj, "topic_count", 0)
        return round(getattr(obj, "completed_topic_count", 0) / total * 100) if total else 0

    @extend_schema_field(serializers.BooleanField())
    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.id == obj.owner_id)


class RoadmapDetailSerializer(RoadmapListSerializer):
    phases = RoadmapPhaseSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)

    class Meta(RoadmapListSerializer.Meta):
        fields = [*RoadmapListSerializer.Meta.fields, "phases", "milestones"]


class RoadmapCreateSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Roadmap
        fields = ["title", "description", "career_goal", "visibility", "status", "target_deadline", "estimated_minutes", "organization_id"]


class TopicProgressUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=TopicProgress.Status.choices)
    confidence = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
