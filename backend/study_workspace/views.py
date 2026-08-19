from collections import defaultdict
from datetime import datetime, time

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.throttling import ScopedRateThrottle

from audit.services import record_audit_event
from core.responses import api_response

from .models import (
    StudyBookmark,
    StudyNote,
    StudyResource,
    StudySession,
    VideoTranscript,
    VideoProgress,
    WatchedInterval,
)
from .serializers import (
    BookmarkSerializer,
    AINoteGenerateSerializer,
    NoteSerializer,
    ProgressSerializer,
    ProgressUpdateSerializer,
    ResourceCreateSerializer,
    ResourceSerializer,
    ResourceUpdateSerializer,
    SessionSerializer,
    SessionStartSerializer,
    SessionUpdateSerializer,
    TranscriptImportSerializer,
    TranscriptSerializer,
)
from .ai_notes import generate_notes
from .pdf import note_pdf
from .services import add_resource, merge_intervals, save_progress
from .transcripts import checksum_for, parse_transcript


def resource_for(user, resource_id):
    item = StudyResource.objects.filter(id=resource_id, created_by=user).first()
    if not item:
        raise NotFound("Study video not found.")
    return item


def session_for(user, session_id):
    item = StudySession.objects.filter(id=session_id, user=user).first()
    if not item:
        raise NotFound("Study session not found.")
    return item


def local_day_bounds():
    today = timezone.localdate()
    zone = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(today, time.min), zone),
        timezone.make_aware(datetime.combine(today, time.max), zone),
    )


def today_activity(user):
    start, end = local_day_bounds()
    sessions = StudySession.objects.filter(user=user, started_at__range=(start, end))
    now = timezone.now()
    active_seconds = 0
    for item in sessions:
        active_seconds += item.active_seconds
        if item.status == StudySession.Status.ACTIVE:
            active_seconds += max(0, int((now - item.last_transition_at).total_seconds()))

    intervals = WatchedInterval.objects.filter(
        video_progress__user=user, created_at__range=(start, end)
    ).values_list(
        "video_progress__resource_id", "start_seconds", "end_seconds"
    )
    grouped = defaultdict(list)
    playback_seconds = 0
    for resource_id, interval_start, interval_end in intervals:
        playback_seconds += interval_end - interval_start
        grouped[resource_id].append((interval_start, interval_end))
    unique_seconds = sum(
        interval_end - interval_start
        for values in grouped.values()
        for interval_start, interval_end in merge_intervals(values)
    )
    progress_today = VideoProgress.objects.filter(
        user=user, last_watched_at__range=(start, end)
    )
    return {
        "active_study_seconds": active_seconds,
        "video_playback_seconds": playback_seconds,
        "unique_watched_seconds": unique_seconds,
        "videos_studied": progress_today.values("resource_id").distinct().count(),
        "videos_completed": VideoProgress.objects.filter(
            user=user, completed_at__range=(start, end)
        ).count(),
        "notes_created": StudyNote.objects.filter(
            user=user, created_at__range=(start, end)
        ).count(),
        "bookmarks_created": StudyBookmark.objects.filter(
            user=user, created_at__range=(start, end)
        ).count(),
    }


class WorkspaceView(GenericAPIView):
    serializer_class = ResourceSerializer

    def get(self, request):
        resources = list(
            StudyResource.objects.filter(created_by=request.user).select_related("transcript").prefetch_related(
                "progress_records__watched_intervals"
            )
        )
        requested = request.query_params.get("resource_id")
        current = next(
            (item for item in resources if str(item.id) == requested),
            resources[0] if resources else None,
        )
        active_session = StudySession.objects.filter(
            user=request.user,
            status__in=[StudySession.Status.ACTIVE, StudySession.Status.PAUSED],
        ).first()
        data = {
            "library": {"title": "My video library", "count": len(resources)},
            "resources": ResourceSerializer(
                resources, many=True, context={"user": request.user}
            ).data,
            "current_resource_id": str(current.id) if current else None,
            "notes": NoteSerializer(
                StudyNote.objects.filter(user=request.user, resource=current), many=True
            ).data
            if current
            else [],
            "bookmarks": BookmarkSerializer(
                StudyBookmark.objects.filter(user=request.user, resource=current),
                many=True,
            ).data
            if current
            else [],
            "today_activity": today_activity(request.user),
            "active_session": SessionSerializer(active_session).data
            if active_session
            else None,
            "ai_notes_available": bool(settings.OPENAI_API_KEY),
        }
        return api_response(data, request=request)


