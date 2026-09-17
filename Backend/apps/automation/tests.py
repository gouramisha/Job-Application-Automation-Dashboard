from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.applications.models import Application
from apps.jobs.models import Job, JobStatus

from .field_map import answer_for, choose_option, is_sensitive, match_field
from .models import AutomationRun, SupportedSite
from .runner import FillResult
from .services import execute_run, may_auto_submit, normalise_domain, queue_run, resolve_site

User = get_user_model()


class FieldMapTests(APITestCase):
    def test_specific_labels_beat_generic_ones(self):
        self.assertEqual(match_field({"tag": "input", "type": "text", "label": "First Name"}), "first_name")
        self.assertEqual(match_field({"tag": "input", "type": "text", "label": "Last Name"}), "last_name")
        self.assertEqual(match_field({"tag": "input", "type": "text", "label": "Full Name"}), "full_name")

    def test_word_boundaries_prevent_false_positives(self):
        # 'name' must not fire inside 'username'.
        self.assertIsNone(match_field({"tag": "input", "type": "text", "label": "Username", "name": "username"}))

    def test_sensitive_fields_are_never_matched(self):
        for label in ["Date of Birth", "Gender", "Race / Ethnicity", "SSN",
                      "Bank account number", "Veteran status", "Disability status",
                      "I agree to the terms", "Enter the CAPTCHA"]:
            with self.subTest(label=label):
                control = {"tag": "input", "type": "text", "label": label}
                self.assertTrue(is_sensitive(control))
                self.assertIsNone(match_field(control))

    def test_password_inputs_are_sensitive_regardless_of_label(self):
        self.assertTrue(is_sensitive({"tag": "input", "type": "password", "label": "Secret"}))

    def test_matching_uses_every_attribute_not_just_the_label(self):
        self.assertEqual(
            match_field({"tag": "input", "type": "text", "label": "", "name": "linkedin_profile"}),
            "linkedin_url",
        )
        self.assertEqual(
            match_field({"tag": "input", "type": "text", "placeholder": "your.name@company.com",
                         "aria_label": "Email"}),
            "email",
        )

    def test_textarea_only_fields_ignore_text_inputs(self):
        self.assertEqual(match_field({"tag": "textarea", "label": "Cover letter"}), "summary")
        self.assertIsNone(match_field({"tag": "input", "type": "text", "label": "Cover letter"}))

    def test_answer_falls_back_to_saved_custom_questions(self):
        control = {"tag": "textarea", "label": "How did you hear about this role?"}
        values = {"How did you hear about this role?": "LinkedIn"}
        self.assertEqual(answer_for(control, values), "LinkedIn")

    def test_answer_returns_none_when_nothing_is_saved(self):
        self.assertIsNone(answer_for({"tag": "input", "type": "text", "label": "Phone"}, {}))

    def test_choose_option_refuses_to_guess_wildly(self):
        options = ["Yes", "No", "Prefer not to say"]
        self.assertEqual(choose_option(options, "yes"), "Yes")
        self.assertEqual(choose_option(options, "No"), "No")
        self.assertIsNone(choose_option(options, "Maybe someday"))
        self.assertIsNone(choose_option(options, ""))


class SiteResolutionTests(APITestCase):
    def setUp(self):
        self.site = SupportedSite.objects.create(name="Greenhouse", domain="greenhouse.io")

    def test_normalise_domain_strips_www(self):
        self.assertEqual(normalise_domain("https://www.greenhouse.io/x"), "greenhouse.io")

    def test_subdomains_resolve_to_the_registered_site(self):
        # One 'greenhouse.io' row must cover every company board hosted there.
        self.assertEqual(resolve_site("https://boards.greenhouse.io/acme/jobs/1"), self.site)
        self.assertEqual(resolve_site("https://greenhouse.io/acme"), self.site)

    def test_unrelated_hosts_do_not_resolve(self):
        self.assertIsNone(resolve_site("https://evil-greenhouse.io/x"))
        self.assertIsNone(resolve_site("https://random.example.com/apply"))
        self.assertIsNone(resolve_site("not-a-url"))


