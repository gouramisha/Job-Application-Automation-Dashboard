from django.db import models
from django.utils import timezone


class Reminder(models.Model):
    """A dated nudge - usually a follow-up on an application that has gone
    quiet, sometimes an interview or a posting deadline."""

    class Kind(models.TextChoices):
        FOLLOW_UP = "follow_up", "Follow up"
        INTERVIEW = "interview", "Interview"
        DEADLINE = "deadline", "Application deadline"
        TASK = "task", "Task"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="reminders"
    )
    job = models.ForeignKey(
        "jobs.Job", on_delete=models.CASCADE, related_name="reminders",
        null=True, blank=True,
    )
    application = models.ForeignKey(
        "applications.Application", on_delete=models.SET_NULL,
        related_name="reminders", null=True, blank=True,
    )

    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.FOLLOW_UP)
    due_date = models.DateField(db_index=True)
    notes = models.TextField(blank=True)
    is_done = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reminders_reminder"
        ordering = ["is_done", "due_date"]
        indexes = [models.Index(fields=["user", "is_done", "due_date"])]

    def __str__(self):
        return f"{self.title} ({self.due_date})"

    @property
    def is_overdue(self) -> bool:
        return not self.is_done and self.due_date < timezone.localdate()

    @property
    def days_until_due(self) -> int:
        return (self.due_date - timezone.localdate()).days

    def mark_done(self):
        self.is_done = True
        self.completed_at = timezone.now()
        self.save(update_fields=["is_done", "completed_at", "updated_at"])

    def reopen(self):
        self.is_done = False
        self.completed_at = None
        self.save(update_fields=["is_done", "completed_at", "updated_at"])
