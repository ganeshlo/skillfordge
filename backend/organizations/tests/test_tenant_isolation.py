from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from organizations.models import Organization, OrganizationMembership


def create_user(email):
    user = User.objects.create_user(email, "A-strong-test-password-482!", full_name=email.split("@")[0])
    UserProfile.objects.create(user=user)
    UserPreference.objects.create(user=user)
    return user


class TenantIsolationTests(APITestCase):
    def setUp(self):
        self.owner = create_user("owner@example.com")
        self.outsider = create_user("outsider@example.com")
        self.organization = Organization.objects.create(name="Secure Org", slug="secure-org", created_by=self.owner)
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role=OrganizationMembership.Role.ORG_ADMIN,
        )

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_outsider_cannot_list_other_tenant(self):
        self.authenticate(self.outsider)
        response = self.client.get(reverse("organization-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    def test_outsider_cannot_view_members(self):
        self.authenticate(self.outsider)
        response = self.client.get(reverse("organization-members", args=[self.organization.id]))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_view_members(self):
        self.authenticate(self.owner)
        response = self.client.get(reverse("organization-members", args=[self.organization.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)

