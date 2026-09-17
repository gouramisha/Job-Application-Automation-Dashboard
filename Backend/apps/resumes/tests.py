from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Resume

User = get_user_model()


def upload(name="resume.pdf", content=b"%PDF-1.4 fake resume"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


class ResumeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="r@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)

    def _create(self, name, **extra):
        return self.client.post(
            "/api/resumes/", {"name": name, "file": upload(), **extra}, format="multipart"
        )

    def test_first_resume_becomes_default_automatically(self):
        response = self._create("Backend 2026")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Without this the user uploads a file and still has nothing selected
        # for the automation module to attach.
        self.assertTrue(response.data["is_default"])

    def test_promoting_a_resume_demotes_the_previous_default(self):
        first = self._create("First").data
        second = self._create("Second").data
        self.assertTrue(first["is_default"])
        self.assertFalse(second["is_default"])

        response = self.client.post(f"/api/resumes/{second['id']}/set-default/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_default"])

        self.assertFalse(Resume.objects.get(pk=first["id"]).is_default)
        self.assertEqual(Resume.objects.filter(user=self.user, is_default=True).count(), 1)

    def test_deleting_the_default_promotes_another_resume(self):
        first = self._create("First").data
        self._create("Second")

        self.client.delete(f"/api/resumes/{first['id']}/")
        remaining = Resume.objects.filter(user=self.user)
        self.assertEqual(remaining.count(), 1)
        # A user with resumes should never be left with no default.
        self.assertTrue(remaining.first().is_default)

    def test_deleting_the_only_resume_leaves_none(self):
        only = self._create("Only").data
        self.client.delete(f"/api/resumes/{only['id']}/")
        self.assertEqual(Resume.objects.filter(user=self.user).count(), 0)

    def test_duplicate_name_rejected_case_insensitively(self):
        self._create("Backend")
        response = self._create("backend")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_rejects_unsupported_file_type(self):
        response = self.client.post(
            "/api/resumes/",
            {"name": "Exe", "file": SimpleUploadedFile("virus.exe", b"MZ", content_type="application/octet-stream")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_oversized_file(self):
        response = self.client.post(
            "/api/resumes/",
            {"name": "Huge", "file": upload("big.pdf", b"x" * (10 * 1024 * 1024 + 1))},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_resumes_are_scoped_to_their_owner(self):
        other = User.objects.create_user(email="other@example.com", password="StrongPass123!")
        theirs = Resume.objects.create(user=other, name="Theirs", file=upload())
        self.assertEqual(self.client.get("/api/resumes/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/resumes/{theirs.pk}/").status_code, status.HTTP_404_NOT_FOUND
        )

    def tearDown(self):
        # Uploads land in MEDIA_ROOT even under test; clean up after ourselves.
        for resume in Resume.objects.all():
            if resume.file:
                resume.file.delete(save=False)
