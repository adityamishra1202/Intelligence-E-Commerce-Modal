"""End to end: a JSON source is synced, then chat answers from the synced rows."""
from django.core.cache import cache
from rest_framework.test import APIClient

from assistant.tests.fakes import extraction, patch_embeddings, patch_llm, route
from ingestion.tests.test_sync_service import SyncTestBase
from websites.models import Website

URL = "/api/chat/"
HEADPHONES = extraction(keywords=["headphones"], category="headphones")


def source_record(i, title, price, brand=None, **extra):
    data = {"sku": f"S-{i}", "name": title, "cost": price, "stars": 4.5, "type": "headphones",
            "stock": "yes", "link": f"https://shop.example.com/p/{i}"}
    if brand:
        data["maker"] = brand
    data.update(extra)
    return data


# The only thing a new JSON-based website needs: a field_map from its names to canonical names.
FIELD_MAP = {"external_product_id": "sku", "title": "name", "price": "cost", "rating": "stars",
             "category": "type", "is_available": "stock", "product_url": "link", "brand": "maker"}


class SyncThenChatTests(SyncTestBase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.client = APIClient()

    def new_site(self, name, records):
        path = self.temp_file()
        self.write(records, path)
        return Website.objects.create(
            name=name, base_url=f"https://{name.lower()}.example.com", connector_type="json_file",
            connector_config={"path": path, "field_map": FIELD_MAP}, default_currency="USD", sync_enabled=True,
        ), path

    def chat(self, message, website_ids, llm=None):
        with patch_llm(default=llm or route(HEADPHONES)), patch_embeddings():
            return self.client.post(URL, {"message": message, "website_ids": website_ids}, format="json").json()

    def test_fourth_json_website_needs_only_configuration(self):
        site, _ = self.new_site("Fourth", [
            source_record(1, "Sony WH-CH720N Wireless Headphones", 99.00),
            source_record(2, "Acme Studio Headphones", 59.00, brand="Acme"),
        ])
        run = self.sync(site)
        self.assertEqual((run.status, run.created_count), ("success", 2))

        data = self.chat("Sony headphones under $150", [site.id],
                         llm=route(extraction(keywords=["headphones"], category="headphones", brand="Sony",
                                              max_price=150, currency="USD")))
        self.assertEqual([p["title"] for p in data["products"]], ["Sony WH-CH720N Wireless Headphones"])
        product = data["products"][0]
        self.assertEqual(product["brand"], "Sony")  # derived from the title
        self.assertEqual(product["product_url"], "https://shop.example.com/p/1")
        self.assertEqual(product["price"], "99.00")
        self.assertFalse(data["website_freshness"][0]["stale"])
        self.assertEqual(data["notices"], [])

    def test_price_change_in_source_reaches_the_next_chat(self):
        site, path = self.new_site("Pricey", [
            source_record(1, "Acme Wireless Headphones", 120.00),
            source_record(2, "Acme Studio Headphones", 80.00),
        ])
        self.sync(site)
        self.write([
            source_record(1, "Acme Wireless Headphones", 95.50),
            source_record(2, "Acme Studio Headphones", 80.00),
        ], path)
        run = self.sync(site)
        self.assertEqual((run.updated_count, run.unchanged_count, run.embed_calls), (1, 1, 0))

        data = self.chat("Acme headphones", [site.id])
        prices = {p["title"]: p["price"] for p in data["products"]}
        self.assertEqual(prices["Acme Wireless Headphones"], "95.50")

    def test_scope_isolation_between_synced_sites(self):
        one, _ = self.new_site("One", [source_record(1, "Acme Headphones One", 50)])
        two, _ = self.new_site("Two", [source_record(1, "Acme Headphones Two", 60)])
        self.sync(one)
        self.sync(two)
        data = self.chat("headphones", [two.id])
        self.assertEqual({p["website_name"] for p in data["products"]}, {"Two"})
        both = self.chat("headphones", [one.id, two.id])
        self.assertEqual(both["total_products"], 2)
        self.assertEqual(len(both["website_freshness"]), 2)
