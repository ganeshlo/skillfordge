from django.db.models import Count, Q

from organizations.models import OrganizationMembership
from .models import Roadmap


def visible_roadmaps(*, user):
    organization_ids = OrganizationMembership.objects.filter(
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    ).values_list("organization_id", flat=True)
    return Roadmap.objects.filter(deleted_at__isnull=True).filter(
        Q(owner=user)
        | Q(visibility=Roadmap.Visibility.PUBLIC)
        | Q(visibility=Roadmap.Visibility.ORGANIZATION, organization_id__in=organization_ids)
    ).select_related("owner", "organization").annotate(
        topic_count=Count("phases__modules__topics", distinct=True),
        completed_topic_count=Count(
            "phases__modules__topics__progress_records",
            filter=Q(
                phases__modules__topics__progress_records__user=user,
                phases__modules__topics__progress_records__status="completed",
            ),
            distinct=True,
        ),
    ).distinct()


def roadmap_detail(*, user, roadmap_id):
    return visible_roadmaps(user=user).prefetch_related(
        "phases__modules__topics__resources",
        "phases__modules__topics__progress_records",
        "milestones",
    ).filter(id=roadmap_id).first()

