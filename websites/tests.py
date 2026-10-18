"""GET /api/websites/ contract."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from websites.models import Website


class WebsiteListTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.fresh = Website.objects.create(name="Fresh", base_url="https://fresh.example.com",
                                            default_currency="USD", last_synced_at=now)
        self.old = Website.objects.create(name="Old", base_url="https://old.example.com",
                                          last_synced_at=now - timedelta(days=2))
        self.never = Website.objects.create(name="Never", base_url="https://never.example.com")
        Website.objects.create(name="Hidden", base_url="https://hidden.example.com", is_active=False)

    def test_shape_and_stale_flag(self):
        response = APIClient().get("/api/websites/")
        self.assertEqual(response.status_code, 200)
        rows = {row["name"]: row for row in response.json()}
        self.assertEqual(set(rows), {"Fresh", "Old", "Never"})  # inactive websites hidden
        self.assertEqual(set(rows["Fresh"]), {"id", "name", "base_url", "default_currency", "last_synced_at", "stale"})
        self.assertFalse(rows["Fresh"]["stale"])
        self.assertTrue(rows["Old"]["stale"])
        self.assertTrue(rows["Never"]["stale"])
        self.assertIsNone(rows["Never"]["last_synced_at"])
        self.assertEqual(rows["Fresh"]["default_currency"], "USD")

    def test_no_connector_secrets_exposed(self):
        Website.objects.filter(id=self.fresh.id).update(connector_config={"headers_env": {"X-Key": "SOME_ENV"}})
        text = APIClient().get("/api/websites/").content.decode()
        self.assertNotIn("connector_config", text)
        self.assertNotIn("SOME_ENV", text)
