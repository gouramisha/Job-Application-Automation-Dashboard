"""Reminder creation that other apps call into."""
from datetime import timedelta

from django.utils import timezone

from .models import Reminder


def schedule_follow_up(application):
    """Create the post-application follow-up nudge, honouring user settings.

    Returns the Reminder, or None when the user has auto-scheduling switched
    off. Safe to call more than once for the same application.
    """
    user = application.user
    settings_obj = getattr(user, "settings", None)
    if settings_obj is None or not settings_obj.auto_create_follow_ups:
        return None

    existing = Reminder.objects.filter(
        user=user, application=application, kind=Reminder.Kind.FOLLOW_UP
    ).first()
    if existing:
        return existing

    days = settings_obj.default_follow_up_days or 7
    job = application.job
    return Reminder.objects.create(
        user=user,
        job=job,
        application=application,
        kind=Reminder.Kind.FOLLOW_UP,
        title=f"Follow up with {job.company_name} about {job.job_title}",
        due_date=timezone.localdate() + timedelta(days=days),
        notes="Auto-scheduled when the application was recorded.",
    )
