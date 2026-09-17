"""Aggregations behind the Dashboard and Analytics pages.

All of these are single grouped queries rather than per-status counts in a
loop, so the dashboard stays one round trip to the database regardless of how
many statuses exist.
"""
from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, F
from django.db.models.functions import TruncWeek
from django.utils import timezone

from apps.applications.models import Application
from apps.jobs.models import ACTIVE_STATUSES, SENT_STATUSES, Job, JobStatus
from apps.reminders.models import Reminder


def status_counts(user) -> dict[str, int]:
    """Every status mapped to its count, including the ones sitting at zero."""
    rows = (
        Job.objects.filter(user=user)
        .values("status")
        .annotate(count=Count("id"))
    )
    counts = {status: 0 for status, _ in JobStatus.choices}
    counts.update({row["status"]: row["count"] for row in rows})
    return counts


def summary(user) -> dict:
    """The stat tiles across the top of the dashboard."""
    counts = status_counts(user)
    total_jobs = sum(counts.values())
    applications_sent = sum(counts[s] for s in SENT_STATUSES)
    shortlisted = counts[JobStatus.SHORTLISTED]
    interviews = counts[JobStatus.INTERVIEW]
    selected = counts[JobStatus.SELECTED]
    rejected = counts[JobStatus.REJECTED]

    def rate(numerator: int, denominator: int) -> float:
        return round(numerator / denominator * 100, 1) if denominator else 0.0

    # Interview rate and offer rate are both measured against applications
    # actually sent - measuring against total_jobs would flatter the numbers
    # by counting jobs that were only ever saved.
    return {
        "total_jobs": total_jobs,
        "saved": counts[JobStatus.SAVED],
        "applications_sent": applications_sent,
        "shortlisted": shortlisted,
        "interviews": interviews,
        "selected": selected,
        "rejected": rejected,
        "in_progress": sum(counts[s] for s in ACTIVE_STATUSES),
        "response_rate": rate(shortlisted + interviews + selected + rejected, applications_sent),
        "interview_rate": rate(interviews + selected, applications_sent),
        "success_rate": rate(selected, applications_sent),
        "rejection_rate": rate(rejected, applications_sent),
        "pending_reminders": Reminder.objects.filter(user=user, is_done=False).count(),
        "overdue_reminders": Reminder.objects.filter(
            user=user, is_done=False, due_date__lt=timezone.localdate()
        ).count(),
    }


def funnel(user) -> list[dict]:
    """Applied -> Shortlisted -> Interview -> Selected, with drop-off.

    Each stage counts everyone who reached *at least* that stage, so the
    funnel only ever narrows.
    """
    counts = status_counts(user)
    reached_applied = sum(counts[s] for s in SENT_STATUSES)
    reached_shortlist = (
        counts[JobStatus.SHORTLISTED] + counts[JobStatus.INTERVIEW] + counts[JobStatus.SELECTED]
    )
    reached_interview = counts[JobStatus.INTERVIEW] + counts[JobStatus.SELECTED]
    reached_selected = counts[JobStatus.SELECTED]

    stages = [
        ("Applied", reached_applied),
        ("Shortlisted", reached_shortlist),
        ("Interview", reached_interview),
        ("Selected", reached_selected),
    ]
    top = reached_applied or 1
    return [
        {"stage": name, "count": count, "percent": round(count / top * 100, 1)}
        for name, count in stages
    ]


def timeline(user, days: int = 30, bucket: str = "day") -> list[dict]:
    """Applications per day (or week) over a window, zero-filled.

    Zero-filling matters: Recharts draws a misleading line if it only gets the
    days that happened to have activity.
    """
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    by_week = bucket == "week"

    queryset = Job.objects.filter(
        user=user, applied_date__gte=start, applied_date__lte=today
    )
    if by_week:
        # TruncWeek snaps to the Monday of each week, so the zero-fill cursor
        # below has to start on a Monday too or the keys never line up.
        rows = (
            queryset.annotate(period=TruncWeek("applied_date"))
            .values("period")
            .annotate(count=Count("id"))
        )
        start -= timedelta(days=start.weekday())
    else:
        # applied_date is already a DateField - truncating it is both
        # unnecessary and, on SQLite, broken.
        rows = queryset.values(period=F("applied_date")).annotate(count=Count("id"))

    by_period = {}
    for row in rows:
        period = row["period"]
        if period is None:
            continue
        by_period[period.date() if hasattr(period, "date") else period] = row["count"]

    step = 7 if by_week else 1
    points, cursor = [], start
    while cursor <= today:
        points.append({"date": cursor.isoformat(), "applications": by_period.get(cursor, 0)})
        cursor += timedelta(days=step)
    return points


def status_timeline(user, days: int = 90) -> list[dict]:
    """Outcome transitions per week - the stacked area chart on Analytics."""
    start = timezone.localdate() - timedelta(days=days)
    rows = (
        Job.objects.filter(user=user, created_at__date__gte=start)
        .annotate(period=TruncWeek("created_at"))
        .values("period", "status")
        .annotate(count=Count("id"))
        .order_by("period")
    )

    buckets: dict[str, dict] = {}
    for row in rows:
        key = row["period"].date().isoformat()
        bucket = buckets.setdefault(
            key, {"date": key, **{status: 0 for status, _ in JobStatus.choices}}
        )
        bucket[row["status"]] = row["count"]
    return list(buckets.values())


def _labelled_breakdown(rows, value_key: str, labels: dict[str, str] | None = None):
    return [
        {
            "key": row[value_key] or "unknown",
            "label": (labels or {}).get(row[value_key], row[value_key] or "Unknown"),
            "count": row["count"],
        }
        for row in rows
    ]


def breakdowns(user) -> dict:
    """Slices for the Analytics page pies and bars."""
    jobs = Job.objects.filter(user=user)

    # Status is ordinal, and the chart colours it with a light-to-dark ramp.
    # Sorting by count would scramble that ramp, so these rows stay in
    # lifecycle order and include the statuses sitting at zero.
    status_totals = dict(
        jobs.values_list("status").annotate(count=Count("id"))
    )
    by_status = [
        {"status": value, "count": status_totals.get(value, 0)}
        for value, _ in JobStatus.choices
    ]
    by_source = jobs.values("source").annotate(count=Count("id")).order_by("-count")
    by_company = (
        jobs.values("company_name").annotate(count=Count("id")).order_by("-count")[:10]
    )
    by_method = (
        Application.objects.filter(user=user)
        .values("method")
        .annotate(count=Count("id"))
        .order_by("-count")
    )


    status_labels = dict(JobStatus.choices)
    source_labels = dict(Job._meta.get_field("source").choices)
    method_labels = dict(Application._meta.get_field("method").choices)

    return {
        "by_status": _labelled_breakdown(by_status, "status", status_labels),
        "by_source": _labelled_breakdown(by_source, "source", source_labels),
        "by_method": _labelled_breakdown(by_method, "method", method_labels),
        "top_companies": [
            {"key": row["company_name"], "label": row["company_name"], "count": row["count"]}
            for row in by_company
        ],
    }


def recent_applications(user, limit: int = 8) -> list:
    """Rows for the dashboard's Recent applications table."""
    return list(
        Application.objects.filter(user=user)
        .select_related("job", "resume")
        .order_by("-created_at")[:limit]
    )


def upcoming_reminders(user, days: int = 14, limit: int = 6) -> list:
    horizon = timezone.localdate() + timedelta(days=days)
    return list(
        Reminder.objects.filter(user=user, is_done=False, due_date__lte=horizon)
        .select_related("job")
        .order_by("due_date")[:limit]
    )
