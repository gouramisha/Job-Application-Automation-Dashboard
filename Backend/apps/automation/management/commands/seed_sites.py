"""Seed the automation allowlist.

Everything here ships with ``supports_official_api=False``: assisted filling
only, user presses Submit. Flip that flag for a host only after you have read
that vendor's terms and wired up their documented application API.
"""
from django.core.management.base import BaseCommand

from apps.automation.models import SupportedSite

SITES = [
    {
        "name": "Greenhouse",
        "domain": "greenhouse.io",
        "notes": "Job Boards API is read-only for postings; submission is via the hosted form.",
        "api_docs_url": "https://developers.greenhouse.io/job-board.html",
    },
    {
        "name": "Lever",
        "domain": "lever.co",
        "notes": "Postings API is public; the apply endpoint needs an employer key we do not hold.",
        "api_docs_url": "https://github.com/lever/postings-api",
    },
    {
        "name": "Ashby",
        "domain": "ashbyhq.com",
        "notes": "Standard hosted application form.",
    },
    {
        "name": "Workable",
        "domain": "workable.com",
        "notes": "Hosted form. Selector overrides may be needed for the custom question block.",
    },
    {
        "name": "SmartRecruiters",
        "domain": "smartrecruiters.com",
        "notes": "Hosted form.",
    },
    {
        "name": "Workday",
        "domain": "myworkdayjobs.com",
        "notes": "Multi-step wizard behind a login. The filler handles page one only.",
    },
]


class Command(BaseCommand):
    help = "Populate the supported-site allowlist with common ATS hosts."

    def handle(self, *args, **options):
        created_count = 0
        for entry in SITES:
            _, created = SupportedSite.objects.get_or_create(
                domain=entry["domain"],
                defaults={
                    "name": entry["name"],
                    "is_enabled": True,
                    "supports_official_api": False,
                    "notes": entry.get("notes", ""),
                    "api_docs_url": entry.get("api_docs_url", ""),
                },
            )
            created_count += int(created)
            self.stdout.write(f"  {'added' if created else 'exists'}: {entry['name']}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Allowlist ready: {created_count} added, {len(SITES) - created_count} already present."
            )
        )
        self.stdout.write(
            "All seeded sites are assisted-fill only - you press Submit yourself."
        )
