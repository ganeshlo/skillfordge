from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from audit.services import record_audit_event
from organizations.models import Organization, OrganizationMembership
from .models import Resource, Roadmap, RoadmapModule, RoadmapPhase, Topic, TopicProgress


def _assert_owner(user, roadmap):
    if roadmap.owner_id != user.id:
        raise PermissionDenied("Only the roadmap owner can change its structure.")


@transaction.atomic
def create_roadmap(*, user, request=None, organization_id=None, **data):
    organization = None
    if organization_id:
        organization = Organization.objects.filter(id=organization_id, deleted_at__isnull=True).first()
        if not organization or not OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            status=OrganizationMembership.Status.ACTIVE,
        ).exists():
            raise PermissionDenied("You are not an active member of this organization.")
    if data.get("visibility") == Roadmap.Visibility.ORGANIZATION and not organization:
        raise ValidationError({"organization_id": "Organization visibility requires an organization."})
    roadmap = Roadmap.objects.create(owner=user, organization=organization, **data)
    record_audit_event(action="roadmap.created", actor=user, organization=organization, target=roadmap, request=request)
    return roadmap


def _next_position(queryset):
    last = queryset.order_by("-position").values_list("position", flat=True).first()
    return (last + 1) if last is not None else 0


@transaction.atomic
def add_phase(*, user, roadmap, request=None, **data):
    _assert_owner(user, roadmap)
    data.setdefault("position", _next_position(roadmap.phases))
    try:
        phase = RoadmapPhase.objects.create(roadmap=roadmap, **data)
    except IntegrityError:
        raise ValidationError({"position": "That phase position is already occupied."})
    roadmap.save(update_fields=["updated_at"])
    return phase


@transaction.atomic
def add_module(*, user, phase, **data):
    _assert_owner(user, phase.roadmap)
    data.setdefault("position", _next_position(phase.modules))
    try:
        module = RoadmapModule.objects.create(phase=phase, **data)
    except IntegrityError:
        raise ValidationError({"position": "That module position is already occupied."})
    phase.roadmap.save(update_fields=["updated_at"])
    return module


@transaction.atomic
def add_topic(*, user, module, **data):
    _assert_owner(user, module.phase.roadmap)
    data.setdefault("position", _next_position(module.topics))
    try:
        topic = Topic.objects.create(module=module, **data)
    except IntegrityError:
        raise ValidationError({"position": "That topic position is already occupied."})
    module.phase.roadmap.save(update_fields=["updated_at"])
    return topic


@transaction.atomic
def add_resource(*, user, topic, **data):
    _assert_owner(user, topic.module.phase.roadmap)
    data.setdefault("position", _next_position(topic.resources))
    return Resource.objects.create(topic=topic, **data)


@transaction.atomic
def update_topic_progress(*, user, topic, status, confidence=None, request=None):
    roadmap = topic.module.phase.roadmap
    if not (
        roadmap.owner_id == user.id
        or roadmap.visibility == Roadmap.Visibility.PUBLIC
        or OrganizationMembership.objects.filter(user=user, organization=roadmap.organization, status=OrganizationMembership.Status.ACTIVE).exists()
    ):
        raise PermissionDenied("You cannot access this roadmap topic.")
    now = timezone.now()
    progress, _ = TopicProgress.objects.update_or_create(
        user=user,
        topic=topic,
        defaults={
            "status": status,
            "confidence": confidence,
            "last_studied_at": now,
            "completed_at": now if status == TopicProgress.Status.COMPLETED else None,
        },
    )
    record_audit_event(action="roadmap.topic_progress_updated", actor=user, organization=roadmap.organization, target=topic, request=request, metadata={"status": status})
    return progress
