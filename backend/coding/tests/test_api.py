from django.urls import reverse
from django.test import override_settings
from django.utils import timezone
from unittest.mock import patch
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from billing.models import Plan
from billing.services import activate_subscription
from coding.models import CodingProject, ExecutionJob, ProjectFile, ProjectFileRevision
from coding.services import create_file
from coding.validation import MAX_FILE_BYTES


def create_user(email):
    user = User.objects.create_user(email, "A-strong-test-password-482!", full_name=email.split("@")[0])
    UserProfile.objects.create(user=user)
    UserPreference.objects.create(user=user)
    return user


class CodingWorkspaceAPITests(APITestCase):
    def setUp(self):
        self.owner = create_user("code-owner@example.com")
        self.outsider = create_user("code-outsider@example.com")

    def authenticate(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

    def test_create_project_with_starter_file(self):
        self.authenticate(self.owner)
        response = self.client.post(reverse("coding-project-list"), {
            "name": "Python Practice",
            "description": "Algorithm exercises",
            "primary_language": "python",
            "include_starter": True,
        }, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["files"][0]["path"], "main.py")
        self.assertIn("Hello from LearnOS", response.data["data"]["files"][0]["content"])
        self.assertEqual(ProjectFileRevision.objects.count(), 1)

    def test_all_runnable_languages_have_starter_files(self):
        pro, _ = Plan.objects.update_or_create(
            code="pro",
            defaults={"name": "Pro", "amount_minor": 100, "duration_days": 30, "limits": {"coding_projects": None}},
        )
        activate_subscription(user=self.owner, plan=pro)
        self.authenticate(self.owner)
        for language in ["typescript", "java", "c", "cpp", "go", "rust", "php", "ruby", "kotlin", "sql"]:
            response = self.client.post(reverse("coding-project-list"), {
                "name": f"{language} starter", "primary_language": language, "include_starter": True,
            }, format="json")
            self.assertEqual(response.status_code, 201, language)
            self.assertEqual(response.data["data"]["files"][0]["language"], language)

    def test_free_plan_is_limited_to_three_active_projects(self):
        Plan.objects.update_or_create(
            code="free",
            defaults={"name": "Free", "amount_minor": 0, "duration_days": 32700, "limits": {"coding_projects": 3}},
        )
        self.authenticate(self.owner)
        for number in range(3):
            response = self.client.post(reverse("coding-project-list"), {
                "name": f"Free project {number + 1}", "primary_language": "python", "include_starter": False,
            }, format="json")
            self.assertEqual(response.status_code, 201)

        blocked = self.client.post(reverse("coding-project-list"), {
            "name": "Fourth project", "primary_language": "python", "include_starter": False,
        }, format="json")

        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(blocked.data["error"]["code"], "coding_project_limit_exceeded")
        self.assertEqual(CodingProject.objects.filter(owner=self.owner, deleted_at__isnull=True).count(), 3)

    def test_deleted_project_releases_a_free_plan_slot(self):
        Plan.objects.update_or_create(
            code="free",
            defaults={"name": "Free", "amount_minor": 0, "duration_days": 32700, "limits": {"coding_projects": 3}},
        )
        projects = [CodingProject.objects.create(owner=self.owner, name=f"Project {number}") for number in range(3)]
        projects[0].deleted_at = timezone.now()
        projects[0].save(update_fields=["deleted_at", "updated_at"])
        self.authenticate(self.owner)

        response = self.client.post(reverse("coding-project-list"), {
            "name": "Replacement project", "primary_language": "python", "include_starter": False,
        }, format="json")

        self.assertEqual(response.status_code, 201)

    def test_autosave_creates_immutable_revision(self):
        self.authenticate(self.owner)
        project = CodingProject.objects.create(owner=self.owner, name="Versioned")
        created = self.client.post(reverse("coding-file-create", args=[project.id]), {
            "path": "src/main.py", "content": "print('one')\n", "language": "python",
        }, format="json")
        file_id = created.data["data"]["id"]
        updated = self.client.patch(reverse("coding-file-detail", args=[file_id]), {"content": "print('two')\n"}, format="json")

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["data"]["version"], 2)
        self.assertEqual(ProjectFileRevision.objects.filter(file_id=file_id).count(), 2)
        self.assertNotEqual(created.data["data"]["checksum"], updated.data["data"]["checksum"])

    def test_path_traversal_and_oversized_files_are_rejected(self):
        self.authenticate(self.owner)
        project = CodingProject.objects.create(owner=self.owner, name="Secure files")
        traversal = self.client.post(reverse("coding-file-create", args=[project.id]), {
            "path": "../../secrets.txt", "content": "nope", "language": "plaintext",
        }, format="json")
        oversized = self.client.post(reverse("coding-file-create", args=[project.id]), {
            "path": "large.txt", "content": "x" * (MAX_FILE_BYTES + 1), "language": "plaintext",
        }, format="json")
        self.assertEqual(traversal.status_code, 400)
        self.assertEqual(oversized.status_code, 400)
        self.assertEqual(ProjectFile.objects.count(), 0)

    def test_project_and_file_are_isolated_from_other_users(self):
        project = CodingProject.objects.create(owner=self.owner, name="Private code")
        self.authenticate(self.outsider)
        detail = self.client.get(reverse("coding-project-detail", args=[project.id]))
        create_file = self.client.post(reverse("coding-file-create", args=[project.id]), {
            "path": "stolen.py", "content": "", "language": "python",
        }, format="json")
        self.assertEqual(detail.status_code, 404)
        self.assertEqual(create_file.status_code, 404)

    @override_settings(EXECUTION_ENABLED=False)
    def test_capabilities_never_claim_execution_on_django(self):
        self.authenticate(self.owner)
        response = self.client.get(reverse("coding-capabilities"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["editor"])
        self.assertFalse(response.data["data"]["execution"])
        self.assertIn("isolated runner", response.data["data"]["execution_message"])

    def test_execution_cors_preflight_allows_idempotency_header(self):
        response = self.client.options(
            reverse("coding-execution-list"),
            HTTP_ORIGIN="http://localhost:3000",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization,content-type,idempotency-key",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("idempotency-key", response.headers["Access-Control-Allow-Headers"].lower())

    @override_settings(EXECUTION_ENABLED=False)
    def test_execution_fails_closed_without_controller(self):
        self.authenticate(self.owner)
        project = CodingProject.objects.create(owner=self.owner, name="Fail closed")
        file = create_file(user=self.owner, project=project, path="main.py", content="print(1)", language="python")
        response = self.client.post(
            reverse("coding-execution-list"),
            {"file_id": str(file.id), "stdin": ""},
            format="json",
            HTTP_IDEMPOTENCY_KEY="execution-unavailable-1",
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(ExecutionJob.objects.count(), 0)

    @override_settings(
        EXECUTION_ENABLED=True,
        EXECUTION_CONTROLLER_URL="https://controller.internal",
        EXECUTION_CONTROLLER_SECRET="test-controller-secret",
    )
    @patch("coding.views.dispatch_execution_job.delay")
    def test_execution_job_is_idempotent_and_dispatches_after_commit(self, dispatch):
        self.authenticate(self.owner)
        project = CodingProject.objects.create(owner=self.owner, name="Runnable")
        file = create_file(user=self.owner, project=project, path="main.py", content="print(1)", language="python")
        payload = {"file_id": str(file.id), "stdin": "input"}
        with self.captureOnCommitCallbacks(execute=True):
            first = self.client.post(reverse("coding-execution-list"), payload, format="json", HTTP_IDEMPOTENCY_KEY="same-execution-key")
        second = self.client.post(reverse("coding-execution-list"), payload, format="json", HTTP_IDEMPOTENCY_KEY="same-execution-key")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.data["data"]["id"], second.data["data"]["id"])
        self.assertEqual(ExecutionJob.objects.count(), 1)
        dispatch.assert_called_once()

    @override_settings(EXECUTION_ENABLED=True)
    @patch("coding.views.cancel_controller_job.delay")
    def test_owner_can_cancel_job_but_outsider_cannot_read_it(self, cancel):
        project = CodingProject.objects.create(owner=self.owner, name="Cancel")
        file = create_file(user=self.owner, project=project, path="main.py", content="print(1)", language="python")
        job = ExecutionJob.objects.create(
            requested_by=self.owner, project=project, source_file=file, language="python",
            source_snapshot=file.content, idempotency_key="cancel-job-key", limits={"timeout_seconds": 10},
        )
        self.authenticate(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("coding-execution-cancel", args=[job.id]), {}, format="json")
        self.assertEqual(response.data["data"]["status"], "cancelled")
        cancel.assert_called_once()

        self.authenticate(self.outsider)
        hidden = self.client.get(reverse("coding-execution-detail", args=[job.id]))
        self.assertEqual(hidden.status_code, 404)
