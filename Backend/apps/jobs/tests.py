from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .matching import rank_jobs, score_job
from .models import Job, JobStatus, JobStatusHistory

User = get_user_model()


def make_job(user, **overrides):
    defaults = {
        "company_name": "Acme",
        "job_title": "Backend Engineer",
        "location": "Bengaluru, India",
        "skills": "Python, Django, PostgreSQL",
        "experience_required": "3-5 years",
    }
    return Job.objects.create(user=user, **{**defaults, **overrides})


class JobApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="u@example.com", password="StrongPass123!")
        self.other = User.objects.create_user(email="o@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)

    def test_create_logs_initial_status_history(self):
        response = self.client.post(
            "/api/jobs/", {"company_name": "Acme", "job_title": "Dev"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        job = Job.objects.get(pk=response.data["id"])
        self.assertEqual(job.status_history.count(), 1)
        self.assertEqual(job.status_history.first().to_status, JobStatus.SAVED)

    def test_duplicate_job_url_is_a_field_error_not_a_500(self):
        make_job(self.user, job_url="https://jobs.example.com/1")
        response = self.client.post(
            "/api/jobs/",
            {"company_name": "Other", "job_title": "Dev", "job_url": "https://jobs.example.com/1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("job_url", response.data)

    def test_same_url_allowed_for_a_different_user(self):
        make_job(self.other, job_url="https://jobs.example.com/1")
        response = self.client.post(
            "/api/jobs/",
            {"company_name": "Acme", "job_title": "Dev", "job_url": "https://jobs.example.com/1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_users_cannot_see_or_touch_each_others_jobs(self):
        theirs = make_job(self.other, company_name="Secret Corp")
        self.assertEqual(self.client.get("/api/jobs/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/jobs/{theirs.pk}/").status_code, status.HTTP_404_NOT_FOUND
        )
        self.assertEqual(
            self.client.delete(f"/api/jobs/{theirs.pk}/").status_code, status.HTTP_404_NOT_FOUND
        )

    def test_status_transition_records_history_and_backfills_applied_date(self):
        job = make_job(self.user)
        self.assertIsNone(job.applied_date)

        response = self.client.post(
            f"/api/jobs/{job.pk}/status/",
            {"status": "applied", "note": "Submitted via portal"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.APPLIED)
        # Moving into a sent state without a date is an oversight worth fixing
        # rather than a datapoint worth losing.
        self.assertEqual(job.applied_date, timezone.localdate())

        history = JobStatusHistory.objects.filter(job=job, to_status=JobStatus.APPLIED).first()
        self.assertEqual(history.from_status, JobStatus.SAVED)
        self.assertEqual(history.note, "Submitted via portal")

    def test_repeated_status_transition_does_not_duplicate_history(self):
        job = make_job(self.user, status=JobStatus.APPLIED)
        before = job.status_history.count()
        self.client.post(f"/api/jobs/{job.pk}/status/", {"status": "applied"}, format="json")
        self.assertEqual(job.status_history.count(), before)

    def test_search_and_filter(self):
        make_job(self.user, company_name="Stripe", job_title="Backend Engineer")
        make_job(self.user, company_name="Zoho", job_title="Frontend Dev", status=JobStatus.APPLIED)

        self.assertEqual(self.client.get("/api/jobs/?search=Stripe").data["count"], 1)
        self.assertEqual(self.client.get("/api/jobs/?status=applied").data["count"], 1)
        self.assertEqual(self.client.get("/api/jobs/?status=saved,applied").data["count"], 2)
        self.assertEqual(self.client.get("/api/jobs/?search=nothinghere").data["count"], 0)

    def test_options_endpoint_exposes_every_status(self):
        response = self.client.get("/api/jobs/options/")
        values = [row["value"] for row in response.data["statuses"]]
        self.assertEqual(
            values, ["saved", "applied", "shortlisted", "interview", "selected", "rejected"]
        )


class MatchingTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="m@example.com", password="StrongPass123!")
        profile = self.user.profile
        profile.desired_roles = "Backend Engineer, Python Developer"
        profile.desired_locations = "Bengaluru, Pune"
        profile.skills = "Python, Django, PostgreSQL, Redis"
        profile.years_experience = 4
        profile.open_to_remote = True
        profile.save()
        self.profile = profile
        self.client.force_authenticate(self.user)

    def test_exact_role_location_and_experience_scores_highly(self):
        job = make_job(
            self.user,
            job_title="Backend Engineer",
            location="Bengaluru, India",
            experience_required="3-5 years",
            skills="Python, Django, PostgreSQL, Redis",
        )
        score, reasons = score_job(job, self.profile)
        self.assertEqual(score, 100)
        self.assertEqual(len(reasons), 4)

    def test_unrelated_role_scores_nothing(self):
        job = make_job(
            self.user,
            job_title="Graphic Designer",
            location="Berlin, Germany",
            experience_required="10+ years",
            skills="Photoshop, Illustrator",
        )
        score, reasons = score_job(job, self.profile)
        self.assertEqual(score, 0)
        self.assertEqual(reasons, [])

    def test_remote_job_matches_when_open_to_remote(self):
        job = make_job(self.user, location="Remote", is_remote=True, experience_required="")
        _, reasons = score_job(job, self.profile)
        self.assertIn("Remote, and you are open to remote", reasons)

    def test_near_miss_on_experience_still_surfaces(self):
        job = make_job(self.user, experience_required="5-8 years", skills="")
        _, reasons = score_job(job, self.profile)
        # One year short is worth showing; five years short is not.
        self.assertTrue(any("Close to" in r for r in reasons))

    def test_ranking_is_ordered_and_filters_out_zero_scores(self):
        weak = make_job(self.user, job_title="Chef", location="Paris",
                        experience_required="", skills="Cooking")
        strong = make_job(self.user, job_title="Backend Engineer", location="Bengaluru",
                          company_name="Strong", job_url="https://x.co/2")
        ranked = rank_jobs([weak, strong], self.profile)
        self.assertEqual([j.pk for j in ranked], [strong.pk])

    def test_matches_endpoint_only_considers_saved_jobs(self):
        make_job(self.user, job_title="Backend Engineer", location="Bengaluru")
        make_job(self.user, job_title="Backend Engineer", location="Bengaluru",
                 company_name="Applied Co", job_url="https://x.co/3", status=JobStatus.APPLIED)

        response = self.client.get("/api/jobs/matches/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # A job you already applied to is not a suggestion for what to do next.
        self.assertEqual(response.data["count"], 1)
        self.assertGreater(response.data["results"][0]["match_score"], 0)
        self.assertTrue(response.data["results"][0]["match_reasons"])


class JobModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="mo@example.com", password="StrongPass123!")

    def test_applied_date_is_not_overwritten_when_already_set(self):
        past = timezone.localdate() - timedelta(days=10)
        job = make_job(self.user, status=JobStatus.APPLIED, applied_date=past)
        job.status = JobStatus.INTERVIEW
        job.save()
        job.refresh_from_db()
        self.assertEqual(job.applied_date, past)

    def test_saved_jobs_keep_a_null_applied_date(self):
        job = make_job(self.user, status=JobStatus.SAVED)
        self.assertIsNone(job.applied_date)

    def test_skill_list_splits_and_strips(self):
        job = make_job(self.user, skills="Python ,  Django,, PostgreSQL ")
        self.assertEqual(job.skill_list, ["Python", "Django", "PostgreSQL"])
