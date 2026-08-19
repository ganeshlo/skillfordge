from django.urls import reverse
from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User
from audit.models import AuditLog


class AccountAPITests(APITestCase):
    def test_local_frontend_origin_is_allowed(self):
        response = self.client.get(reverse("health-live"), HTTP_ORIGIN="http://127.0.0.1:3000")
        self.assertEqual(response["Access-Control-Allow-Origin"], "http://127.0.0.1:3000")

    def test_registration_hashes_password_and_records_audit_event(self):
        response = self.client.post(reverse("auth-register"), {
            "email": "Learner@Example.com",
            "full_name": "Ada Learner",
            "password": "A-strong-test-password-482!",
        }, format="json")

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="learner@example.com")
        self.assertTrue(user.check_password("A-strong-test-password-482!"))
        self.assertNotEqual(user.password, "A-strong-test-password-482!")
        self.assertTrue(AuditLog.objects.filter(actor=user, action="account.registered").exists())
        self.assertIn("X-Request-ID", response)

    def test_authenticated_user_can_complete_onboarding(self):
        user = User.objects.create_user("user@example.com", "A-strong-test-password-482!", full_name="Test User")
        from accounts.models import UserPreference, UserProfile
        UserProfile.objects.create(user=user)
        UserPreference.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

        response = self.client.post(reverse("onboarding"), {
            "professional_role": "Developer",
            "experience_level": "intermediate",
            "career_goal": "AI engineer",
            "learning_goals": ["Build production AI systems"],
            "current_skills": ["Python"],
            "target_skills": ["Django", "RAG"],
            "preferred_languages": ["Python", "TypeScript"],
            "daily_minutes": 60,
            "weekly_target_minutes": 420,
            "learning_style": "project based",
            "timezone": "Asia/Kolkata",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        user.profile.refresh_from_db()
        user.preferences.refresh_from_db()
        self.assertIsNotNone(user.profile.onboarding_completed_at)
        self.assertEqual(user.preferences.timezone, "Asia/Kolkata")

    def test_login_places_refresh_token_in_httponly_cookie(self):
        user = User.objects.create_user("auth@example.com", "A-strong-test-password-482!", full_name="Auth User")
        response = self.client.post(reverse("auth-token"), {
            "email": user.email,
            "password": "A-strong-test-password-482!",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data["data"])
        self.assertIn("learnos_refresh", response.cookies)
        self.assertTrue(response.cookies["learnos_refresh"]["httponly"])

    def test_authenticated_user_can_edit_safe_profile_fields(self):
        user = User.objects.create_user("profile@example.com", "A-strong-test-password-482!", full_name="Old Name")
        from accounts.models import UserPreference, UserProfile
        UserProfile.objects.create(user=user)
        UserPreference.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

        response = self.client.patch(reverse("me"), {
            "full_name": "New Name",
            "professional_role": "Engineer",
            "experience_level": "advanced",
            "career_goal": "Platform engineer",
            "daily_minutes": 90,
            "weekly_target_minutes": 500,
            "theme": "dark",
        }, format="json")

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        user.profile.refresh_from_db()
        self.assertEqual(user.full_name, "New Name")
        self.assertEqual(user.profile.professional_role, "Engineer")
        self.assertEqual(user.profile.daily_minutes, 90)
        user.preferences.refresh_from_db()
        self.assertEqual(user.preferences.theme, "dark")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
    def test_password_reset_is_single_use_and_changes_login_password(self):
        user = User.objects.create_user("reset@example.com", "A-strong-old-password-482!", full_name="Reset User")
        forgot = self.client.post(reverse("auth-forgot-password"), {"email": user.email}, format="json")
        self.assertEqual(forgot.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        reset_url = forgot.data["data"]["debug_reset_url"]
        from urllib.parse import parse_qs, urlparse
        params = parse_qs(urlparse(reset_url).query)

        payload = {"uid": params["uid"][0], "token": params["token"][0], "new_password": "A-strong-new-password-593!"}
        reset = self.client.post(reverse("auth-reset-password"), payload, format="json")
        self.assertEqual(reset.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("A-strong-new-password-593!"))

        reused = self.client.post(reverse("auth-reset-password"), payload, format="json")
        self.assertEqual(reused.status_code, 400)
        self.assertTrue(AuditLog.objects.filter(actor=user, action="account.password_reset_completed").exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_forgot_password_does_not_reveal_unknown_account(self):
        response = self.client.post(reverse("auth-forgot-password"), {"email": "missing@example.com"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("debug_reset_url", response.data["data"])
        self.assertEqual(len(mail.outbox), 0)
