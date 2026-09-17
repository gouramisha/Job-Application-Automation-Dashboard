from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import Job

from .models import Reminder

User = get_user_model()


class ReminderTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="rem@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)
        self.job = Job.objects.create(user=self.user, company_name="Acme", job_title="Dev")
        self.today = timezone.localdate()

    def _reminder(self, days_offset, **extra):
        return Reminder.objects.create(
            user=self.user, job=self.job, title=f"Ping {days_offset}",
            due_date=self.today + timedelta(days=days_offset), **extra
        )

    def test_overdue_flag_and_days_until_due(self):
        overdue = self._reminder(-3)
        future = self._reminder(5)
        self.assertTrue(overdue.is_overdue)
        self.assertEqual(overdue.days_until_due, -3)
        self.assertFalse(future.is_overdue)
        self.assertEqual(future.days_until_due, 5)

    def test_completed_reminders_are_never_overdue(self):
        reminder = self._reminder(-10, is_done=True)
        self.assertFalse(reminder.is_overdue)

    def test_complete_and_reopen(self):
        reminder = self._reminder(2)
        response = self.client.post(f"/api/reminders/{reminder.pk}/complete/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_done"])
        self.assertIsNotNone(response.data["completed_at"])

        response = self.client.post(f"/api/reminders/{reminder.pk}/reopen/")
        self.assertFalse(response.data["is_done"])
        self.assertIsNone(response.data["completed_at"])

    def test_upcoming_excludes_done_and_far_future(self):
        self._reminder(-2)
        self._reminder(3)
        self._reminder(30)
        self._reminder(1, is_done=True)

        response = self.client.get("/api/reminders/upcoming/?days=7")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Overdue and due-soon, nothing completed, nothing a month away.
        self.assertEqual(len(response.data), 2)
        self.assertLess(response.data[0]["days_until_due"], response.data[1]["days_until_due"])

    def test_overdue_filter(self):
        self._reminder(-1)
        self._reminder(4)
        self.assertEqual(self.client.get("/api/reminders/?overdue=true").data["count"], 1)
        self.assertEqual(self.client.get("/api/reminders/?overdue=false").data["count"], 1)

    def test_reminders_are_scoped_to_their_owner(self):
        other = User.objects.create_user(email="ro@example.com", password="StrongPass123!")
        theirs = Reminder.objects.create(user=other, title="Theirs", due_date=self.today)
        self.assertEqual(self.client.get("/api/reminders/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/reminders/{theirs.pk}/").status_code, status.HTTP_404_NOT_FOUND
        )

    def test_cannot_attach_a_reminder_to_another_users_job(self):
        other = User.objects.create_user(email="rj@example.com", password="StrongPass123!")
        theirs = Job.objects.create(user=other, company_name="X", job_title="Y")
        response = self.client.post(
            "/api/reminders/",
            {"title": "Sneaky", "due_date": self.today.isoformat(), "job": theirs.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
