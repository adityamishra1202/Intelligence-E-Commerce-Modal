"""
Kept so existing instructions keep working. It now runs the ShopZone connector
through the shared SyncService instead of writing products itself.
"""
import os

from django.core.management.base import BaseCommand, CommandError

from ingestion.management.commands.sync_website import report
from ingestion.sync_service import SyncService
from websites.models import Website


class Command(BaseCommand):
    help = "Import ShopZone products from products-export.json (via the ShopZone connector)."

    def handle(self, *args, **options):
        base_url = os.environ.get("SHOPZONE_BASE_URL")
        currency = (os.environ.get("SHOPZONE_CURRENCY") or "").upper()
        if not base_url or len(currency) != 3:
            raise CommandError("Set SHOPZONE_BASE_URL and a three-letter SHOPZONE_CURRENCY before importing.")

        website, _ = Website.objects.get_or_create(base_url=base_url, defaults={"name": "ShopZone", "is_active": True})
        changed = []
        if website.connector_type == "manual":
            website.connector_type = "shopzone"
            changed.append("connector_type")
        if not website.default_currency:
            website.default_currency = currency
            changed.append("default_currency")
        if changed:
            website.save(update_fields=changed + ["updated_at"])

        run = SyncService().run(website, triggered_by="command:import_shopzone")
        report(self.stdout, self.style, run)
        if run.status == "failed":
            raise CommandError("Import failed.")
