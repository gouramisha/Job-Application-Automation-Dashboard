from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import Job, JobStatus
from apps.reminders.models import Reminder
from apps.resumes.models import Resume
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Application

User = get_user_model()


class QuickApplyTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="q@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)
        self.job = Job.objects.create(
            user=self.user, company_name="Acme", job_title="Backend Engineer"
        )
        self.resume = Resume.objects.create(
            user=self.user, name="Default",
            file=SimpleUploadedFile("r.pdf", b"%PDF-1.4", content_type="application/pdf"),
            is_default=True,
        )

    def test_quick_apply_creates_application_and_advances_the_job(self):
        response = self.client.post(
            "/api/applications/quick-apply/", {"job": self.job.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.APPLIED)
        self.assertIsNotNone(self.job.applied_date)

        application = Application.objects.get(pk=response.data["id"])
        self.assertEqual(application.outcome, Application.Outcome.SUBMITTED)
        self.assertEqual(application.method, Application.Method.MANUAL)
        self.assertIsNotNone(application.submitted_at)

    def test_quick_apply_falls_back_to_the_default_resume(self):
        response = self.client.post(
            "/api/applications/quick-apply/", {"job": self.job.pk}, format="json"
        )
        self.assertEqual(response.data["resume"], self.resume.pk)
        self.assertEqual(response.data["resume_label"], "Default")

    def test_quick_apply_schedules_a_follow_up(self):
        self.client.post("/api/applications/quick-apply/", {"job": self.job.pk}, format="json")
        reminder = Reminder.objects.get(user=self.user, kind=Reminder.Kind.FOLLOW_UP)
        self.assertIn("Acme", reminder.title)
        self.assertEqual(reminder.days_until_due, 7)

    def test_no_follow_up_when_the_user_opted_out(self):
        self.user.settings.auto_create_follow_ups = False
        self.user.settings.save()
        self.client.post("/api/applications/quick-apply/", {"job": self.job.pk}, format="json")
        self.assertFalse(Reminder.objects.filter(user=self.user).exists())

    def test_quick_apply_does_not_demote_a_job_already_further_along(self):
        self.job.status = JobStatus.INTERVIEW
        self.job.save()
        self.client.post("/api/applications/quick-apply/", {"job": self.job.pk}, format="json")
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.INTERVIEW)

    def test_cannot_apply_to_another_users_job(self):
        other = User.objects.create_user(email="x@example.com", password="StrongPass123!")
        theirs = Job.objects.create(user=other, company_name="Secret", job_title="Dev")
        response = self.client.post(
            "/api/applications/quick-apply/", {"job": theirs.pk}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resume_label_survives_resume_deletion(self):
        self.client.post("/api/applications/quick-apply/", {"job": self.job.pk}, format="json")
        self.resume.delete()
        application = Application.objects.get(user=self.user)
        # The FK nulls out, but the snapshot keeps the history readable.
        self.assertIsNone(application.resume)
        self.assertEqual(application.resume_name_snapshot, "Default")

    def test_mark_submitted_promotes_a_prepared_application(self):
        application = Application.objects.create(
            user=self.user, job=self.job, outcome=Application.Outcome.PREPARED,
            method=Application.Method.ASSISTED,
        )
        response = self.client.post(f"/api/applications/{application.pk}/mark-submitted/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        application.refresh_from_db()
        self.assertEqual(application.outcome, Application.Outcome.SUBMITTED)
        self.assertIsNotNone(application.submitted_at)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.APPLIED)

    def tearDown(self):
        for resume in Resume.objects.all():
            if resume.file:
                resume.file.delete(save=False)
