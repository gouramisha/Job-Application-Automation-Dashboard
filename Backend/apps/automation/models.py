from django.db import models
from django.utils import timezone


class SupportedSite(models.Model):
    """Allowlist of application hosts the form filler will touch.

    Two separate flags on purpose:

    * ``is_enabled`` - the filler may open pages on this host and type into
      the form. This is assistive: a human still reviews and submits.
    * ``supports_official_api`` - the vendor publishes a documented
      application API. Only these hosts are ever eligible for an automated
      submit, and even then the global and per-user switches must also be on.

    Anything not listed here is refused outright rather than fumbled at.
    """

    name = models.CharField(max_length=100, unique=True)
    domain = models.CharField(
        max_length=180, unique=True, help_text="Hostname, e.g. 'boards.greenhouse.io'."
    )
    is_enabled = models.BooleanField(
        default=True, help_text="Allow assisted form filling on this host."
    )
    supports_official_api = models.BooleanField(
        default=False,
        help_text="Vendor publishes a documented application API. Required for auto-submit.",
    )
    api_docs_url = models.URLField(blank=True)
    notes = models.TextField(
        blank=True, help_text="Terms-of-service notes, quirks, selector overrides."
    )
    selector_overrides = models.JSONField(
        default=dict, blank=True,
        help_text="canonical_field -> CSS selector, for sites the generic heuristics miss.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automation_supported_site"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.domain})"

    @property
    def auto_submit_eligible(self) -> bool:
        return self.is_enabled and self.supports_official_api


class AutomationRun(models.Model):
    """One execution of the form filler against one job posting.

    Created by the API in ``QUEUED`` state and picked up by the worker
    process, so a browser never spins up inside a web request.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        AWAITING_REVIEW = "awaiting_review", "Filled - awaiting your review and submit"
        SUBMITTED = "submitted", "Submitted via official API"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        UNSUPPORTED = "unsupported", "Site not supported"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="automation_runs"
    )
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="automation_runs"
    )
    application = models.OneToOneField(
        "applications.Application", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="automation_run",
    )
    resume = models.ForeignKey(
        "resumes.Resume", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="automation_runs",
    )
    site = models.ForeignKey(
        SupportedSite, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="runs",
    )

    target_url = models.URLField(max_length=500)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True
    )

    # What the run actually managed to do
    fields_filled = models.JSONField(
        default=dict, blank=True, help_text="canonical_field -> value that was typed."
    )
    fields_skipped = models.JSONField(
        default=list, blank=True, help_text="Fields found but left for the user."
    )
    unanswered_questions = models.JSONField(
        default=list, blank=True,
        help_text="Questions with no saved answer. Surfaced so the user can add them.",
    )
    resume_uploaded = models.BooleanField(default=False)
    screenshot = models.ImageField(upload_to="automation/screenshots/", blank=True, null=True)

    # Why it stopped where it stopped
    submit_attempted = models.BooleanField(default=False)
    stop_reason = models.CharField(
        max_length=255, blank=True,
        help_text="Why the run halted before submitting, in plain language.",
    )
    error_message = models.TextField(blank=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automation_run"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "-created_at"]), models.Index(fields=["status"])]

    def __str__(self):
        return f"Run #{self.pk} {self.target_url} [{self.status}]"

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        return self.status not in {self.Status.QUEUED, self.Status.RUNNING}

    def log(self, message: str, level: str = "info", detail: dict | None = None):
        return AutomationLog.objects.create(
            run=self, level=level, message=message, detail=detail or {}
        )

    def mark_started(self):
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def mark_finished(self, status: str, stop_reason: str = "", error: str = ""):
        self.status = status
        self.stop_reason = stop_reason
        self.error_message = error
        self.finished_at = timezone.now()
        self.save(
            update_fields=["status", "stop_reason", "error_message", "finished_at"]
        )


class AutomationLog(models.Model):
    """Step-by-step trace of a run, streamed to the dashboard detail panel."""

    class Level(models.TextChoices):
        DEBUG = "debug", "Debug"
        INFO = "info", "Info"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    run = models.ForeignKey(AutomationRun, on_delete=models.CASCADE, related_name="logs")
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    message = models.CharField(max_length=500)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "automation_log"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.level}] {self.message}"
