from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import CodingProject, ExecutionJob, ProjectFile, ProjectFileRevision
from .validation import ALLOWED_LANGUAGES, validate_content, validate_project_path


class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = ["id", "path", "content", "language", "version", "checksum", "size_bytes", "created_at", "updated_at"]
        read_only_fields = ["id", "version", "checksum", "size_bytes", "created_at", "updated_at"]

    def validate_path(self, value):
        return validate_project_path(value)

    def validate_content(self, value):
        return validate_content(value)

    def validate_language(self, value):
        if value not in ALLOWED_LANGUAGES:
            raise serializers.ValidationError("This language is not currently supported by the workspace.")
        return value


class CodingProjectListSerializer(serializers.ModelSerializer):
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = CodingProject
        fields = ["id", "name", "description", "primary_language", "status", "file_count", "created_at", "updated_at"]
        read_only_fields = ["id", "file_count", "created_at", "updated_at"]

    @extend_schema_field(serializers.IntegerField())
    def get_file_count(self, obj):
        return len(obj.files.all())


class CodingProjectDetailSerializer(CodingProjectListSerializer):
    files = ProjectFileSerializer(many=True, read_only=True)

    class Meta(CodingProjectListSerializer.Meta):
        fields = [*CodingProjectListSerializer.Meta.fields, "files"]


class CodingProjectCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    description = serializers.CharField(required=False, allow_blank=True)
    primary_language = serializers.ChoiceField(choices=sorted(ALLOWED_LANGUAGES - {"plaintext", "markdown", "json"}))
    include_starter = serializers.BooleanField(default=True)


class ProjectFileRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFileRevision
        fields = ["id", "version", "checksum", "created_at"]


class CodingCapabilitiesSerializer(serializers.Serializer):
    editor = serializers.BooleanField()
    autosave = serializers.BooleanField()
    version_history = serializers.BooleanField()
    project_download = serializers.BooleanField()
    execution = serializers.BooleanField()
    execution_message = serializers.CharField()
    languages = serializers.ListField(child=serializers.CharField())


class ExecutionJobCreateSerializer(serializers.Serializer):
    file_id = serializers.UUIDField()
    stdin = serializers.CharField(required=False, allow_blank=True, default="")


class ExecutionJobSerializer(serializers.ModelSerializer):
    file_path = serializers.CharField(source="source_file.path", allow_null=True, read_only=True)

    class Meta:
        model = ExecutionJob
        fields = [
            "id", "project_id", "file_path", "language", "status", "limits", "stdout", "stderr",
            "exit_code", "error_code", "started_at", "finished_at", "cancelled_at", "runtime_ms",
            "memory_bytes", "created_at", "updated_at",
        ]