class ResourceListView(GenericAPIView):
    serializer_class = ResourceCreateSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            item = add_resource(request.user, **serializer.validated_data)
        except IntegrityError as exc:
            raise ValidationError({"external_url": "Video already added."}) from exc
        return api_response(
            ResourceSerializer(item, context={"user": request.user}).data,
            request=request,
            status=status.HTTP_201_CREATED,
        )


class ResourceDetailView(GenericAPIView):
    serializer_class = ResourceUpdateSerializer

    def patch(self, request, resource_id):
        serializer = self.get_serializer(
            resource_for(request.user, resource_id), data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_response(
            ResourceSerializer(serializer.instance, context={"user": request.user}).data,
            request=request,
        )

    def delete(self, request, resource_id):
        resource_for(request.user, resource_id).delete()
        return api_response({"deleted": True}, request=request)


class ProgressView(GenericAPIView):
    serializer_class = ProgressUpdateSerializer

    def patch(self, request, resource_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data
        progress = save_progress(
            request.user,
            resource_for(request.user, resource_id),
            value["current_position"],
            value["duration_seconds"],
            value["playback_speed"],
            value.get("interval_start"),
            value.get("interval_end"),
            value.get("client_event_id", ""),
        )
        return api_response(ProgressSerializer(progress).data, request=request)


def validate_timestamp(resource, value):
    if resource.duration_seconds and value > resource.duration_seconds + 2:
        raise ValidationError({"timestamp_seconds": "Timestamp exceeds video duration."})


class NoteListView(GenericAPIView):
    serializer_class = NoteSerializer

    def post(self, request, resource_id):
        resource = resource_for(request.user, resource_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validate_timestamp(resource, serializer.validated_data["timestamp_seconds"])
        item = StudyNote.objects.create(
            user=request.user, resource=resource, **serializer.validated_data
        )
        return api_response(
            self.get_serializer(item).data,
            request=request,
            status=status.HTTP_201_CREATED,
        )


class NoteDetailView(GenericAPIView):
    serializer_class = NoteSerializer

    def object(self, request, note_id):
        item = StudyNote.objects.filter(id=note_id, user=request.user).first()
        if not item:
            raise NotFound("Note not found.")
        return item

    def patch(self, request, note_id):
        item = self.object(request, note_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validate_timestamp(
            item.resource,
            serializer.validated_data.get("timestamp_seconds", item.timestamp_seconds),
        )
        serializer.save()
        return api_response(serializer.data, request=request)

    def delete(self, request, note_id):
        self.object(request, note_id).delete()
        return api_response({"deleted": True}, request=request)


class TranscriptView(GenericAPIView):
    serializer_class = TranscriptImportSerializer

    def get(self, request, resource_id):
        resource = resource_for(request.user, resource_id)
        transcript = VideoTranscript.objects.filter(resource=resource, imported_by=request.user).first()
        return api_response(TranscriptSerializer(transcript).data if transcript else None, request=request)

    def put(self, request, resource_id):
        resource = resource_for(request.user, resource_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        full_text, segments = parse_transcript(values["content"], values["content_format"])
        transcript, _ = VideoTranscript.objects.update_or_create(
            resource=resource,
            defaults={
                "imported_by": request.user,
                "language": values["language"].lower(),
                "source": VideoTranscript.Source.MANUAL,
                "full_text": full_text,
                "segments": segments,
                "checksum": checksum_for(full_text),
            },
        )
        record_audit_event(
            action="study.transcript_imported", actor=request.user, target=resource, request=request,
            metadata={"source": "manual", "segments": len(segments)},
        )
        return api_response(TranscriptSerializer(transcript).data, request=request)


class AINoteGenerateView(GenericAPIView):
    serializer_class = AINoteGenerateSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_notes"

    def post(self, request, resource_id):
        resource = resource_for(request.user, resource_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = generate_notes(
            user=request.user, resource=resource, request=request, **serializer.validated_data
        )
        return api_response(NoteSerializer(note).data, request=request, status=status.HTTP_201_CREATED)


class NotePdfView(NoteDetailView):
    def get(self, request, note_id):
        note = self.object(request, note_id)
        response = HttpResponse(note_pdf(note), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="learnos-note-{note.id}.pdf"'
        response["X-Content-Type-Options"] = "nosniff"
        return response


class BookmarkListView(GenericAPIView):
    serializer_class = BookmarkSerializer

    def post(self, request, resource_id):
        resource = resource_for(request.user, resource_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validate_timestamp(resource, serializer.validated_data["timestamp_seconds"])
        item = StudyBookmark.objects.create(
            user=request.user, resource=resource, **serializer.validated_data
        )
        return api_response(
            self.get_serializer(item).data,
            request=request,
            status=status.HTTP_201_CREATED,
        )


class BookmarkDetailView(GenericAPIView):
    serializer_class = BookmarkSerializer

    def object(self, request, bookmark_id):
        item = StudyBookmark.objects.filter(id=bookmark_id, user=request.user).first()
        if not item:
            raise NotFound("Bookmark not found.")
        return item

    def patch(self, request, bookmark_id):
        item = self.object(request, bookmark_id)
        serializer = self.get_serializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validate_timestamp(
            item.resource,
            serializer.validated_data.get("timestamp_seconds", item.timestamp_seconds),
        )
        serializer.save()
        return api_response(serializer.data, request=request)

    def delete(self, request, bookmark_id):
        self.object(request, bookmark_id).delete()
        return api_response({"deleted": True}, request=request)


def accrue_session(item, idle=False):
    now = timezone.now()
    elapsed = max(0, min(120, int((now - item.last_transition_at).total_seconds())))
    if item.status == StudySession.Status.ACTIVE:
        if idle:
            item.idle_seconds += elapsed
        else:
            item.active_seconds += elapsed
    elif item.status == StudySession.Status.PAUSED:
        item.paused_seconds += elapsed
    item.last_transition_at = now
    return now


class SessionStartView(GenericAPIView):
    serializer_class = SessionStartSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        existing = StudySession.objects.select_for_update().filter(
            user=request.user,
            status__in=[StudySession.Status.ACTIVE, StudySession.Status.PAUSED],
        ).first()
        if existing:
            raise ValidationError({"session": "End the current study session first."})
        resource_id = serializer.validated_data.get("resource_id")
        resource = resource_for(request.user, resource_id) if resource_id else None
        now = timezone.now()
        item = StudySession.objects.create(
            user=request.user,
            resource=resource,
            started_at=now,
            last_transition_at=now,
            session_goal=serializer.validated_data.get("session_goal", "").strip(),
        )
        return api_response(
            SessionSerializer(item).data, request=request, status=status.HTTP_201_CREATED
        )


class SessionActionView(GenericAPIView):
    serializer_class = SessionUpdateSerializer

    @transaction.atomic
    def patch(self, request, session_id, action):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = StudySession.objects.select_for_update().get(
            id=session_for(request.user, session_id).id
        )
        if item.status == StudySession.Status.ENDED:
            raise ValidationError({"session": "This study session has ended."})
        now = accrue_session(item, serializer.validated_data.get("idle", False))
        if action == "pause":
            item.status = StudySession.Status.PAUSED
        elif action == "resume":
            item.status = StudySession.Status.ACTIVE
        elif action == "end":
            item.status = StudySession.Status.ENDED
            item.ended_at = now
            item.session_summary = serializer.validated_data.get(
                "session_summary", item.session_summary
            )
        elif action != "heartbeat":
            raise NotFound("Unknown session action.")
        item.save()
        return api_response(SessionSerializer(item).data, request=request)
