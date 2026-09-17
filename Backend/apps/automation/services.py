"""Turns an AutomationRun row into a browser session and back again.

This is where the safety policy lives. ``resolve_site`` decides whether we
touch a URL at all; ``may_auto_submit`` decides whether the Submit button is
ever pressed. The Playwright layer has no opinion of its own - it does what
the plan says.
"""
from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application
from apps.jobs.models import JobStatus, JobStatusHistory
from apps.reminders.services import schedule_follow_up

from .models import AutomationRun, SupportedSite
from .runner import FillPlan, run_fill

logger = logging.getLogger(__name__)


def normalise_domain(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def resolve_site(url: str) -> SupportedSite | None:
    """Find the allowlist entry covering a URL.

    Matches the registered domain or any subdomain of it, so one
    'greenhouse.io' row covers every company board hosted there.
    """
    host = normalise_domain(url)
    if not host:
        return None
    for site in SupportedSite.objects.all():
        domain = site.domain.lower().lstrip(".")
        if host == domain or host.endswith("." + domain):
            return site
    return None


def may_auto_submit(user, site: SupportedSite | None) -> tuple[bool, str]:
    """Three independent switches must all be on before we press Submit.

    Returns (allowed, reason_when_not) so the caller can log why it stopped.
    """
    if site is None or not site.auto_submit_eligible:
        return False, "This site has no official application API, so you submit it yourself."
    if not getattr(settings, "AUTOMATION_ALLOW_AUTO_SUBMIT", False):
        return False, "Automated submission is disabled for this deployment."
    user_settings = getattr(user, "settings", None)
    if user_settings is None or not user_settings.allow_auto_submit:
        return False, "You have automated submission switched off in Settings."
    return True, ""


@transaction.atomic
def queue_run(*, user, job, resume=None, target_url: str = "") -> AutomationRun:
    """Create a queued run for the worker to pick up.

    Returns immediately - no browser is launched inside the web request.
    A run for an unsupported host is created in the UNSUPPORTED state so the
    refusal is visible in the dashboard rather than being a silent 400.
    """
    url = target_url or job.job_url
    if not url:
        raise ValueError("This job has no application URL to open.")

    site = resolve_site(url)
    run = AutomationRun.objects.create(
        user=user, job=job, resume=resume, site=site, target_url=url
    )

    if site is None or not site.is_enabled:
        run.mark_finished(
            AutomationRun.Status.UNSUPPORTED,
            stop_reason=(
                f"{normalise_domain(url)} is not on the supported-site allowlist. "
                "Add it in the admin once you have checked that site's terms of service."
            ),
        )
        run.log("Refused: host is not allowlisted", level="warning", detail={"host": normalise_domain(url)})
        return run

    run.log("Queued for the automation worker", detail={"site": site.name})
    return run


def build_plan(run: AutomationRun) -> FillPlan:
    """Assemble the profile values, resume path and submit permission."""
    profile = run.user.profile
    values = profile.as_form_values()

    resume_path = None
    if run.resume and run.resume.file:
        resume_path = run.resume.file.path

    allowed, _ = may_auto_submit(run.user, run.site)

    return FillPlan(
        url=run.target_url,
        values={k: v for k, v in values.items() if v not in (None, "")},
        resume_path=resume_path,
        selector_overrides=(run.site.selector_overrides if run.site else {}) or {},
        allow_submit=allowed,
        headless=getattr(settings, "AUTOMATION_HEADLESS", False),
        timeout_ms=getattr(settings, "AUTOMATION_TIMEOUT_MS", 30_000),
        # MEDIA_ROOT is allowed to be a plain string, so coerce before joining.
        screenshot_path=str(
            Path(settings.MEDIA_ROOT) / "automation" / "screenshots" / f"run_{run.pk}.png"
        ),
    )


def execute_run(run: AutomationRun) -> AutomationRun:
    """Drive one queued run to completion. Called by the worker process."""
    if run.status != AutomationRun.Status.QUEUED:
        logger.info("Run %s is not queued (%s); skipping", run.pk, run.status)
        return run

    run.mark_started()
    allowed, refusal = may_auto_submit(run.user, run.site)
    if not allowed:
        run.log("Auto-submit withheld: " + refusal, level="info")

    try:
        plan = build_plan(run)
    except Exception as exc:  # noqa: BLE001
        run.log(f"Could not build the fill plan: {exc}", level="error")
        run.mark_finished(AutomationRun.Status.FAILED, error=str(exc))
        return run

    result = run_fill(plan)

    for level, message, detail in result.events:
        run.log(message, level=level, detail=detail)

    run.fields_filled = result.filled
    run.fields_skipped = result.skipped
    run.unanswered_questions = result.unanswered
    run.resume_uploaded = result.resume_uploaded
    run.submit_attempted = result.submit_attempted
    run.save(
        update_fields=[
            "fields_filled", "fields_skipped", "unanswered_questions",
            "resume_uploaded", "submit_attempted",
        ]
    )
    _attach_screenshot(run, result.screenshot_path)

    if result.error:
        run.mark_finished(
            AutomationRun.Status.FAILED, stop_reason=result.stop_reason, error=result.error
        )
    elif result.submitted:
        run.mark_finished(AutomationRun.Status.SUBMITTED, stop_reason=result.stop_reason)
    else:
        run.mark_finished(
            AutomationRun.Status.AWAITING_REVIEW,
            stop_reason=result.stop_reason or refusal,
        )

    _record_application(run, result)
    return run


def _attach_screenshot(run: AutomationRun, path: str | None) -> None:
    if not path:
        return
    try:
        with open(path, "rb") as handle:
            run.screenshot.save(f"run_{run.pk}.png", ContentFile(handle.read()), save=True)
    except OSError as exc:
        logger.warning("Could not attach screenshot for run %s: %s", run.pk, exc)


@transaction.atomic
def _record_application(run: AutomationRun, result) -> None:
    """Persist the attempt as an Application row.

    An assisted run lands in PREPARED, not SUBMITTED - the dashboard shows a
    'I submitted this' button, and only the user pressing it advances the job
    to Applied. That keeps the tracker honest about what actually went out.
    """
    if run.status in (AutomationRun.Status.UNSUPPORTED, AutomationRun.Status.CANCELLED):
        return

    submitted_via_api = run.status == AutomationRun.Status.SUBMITTED
    application = run.application or Application(user=run.user, job=run.job)
    application.resume = run.resume
    application.method = (
        Application.Method.API if submitted_via_api else Application.Method.ASSISTED
    )
    application.answers = run.fields_filled
    application.error_message = run.error_message

    if run.status == AutomationRun.Status.FAILED:
        application.outcome = Application.Outcome.FAILED
    elif submitted_via_api:
        application.outcome = Application.Outcome.SUBMITTED
        application.submitted_at = timezone.now()
    else:
        application.outcome = Application.Outcome.PREPARED

    application.save()

    if run.application_id != application.pk:
        run.application = application
        run.save(update_fields=["application"])

    # Only a genuine submission moves the job forward and starts the clock on
    # a follow-up. A prepared form has not been sent anywhere yet.
    if submitted_via_api:
        job = run.job
        if job.status == JobStatus.SAVED:
            job.status = JobStatus.APPLIED
            job.save()
            JobStatusHistory.objects.create(
                job=job,
                from_status=JobStatus.SAVED,
                to_status=JobStatus.APPLIED,
                note="Submitted through the official API",
            )
        schedule_follow_up(application)
