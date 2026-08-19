from django.conf import settings
from django.db import models

from core.models import SoftDeleteModel, TimestampedModel


class Organization(SoftDeleteModel):
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_organizations")
    private_notes_visible = models.BooleanField(default=False, help_text="Requires explicit user sharing before access is possible.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class OrganizationMembership(TimestampedModel):
    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        MENTOR = "mentor", "Mentor"
        INSTRUCTOR = "instructor", "Instructor"
        TEAM_LEAD = "team_lead", "Team lead"
        MANAGER = "manager", "Manager"
        LEARNING_ADMIN = "learning_admin", "Learning administrator"
        ORG_ADMIN = "org_admin", "Organization administrator"

    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    organization = models.ForeignKey(Organization, related_name="memberships", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="organization_memberships", on_delete=models.CASCADE)
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["organization", "user"], name="unique_organization_member")]
        indexes = [models.Index(fields=["organization", "status", "role"])]

