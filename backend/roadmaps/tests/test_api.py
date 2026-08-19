from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from organizations.models import Organization, OrganizationMembership
from roadmaps.models import Roadmap, TopicProgress


def user_with_profile(email):
    user = User.objects.create_user(email, "A-strong-test-password-482!", full_name=email.split("@")[0])
    UserProfile.objects.create(user=user)
    UserPreference.objects.create(user=user)
    return user


class RoadmapAPITests(APITestCase):
    def setUp(self):
        self.owner = user_with_profile("roadmap-owner@example.com")
        self.outsider = user_with_profile("roadmap-outsider@example.com")

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_owner_can_build_hierarchy_and_complete_topic(self):
        self.authenticate(self.owner)
        created = self.client.post(reverse("roadmap-list"), {
            "title": "Backend Engineer",
            "description": "A practical backend learning path",
            "career_goal": "Backend engineer",
            "visibility": "private",
        }, format="json")
        self.assertEqual(created.status_code, 201)
        roadmap_id = created.data["data"]["id"]

        phase = self.client.post(reverse("roadmap-phase-create", args=[roadmap_id]), {"title": "Foundations"}, format="json")
        module = self.client.post(reverse("roadmap-module-create", args=[phase.data["data"]["id"]]), {"title": "Python"}, format="json")
        topic = self.client.post(reverse("roadmap-topic-create", args=[module.data["data"]["id"]]), {"title": "Functions", "estimated_minutes": 45}, format="json")
        resource = self.client.post(reverse("roadmap-resource-create", args=[topic.data["data"]["id"]]), {"title": "Python documentation", "url": "https://docs.python.org/3/", "resource_type": "article"}, format="json")
        progress = self.client.post(reverse("roadmap-topic-progress", args=[topic.data["data"]["id"]]), {"status": "completed", "confidence": 4}, format="json")
        milestone = self.client.post(reverse("roadmap-milestone-create", args=[roadmap_id]), {"title": "Ship the API"}, format="json")
        milestone_done = self.client.patch(reverse("roadmap-milestone-detail", args=[milestone.data["data"]["id"]]), {"completed": True}, format="json")

        self.assertEqual([phase.status_code, module.status_code, topic.status_code, resource.status_code, progress.status_code, milestone.status_code, milestone_done.status_code], [201, 201, 201, 201, 200, 201, 200])
        detail = self.client.get(reverse("roadmap-detail", args=[roadmap_id]))
        self.assertTrue(detail.data["data"]["is_owner"])
        self.assertEqual(detail.data["data"]["topic_count"], 1)
        self.assertEqual(detail.data["data"]["progress_percentage"], 100)
        self.assertEqual(detail.data["data"]["phases"][0]["modules"][0]["topics"][0]["progress"]["confidence"], 4)
        self.assertIsNotNone(detail.data["data"]["milestones"][0]["completed_at"])
        self.assertEqual(TopicProgress.objects.filter(user=self.owner, status="completed").count(), 1)

    def test_private_roadmap_is_not_visible_cross_user(self):
        roadmap = Roadmap.objects.create(owner=self.owner, title="Private path")
        self.authenticate(self.outsider)
        listing = self.client.get(reverse("roadmap-list"))
        detail = self.client.get(reverse("roadmap-detail", args=[roadmap.id]))
        self.assertEqual(listing.data["data"], [])
        self.assertEqual(detail.status_code, 404)

    def test_active_organization_member_can_view_organization_roadmap(self):
        organization = Organization.objects.create(name="Learning Team", slug="learning-team", created_by=self.owner)
        OrganizationMembership.objects.create(organization=organization, user=self.owner, role="org_admin")
        OrganizationMembership.objects.create(organization=organization, user=self.outsider, role="member")
        roadmap = Roadmap.objects.create(
            owner=self.owner,
            organization=organization,
            title="Team backend path",
            visibility=Roadmap.Visibility.ORGANIZATION,
        )
        self.authenticate(self.outsider)
        response = self.client.get(reverse("roadmap-detail", args=[roadmap.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["organization_name"], "Learning Team")

    def test_outsider_cannot_create_roadmap_for_organization(self):
        organization = Organization.objects.create(name="Private Team", slug="private-team", created_by=self.owner)
        self.authenticate(self.outsider)
        response = self.client.post(reverse("roadmap-list"), {
            "title": "Unauthorized path",
            "visibility": "organization",
            "organization_id": str(organization.id),
        }, format="json")
        self.assertEqual(response.status_code, 403)
