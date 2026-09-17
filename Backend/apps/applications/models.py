from django.db import models
from django.utils import timezone


class Application(models.Model):
    """A concrete attempt to apply to a job.

    A Job carries the lifecycle status; an Application records each submission
    (manual or automation-assisted), which resume went with it, and what the
    user answered. One job can have several attempts — a re-apply after six
    months, or a retry with a different resume.
    """

    class Method(models.TextChoices):
        MANUAL = "manual", "Filled manually"
        ASSISTED = "assisted", "Automation-assisted"
        API = "api", "Official API"

    class Outcome(models.TextChoices):
        DRAFT = "draft", "Draft"
        PREPARED = "prepared", "Prepared — awaiting your submit"
        SUBMITTED = "submitted", "Submitted"
        FAILED = "failed", "Failed"
        ABANDONED = "abandoned", "Abandoned"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="applications"
    )
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="applications"
    )
    resume = models.ForeignKey(
        "resumes.Resume",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
        help_text="Which resume was sent. Kept if the resume is later deleted.",
    )
    resume_name_snapshot = models.CharField(
        max_length=150, blank=True,
        help_text="Resume label at submission time, so history survives deletion.",
    )

    method = models.CharField(max_length=16, choices=Method.choices, default=Method.MANUAL)
    outcome = models.CharField(
        max_length=16, choices=Outcome.choices, default=Outcome.DRAFT, db_index=True
    )

    cover_letter = models.TextField(blank=True)
    answers = models.JSONField(
        default=dict, blank=True,
        help_text="Screening question -> answer pairs used for this application.",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "applications_application"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "outcome"]),
        ]

    def __str__(self):
        return f"{self.job} ({self.get_outcome_display()})"

    def save(self, *args, **kwargs):
        if self.resume and not self.resume_name_snapshot:
            self.resume_name_snapshot = self.resume.name
        if self.outcome == self.Outcome.SUBMITTED and self.submitted_at is None:
            self.submitted_at = timezone.now()
        super().save(*args, **kwargs)
