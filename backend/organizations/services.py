from django.db import transaction
from django.utils.text import slugify
from rest_framework.exceptions import ValidationError

from audit.services import record_audit_event
from .models import Organization, OrganizationMembership


@transaction.atomic
def create_organization(*, user, name, slug=None, request=None):
    resolved_slug = slugify(slug or name)
    if not resolved_slug:
        raise ValidationError({"slug": "A valid organization slug is required."})
    if Organization.objects.filter(slug=resolved_slug).exists():
        raise ValidationError({"slug": "This organization slug is already in use."})
    organization = Organization.objects.create(name=name.strip(), slug=resolved_slug, created_by=user)
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.ORG_ADMIN,
    )
    record_audit_event(action="organization.created", actor=user, organization=organization, request=request, target=organization)
    return organization

