"""Worker loop that executes queued automation runs.

Kept out of the request/response cycle on purpose: a Playwright browser can
sit open for minutes waiting for the user to review a filled form, which is
not something a WSGI worker should be holding.

    python manage.py run_automation_worker           # poll forever
    python manage.py run_automation_worker --once    # drain and exit
    python manage.py run_automation_worker --run-id 7
"""
import time

from django.core.management.base import BaseCommand, CommandError

from apps.automation.models import AutomationRun
from apps.automation.services import execute_run


class Command(BaseCommand):
    help = "Execute queued Playwright form-fill runs."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Drain the queue and exit.")
        parser.add_argument("--run-id", type=int, help="Execute one specific run and exit.")
        parser.add_argument(
            "--interval", type=float, default=3.0, help="Seconds between polls (default 3)."
        )

    def handle(self, *args, **options):
        if options["run_id"]:
            run = AutomationRun.objects.filter(pk=options["run_id"]).first()
            if run is None:
                raise CommandError(f"No automation run with id {options['run_id']}.")
            self._execute(run)
            return

        self.stdout.write(self.style.SUCCESS("Automation worker started. Ctrl+C to stop."))
        while True:
            queued = AutomationRun.objects.filter(
                status=AutomationRun.Status.QUEUED
            ).order_by("created_at")

            if not queued.exists():
                if options["once"]:
                    self.stdout.write("Queue is empty. Exiting.")
                    return
                time.sleep(options["interval"])
                continue

            for run in queued:
                self._execute(run)

    def _execute(self, run):
        self.stdout.write(f"Run #{run.pk}: {run.target_url}")
        try:
            execute_run(run)
        except Exception as exc:  # noqa: BLE001 - one bad run must not kill the loop
            run.refresh_from_db()
            run.log(f"Worker crashed: {exc}", level="error")
            run.mark_finished(AutomationRun.Status.FAILED, error=str(exc))
            self.stderr.write(self.style.ERROR(f"Run #{run.pk} failed: {exc}"))
            return

        run.refresh_from_db()
        style = self.style.SUCCESS if run.status != AutomationRun.Status.FAILED else self.style.ERROR
        self.stdout.write(style(f"Run #{run.pk}: {run.get_status_display()}"))
        if run.stop_reason:
            self.stdout.write(f"  {run.stop_reason}")
