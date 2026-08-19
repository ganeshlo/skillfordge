from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import User, UserPreference, UserProfile
from knowledge_base.models import (
    CodeSnippet,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeNote,
    KnowledgeNoteVersion,
)


def create_user(email):
    account = User.objects.create_user(
        email, "A-strong-test-password-482!", full_name=email.split("@")[0]
    )
    UserProfile.objects.create(user=account)
    UserPreference.objects.create(user=account)
    return account


class KnowledgeBaseAPITests(APITestCase):
    def setUp(self):
        self.owner = create_user("knowledge@example.com")
        self.other = create_user("other-knowledge@example.com")

    def authenticate(self, user):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}"
        )

    @patch("knowledge_base.services.index_note_task.delay")
    def test_note_autosave_creates_versions_and_is_private(self, index_task):
        self.authenticate(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            created = self.client.post(
                reverse("knowledge-note-list"),
                {"title": "JWT notes", "content": "# JWT\n\nTokens carry claims."},
                format="json",
            )
        self.assertEqual(created.status_code, 201)
        note_id = created.data["data"]["id"]
        with self.captureOnCommitCallbacks(execute=True):
            updated = self.client.patch(
                reverse("knowledge-note-detail", args=[note_id]),
                {"content": "# JWT\n\nAccess tokens expire."},
                format="json",
            )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["data"]["current_version"], 2)
        self.assertEqual(
            KnowledgeNoteVersion.objects.filter(note_id=note_id).count(), 2
        )
        self.assertEqual(index_task.call_count, 2)

        self.authenticate(self.other)
        hidden = self.client.get(reverse("knowledge-note-detail", args=[note_id]))
        self.assertEqual(hidden.status_code, 404)

    def test_folder_hierarchy_rejects_cross_user_parent(self):
        self.authenticate(self.other)
        foreign = self.client.post(
            reverse("knowledge-folder-list"), {"name": "Private"}, format="json"
        ).data["data"]
        self.authenticate(self.owner)
        response = self.client.post(
            reverse("knowledge-folder-list"),
            {"name": "Stolen child", "parent_id": foreign["id"]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("knowledge_base.services.process_document_task.delay")
    def test_secure_document_upload_and_private_download(self, process_task):
        self.authenticate(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            uploaded = self.client.post(
                reverse("knowledge-document-list"),
                {"title": "Reference", "file": SimpleUploadedFile("reference.txt", b"JWT authentication reference")},
                format="multipart",
            )
        self.assertEqual(uploaded.status_code, 201)
        document_id = uploaded.data["data"]["id"]
        process_task.assert_called_once_with(document_id)
        download = self.client.get(
            reverse("knowledge-document-content", args=[document_id])
        )
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download["X-Content-Type-Options"], "nosniff")

        self.authenticate(self.other)
        hidden = self.client.get(
            reverse("knowledge-document-content", args=[document_id])
        )
        self.assertEqual(hidden.status_code, 404)

    def test_rejects_unsupported_upload(self):
        self.authenticate(self.owner)
        response = self.client.post(
            reverse("knowledge-document-list"),
            {"file": SimpleUploadedFile("malware.exe", b"MZ fake executable")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(KnowledgeDocument.objects.exists())

    def test_snippet_library_is_user_scoped(self):
        self.authenticate(self.owner)
        created = self.client.post(
            reverse("knowledge-snippet-list"),
            {
                "title": "Decode JWT",
                "description": "Inspect claims",
                "language": "python",
                "code": "jwt.decode(token, key, algorithms=['HS256'])",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(CodeSnippet.objects.get().owner, self.owner)
        self.authenticate(self.other)
        listing = self.client.get(reverse("knowledge-snippet-list"))
        self.assertEqual(listing.data["data"], [])

    def test_keyword_search_returns_owned_chunks(self):
        note = KnowledgeNote.objects.create(
            owner=self.owner, title="JWT Authentication", content="Refresh token rotation"
        )
        KnowledgeChunk.objects.create(
            owner=self.owner,
            note=note,
            source_type=KnowledgeChunk.Source.NOTE,
            chunk_index=0,
            content="JWT access tokens and refresh token rotation",
        )
        other_note = KnowledgeNote.objects.create(
            owner=self.other, title="Private", content="JWT private secret"
        )
        KnowledgeChunk.objects.create(
            owner=self.other,
            note=other_note,
            source_type=KnowledgeChunk.Source.NOTE,
            chunk_index=0,
            content="JWT private secret",
        )
        self.authenticate(self.owner)
        result = self.client.post(
            reverse("knowledge-search"), {"query": "JWT"}, format="json"
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(result.data["data"]["results"]), 1)
        self.assertEqual(result.data["data"]["results"][0]["title"], "JWT Authentication")

    @patch("knowledge_base.ai._generate", return_value="Use rotation [S1].")
    def test_rag_answer_contains_owned_source_citations(self, generate):
        note = KnowledgeNote.objects.create(
            owner=self.owner, title="Security notes", content="Rotate refresh tokens"
        )
        KnowledgeChunk.objects.create(
            owner=self.owner,
            note=note,
            source_type=KnowledgeChunk.Source.NOTE,
            chunk_index=0,
            content="Refresh token rotation limits replay attacks.",
        )
        self.authenticate(self.owner)
        result = self.client.post(
            reverse("knowledge-ask"),
            {"question": "Why rotate refresh tokens?"},
            format="json",
        )
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["data"]["answer"], "Use rotation [S1].")
        self.assertEqual(result.data["data"]["citations"][0]["source_id"], str(note.id))
        generate.assert_called_once()
