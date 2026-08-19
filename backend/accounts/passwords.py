from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

from audit.services import record_audit_event
from .models import User


def request_password_reset(*, email, request=None):
    """Issue a single-use reset link without revealing whether the account exists."""
    user = User.objects.filter(email=email.lower(), is_active=True).first()
    if not user:
        make_password(None)
        return None

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
    send_mail(
        subject="Reset your LearnOS password",
        message=(
            f"Hello {user.full_name},\n\n"
            "Use the link below to reset your LearnOS password. "
            "If you did not request this, you can safely ignore this email.\n\n"
            f"{reset_url}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    record_audit_event(action="account.password_reset_requested", actor=user, request=request, target=user)
    return reset_url


def reset_password(*, uid, token, new_password, request=None):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id, is_active=True)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        raise ValidationError({"token": "This password reset link is invalid or expired."})

    if not default_token_generator.check_token(user, token):
        raise ValidationError({"token": "This password reset link is invalid or expired."})
    try:
        validate_password(new_password, user=user)
    except DjangoValidationError as exc:
        raise ValidationError({"new_password": list(exc.messages)})

    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])
    record_audit_event(action="account.password_reset_completed", actor=user, request=request, target=user)
    return user
