from decimal import Decimal
from rest_framework import serializers
from .models import (
    StudyBookmark,
    StudyNote,
    StudyResource,
    StudySession,
    TopicStudyProgress,
    VideoTranscript,
    VideoProgress,
    WatchedInterval,
)
from .services import youtube_id


class IntervalSerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchedInterval
        fields = ["id", "start_seconds", "end_seconds"]


class ProgressSerializer(serializers.ModelSerializer):
    watched_intervals = IntervalSerializer(many=True, read_only=True)

    class Meta:
        model = VideoProgress
        fields = [
            "id",
            "last_position_seconds",
            "unique_watched_seconds",
            "completion_percentage",
            "playback_speed",
            "completed",
            "completed_at",
            "last_watched_at",
            "watched_intervals",
            "updated_at",
        ]


class ResourceSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    transcript = serializers.SerializerMethodField()

    class Meta:
        model = StudyResource
        ref_name = "StudyWorkspaceResource"
        fields = [
            "id",
            "title",
            "external_url",
            "youtube_video_id",
            "channel_name",
            "duration_seconds",
            "display_order",
            "progress",
            "transcript",
        ]

    def get_progress(self, obj) -> dict | None:
        user = self.context["user"]
        item = (
            obj.progress_records.filter(user=user)
            .prefetch_related("watched_intervals")
            .first()
        )
        return ProgressSerializer(item).data if item else None

    def get_transcript(self, obj):
        try:
            transcript = obj.transcript
        except VideoTranscript.DoesNotExist:
            return {"available": False, "has_timestamps": False, "language": None}
        return {
            "available": True,
            "has_timestamps": bool(transcript.segments),
            "language": transcript.language,
        }


class ResourceCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=240, required=False, allow_blank=True)
    external_url = serializers.URLField(max_length=1000)
    channel_name = serializers.CharField(
        max_length=180, required=False, allow_blank=True
    )

    def validate_external_url(self, value):
        youtube_id(value)
        return value


class ResourceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyResource
        fields = ["title", "channel_name"]


class ProgressUpdateSerializer(serializers.Serializer):
    current_position = serializers.IntegerField(min_value=0)
    duration_seconds = serializers.IntegerField(min_value=0, default=0)
    playback_speed = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        min_value=Decimal("0.25"),
        max_value=Decimal("2"),
        default=Decimal("1"),
    )
    interval_start = serializers.IntegerField(min_value=0, required=False)
    interval_end = serializers.IntegerField(min_value=1, required=False)
    client_event_id = serializers.CharField(
        max_length=128, required=False, allow_blank=True
    )


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyNote
        fields = [
            "id",
            "timestamp_seconds",
            "range_end_seconds",
            "content",
            "content_format",
            "is_pinned",
            "is_important",
            "tags",
            "source",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "source", "created_at", "updated_at"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Note cannot be empty.")
        if len(value.encode()) > 51200:
            raise serializers.ValidationError("Note is too large.")
        return value.strip()

    def validate(self, attrs):
        start = attrs.get("timestamp_seconds", getattr(self.instance, "timestamp_seconds", 0))
        end = attrs.get("range_end_seconds", getattr(self.instance, "range_end_seconds", None))
        if end is not None and end <= start:
            raise serializers.ValidationError({"range_end_seconds": "Range end must be after its start."})
        return attrs


class TranscriptImportSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=500_000, trim_whitespace=False)
    content_format = serializers.ChoiceField(choices=["auto", "plain", "srt", "vtt"], default="auto")
    language = serializers.RegexField(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})?$", max_length=16, default="en")

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Transcript cannot be empty.")
        return value


class TranscriptSerializer(serializers.ModelSerializer):
    segment_count = serializers.SerializerMethodField()
    has_timestamps = serializers.SerializerMethodField()

    class Meta:
        model = VideoTranscript
        fields = ["language", "source", "segment_count", "has_timestamps", "updated_at"]

    def get_segment_count(self, obj):
        return len(obj.segments)

    def get_has_timestamps(self, obj):
        return bool(obj.segments)


class AINoteGenerateSerializer(serializers.Serializer):
    mode = serializers.ChoiceField(choices=["full", "range"])
    start_seconds = serializers.IntegerField(min_value=0, default=0)
    end_seconds = serializers.IntegerField(min_value=1, required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["mode"] == "range":
            end = attrs.get("end_seconds")
            if end is None:
                raise serializers.ValidationError({"end_seconds": "Range end is required."})
            if end <= attrs["start_seconds"]:
                raise serializers.ValidationError({"end_seconds": "Range end must be after its start."})
        return attrs


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyBookmark
        fields = [
            "id",
            "timestamp_seconds",
            "label",
            "description",
            "bookmark_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_label(self, value):
        if not value.strip():
            raise serializers.ValidationError("Bookmark label cannot be empty.")
        return value.strip()


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = [
            "id", "resource", "started_at", "ended_at", "last_transition_at",
            "active_seconds", "paused_seconds", "idle_seconds", "session_goal",
            "session_summary", "status", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "resource", "started_at", "ended_at", "last_transition_at",
            "active_seconds", "paused_seconds", "idle_seconds", "status",
            "created_at", "updated_at",
        ]


class SessionStartSerializer(serializers.Serializer):
    resource_id = serializers.UUIDField(required=False, allow_null=True)
    session_goal = serializers.CharField(max_length=240, required=False, allow_blank=True)


class SessionUpdateSerializer(serializers.Serializer):
    session_summary = serializers.CharField(required=False, allow_blank=True, max_length=5000)
    idle = serializers.BooleanField(required=False, default=False)


class TopicProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicStudyProgress
        fields = [
            "completion_percentage",
            "confidence_rating",
            "difficulty_rating",
            "personal_summary",
            "completed",
            "updated_at",
        ]
