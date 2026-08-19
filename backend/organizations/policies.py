from .models import OrganizationMembership


ADMIN_ROLES = {
    OrganizationMembership.Role.LEARNING_ADMIN,
    OrganizationMembership.Role.ORG_ADMIN,
}


def active_membership(*, user, organization):
    return OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()

