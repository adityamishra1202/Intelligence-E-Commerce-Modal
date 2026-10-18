from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from websites.models import Website
from products.models import Product


class ProductListAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        # Create two separate websites.
        self.shopzone = Website.objects.create(
            name="ShopZone",
            base_url="https://shopzone.example.com",
            is_active=True,
        )

        self.other_site = Website.objects.create(
            name="OtherStore",
            base_url="https://otherstore.example.com",
            is_active=True,
        )

        # Product belonging to ShopZone.
        self.iphone = Product.objects.create(
            website=self.shopzone,
            external_product_id="SZ-001",
            title="Apple iPhone 15 Pro",
            description="Apple smartphone",
            category="Electronics",
            price=Decimal("999.00"),
            currency="USD",
            is_available=True,
        )

        # Another product belonging to ShopZone.
        self.headphones = Product.objects.create(
            website=self.shopzone,
            external_product_id="SZ-002",
            title="Sony Headphones",
            description="Wireless headphones",
            category="Electronics",
            price=Decimal("199.00"),
            currency="USD",
            is_available=True,
        )

        # Product belonging to another website.
        self.other_product = Product.objects.create(
            website=self.other_site,
            external_product_id="OS-001",
            title="OtherStore Laptop",
            description="Laptop from another store",
            category="Electronics",
            price=Decimal("799.00"),
            currency="USD",
            is_available=True,
        )

    def get_products(self, **params):
        return self.client.get(
            "/api/products/",
            params,
        )

    def test_website_filter_prevents_cross_website_results(self):
        response = self.get_products(
            website_id=self.shopzone.id
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        returned_ids = {
            item["external_product_id"]
            for item in results
        }

        self.assertEqual(
            returned_ids,
            {"SZ-001", "SZ-002"},
        )

        self.assertNotIn(
            "OS-001",
            returned_ids,
        )

    def test_website_id_is_required(self):
        response = self.get_products()

        self.assertEqual(response.status_code, 400)

    def test_search_filters_products(self):
        response = self.get_products(
            website_id=self.shopzone.id,
            search="iPhone",
        )

        self.assertEqual(response.status_code, 200)

        results = response.data["results"]

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["external_product_id"],
            "SZ-001",
        )

    def test_max_price_filter(self):
        response = self.get_products(
            website_id=self.shopzone.id,
            max_price="500",
        )

        self.assertEqual(response.status_code, 200)

        returned_ids = {
            item["external_product_id"]
            for item in response.data["results"]
        }

        self.assertEqual(returned_ids, {"SZ-002"})

    def test_invalid_website_id_is_rejected(self):
        response = self.get_products(
            website_id="invalid"
        )

        self.assertEqual(response.status_code, 400)

    def test_inactive_website_returns_no_products(self):
        self.shopzone.is_active = False
        self.shopzone.save()

        response = self.get_products(
            website_id=self.shopzone.id
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)

    def test_product_list_includes_brand(self):
        self.headphones.brand = "Sony"
        self.headphones.save()
        response = self.get_products(website_id=self.shopzone.id, search="Sony")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["brand"], "Sony")
