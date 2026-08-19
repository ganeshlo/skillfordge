from django.db import IntegrityError
from django.db.models import Count, Q
from django.http import FileResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.throttling import ScopedRateThrottle

from core.responses import api_response

from .ai import answer_question, run_source_action
from .embeddings import embedding_available
from .models import (
    CodeSnippet,
    DocumentHighlight,
    KnowledgeDocument,
    KnowledgeFolder,
    KnowledgeNote,
    KnowledgeTag,
)
from .retrieval import search_knowledge
from .serializers import (
    AIActionSerializer,
    AskSerializer,
    DocumentSerializer,
    DocumentUploadSerializer,
    FolderSerializer,
    HighlightSerializer,
    NoteSerializer,
    NoteVersionSerializer,
    SearchSerializer,
    SnippetSerializer,
    TagSerializer,
)
from .services import (
    UNSET,
    create_document,
    create_folder,
    create_note,
    folder_for,
    owned_or_404,
    soft_delete,
    tags_for,
    update_note,
)
from .validation import validate_folder_parent


class KnowledgeDashboardView(GenericAPIView):
    serializer_class = NoteSerializer

    def get(self, request):
        notes = KnowledgeNote.objects.filter(
            owner=request.user, deleted_at__isnull=True, is_archived=False
        ).prefetch_related("tags")
        documents = KnowledgeDocument.objects.filter(
            owner=request.user, deleted_at__isnull=True
        ).prefetch_related("tags")
        snippets = CodeSnippet.objects.filter(
            owner=request.user, deleted_at__isnull=True
        ).prefetch_related("tags")
        folders = KnowledgeFolder.objects.filter(owner=request.user).annotate(
            item_count=Count("notes", distinct=True) + Count("documents", distinct=True) + Count("snippets", distinct=True)
        )
        data = {
            "counts": {
                "notes": notes.count(),
                "documents": documents.count(),
                "snippets": snippets.count(),
                "favorites": notes.filter(is_favorite=True).count()
                + documents.filter(is_favorite=True).count()
                + snippets.filter(is_favorite=True).count(),
            },
            "folders": FolderSerializer(folders, many=True).data,
            "tags": TagSerializer(
                KnowledgeTag.objects.filter(owner=request.user), many=True
            ).data,
            "recent_notes": NoteSerializer(notes[:8], many=True).data,
            "recent_documents": DocumentSerializer(documents[:8], many=True).data,
            "recent_snippets": SnippetSerializer(snippets[:8], many=True).data,
            "semantic_search_available": embedding_available(),
        }
        return api_response(data, request=request)


