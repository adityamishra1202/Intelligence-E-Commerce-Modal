from django.core.management.base import BaseCommand, CommandError

from ingestion.sync_service import SyncService
from websites.models import Website


def report(stdout, style, run):
    label = " (dry run, nothing written)" if run.dry_run else ""
    stdout.write(
        f"{run.website.name}: {run.status}{label} - fetched {run.fetched_count}, created {run.created_count}, "
        f"updated {run.updated_count}, unchanged {run.unchanged_count}, deactivated {run.deactivated_count}, "
        f"errors {run.error_count}"
        + ("" if run.dry_run else f", embedded {getattr(run, 'embedded_count', 0)}, "
                                  f"embeddings reused {getattr(run, 'embedding_reused_count', 0)}")
    )
    for error in run.error_summary[:10]:
        stdout.write(style.WARNING(f"  - {error}"))
    if len(run.error_summary) > 10:
        stdout.write(f"  ... {len(run.error_summary) - 10} more (see SyncRun {run.id} in the admin)")


class Command(BaseCommand):
    help = "Synchronise one website's products from its connector."

    def add_arguments(self, parser):
        parser.add_argument("--website-id", type=int, required=True)
        parser.add_argument("--dry-run", action="store_true", help="Compute changes without writing products.")

    def handle(self, *args, **options):
        website = Website.objects.filter(id=options["website_id"]).first()
        if website is None:
            raise CommandError(f"Website {options['website_id']} does not exist.")
        run = SyncService().run(website, dry_run=options["dry_run"], triggered_by="command:sync_website")
        report(self.stdout, self.style, run)
        if run.status == "failed":
            raise CommandError("Sync failed.")
