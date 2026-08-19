from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from audit.models import AuditLog


class DashboardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("dashboard@example.com", "A-strong-test-password-482!", full_name="Dashboard User")
        self.profile = UserProfile.objects.create(
            user=self.user,
            professional_role="Developer",
            experience_level="intermediate",
            career_goal="Backend engineer",
            target_skills=["Django", "PostgreSQL"],
            current_skills=["Python"],
            preferred_languages=["Python"],
            daily_minutes=60,
            weekly_target_minutes=420,
        )
        UserPreference.objects.create(user=self.user)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.user)}")

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 401)

    def test_dashboard_returns_real_profile_targets_and_request_id(self):
        self.authenticate()
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["overview"]["career_goal"], "Backend engineer")
        self.assertEqual(response.data["data"]["targets"]["weekly_target_minutes"], 420)
        self.assertEqual(response.data["data"]["targets"]["target_skills"], ["Django", "PostgreSQL"])
        self.assertEqual(response.data["data"]["next_action"]["type"], "onboarding")
        self.assertEqual(response.data["request_id"], response["X-Request-ID"])

    def test_recent_activity_is_scoped_to_current_user(self):
        outsider = User.objects.create_user("outsider-dashboard@example.com", "A-strong-test-password-482!", full_name="Outsider")
        own = AuditLog.objects.create(actor=self.user, action="account.registered")
        AuditLog.objects.create(actor=outsider, action="account.password_reset_completed")
        self.authenticate()

        response = self.client.get(reverse("dashboard"))
        activity_ids = [item["id"] for item in response.data["data"]["recent_activity"]]
        self.assertEqual(activity_ids, [str(own.id)])

