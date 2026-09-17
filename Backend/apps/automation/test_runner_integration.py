"""End-to-end test of the Playwright filler against a local HTML fixture.

This is the only test that launches a real browser. It is skipped rather than
failed when the Playwright browsers are not installed, so a fresh checkout can
still run the rest of the suite:

    python -m playwright install chromium
"""
import pathlib
import tempfile
import unittest

from django.test import SimpleTestCase

from .runner import FillPlan, run_fill

FIXTURE = pathlib.Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "sample_application_form.html"


def browser_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            playwright.chromium.launch(headless=True).close()
        return True
    except Exception:  # noqa: BLE001 - browser binaries missing
        return False


PROFILE_VALUES = {
    "first_name": "Demo",
    "last_name": "Candidate",
    "full_name": "Demo Candidate",
    "email": "demo@example.com",
    "phone": "+91 98765 43210",
    "linkedin_url": "https://linkedin.com/in/demo-candidate",
    "github_url": "https://github.com/demo-candidate",
    "current_company": "Acme Systems",
    "years_experience": "4.5",
    "expected_salary": "3200000",
    "notice_period_days": "30",
    "work_authorization": "Citizen",
    "willing_to_relocate": "Yes",
    "summary": "Backend engineer with 4+ years building Django APIs at scale.",
    "How did you hear about this role?": "LinkedIn",
    "Are you open to remote work?": "Yes",
}


@unittest.skipUnless(FIXTURE.exists(), "form fixture is missing")
@unittest.skipUnless(browser_available(), "Playwright chromium is not installed")
class FormFillerIntegrationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        resume = pathlib.Path(tempfile.gettempdir()) / "jobtrack_test_resume.pdf"
        resume.write_bytes(b"%PDF-1.4\n% resume fixture\n")
        cls.resume_path = str(resume)

        cls.result = run_fill(
            FillPlan(
                url=FIXTURE.resolve().as_uri(),
                values=PROFILE_VALUES,
                resume_path=cls.resume_path,
                allow_submit=False,
                headless=True,
                timeout_ms=20_000,
            )
        )

    def test_run_completes_without_error(self):
        self.assertEqual(self.result.error, "")

    def test_fills_fields_found_by_each_label_strategy(self):
        filled = self.result.filled
        # <label for>
        self.assertEqual(filled["first_name"], "Demo")
        # input type, where the placeholder text would have misled a matcher
        self.assertEqual(filled["email"], "demo@example.com")
        # wrapping <label>
        self.assertEqual(filled["phone"], "+91 98765 43210")
        # aria-label only
        self.assertEqual(filled["linkedin_url"], "https://linkedin.com/in/demo-candidate")
        # nearby text, no label element at all
        self.assertEqual(filled["current_company"], "Acme Systems")

    def test_selects_the_matching_dropdown_option(self):
        self.assertEqual(self.result.filled["work_authorization"], "Citizen")
        self.assertEqual(self.result.filled["willing_to_relocate"], "Yes")

    def test_answers_a_saved_custom_question(self):
        self.assertEqual(self.result.filled["How did you hear about this role?"], "LinkedIn")

    def test_ticks_an_answerable_checkbox(self):
        self.assertIn("Are you open to remote work?", self.result.filled)

    def test_never_touches_sensitive_fields(self):
        """The safety property that matters most: demographic, financial and
        consent questions are always left for the user."""
        skipped = {item["label"]: item["reason"] for item in self.result.skipped}
        for label in ["Date of Birth", "Gender", "Social Security Number", "Veteran status"]:
            self.assertIn(label, skipped, f"{label} should have been skipped")
            self.assertIn("Sensitive", skipped[label])

        # Auto-accepting terms would be the worst possible failure here.
        terms = next(k for k in skipped if "agree to the terms" in k)
        self.assertIn("Sensitive", skipped[terms])
        self.assertNotIn(terms, self.result.filled)

    def test_leaves_prefilled_values_alone(self):
        skipped = {item["label"]: item["reason"] for item in self.result.skipped}
        self.assertEqual(skipped.get("Source"), "Already has a value")

    def test_reports_required_questions_it_could_not_answer(self):
        self.assertTrue(
            any("most proud of" in question for question in self.result.unanswered),
            self.result.unanswered,
        )

    def test_uploads_the_resume(self):
        self.assertTrue(self.result.resume_uploaded)

    def test_stops_before_submitting(self):
        """Without allow_submit, the run must never press the button."""
        self.assertFalse(self.result.submit_attempted)
        self.assertFalse(self.result.submitted)
        self.assertIn("Submit is yours to click", self.result.stop_reason)
