from django.db import models
from django.utils import timezone


class JobStatus(models.TextChoices):
    """The application lifecycle. Ordering matters: the analytics funnel and
    the conversion-rate calculation both walk this list in order."""

    SAVED = "saved", "Saved"
    APPLIED = "applied", "Applied"
    SHORTLISTED = "shortlisted", "Shortlisted"
    INTERVIEW = "interview", "Interview"
    SELECTED = "selected", "Selected"
    REJECTED = "rejected", "Rejected"


#: Statuses that mean the user actually submitted an application.
ACTIVE_STATUSES = [
    JobStatus.APPLIED,
    JobStatus.SHORTLISTED,
    JobStatus.INTERVIEW,
    JobStatus.SELECTED,
]

#: Statuses that count as "an application was sent" for conversion metrics.
SENT_STATUSES = ACTIVE_STATUSES + [JobStatus.REJECTED]


class Job(models.Model):
    """A single job opportunity tracked by one user."""

    class Source(models.TextChoices):
        LINKEDIN = "linkedin", "LinkedIn"
        INDEED = "indeed", "Indeed"
        NAUKRI = "naukri", "Naukri"
        GLASSDOOR = "glassdoor", "Glassdoor"
        GREENHOUSE = "greenhouse", "Greenhouse"
        LEVER = "lever", "Lever"
        COMPANY_SITE = "company_site", "Company site"
        REFERRAL = "referral", "Referral"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="jobs"
    )

    company_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    job_url = models.URLField(max_length=500, blank=True)
    salary = models.CharField(
        max_length=120, blank=True, help_text="Free text, e.g. '18-24 LPA' or '$120k'."
    )
    experience_required = models.CharField(
        max_length=120, blank=True, help_text="Free text, e.g. '3-5 years'."
    )
    skills = models.TextField(blank=True, help_text="Comma-separated skills.")
    job_description = models.TextField(blank=True)
    source = models.CharField(max_length=32, choices=Source.choices, default=Source.OTHER)
    status = models.CharField(
        max_length=20, choices=JobStatus.choices, default=JobStatus.SAVED, db_index=True
    )
    applied_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    is_remote = models.BooleanField(default=False)
    is_favourite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs_job"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "-created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job_url"],
                condition=~models.Q(job_url=""),
                name="unique_job_url_per_user",
            )
        ]

    def __str__(self):
        return f"{self.job_title} @ {self.company_name}"

    @property
    def skill_list(self) -> list[str]:
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    def save(self, *args, **kwargs):
        # Moving a job into a "sent" state without a date is almost always an
        # oversight in the UI, so backfill today rather than lose the datapoint.
        if self.status in SENT_STATUSES and self.applied_date is None:
            self.applied_date = timezone.localdate()
        super().save(*args, **kwargs)


class JobStatusHistory(models.Model):
    """Append-only log of status transitions. Drives the analytics timeline
    and the 'time to interview' style metrics."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, choices=JobStatus.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=JobStatus.choices)
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "jobs_status_history"
        ordering = ["-changed_at"]
        verbose_name_plural = "job status history"

    def __str__(self):
        return f"{self.job_id}: {self.from_status or '-'} -> {self.to_status}"
