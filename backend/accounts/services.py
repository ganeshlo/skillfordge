from django.db import transaction
from django.utils import timezone

from audit.services import record_audit_event
from .models import User, UserPreference, UserProfile


@transaction.atomic
def register_user(*, email, password, full_name, request=None):
    user = User.objects.create_user(email=email, password=password, full_name=full_name.strip())
    UserProfile.objects.create(user=user)
    UserPreference.objects.create(user=user)
    record_audit_event(action="account.registered", actor=user, request=request, target=user)
    return user


@transaction.atomic
def complete_onboarding(*, user, validated_data, request=None):
    profile = user.profile
    preference_fields = {"learning_style", "timezone"}
    for field, value in validated_data.items():
        if field not in preference_fields:
            setattr(profile, field, value)
    profile.onboarding_completed_at = timezone.now()
    profile.save()
    for field in preference_fields:
        if field in validated_data:
            setattr(user.preferences, field, validated_data[field])
    user.preferences.save()
    record_audit_event(action="account.onboarding_completed", actor=user, request=request, target=user)
    return profile