class FolderListView(GenericAPIView):
    serializer_class = FolderSerializer

    def get(self, request):
        items = KnowledgeFolder.objects.filter(owner=request.user).annotate(
            item_count=Count("notes", distinct=True) + Count("documents", distinct=True) + Count("snippets", distinct=True)
        )
        return api_response(self.get_serializer(items, many=True).data, request=request)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_folder(
            user=request.user, request=request, **serializer.validated_data
        )
        item.item_count = 0
        return api_response(
            self.get_serializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class FolderDetailView(GenericAPIView):
    serializer_class = FolderSerializer

    def object(self, request, folder_id):
        return owned_or_404(KnowledgeFolder, user=request.user, item_id=folder_id)

    def patch(self, request, folder_id):
        item = self.object(request, folder_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if "parent_id" in values:
            parent = folder_for(request.user, values.pop("parent_id"))
            validate_folder_parent(owner=request.user, parent=parent, instance=item)
            item.parent = parent
        for field, value in values.items():
            setattr(item, field, value)
        item.save()
        item.item_count = item.notes.count() + item.documents.count() + item.snippets.count()
        return api_response(self.get_serializer(item).data, request=request)

    def delete(self, request, folder_id):
        item = self.object(request, folder_id)
        if item.children.exists():
            raise ValidationError({"folder": "Move or delete child folders first."})
        item.notes.update(folder=None)
        item.documents.update(folder=None)
        item.snippets.update(folder=None)
        item.delete()
        return api_response({"deleted": True}, request=request)


class TagListView(GenericAPIView):
    serializer_class = TagSerializer

    def get(self, request):
        return api_response(
            self.get_serializer(KnowledgeTag.objects.filter(owner=request.user), many=True).data,
            request=request,
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = KnowledgeTag.objects.create(owner=request.user, **serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError({"name": "This tag already exists."}) from exc
        return api_response(
            self.get_serializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class TagDetailView(TagListView):
    def object(self, request, tag_id):
        return owned_or_404(KnowledgeTag, user=request.user, item_id=tag_id)

    def patch(self, request, tag_id):
        item = self.object(request, tag_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(item, field, value)
        try:
            item.save()
        except IntegrityError as exc:
            raise ValidationError({"name": "This tag already exists."}) from exc
        return api_response(self.get_serializer(item).data, request=request)

    def delete(self, request, tag_id):
        self.object(request, tag_id).delete()
        return api_response({"deleted": True}, request=request)


class NoteListView(GenericAPIView):
    serializer_class = NoteSerializer

    def queryset(self, request):
        items = KnowledgeNote.objects.filter(
            owner=request.user, deleted_at__isnull=True
        ).select_related("folder").prefetch_related("tags")
        query = request.query_params.get("q", "").strip()
        if query:
            items = items.filter(Q(title__icontains=query) | Q(content__icontains=query))
        if request.query_params.get("folder_id"):
            items = items.filter(folder_id=request.query_params["folder_id"])
        if request.query_params.get("favorite") == "true":
            items = items.filter(is_favorite=True)
        if request.query_params.get("archived") != "true":
            items = items.filter(is_archived=False)
        return items[:100]

    def get(self, request):
        return api_response(
            self.get_serializer(self.queryset(request), many=True).data, request=request
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_note(
            user=request.user, request=request, **serializer.validated_data
        )
        return api_response(
            self.get_serializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class NoteDetailView(GenericAPIView):
    serializer_class = NoteSerializer

    def object(self, request, note_id):
        return owned_or_404(KnowledgeNote, user=request.user, item_id=note_id)

    def get(self, request, note_id):
        return api_response(self.get_serializer(self.object(request, note_id)).data, request=request)

    def patch(self, request, note_id):
        item = self.object(request, note_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        item = update_note(
            user=request.user,
            note=item,
            request=request,
            folder_id=values.pop("folder_id", UNSET),
            tag_ids=values.pop("tag_ids", UNSET),
            **values,
        )
        return api_response(self.get_serializer(item).data, request=request)

    def delete(self, request, note_id):
        soft_delete(self.object(request, note_id), user=request.user, request=request)
        return api_response({"deleted": True}, request=request)


class NoteVersionListView(NoteDetailView):
    serializer_class = NoteVersionSerializer

    def get(self, request, note_id):
        note = self.object(request, note_id)
        return api_response(self.get_serializer(note.versions.all(), many=True).data, request=request)


class DocumentListView(GenericAPIView):
    serializer_class = DocumentUploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        items = KnowledgeDocument.objects.filter(
            owner=request.user, deleted_at__isnull=True
        ).annotate(highlights_count=Count("highlights")).prefetch_related("tags")[:100]
        return api_response(DocumentSerializer(items, many=True).data, request=request)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_document(
            user=request.user,
            upload=serializer.validated_data["file"],
            title=serializer.validated_data.get("title", ""),
            folder_id=serializer.validated_data.get("folder_id"),
            tag_ids=serializer.validated_data.get("tag_ids", []),
            request=request,
        )
        item.highlights_count = 0
        return api_response(
            DocumentSerializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class DocumentDetailView(GenericAPIView):
    serializer_class = DocumentSerializer

    def object(self, request, document_id):
        return owned_or_404(
            KnowledgeDocument, user=request.user, item_id=document_id
        )

    def get(self, request, document_id):
        item = self.object(request, document_id)
        item.highlights_count = item.highlights.count()
        return api_response(self.get_serializer(item).data, request=request)

    def patch(self, request, document_id):
        item = self.object(request, document_id)
        values = request.data
        if "folder_id" in values:
            item.folder = folder_for(request.user, values.get("folder_id"))
        if "title" in values:
            item.title = str(values["title"]).strip()
        if "is_favorite" in values:
            item.is_favorite = bool(values["is_favorite"])
        if "tag_ids" in values:
            item.tags.set(tags_for(request.user, values["tag_ids"]))
        item.save()
        item.highlights_count = item.highlights.count()
        return api_response(self.get_serializer(item).data, request=request)

    def delete(self, request, document_id):
        soft_delete(self.object(request, document_id), user=request.user, request=request)
        return api_response({"deleted": True}, request=request)


class DocumentContentView(DocumentDetailView):
    def get(self, request, document_id):
        item = self.object(request, document_id)
        preview = request.query_params.get("preview") == "true"
        inline_types = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
        response = FileResponse(
            item.file.open("rb"),
            content_type=item.mime_type,
            as_attachment=not (preview and item.mime_type in inline_types),
            filename=item.original_filename,
        )
        response["X-Content-Type-Options"] = "nosniff"
        response["Cache-Control"] = "private, no-store"
        return response


class DocumentTextView(DocumentDetailView):
    def get(self, request, document_id):
        item = self.object(request, document_id)
        return api_response(
            {
                "text": item.extracted_text,
                "status": item.status,
                "page_count": item.page_count,
            },
            request=request,
        )


class HighlightListView(DocumentDetailView):
    serializer_class = HighlightSerializer

    def get(self, request, document_id):
        document = self.object(request, document_id)
        return api_response(self.get_serializer(document.highlights.all(), many=True).data, request=request)

    def post(self, request, document_id):
        document = self.object(request, document_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = DocumentHighlight.objects.create(
            owner=request.user, document=document, **serializer.validated_data
        )
        return api_response(
            self.get_serializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class HighlightDetailView(GenericAPIView):
    serializer_class = HighlightSerializer

    def object(self, request, highlight_id):
        return owned_or_404(
            DocumentHighlight, user=request.user, item_id=highlight_id
        )

    def patch(self, request, highlight_id):
        item = self.object(request, highlight_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(serializer.data, request=request)

    def delete(self, request, highlight_id):
        self.object(request, highlight_id).delete()
        return api_response({"deleted": True}, request=request)


class SnippetListView(GenericAPIView):
    serializer_class = SnippetSerializer

    def queryset(self, request):
        items = CodeSnippet.objects.filter(
            owner=request.user, deleted_at__isnull=True
        ).prefetch_related("tags")
        if request.query_params.get("language"):
            items = items.filter(language=request.query_params["language"])
        return items[:100]

    def get(self, request):
        return api_response(self.get_serializer(self.queryset(request), many=True).data, request=request)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        folder_id = values.pop("folder_id", None)
        tag_ids = values.pop("tag_ids", [])
        item = CodeSnippet.objects.create(
            owner=request.user,
            folder=folder_for(request.user, folder_id),
            **values,
        )
        item.tags.set(tags_for(request.user, tag_ids))
        return api_response(
            self.get_serializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class SnippetDetailView(SnippetListView):
    def object(self, request, snippet_id):
        return owned_or_404(CodeSnippet, user=request.user, item_id=snippet_id)

    def patch(self, request, snippet_id):
        item = self.object(request, snippet_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if "folder_id" in values:
            item.folder = folder_for(request.user, values.pop("folder_id"))
        tag_ids = values.pop("tag_ids", None)
        for field, value in values.items():
            setattr(item, field, value)
        item.save()
        if tag_ids is not None:
            item.tags.set(tags_for(request.user, tag_ids))
        return api_response(self.get_serializer(item).data, request=request)

    def delete(self, request, snippet_id):
        soft_delete(self.object(request, snippet_id), user=request.user, request=request)
        return api_response({"deleted": True}, request=request)


class SearchView(GenericAPIView):
    serializer_class = SearchSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            search_knowledge(user=request.user, **serializer.validated_data),
            request=request,
        )


class AskView(GenericAPIView):
    serializer_class = AskSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "knowledge_ai"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            answer_question(
                user=request.user,
                question=serializer.validated_data["question"],
                request=request,
            ),
            request=request,
        )


class AIActionView(GenericAPIView):
    serializer_class = AIActionSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "knowledge_ai"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return api_response(
            run_source_action(
                user=request.user, request=request, **serializer.validated_data
            ),
            request=request,
        )
