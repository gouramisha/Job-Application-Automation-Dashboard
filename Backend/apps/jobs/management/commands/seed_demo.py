"""Create a demo account with a realistic spread of jobs, applications and
reminders - enough for the dashboard charts to look like a real search.

    python manage.py seed_demo
    python manage.py seed_demo --reset
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.applications.models import Application
from apps.jobs.models import Job, JobStatus, JobStatusHistory
from apps.reminders.models import Reminder

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPass123!"

COMPANIES = [
    ("Stripe", "Backend Engineer", "Bengaluru, India", "18-28 LPA", "3-5 years"),
    ("Razorpay", "Senior Python Developer", "Remote", "24-34 LPA", "4-7 years"),
    ("Zerodha", "Full Stack Developer", "Bengaluru, India", "20-30 LPA", "3-6 years"),
    ("Freshworks", "Django Developer", "Chennai, India", "16-24 LPA", "2-4 years"),
    ("Atlassian", "Software Engineer II", "Remote", "$110k-$140k", "3-5 years"),
    ("Zoho", "Backend Developer", "Chennai, India", "12-18 LPA", "2-4 years"),
    ("Swiggy", "SDE-2 Backend", "Bengaluru, India", "26-38 LPA", "4-6 years"),
    ("PhonePe", "Platform Engineer", "Pune, India", "22-32 LPA", "3-6 years"),
    ("Meesho", "Python Engineer", "Remote", "20-28 LPA", "3-5 years"),
    ("CRED", "Backend Engineer", "Bengaluru, India", "28-40 LPA", "4-8 years"),
    ("Postman", "API Platform Engineer", "Remote", "24-36 LPA", "4-7 years"),
    ("Hasura", "Developer Advocate", "Remote", "18-26 LPA", "2-5 years"),
    ("Chargebee", "Senior Backend Engineer", "Chennai, India", "25-35 LPA", "5-8 years"),
    ("Groww", "Backend Developer", "Bengaluru, India", "20-30 LPA", "3-5 years"),
    ("Dunzo", "Python Developer", "Bengaluru, India", "15-22 LPA", "2-4 years"),
    ("Flipkart", "SDE-2", "Bengaluru, India", "30-45 LPA", "4-7 years"),
    ("Myntra", "Backend Engineer", "Bengaluru, India", "22-32 LPA", "3-6 years"),
    ("Udaan", "Senior Developer", "Remote", "24-34 LPA", "4-7 years"),
]

SKILL_POOL = [
    "Python", "Django", "DRF", "PostgreSQL", "React", "Docker", "AWS",
    "Redis", "Celery", "REST APIs", "Git", "Kubernetes", "GraphQL", "pytest",
]

SOURCES = [s for s, _ in Job.Source.choices if s != "other"]

# Weighted so the funnel narrows the way a real search does.
STATUS_WEIGHTS = [
    (JobStatus.SAVED, 5),
    (JobStatus.APPLIED, 6),
    (JobStatus.SHORTLISTED, 3),
    (JobStatus.INTERVIEW, 2),
    (JobStatus.SELECTED, 1),
    (JobStatus.REJECTED, 4),
]


class Command(BaseCommand):
    help = "Create a demo user with sample jobs, applications and reminders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete the demo user's existing jobs before seeding.",
        )
        parser.add_argument("--email", default=DEMO_EMAIL)

    @transaction.atomic
    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        email = options["email"]
        user, created = User.objects.get_or_create(
            email=email, defaults={"first_name": "Demo", "last_name": "Candidate"}
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user {email}"))
        else:
            self.stdout.write(f"Using existing user {email}")

        self._fill_profile(user)

        if options["reset"]:
            deleted, _ = Job.objects.filter(user=user).delete()
            self.stdout.write(f"Cleared {deleted} existing rows")

        random.seed(42)  # Reproducible demo data across runs.
        jobs = self._create_jobs(user)
        applications = self._create_applications(user, jobs)
        self._create_reminders(user, jobs, applications)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(jobs)} jobs and {len(applications)} applications."
            )
        )
        self.stdout.write(f"Log in with  {email}  /  {DEMO_PASSWORD}")

    def _fill_profile(self, user):
        profile = user.profile
        profile.phone = "+91 98765 43210"
        profile.city, profile.state, profile.country = "Bengaluru", "Karnataka", "India"
        profile.linkedin_url = "https://linkedin.com/in/demo-candidate"
        profile.github_url = "https://github.com/demo-candidate"
        profile.portfolio_url = "https://demo-candidate.dev"
        profile.current_title = "Backend Engineer"
        profile.current_company = "Acme Systems"
        profile.years_experience = 4.5
        profile.skills = "Python, Django, DRF, PostgreSQL, React, Docker, AWS, Redis"
        profile.summary = (
            "Backend engineer with 4+ years building Django APIs at scale. "
            "Comfortable owning a service end to end, from schema design to on-call."
        )
        profile.desired_roles = "Backend Engineer, Senior Python Developer, Full Stack Developer"
        profile.desired_locations = "Bengaluru, Remote"
        profile.open_to_remote = True
        profile.willing_to_relocate = True
        profile.expected_salary_min = 2400000
        profile.expected_salary_max = 3200000
        profile.salary_currency = "INR"
        profile.notice_period_days = 30
        profile.custom_answers = {
            "How did you hear about this role?": "LinkedIn",
            "Why do you want to work here?": (
                "I want to work on high-traffic Python systems with a team that "
                "takes code review and testing seriously."
            ),
        }
        profile.save()

    def _create_jobs(self, user):
        statuses = [s for s, weight in STATUS_WEIGHTS for _ in range(weight)]
        today = timezone.localdate()
        jobs = []

        for index, (company, title, location, salary, experience) in enumerate(COMPANIES):
            status = random.choice(statuses)
            days_ago = random.randint(1, 75)
            applied = None if status == JobStatus.SAVED else today - timedelta(days=days_ago)

            job = Job(
                user=user,
                company_name=company,
                job_title=title,
                location=location,
                job_url=f"https://boards.greenhouse.io/{company.lower().replace(' ', '')}/jobs/{4000 + index}",
                salary=salary,
                experience_required=experience,
                skills=", ".join(random.sample(SKILL_POOL, k=random.randint(4, 7))),
                job_description=(
                    f"{company} is hiring a {title}. You will own backend services, "
                    "design APIs, and work closely with product to ship features that "
                    "reach millions of users."
                ),
                source=random.choice(SOURCES),
                status=status,
                applied_date=applied,
                is_remote="remote" in location.lower(),
                is_favourite=random.random() < 0.2,
                notes=random.choice(
                    ["", "", "Referred by a friend on the platform team.",
                     "Recruiter reached out first.", "Great Glassdoor reviews."]
                ),
            )
            job.save()
            # Backdate creation so the timeline chart is not a single spike.
            Job.objects.filter(pk=job.pk).update(
                created_at=timezone.now() - timedelta(days=days_ago + 2)
            )
            JobStatusHistory.objects.create(
                job=job, from_status="", to_status=JobStatus.SAVED, note="Job added"
            )
            if status != JobStatus.SAVED:
                JobStatusHistory.objects.create(
                    job=job, from_status=JobStatus.SAVED, to_status=status
                )
            jobs.append(job)
        return jobs

    def _create_applications(self, user, jobs):
        applications = []
        for job in jobs:
            if job.status == JobStatus.SAVED:
                continue
            method = random.choice(
                [Application.Method.MANUAL, Application.Method.MANUAL, Application.Method.ASSISTED]
            )
            application = Application.objects.create(
                user=user,
                job=job,
                method=method,
                outcome=Application.Outcome.SUBMITTED,
                submitted_at=timezone.make_aware(
                    timezone.datetime.combine(job.applied_date, timezone.datetime.min.time())
                ) if job.applied_date else timezone.now(),
                answers={"How did you hear about this role?": "LinkedIn"},
                notes="Seeded demo application.",
            )
            applications.append(application)
        return applications

    def _create_reminders(self, user, jobs, applications):
        today = timezone.localdate()
        for application in applications[:6]:
            Reminder.objects.create(
                user=user,
                job=application.job,
                application=application,
                kind=Reminder.Kind.FOLLOW_UP,
                title=f"Follow up with {application.job.company_name}",
                due_date=today + timedelta(days=random.randint(-4, 10)),
                notes="Check in if there has been no response.",
            )

        interviewing = [j for j in jobs if j.status == JobStatus.INTERVIEW]
        for job in interviewing[:2]:
            Reminder.objects.create(
                user=user,
                job=job,
                kind=Reminder.Kind.INTERVIEW,
                title=f"Technical round - {job.company_name}",
                due_date=today + timedelta(days=random.randint(1, 8)),
                notes="Revise system design and the STAR stories.",
            )
