from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User, UserPreference, UserProfile
from study_workspace.models import (
    AINoteGeneration,
    StudyNote,
    StudyResource,
    StudySession,
    VideoTranscript,
    WatchedInterval,
)


def user(email):
    item = User.objects.create_user(
        email, "A-strong-test-password-482!", full_name="Learner"
    )
    UserProfile.objects.create(user=item)
    UserPreference.objects.create(user=item)
    return item


class StudyWorkspaceTests(APITestCase):
    def setUp(self):
        self.owner = user("study@example.com")
        self.other = user("other@example.com")
        self.resource = StudyResource.objects.create(
            created_by=self.owner,
            title="Lesson",
            external_url="https://youtu.be/dQw4w9WgXcQ",
            youtube_video_id="dQw4w9WgXcQ",
            duration_seconds=100,
        )

    def auth(self, account):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(account)}"
        )

    @patch("study_workspace.services.youtube_metadata", return_value={"title": "Fetched lesson", "channel_name": "Teacher"})
    def test_add_video_and_reject_non_youtube_url(self, _metadata):
        self.auth(self.owner)
        good = self.client.post(
            reverse("study-resource-list"),
            {
                "external_url": "https://youtube.com/watch?v=aqz-KE-bpKQ",
            },
            format="json",
        )
        bad = self.client.post(
            reverse("study-resource-list"),
            {"title": "Bad", "external_url": "https://example.com/video"},
            format="json",
        )
        self.assertEqual(good.status_code, 201)
        self.assertEqual(good.data["data"]["title"], "Fetched lesson")
        self.assertEqual(good.data["data"]["channel_name"], "Teacher")
        self.assertEqual(bad.status_code, 400)

    def test_progress_counts_unique_overlap_and_deduplicates_events(self):
        self.auth(self.owner)
        url = reverse("study-resource-progress", args=[self.resource.id])
        self.client.patch(
            url,
            {
                "current_position": 10,
                "duration_seconds": 100,
                "playback_speed": 1,
                "interval_start": 0,
                "interval_end": 10,
                "client_event_id": "event-one",
            },
            format="json",
        )
        result = self.client.patch(
            url,
            {
                "current_position": 15,
                "duration_seconds": 100,
                "playback_speed": 1,
                "interval_start": 8,
                "interval_end": 15,
                "client_event_id": "event-two",
            },
            format="json",
        )
        self.client.patch(
            url,
            {
                "current_position": 15,
                "duration_seconds": 100,
                "playback_speed": 1,
                "interval_start": 8,
                "interval_end": 15,
                "client_event_id": "event-two",
            },
            format="json",
        )
        self.assertEqual(result.data["data"]["unique_watched_seconds"], 15)
        self.assertEqual(WatchedInterval.objects.count(), 2)

    def test_timestamped_notes_are_private(self):
        self.auth(self.owner)
        created = self.client.post(
            reverse("study-note-list", args=[self.resource.id]),
            {
                "timestamp_seconds": 12,
                "content": "Important concept",
                "tags": ["react"],
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.auth(self.other)
        hidden = self.client.patch(
            reverse("study-note-detail", args=[created.data["data"]["id"]]),
            {"content": "Changed"},
            format="json",
        )
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(StudyNote.objects.get().content, "Important concept")

    def test_import_timestamped_transcript_and_generate_range_notes(self):
        self.auth(self.owner)
        imported = self.client.put(
            reverse("study-transcript", args=[self.resource.id]),
            {
                "language": "en",
                "content_format": "srt",
                "content": "1\n00:00:05,000 --> 00:00:15,000\nState stores changing data.\n\n2\n00:00:15,000 --> 00:00:25,000\nProps pass data to a component.",
            },
            format="json",
        )
        self.assertEqual(imported.status_code, 200)
        self.assertTrue(imported.data["data"]["has_timestamps"])
        self.assertEqual(VideoTranscript.objects.get().segments[0]["start"], 5.0)

        with patch(
            "study_workspace.ai_notes._request_notes",
            return_value=("# React data\n\n- State changes over time.", 120, 30),
        ):
            generated = self.client.post(
                reverse("study-ai-note-generate", args=[self.resource.id]),
                {"mode": "range", "start_seconds": 5, "end_seconds": 20},
                format="json",
            )

        self.assertEqual(generated.status_code, 201)
        self.assertEqual(generated.data["data"]["source"], "ai")
        self.assertEqual(generated.data["data"]["range_end_seconds"], 20)
        self.assertTrue(generated.data["data"]["is_pinned"])
        generation = AINoteGeneration.objects.get()
        self.assertEqual(generation.status, AINoteGeneration.Status.SUCCEEDED)
        self.assertEqual(generation.input_tokens, 120)

    def test_ai_notes_require_transcript_and_resource_ownership(self):
        self.auth(self.owner)
        missing = self.client.post(
            reverse("study-ai-note-generate", args=[self.resource.id]),
            {"mode": "full", "start_seconds": 0},
            format="json",
        )
        self.assertEqual(missing.status_code, 400)

        self.auth(self.other)
        hidden = self.client.put(
            reverse("study-transcript", args=[self.resource.id]),
            {"content_format": "plain", "content": "Private transcript"},
            format="json",
        )
        self.assertEqual(hidden.status_code, 404)

    def test_owner_can_download_note_as_pdf(self):
        note = StudyNote.objects.create(
            user=self.owner, resource=self.resource, timestamp_seconds=0,
            content="# Lesson notes\n\n- Important concept",
        )
        self.auth(self.owner)
        response = self.client.get(reverse("study-note-pdf", args=[note.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

        self.auth(self.other)
        hidden = self.client.get(reverse("study-note-pdf", args=[note.id]))
        self.assertEqual(hidden.status_code, 404)

    def test_seeking_to_end_does_not_complete(self):
        self.auth(self.owner)
        result = self.client.patch(
            reverse("study-resource-progress", args=[self.resource.id]),
            {"current_position": 99, "duration_seconds": 100, "playback_speed": 1},
            format="json",
        )
        self.assertFalse(result.data["data"]["completed"])

    def test_personal_library_does_not_expose_another_users_video(self):
        StudyResource.objects.create(
            created_by=self.other,
            title="Private lesson",
            external_url="https://youtu.be/aqz-KE-bpKQ",
            youtube_video_id="aqz-KE-bpKQ",
        )
        self.auth(self.owner)
        result = self.client.get(reverse("study-workspace"))
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data["data"]["resources"]), 1)
        self.assertEqual(result.data["data"]["resources"][0]["id"], str(self.resource.id))

    def test_study_session_lifecycle_and_activity(self):
        self.auth(self.owner)
        started = self.client.post(
            reverse("study-session-start"),
            {"resource_id": str(self.resource.id), "session_goal": "Learn intervals"},
            format="json",
        )
        self.assertEqual(started.status_code, 201)
        session_id = started.data["data"]["id"]
        paused = self.client.patch(
            reverse("study-session-action", args=[session_id, "pause"]), {}, format="json"
        )
        self.assertEqual(paused.data["data"]["status"], StudySession.Status.PAUSED)
        resumed = self.client.patch(
            reverse("study-session-action", args=[session_id, "resume"]), {}, format="json"
        )
        self.assertEqual(resumed.data["data"]["status"], StudySession.Status.ACTIVE)
        ended = self.client.patch(
            reverse("study-session-action", args=[session_id, "end"]), {}, format="json"
        )
        self.assertEqual(ended.data["data"]["status"], StudySession.Status.ENDED)
        workspace = self.client.get(reverse("study-workspace"))
        self.assertIn("today_activity", workspace.data["data"])