class SubmitPolicyTests(APITestCase):
    """The three-switch gate is the core safety property of this project."""

    def setUp(self):
        self.user = User.objects.create_user(email="s@example.com", password="StrongPass123!")
        self.api_site = SupportedSite.objects.create(
            name="PartnerATS", domain="partner-ats.com", supports_official_api=True
        )
        self.plain_site = SupportedSite.objects.create(name="Greenhouse", domain="greenhouse.io")

    def _allow_user(self):
        self.user.settings.allow_auto_submit = True
        self.user.settings.save()
        self.user.refresh_from_db()

    def test_no_site_means_no_submit(self):
        allowed, reason = may_auto_submit(self.user, None)
        self.assertFalse(allowed)
        self.assertIn("no official application API", reason)

    @override_settings(AUTOMATION_ALLOW_AUTO_SUBMIT=True)
    def test_site_without_official_api_never_submits(self):
        self._allow_user()
        allowed, reason = may_auto_submit(self.user, self.plain_site)
        self.assertFalse(allowed)
        self.assertIn("no official application API", reason)

    @override_settings(AUTOMATION_ALLOW_AUTO_SUBMIT=False)
    def test_deployment_switch_off_blocks_even_an_api_site(self):
        self._allow_user()
        allowed, reason = may_auto_submit(self.user, self.api_site)
        self.assertFalse(allowed)
        self.assertIn("disabled for this deployment", reason)

    @override_settings(AUTOMATION_ALLOW_AUTO_SUBMIT=True)
    def test_user_switch_off_blocks_even_an_api_site(self):
        allowed, reason = may_auto_submit(self.user, self.api_site)
        self.assertFalse(allowed)
        self.assertIn("switched off in Settings", reason)

    @override_settings(AUTOMATION_ALLOW_AUTO_SUBMIT=True)
    def test_all_three_switches_on_is_the_only_path_to_submit(self):
        self._allow_user()
        allowed, reason = may_auto_submit(self.user, self.api_site)
        self.assertTrue(allowed)
        self.assertEqual(reason, "")

    @override_settings(AUTOMATION_ALLOW_AUTO_SUBMIT=True)
    def test_disabled_api_site_is_not_eligible(self):
        self._allow_user()
        self.api_site.is_enabled = False
        self.api_site.save()
        allowed, _ = may_auto_submit(self.user, self.api_site)
        self.assertFalse(allowed)


class RunLifecycleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="run@example.com", password="StrongPass123!")
        self.client.force_authenticate(self.user)
        SupportedSite.objects.create(name="Greenhouse", domain="greenhouse.io")
        self.job = Job.objects.create(
            user=self.user, company_name="Acme", job_title="Backend Engineer",
            job_url="https://boards.greenhouse.io/acme/jobs/1",
        )

    def test_queue_run_creates_a_queued_run_without_launching_a_browser(self):
        run = queue_run(user=self.user, job=self.job)
        self.assertEqual(run.status, AutomationRun.Status.QUEUED)
        self.assertEqual(run.site.name, "Greenhouse")

    def test_unsupported_host_is_recorded_not_silently_dropped(self):
        job = Job.objects.create(
            user=self.user, company_name="Sketchy", job_title="Dev",
            job_url="https://sketchy-jobs.example.com/apply",
        )
        run = queue_run(user=self.user, job=job)
        # A visible refusal beats a 400 the dashboard has to explain.
        self.assertEqual(run.status, AutomationRun.Status.UNSUPPORTED)
        self.assertIn("allowlist", run.stop_reason)
        self.assertTrue(run.logs.filter(level="warning").exists())

    def test_queue_run_rejects_a_job_with_no_url(self):
        job = Job.objects.create(user=self.user, company_name="NoUrl", job_title="Dev")
        with self.assertRaises(ValueError):
            queue_run(user=self.user, job=job)

    def test_start_endpoint_returns_the_run(self):
        response = self.client.post("/api/automation/runs/start/", {"job": self.job.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "queued")
        self.assertIn("logs", response.data)

    def test_start_endpoint_rejects_another_users_job(self):
        other = User.objects.create_user(email="oo@example.com", password="StrongPass123!")
        theirs = Job.objects.create(user=other, company_name="X", job_title="Y",
                                    job_url="https://boards.greenhouse.io/x/1")
        response = self.client.post("/api/automation/runs/start/", {"job": theirs.pk}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_preflight_reports_the_submit_policy_before_anything_launches(self):
        response = self.client.get(
            "/api/automation/runs/preflight/?url=https://boards.greenhouse.io/acme/jobs/1"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["supported"])
        self.assertFalse(response.data["will_auto_submit"])

        response = self.client.get("/api/automation/runs/preflight/?url=https://nope.example.com/x")
        self.assertFalse(response.data["supported"])

    def test_runs_are_scoped_to_their_owner(self):
        other = User.objects.create_user(email="o2@example.com", password="StrongPass123!")
        job = Job.objects.create(user=other, company_name="X", job_title="Y",
                                 job_url="https://boards.greenhouse.io/x/2")
        theirs = queue_run(user=other, job=job)
        self.assertEqual(self.client.get("/api/automation/runs/").data["count"], 0)
        self.assertEqual(
            self.client.get(f"/api/automation/runs/{theirs.pk}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_cancel_a_queued_run(self):
        run = queue_run(user=self.user, job=self.job)
        response = self.client.post(f"/api/automation/runs/{run.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "cancelled")

    def test_cannot_cancel_a_finished_run(self):
        run = queue_run(user=self.user, job=self.job)
        run.mark_finished(AutomationRun.Status.AWAITING_REVIEW)
        response = self.client.post(f"/api/automation/runs/{run.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ExecuteRunTests(APITestCase):
    """execute_run is tested with the Playwright layer mocked - the browser
    itself is exercised separately against a local HTML fixture."""

    def setUp(self):
        self.user = User.objects.create_user(email="e@example.com", password="StrongPass123!")
        self.site = SupportedSite.objects.create(name="Greenhouse", domain="greenhouse.io")
        self.job = Job.objects.create(
            user=self.user, company_name="Acme", job_title="Backend Engineer",
            job_url="https://boards.greenhouse.io/acme/jobs/1",
        )

    def _run_with(self, result):
        run = queue_run(user=self.user, job=self.job)
        with patch("apps.automation.services.run_fill", return_value=result):
            execute_run(run)
        run.refresh_from_db()
        return run

    def test_assisted_run_stops_at_awaiting_review(self):
        result = FillResult(
            filled={"first_name": "Ada", "email": "e@example.com"},
            resume_uploaded=True,
            stop_reason="Form filled and left open for your review.",
        )
        run = self._run_with(result)

        self.assertEqual(run.status, AutomationRun.Status.AWAITING_REVIEW)
        self.assertFalse(run.submit_attempted)
        self.assertEqual(run.fields_filled, {"first_name": "Ada", "email": "e@example.com"})
        self.assertTrue(run.resume_uploaded)

    def test_assisted_run_does_not_move_the_job_to_applied(self):
        run = self._run_with(FillResult(filled={"email": "e@example.com"}))

        application = run.application
        self.assertEqual(application.outcome, Application.Outcome.PREPARED)
        self.assertEqual(application.method, Application.Method.ASSISTED)
        self.assertIsNone(application.submitted_at)

        self.job.refresh_from_db()
        # Nothing has actually been sent yet, so the tracker must not claim it has.
        self.assertEqual(self.job.status, JobStatus.SAVED)

    def test_failed_run_records_the_error_on_the_application(self):
        run = self._run_with(FillResult(error="TimeoutError: page never loaded"))

        self.assertEqual(run.status, AutomationRun.Status.FAILED)
        self.assertIn("TimeoutError", run.error_message)
        self.assertEqual(run.application.outcome, Application.Outcome.FAILED)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.SAVED)

    @override_settings(AUTOMATION_ALLOW_AUTO_SUBMIT=True)
    def test_api_submission_advances_the_job_and_schedules_a_follow_up(self):
        from apps.reminders.models import Reminder

        self.site.supports_official_api = True
        self.site.save()
        self.user.settings.allow_auto_submit = True
        self.user.settings.save()

        run = self._run_with(
            FillResult(filled={"email": "e@example.com"}, submitted=True, submit_attempted=True)
        )

        self.assertEqual(run.status, AutomationRun.Status.SUBMITTED)
        self.assertEqual(run.application.outcome, Application.Outcome.SUBMITTED)
        self.assertEqual(run.application.method, Application.Method.API)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, JobStatus.APPLIED)
        self.assertTrue(Reminder.objects.filter(user=self.user).exists())

    def test_events_are_persisted_as_logs(self):
        result = FillResult()
        result.event("info", "Opening the page")
        result.event("warning", "No resume upload field found")
        run = self._run_with(result)

        messages = list(run.logs.values_list("message", flat=True))
        self.assertIn("Opening the page", messages)
        self.assertIn("No resume upload field found", messages)

    def test_unanswered_questions_are_surfaced_for_the_user(self):
        run = self._run_with(
            FillResult(unanswered=["Why do you want to work here?", "Notice period"])
        )
        self.assertEqual(len(run.unanswered_questions), 2)

    def test_unsupported_run_creates_no_application(self):
        job = Job.objects.create(
            user=self.user, company_name="Nope", job_title="Dev",
            job_url="https://unsupported.example.com/apply",
        )
        run = queue_run(user=self.user, job=job)
        execute_run(run)
        run.refresh_from_db()
        self.assertEqual(run.status, AutomationRun.Status.UNSUPPORTED)
        self.assertIsNone(run.application)
