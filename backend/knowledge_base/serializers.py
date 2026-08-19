from rest_framework import serializers

from .models import (
    CodeSnippet,
    DocumentHighlight,
    KnowledgeDocument,
    KnowledgeFolder,
    KnowledgeNote,
    KnowledgeNoteVersion,
    KnowledgeTag,
)
from .validation import validate_color


class FolderSerializer(serializers.ModelSerializer):
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeFolder
        fields = [
            "id", "parent_id", "name", "color", "is_favorite", "item_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "item_count", "created_at", "updated_at"]

    def validate_color(self, value):
        return validate_color(value)

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Folder name cannot be empty.")
        return value.strip()

    def get_item_count(self, obj):
        return getattr(obj, "item_count", 0)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeTag
        fields = ["id", "name", "color", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Tag name cannot be empty.")
        return value.strip().lower()

    def validate_color(self, value):
        return validate_color(value)


class NoteSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    folder_id = serializers.UUIDField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, write_only=True
    )

    class Meta:
        model = KnowledgeNote
        fields = [
            "id", "folder_id", "title", "content", "content_format", "tags", "tag_ids",
            "context_type", "context_label", "source_url", "is_favorite", "is_archived",
            "current_version", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "content_format", "current_version", "created_at", "updated_at"
        ]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Note title cannot be empty.")
        return value.strip()

    def validate_content(self, value):
        if len(value.encode("utf-8")) > 1_048_576:
            raise serializers.ValidationError("Note content cannot exceed 1 MB.")
        return value


class NoteVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNoteVersion
        fields = ["id", "version", "title", "content", "created_at"]


class DocumentSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    highlights_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = KnowledgeDocument
        fields = [
            "id", "folder_id", "title", "original_filename", "mime_type", "size_bytes",
            "status", "error_code", "page_count", "is_favorite", "tags",
            "highlights_count", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "original_filename", "mime_type", "size_bytes", "status", "error_code",
            "page_count", "tags", "highlights_count", "created_at", "updated_at",
        ]


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=240, required=False, allow_blank=True)
    folder_id = serializers.UUIDField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class HighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentHighlight
        fields = [
            "id", "page_number", "start_offset", "end_offset", "quote",
            "annotation", "color", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_quote(self, value):
        if not value.strip():
            raise serializers.ValidationError("Highlighted text cannot be empty.")
        return value.strip()

    def validate_color(self, value):
        return validate_color(value)

    def validate(self, attrs):
        start, end = attrs.get("start_offset"), attrs.get("end_offset")
        if start is not None and end is not None and end <= start:
            raise serializers.ValidationError(
                {"end_offset": "Highlight end must be after its start."}
            )
        return attrs


class SnippetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    folder_id = serializers.UUIDField(required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, write_only=True
    )

    class Meta:
        model = CodeSnippet
        fields = [
            "id", "folder_id", "title", "description", "language", "code",
            "is_favorite", "tags", "tag_ids", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Snippet title cannot be empty.")
        return value.strip()

    def validate_code(self, value):
        if not value.strip():
            raise serializers.ValidationError("Code cannot be empty.")
        if len(value.encode("utf-8")) > 512_000:
            raise serializers.ValidationError("Snippet cannot exceed 500 KB.")
        return value


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(min_length=2, max_length=500)
    limit = serializers.IntegerField(min_value=1, max_value=30, default=12)


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=2000)


class AIActionSerializer(serializers.Serializer):
    source_type = serializers.ChoiceField(choices=["note", "document"])
    source_id = serializers.UUIDField()
    action = serializers.ChoiceField(
        choices=["summary", "flashcards", "interview", "revision", "explain"]
    )
