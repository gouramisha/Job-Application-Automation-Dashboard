from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.jobs.models import Job, JobStatus

from .services import funnel, summary, timeline

User = get_user_model()


class AnalyticsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="an@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)
        self.today = timezone.localdate()

    def _jobs(self, status_value, count, days_ago=1):
        for index in range(count):
            Job.objects.create(
                user=self.user,
                company_name=f"Co{status_value}{index}",
                job_title="Dev",
                status=status_value,
                applied_date=None if status_value == JobStatus.SAVED
                else self.today - timedelta(days=days_ago),
            )

    def test_summary_of_an_empty_account_is_all_zeros_not_a_crash(self):
        data = summary(self.user)
        self.assertEqual(data["total_jobs"], 0)
        self.assertEqual(data["applications_sent"], 0)
        # Every rate must be 0.0, never a ZeroDivisionError.
        for key in ["response_rate", "interview_rate", "success_rate", "rejection_rate"]:
            self.assertEqual(data[key], 0.0)

    def test_summary_counts_and_rates(self):
        self._jobs(JobStatus.SAVED, 5)
        self._jobs(JobStatus.APPLIED, 10)
        self._jobs(JobStatus.SHORTLISTED, 4)
        self._jobs(JobStatus.INTERVIEW, 3)
        self._jobs(JobStatus.SELECTED, 2)
        self._jobs(JobStatus.REJECTED, 6)

        data = summary(self.user)
        self.assertEqual(data["total_jobs"], 30)
        self.assertEqual(data["saved"], 5)
        # Sent = everything except Saved.
        self.assertEqual(data["applications_sent"], 25)
        self.assertEqual(data["shortlisted"], 4)
        self.assertEqual(data["interviews"], 3)
        self.assertEqual(data["selected"], 2)
        self.assertEqual(data["rejected"], 6)
        self.assertEqual(data["in_progress"], 19)

        self.assertEqual(data["success_rate"], 8.0)          # 2 / 25
        self.assertEqual(data["interview_rate"], 20.0)       # (3 + 2) / 25
        self.assertEqual(data["rejection_rate"], 24.0)       # 6 / 25
        self.assertEqual(data["response_rate"], 60.0)        # (4+3+2+6) / 25

    def test_rates_are_measured_against_sent_not_total(self):
        # 100 saved jobs must not dilute a perfect record on the 2 sent.
        self._jobs(JobStatus.SAVED, 100)
        self._jobs(JobStatus.SELECTED, 2)
        self.assertEqual(summary(self.user)["success_rate"], 100.0)

    def test_funnel_only_ever_narrows(self):
        self._jobs(JobStatus.APPLIED, 10)
        self._jobs(JobStatus.SHORTLISTED, 5)
        self._jobs(JobStatus.INTERVIEW, 3)
        self._jobs(JobStatus.SELECTED, 1)

        stages = funnel(self.user)
        counts = [stage["count"] for stage in stages]
        self.assertEqual(counts, [19, 9, 4, 1])
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertEqual(stages[0]["percent"], 100.0)

    def test_timeline_is_zero_filled_across_the_window(self):
        Job.objects.create(user=self.user, company_name="A", job_title="Dev",
                           status=JobStatus.APPLIED, applied_date=self.today)
        Job.objects.create(user=self.user, company_name="B", job_title="Dev",
                           status=JobStatus.APPLIED, applied_date=self.today - timedelta(days=3))

        points = timeline(self.user, days=7)
        # A gap-free series, or the chart draws a misleading line.
        self.assertEqual(len(points), 7)
        self.assertEqual(sum(p["applications"] for p in points), 2)
        self.assertEqual(points[-1]["applications"], 1)

    def test_dashboard_endpoint_bundles_every_panel(self):
        self._jobs(JobStatus.APPLIED, 3)
        response = self.client.get("/api/analytics/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["summary", "funnel", "timeline", "recent_applications", "upcoming_reminders"]:
            self.assertIn(key, response.data)

    def test_analytics_never_leak_across_users(self):
        other = User.objects.create_user(email="ao@example.com", password="StrongPass123!")
        Job.objects.create(user=other, company_name="Theirs", job_title="Dev",
                           status=JobStatus.SELECTED)
        self.assertEqual(summary(self.user)["total_jobs"], 0)

    def test_breakdowns_endpoint(self):
        self._jobs(JobStatus.APPLIED, 2)
        response = self.client.get("/api/analytics/breakdowns/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["by_status", "by_source", "by_method", "top_companies"]:
            self.assertIn(key, response.data)

    def test_weekly_timeline_buckets_align_to_mondays(self):
        for offset in (0, 1, 2, 8):
            Job.objects.create(
                user=self.user, company_name=f"W{offset}", job_title="Dev",
                status=JobStatus.APPLIED, applied_date=self.today - timedelta(days=offset),
            )
        points = timeline(self.user, days=21, bucket="week")
        # Every job must land in a bucket; a misaligned cursor silently drops them.
        self.assertEqual(sum(p["applications"] for p in points), 4)
        for point in points:
            self.assertEqual(timezone.datetime.fromisoformat(point["date"]).weekday(), 0)

    def test_status_timeline_endpoint(self):
        self._jobs(JobStatus.APPLIED, 2)
        response = self.client.get("/api/analytics/status-timeline/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("points", response.data)

    def test_status_breakdown_stays_in_lifecycle_order(self):
        # The chart colours these with a light-to-dark ordinal ramp, so the
        # row order carries meaning and must not follow the counts.
        self._jobs(JobStatus.REJECTED, 9)
        self._jobs(JobStatus.SAVED, 1)
        self._jobs(JobStatus.INTERVIEW, 4)

        rows = self.client.get("/api/analytics/breakdowns/").data["by_status"]
        self.assertEqual(
            [row["key"] for row in rows],
            ["saved", "applied", "shortlisted", "interview", "selected", "rejected"],
        )
        # Statuses with no jobs still appear, so the ramp has no gaps.
        self.assertEqual([row["count"] for row in rows], [1, 0, 0, 4, 0, 9])
