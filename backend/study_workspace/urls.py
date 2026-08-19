from django.urls import path

from .views import (
    BookmarkDetailView,
    BookmarkListView,
    AINoteGenerateView,
    NoteDetailView,
    NoteListView,
    NotePdfView,
    ProgressView,
    ResourceDetailView,
    ResourceListView,
    SessionActionView,
    SessionStartView,
    TranscriptView,
    WorkspaceView,
)

urlpatterns = [
    path("study-workspace/", WorkspaceView.as_view(), name="study-workspace"),
    path("study-resources/", ResourceListView.as_view(), name="study-resource-list"),
    path("study-resources/<uuid:resource_id>/", ResourceDetailView.as_view(), name="study-resource-detail"),
    path("study-resources/<uuid:resource_id>/progress/", ProgressView.as_view(), name="study-resource-progress"),
    path("study-resources/<uuid:resource_id>/notes/", NoteListView.as_view(), name="study-note-list"),
    path("study-resources/<uuid:resource_id>/transcript/", TranscriptView.as_view(), name="study-transcript"),
    path("study-resources/<uuid:resource_id>/ai-notes/", AINoteGenerateView.as_view(), name="study-ai-note-generate"),
    path("study-notes/<uuid:note_id>/", NoteDetailView.as_view(), name="study-note-detail"),
    path("study-notes/<uuid:note_id>/pdf/", NotePdfView.as_view(), name="study-note-pdf"),
    path("study-resources/<uuid:resource_id>/bookmarks/", BookmarkListView.as_view(), name="study-bookmark-list"),
    path("study-bookmarks/<uuid:bookmark_id>/", BookmarkDetailView.as_view(), name="study-bookmark-detail"),
    path("study-sessions/start/", SessionStartView.as_view(), name="study-session-start"),
    path("study-sessions/<uuid:session_id>/<str:action>/", SessionActionView.as_view(), name="study-session-action"),
]
