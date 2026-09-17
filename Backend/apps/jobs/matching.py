"""Scores a job against a user's stated search preferences.

The scorer is deliberately transparent rather than clever: every point it
awards comes back as a human-readable reason, so the Jobs > Matches view can
explain itself. Swapping in an external job-board feed later only means
handing `score_job` a different set of Job-shaped objects.
"""
from __future__ import annotations

import re
from decimal import Decimal

WEIGHTS = {"role": 40, "location": 25, "experience": 20, "skills": 15}

_STOPWORDS = {"senior", "junior", "lead", "staff", "principal", "sr", "jr", "i", "ii", "iii"}


def _tokens(value: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9+#.]+", (value or "").lower()) if t}


def _csv(value: str) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(",") if item.strip()]


def _years_required(text: str) -> tuple[float | None, float | None]:
    """Pull a (min, max) year range out of free text like '3-5 years' or '5+'."""
    if not text:
        return None, None
    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return (numbers[0], None) if "+" in text else (numbers[0], numbers[0])
    return min(numbers), max(numbers)


def _role_score(job, desired_roles: list[str]) -> tuple[int, str | None]:
    if not desired_roles:
        return 0, None
    title_tokens = _tokens(job.job_title) - _STOPWORDS
    best, best_role = 0.0, None
    for role in desired_roles:
        role_tokens = _tokens(role) - _STOPWORDS
        if not role_tokens:
            continue
        overlap = len(title_tokens & role_tokens) / len(role_tokens)
        if overlap > best:
            best, best_role = overlap, role
    if best == 0:
        return 0, None
    points = round(WEIGHTS["role"] * best)
    label = "Exact role match" if best >= 0.999 else f"Role overlaps '{best_role}'"
    return points, f"{label} ({job.job_title})"


def _location_score(job, profile) -> tuple[int, str | None]:
    if job.is_remote and profile.open_to_remote:
        return WEIGHTS["location"], "Remote, and you are open to remote"
    desired = _csv(profile.desired_locations)
    job_location = (job.location or "").lower()
    for wanted in desired:
        if wanted and wanted in job_location:
            return WEIGHTS["location"], f"Location matches '{wanted}'"
    if profile.willing_to_relocate and job_location:
        return round(WEIGHTS["location"] * 0.4), "Different city, but you are open to relocating"
    return 0, None


def _experience_score(job, profile) -> tuple[int, str | None]:
    low, high = _years_required(job.experience_required)
    if low is None:
        return 0, None
    years = float(profile.years_experience or Decimal(0))
    if high is None:
        fits = years >= low
        window = f"{low:g}+ years"
    else:
        fits = low <= years <= high
        window = f"{low:g}-{high:g} years"
    if fits:
        return WEIGHTS["experience"], f"Your {years:g} years fits the {window} requirement"
    # Near-misses still surface: being one year short is worth showing.
    gap = low - years if years < low else years - (high or low)
    if gap <= 1:
        return round(WEIGHTS["experience"] * 0.5), f"Close to the {window} requirement"
    return 0, None


def _skills_score(job, profile) -> tuple[int, str | None]:
    mine = set(_csv(profile.skills))
    theirs = set(_csv(job.skills))
    if not mine or not theirs:
        return 0, None
    shared = mine & theirs
    if not shared:
        return 0, None
    ratio = len(shared) / len(theirs)
    preview = ", ".join(sorted(shared)[:4])
    return round(WEIGHTS["skills"] * ratio), f"{len(shared)} matching skills: {preview}"


def score_job(job, profile) -> tuple[int, list[str]]:
    """Return a 0-100 score and the reasons behind it."""
    reasons: list[str] = []
    total = 0
    for scorer in (_role_score, _location_score, _experience_score, _skills_score):
        points, reason = (
            scorer(job, _csv(profile.desired_roles))
            if scorer is _role_score
            else scorer(job, profile)
        )
        total += points
        if reason:
            reasons.append(reason)
    return min(total, 100), reasons


def rank_jobs(jobs, profile, minimum_score: int = 1):
    """Annotate and sort an iterable of jobs by descending match score."""
    ranked = []
    for job in jobs:
        score, reasons = score_job(job, profile)
        if score >= minimum_score:
            job.match_score = score
            job.match_reasons = reasons
            ranked.append(job)
    ranked.sort(key=lambda j: (-j.match_score, j.company_name.lower()))
    return ranked
