from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from roadmaps.models import Roadmap


class GoalAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("goals@example.com", "A-strong-test-password-482!", full_name="Goal Owner")
        UserProfile.objects.create(user=self.user)
        UserPreference.objects.create(user=self.user)
        self.roadmap = Roadmap.objects.create(owner=self.user, title="Backend roadmap")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.user)}")

    def test_goal_crud_and_completion(self):
        created = self.client.post(reverse("goal-list"), {"title": "Complete roadmap", "category": "career", "priority": "high", "target_value": 10, "current_value": 2, "unit": "topics", "roadmap": str(self.roadmap.id)}, format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["data"]["progress_percentage"], 20)
        goal_id = created.data["data"]["id"]

        completed = self.client.patch(reverse("goal-detail", args=[goal_id]), {"status": "completed"}, format="json")
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(completed.data["data"]["current_value"], 10)
        self.assertIsNotNone(completed.data["data"]["completed_at"])

        deleted = self.client.delete(reverse("goal-detail", args=[goal_id]))
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get(reverse("goal-list")).data["data"], [])

    def test_goal_data_is_owner_scoped(self):
        outsider = User.objects.create_user("other-goals@example.com", "A-strong-test-password-482!", full_name="Other")
        UserProfile.objects.create(user=outsider)
        UserPreference.objects.create(user=outsider)
        foreign = Roadmap.objects.create(owner=outsider, title="Private")
        response = self.client.post(reverse("goal-list"), {"title": "Invalid link", "roadmap": str(foreign.id)}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_analytics_returns_real_shape(self):
        response = self.client.get(reverse("learning-analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["weekly_activity"]), 7)
        self.assertEqual(response.data["data"]["overview"]["active_roadmaps"], 1)
