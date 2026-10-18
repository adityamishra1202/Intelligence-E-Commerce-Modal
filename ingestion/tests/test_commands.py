"""Management commands: sync_website, sync_all, export_website_json, import_shopzone."""
import json
import os
import tempfile
from io import StringIO
from unittest import mock

from django.core.management import CommandError, call_command

from assistant.tests.fakes import patch_embeddings
from ingestion.models import SyncRun
from ingestion.tests.test_sync_service import SyncTestBase, record
from products.models import Product
from websites.models import Website


class CommandTests(SyncTestBase):
    def call(self, *args):
        out = StringIO()
        with patch_embeddings():
            call_command(*args, stdout=out)
        return out.getvalue()

    def test_sync_website_dry_run_writes_nothing(self):
        self.write([record(1), record(2)])
        site = self.site()
        output = self.call("sync_website", "--website-id", str(site.id), "--dry-run")
        self.assertIn("dry run", output)
        self.assertIn("created 2", output)
        self.assertEqual(Product.objects.filter(website=site).count(), 0)
        self.assertTrue(SyncRun.objects.get(website=site).dry_run)

    def test_sync_website_writes(self):
        self.write([record(1)])
        site = self.site()
        self.call("sync_website", "--website-id", str(site.id))
        self.assertEqual(Product.objects.filter(website=site).count(), 1)

    def test_unknown_website(self):
        with self.assertRaises(CommandError):
            self.call("sync_website", "--website-id", "999999")

    def test_failed_sync_exits_with_error(self):
        site = self.site(path=os.path.join(tempfile.gettempdir(), "does-not-exist-ecommerceai.json"))
        with self.assertRaises(CommandError):
            self.call("sync_website", "--website-id", str(site.id))

    def test_sync_all_only_enabled_active_sites(self):
        self.write([record(1)])
        enabled = self.site("Enabled")
        disabled = self.site("Disabled")
        disabled.sync_enabled = False
        disabled.save()
        output = self.call("sync_all")
        self.assertIn("1 website(s), 0 failed", output)
        self.assertEqual(Product.objects.filter(website=enabled).count(), 1)
        self.assertEqual(Product.objects.filter(website=disabled).count(), 0)

    def test_export_then_reimport_is_unchanged(self):
        self.write([record(1, brand="Acme"), record(2)])
        site = self.site()
        self.call("sync_website", "--website-id", str(site.id))
        exported = self.temp_file()
        self.call("export_website_json", "--website-id", str(site.id), "--output", exported)
        rows = json.load(open(exported, encoding="utf-8"))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["external_product_id"], "1")
        self.assertIsInstance(rows[0]["price"], str)

        # A second website onboarded from the export needs only configuration.
        copy = Website.objects.create(
            name="Copy", base_url="https://copy.example.com", connector_type="json_file",
            connector_config={"path": exported}, default_currency="USD", sync_enabled=True,
        )
        self.call("sync_website", "--website-id", str(copy.id))
        original = {p.external_product_id: (p.title, p.price, p.brand) for p in Product.objects.filter(website=site)}
        copied = {p.external_product_id: (p.title, p.price, p.brand) for p in Product.objects.filter(website=copy)}
        self.assertEqual(original, copied)

    def test_import_shopzone_uses_sync_service(self):
        self.write([{"id": 1, "title": "Acme Wireless Headphones", "price": 49.99, "rating": 4.2,
                     "category": "headphones", "inStock": True}])
        env = {"SHOPZONE_BASE_URL": "https://shopzone.example.com", "SHOPZONE_CURRENCY": "USD"}
        with mock.patch.dict(os.environ, env):
            site = Website.objects.create(name="ShopZone", base_url=env["SHOPZONE_BASE_URL"],
                                          connector_type="shopzone", connector_config={"path": self.path},
                                          default_currency="USD")
            self.call("import_shopzone")
        site.refresh_from_db()
        self.assertEqual(site.last_sync_status, "success")
        self.assertEqual(Product.objects.filter(website=site).count(), 1)
        self.assertEqual(SyncRun.objects.get(website=site).triggered_by, "command:import_shopzone")

    def test_import_shopzone_requires_env(self):
        with mock.patch.dict(os.environ, {"SHOPZONE_BASE_URL": "", "SHOPZONE_CURRENCY": ""}):
            with self.assertRaises(CommandError):
                self.call("import_shopzone")
