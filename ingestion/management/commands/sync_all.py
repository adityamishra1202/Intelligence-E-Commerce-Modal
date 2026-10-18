from django.core.management.base import BaseCommand

from ingestion.management.commands.sync_website import report
from ingestion.sync_service import SyncService
from websites.models import Website


class Command(BaseCommand):
    help = "Synchronise every active website that has sync_enabled set (suitable for Task Scheduler)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        websites = Website.objects.filter(is_active=True, sync_enabled=True).order_by("id")
        if not websites:
            self.stdout.write("No active websites have sync_enabled set.")
            return
        failed = 0
        for website in websites:
            run = SyncService().run(website, dry_run=options["dry_run"], triggered_by="command:sync_all")
            report(self.stdout, self.style, run)
            failed += run.status == "failed"
        self.stdout.write(f"Finished: {len(websites)} website(s), {failed} failed.")
