from django.utils import timezone

from .models import Plan, Subscription


DEFAULT_FREE_PROJECT_LIMIT = 3


def effective_plan_for_user(*, user):
    """Return the user's current paid/free plan, falling back to Free."""
    subscription = (
        Subscription.objects.filter(
            user=user,
            status=Subscription.Status.ACTIVE,
            current_period_end__gt=timezone.now(),
            plan__is_active=True,
        )
        .select_related("plan")
        .order_by("-created_at")
        .first()
    )
    if subscription:
        return subscription.plan
    return Plan.objects.filter(code="free", is_active=True).first()


def coding_project_limit_for_user(*, user):
    plan = effective_plan_for_user(user=user)
    if plan is None or plan.code == "free":
        return (plan.limits if plan else {}).get("coding_projects", DEFAULT_FREE_PROJECT_LIMIT)
    return plan.limits.get("coding_projects")
