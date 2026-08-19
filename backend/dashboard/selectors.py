from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from audit.models import AuditLog
from organizations.models import OrganizationMembership
from roadmaps.models import Roadmap
from study_workspace.models import StudySession


ACTIVITY_LABELS = {
    "account.registered": "LearnOS account created",
    "account.onboarding_completed": "Learning profile completed",
    "account.password_reset_requested": "Password reset requested",
    "account.password_reset_completed": "Password updated",
    "organization.created": "Organization workspace created",
    "roadmap.created": "Learning roadmap created",
    "roadmap.deleted": "Learning roadmap deleted",
    "roadmap.topic_progress_updated": "Roadmap topic progress updated",
    "coding.project_created": "Coding project created",
    "coding.project_deleted": "Coding project deleted",
    "coding.file_created": "Project file created",
    "coding.file_deleted": "Project file deleted",
    "coding.execution_requested": "Secure code execution requested",
    "coding.execution_cancelled": "Code execution cancelled",
}

PROFILE_FIELDS = (
    "professional_role",
    "experience_level",
    "career_goal",
    "learning_goals",
    "current_skills",
    "target_skills",
    "preferred_languages",
    "onboarding_completed_at",
)


def _profile_completion(profile):
    completed = sum(bool(getattr(profile, field)) for field in PROFILE_FIELDS)
    return round(completed / len(PROFILE_FIELDS) * 100)


def _next_action(profile, roadmap):
    if not profile.onboarding_completed_at:
        return {
            "type": "onboarding",
            "title": "Finish your learning profile",
            "description": "Tell LearnOS about your goal, skills, and available study time.",
            "label": "Complete profile",
            "href": "/onboarding",
            "available": True,
        }
    if roadmap:
        return {
            "type": "continue_roadmap",
            "title": f"Continue {roadmap.title}",
            "description": "Review your roadmap structure and complete the next focused topic.",
            "label": "Open roadmap",
            "href": f"/roadmaps/{roadmap.id}",
            "available": True,
        }
    return {
        "type": "roadmap",
        "title": "Create your first learning roadmap",
        "description": f"Turn your {profile.career_goal or 'career'} goal into phases, topics, resources, and milestones.",
        "label": "Create roadmap",
        "href": "/roadmaps",
        "available": True,
    }


def get_dashboard(*, user):
    profile = user.profile
    active_roadmap = Roadmap.objects.filter(owner=user, deleted_at__isnull=True, status=Roadmap.Status.ACTIVE).order_by("-updated_at").first()
    memberships = list(
        OrganizationMembership.objects.filter(
            user=user,
            status=OrganizationMembership.Status.ACTIVE,
            organization__deleted_at__isnull=True,
        ).select_related("organization").order_by("organization__name")
    )
    activity = AuditLog.objects.filter(actor=user).only("id", "action", "created_at")[:8]
    today = timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    session_rows = StudySession.objects.filter(user=user, started_at__date__gte=week_start).annotate(day=TruncDate("started_at")).values("day").annotate(seconds=Sum("active_seconds"), sessions=Count("id"))
    session_days = {row["day"]: row for row in session_rows}
    weekly_activity = [{"date": week_start + timedelta(days=index), "minutes": round((session_days.get(week_start + timedelta(days=index), {}).get("seconds") or 0) / 60), "sessions": session_days.get(week_start + timedelta(days=index), {}).get("sessions", 0)} for index in range(7)]

    return {
        "overview": {
            "first_name": user.full_name.split()[0] if user.full_name.split() else "Learner",
            "full_name": user.full_name,
            "professional_role": profile.professional_role,
            "experience_level": profile.experience_level,
            "career_goal": profile.career_goal,
            "profile_completion": _profile_completion(profile),
            "onboarding_complete": bool(profile.onboarding_completed_at),
            "email_verified": bool(user.email_verified_at),
        },
        "targets": {
            "daily_minutes": profile.daily_minutes,
            "weekly_target_minutes": profile.weekly_target_minutes,
            "target_skills": profile.target_skills,
            "current_skills": profile.current_skills,
            "preferred_languages": profile.preferred_languages,
        },
        "organizations": [
            {
                "id": membership.organization_id,
                "name": membership.organization.name,
                "slug": membership.organization.slug,
                "role": membership.role,
            }
            for membership in memberships[:5]
        ],
        "organization_count": len(memberships),
        "recent_activity": [
            {
                "id": event.id,
                "action": event.action,
                "label": ACTIVITY_LABELS.get(event.action, "Workspace activity"),
                "created_at": event.created_at,
            }
            for event in activity
        ],
        "next_action": _next_action(profile, active_roadmap),
        "learning_activity": {
            "weekly_minutes": sum(item["minutes"] for item in weekly_activity),
            "weekly_target_minutes": profile.weekly_target_minutes,
            "days": weekly_activity,
        },
        "modules": [
            {"key": "identity", "label": "Learning profile", "description": "Goals, skills, preferences, and secure identity", "status": "ready", "href": "/onboarding"},
            {"key": "roadmaps", "label": "Roadmaps", "description": "Phases, modules, topics, resources, and milestones", "status": "ready", "href": "/roadmaps"},
            {"key": "study", "label": "Study workspace", "description": "Focused sessions, notes, timers, and resources", "status": "planned", "href": None},
            {"key": "coding", "label": "Coding workspace", "description": "Projects, files, Monaco editor, and version history", "status": "ready", "href": "/code"},
        ],
    }
