import re
import json
from decimal import Decimal
from urllib.request import urlopen
from urllib.parse import parse_qs, urlparse
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from .models import StudyResource, TopicStudyProgress, VideoProgress, WatchedInterval


def youtube_id(url):
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    value = (
        parsed.path.strip("/").split("/")[0]
        if host == "youtu.be"
        else parse_qs(parsed.query).get("v", [""])[0]
        if host in {"youtube.com", "youtube-nocookie.com"} and parsed.path == "/watch"
        else parsed.path.strip("/").split("/")[1]
        if host in {"youtube.com", "youtube-nocookie.com"}
        and parsed.path.startswith(("/embed/", "/shorts/", "/live/"))
        else ""
    )
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        raise ValidationError({"external_url": "Use a valid YouTube or youtu.be URL."})
    return value


def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def youtube_metadata(video_id):
    """Fetch public display metadata without downloading video content."""
    url = (
        "https://www.youtube.com/oembed?format=json&url="
        f"https://www.youtube.com/watch?v={video_id}"
    )
    try:
        with urlopen(url, timeout=3) as response:  # noqa: S310 - host is fixed above
            payload = json.loads(response.read(32768))
        return {
            "title": str(payload.get("title", ""))[:240],
            "channel_name": str(payload.get("author_name", ""))[:180],
        }
    except (OSError, ValueError, TypeError):
        return {"title": "", "channel_name": ""}


@transaction.atomic
def add_resource(user, external_url, title="", channel_name="", topic=None):
    video_id = youtube_id(external_url)
    metadata = youtube_metadata(video_id) if not title.strip() or not channel_name.strip() else {}
    return StudyResource.objects.create(
        topic=topic,
        created_by=user,
        title=title.strip() or metadata.get("title") or "YouTube video",
        external_url=external_url,
        youtube_video_id=video_id,
        channel_name=channel_name.strip() or metadata.get("channel_name", ""),
        display_order=StudyResource.objects.filter(created_by=user).count(),
    )


@transaction.atomic
def save_progress(
    user, resource, position, duration, speed, start=None, end=None, event_id=""
):
    progress, _ = VideoProgress.objects.select_for_update().get_or_create(
        user=user, resource=resource
    )
    if duration and resource.duration_seconds != duration:
        resource.duration_seconds = duration
        resource.save(update_fields=["duration_seconds", "updated_at"])
    total = resource.duration_seconds
    if position < 0 or (total and position > total + 2):
        raise ValidationError({"current_position": "Invalid video position."})
    if start is not None and end is not None:
        if start < 0 or end <= start or (total and end > total + 2):
            raise ValidationError({"watched_interval": "Invalid watched interval."})
        if not event_id:
            raise ValidationError({"client_event_id": "Client event ID is required."})
        WatchedInterval.objects.get_or_create(
            video_progress=progress,
            client_event_id=event_id,
            defaults={"start_seconds": start, "end_seconds": end},
        )
    unique = sum(
        end_value - start_value
        for start_value, end_value in merge_intervals(
            progress.watched_intervals.values_list("start_seconds", "end_seconds")
        )
    )
    percentage = (
        Decimal("0")
        if not total
        else min(Decimal("100"), Decimal(unique * 100) / Decimal(total))
    )
    complete = bool(
        total and percentage >= Decimal(str(settings.STUDY_VIDEO_COMPLETION_PERCENT))
    )
    progress.last_position_seconds = position
    progress.playback_speed = speed
    progress.unique_watched_seconds = unique
    progress.completion_percentage = percentage.quantize(Decimal("0.01"))
    progress.completed = complete
    progress.last_watched_at = timezone.now()
    if complete and not progress.completed_at:
        progress.completed_at = timezone.now()
    progress.save()
    if resource.topic_id:
        topic_progress, _ = TopicStudyProgress.objects.get_or_create(
            user=user, topic=resource.topic
        )
        resource_count = resource.topic.study_resources.count()
        values = VideoProgress.objects.filter(
            user=user, resource__topic=resource.topic
        ).values_list("completion_percentage", flat=True)
        topic_progress.completion_percentage = (
            (sum(values, Decimal("0")) / Decimal(resource_count)).quantize(Decimal("0.01"))
            if resource_count
            else 0
        )
        topic_progress.save()
    return progress
