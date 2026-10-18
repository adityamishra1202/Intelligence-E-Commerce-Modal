"""SyncService: idempotent upserts, safe deactivation, isolation, dry runs."""
import json
import os
import tempfile
from unittest import mock

from django.test import TestCase

from assistant.models import ProductEmbedding
from assistant.tests.fakes import patch_embeddings
from ingestion.models import SyncRun
from ingestion.sync_service import SyncService
from products.models import Product
from websites.models import Website


def record(i, **overrides):
    data = {"id": str(i), "title": f"Acme Wireless Headphones Model {i}", "price": 100 + i,
            "rating": 4.0, "description": f"Model {i}", "features": ["Bluetooth"]}
    data.update(overrides)
    return data


class SyncTestBase(TestCase):
    def setUp(self):
        self.path = self.temp_file()

    def temp_file(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def write(self, records, path=None):
        with open(path or self.path, "w", encoding="utf-8") as handle:
            json.dump(records, handle)

    def site(self, name="Acme", path=None):
        return Website.objects.create(
            name=name, base_url=f"https://{name.lower()}.example.com", connector_type="json_file",
            connector_config={"path": path or self.path, "field_map": {"external_product_id": "id"}},
            default_currency="USD", sync_enabled=True,
        )

    def sync(self, website, **kwargs):
        with patch_embeddings() as embed:
            run = SyncService().run(website, **kwargs)
        run.embed_calls = embed.call_count
        return run


class SyncServiceTests(SyncTestBase):
    def test_first_run_creates_and_embeds(self):
        self.write([record(1), record(2)])
        site = self.site()
        run = self.sync(site)
        self.assertEqual((run.status, run.fetched_count, run.created_count), ("success", 2, 2))
        self.assertEqual(Product.objects.filter(website=site).count(), 2)
        self.assertEqual(ProductEmbedding.objects.filter(product__website=site).count(), 2)
        site.refresh_from_db()
        self.assertEqual(site.last_sync_status, "success")
        self.assertIsNotNone(site.last_synced_at)

    def test_unchanged_second_run_changes_nothing(self):
        self.write([record(1), record(2)])
        site = self.site()
        self.sync(site)
        before = list(Product.objects.filter(website=site).values_list("id", "updated_at"))
        run = self.sync(site)
        self.assertEqual((run.created_count, run.updated_count, run.unchanged_count), (0, 0, 2))
        self.assertEqual(run.embed_calls, 0)
        self.assertEqual(list(Product.objects.filter(website=site).values_list("id", "updated_at")), before)

    def test_price_change_updates_exactly_one_product(self):
        self.write([record(1), record(2)])
        site = self.site()
        self.sync(site)
        self.write([record(1), record(2, price=999)])
        run = self.sync(site)
        self.assertEqual((run.updated_count, run.unchanged_count), (1, 1))
        self.assertEqual(str(Product.objects.get(website=site, external_product_id="2").price), "999.00")
        self.assertEqual(run.embed_calls, 0)  # price is not part of the embedding text

    def test_text_change_reembeds_only_that_product(self):
        self.write([record(1), record(2)])
        site = self.site()
        self.sync(site)
        self.write([record(1), record(2, description="Now with noise cancellation")])
        run = self.sync(site)
        self.assertEqual(run.updated_count, 1)
        self.assertEqual(run.embed_calls, 1)

    def test_removed_product_becomes_unavailable(self):
        self.write([record(1), record(2)])
        site = self.site()
        self.sync(site)
        self.write([record(1)])
        run = self.sync(site)
        self.assertEqual(run.deactivated_count, 1)
        self.assertFalse(Product.objects.get(website=site, external_product_id="2").is_available)

    def test_returning_product_becomes_available_again(self):
        self.write([record(1), record(2)])
        site = self.site()
        self.sync(site)
        self.write([record(1)])
        self.sync(site)
        self.write([record(1), record(2)])
        self.sync(site)
        self.assertTrue(Product.objects.get(website=site, external_product_id="2").is_available)

    def test_failed_fetch_deactivates_nothing(self):
        self.write([record(1), record(2)])
        site = self.site()
        self.sync(site)
        with open(self.path, "w") as handle:
            handle.write("{broken")
        run = self.sync(site)
        self.assertEqual(run.status, "failed")
        self.assertEqual(run.deactivated_count, 0)
        self.assertEqual(Product.objects.filter(website=site, is_available=True).count(), 2)
        site.refresh_from_db()
        self.assertEqual(site.last_sync_status, "failed")

    def test_suspicious_shrink_is_not_applied(self):
        self.write([record(i) for i in range(1, 13)])
        site = self.site()
        self.sync(site)
        self.write([record(1), record(2)])
        run = self.sync(site)
        self.assertEqual(run.status, "partial")
        self.assertEqual(run.deactivated_count, 0)
        self.assertTrue(any("suspicious_shrink" in e for e in run.error_summary))
        self.assertEqual(Product.objects.filter(website=site, is_available=True).count(), 12)

    def test_malformed_record_is_counted_and_skipped(self):
        self.write([record(1), {"id": "", "title": "no id", "price": 1}, record(3, price=-5), "not an object"])
        site = self.site()
        run = self.sync(site)
        self.assertEqual(run.status, "partial")
        self.assertEqual((run.fetched_count, run.created_count, run.error_count), (4, 1, 3))
        self.assertEqual(len(run.error_summary), 3)

    def test_two_websites_never_affect_each_other(self):
        other_path = self.temp_file()
        self.write([record(1), record(2)])
        self.write([record(1, title="Other Store Item"), record(9)], other_path)
        first, second = self.site("First"), self.site("Second", path=other_path)
        self.sync(first)
        self.sync(second)
        self.write([record(1)])  # product 2 disappears from the first source only
        self.sync(first)
        self.assertEqual(Product.objects.filter(website=second, is_available=True).count(), 2)
        self.assertEqual(Product.objects.get(website=second, external_product_id="1").title, "Other Store Item")
        self.assertEqual(Product.objects.get(website=first, external_product_id="1").title,
                         "Acme Wireless Headphones Model 1")

    def test_dry_run_writes_no_products(self):
        self.write([record(1), record(2)])
        site = self.site()
        run = self.sync(site, dry_run=True)
        self.assertEqual((run.dry_run, run.created_count), (True, 2))
        self.assertEqual(Product.objects.filter(website=site).count(), 0)
        site.refresh_from_db()
        self.assertIsNone(site.last_synced_at)
        self.assertEqual(SyncRun.objects.filter(website=site).count(), 1)

    def test_embedding_failure_does_not_fail_sync(self):
        self.write([record(1)])
        site = self.site()
        with patch_embeddings(side_effect=RuntimeError("Ollama down")):
            run = SyncService().run(site)
        self.assertEqual(run.status, "partial")
        self.assertEqual(run.created_count, 1)
        self.assertTrue(any("embedding" in e for e in run.error_summary))

    def test_manual_website_fails_cleanly(self):
        site = Website.objects.create(name="Manual", base_url="https://manual.example.com")
        run = SyncService().run(site)
        self.assertEqual(run.status, "failed")
        self.assertTrue(run.error_summary)

    def test_error_summary_is_capped(self):
        self.write([{"id": str(i), "title": "", "price": 1} for i in range(80)])
        run = self.sync(self.site())
        self.assertEqual(run.error_count, 80)
        self.assertEqual(len(run.error_summary), 50)

    def test_brand_is_derived_when_source_has_none(self):
        self.write([record(1, title="Sony WH-CH520 Wireless Headphones")])
        site = self.site()
        self.sync(site)
        self.assertEqual(Product.objects.get(website=site).brand, "Sony")
