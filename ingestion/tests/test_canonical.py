"""CanonicalProduct validation and the normalizers."""
from decimal import Decimal

from django.test import SimpleTestCase
from pydantic import ValidationError

from ingestion.canonical import CanonicalProduct
from ingestion.normalizers import (
    derive_brand,
    normalize_currency,
    normalize_features,
    strip_html,
    to_bool,
    to_decimal,
)

VALID = {
    "external_product_id": "42",
    "title": "Sony WH-1000XM5 Headphones",
    "price": "328",
    "currency": "usd",
    "rating": 4.7,
    "features": ["Noise canceling", "<b>Bluetooth</b>"],
    "product_url": "https://shop.example.com/p/42",
}


class CanonicalProductTests(SimpleTestCase):
    def test_valid_record(self):
        product = CanonicalProduct(**VALID)
        self.assertEqual(product.price, Decimal("328.00"))
        self.assertEqual(product.currency, "USD")
        self.assertEqual(product.features, ["Noise canceling", "Bluetooth"])

    def test_missing_optional_fields(self):
        product = CanonicalProduct(external_product_id="1", title="Thing", price=1, currency="INR")
        self.assertIsNone(product.rating)
        self.assertEqual(product.product_url, "")
        self.assertTrue(product.is_available)

    def test_negative_price_rejected(self):
        with self.assertRaises(ValidationError):
            CanonicalProduct(**dict(VALID, price=-1))

    def test_bad_currency_rejected(self):
        for currency in ("", "US", "dollars", None):
            with self.assertRaises(ValidationError):
                CanonicalProduct(**dict(VALID, currency=currency))

    def test_rating_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            CanonicalProduct(**dict(VALID, rating=5.5))

    def test_empty_id_or_title_rejected(self):
        with self.assertRaises(ValidationError):
            CanonicalProduct(**dict(VALID, external_product_id=""))
        with self.assertRaises(ValidationError):
            CanonicalProduct(**dict(VALID, title="  "))

    def test_non_http_urls_are_dropped(self):
        product = CanonicalProduct(**dict(VALID, product_url="javascript:alert(1)", images=["ftp://x", "https://img/a.jpg"]))
        self.assertEqual(product.product_url, "")
        self.assertEqual(product.images, ["https://img/a.jpg"])

    def test_content_hash_changes_with_any_field(self):
        a = CanonicalProduct(**VALID)
        self.assertEqual(a.content_hash(), CanonicalProduct(**VALID).content_hash())
        self.assertNotEqual(a.content_hash(), CanonicalProduct(**dict(VALID, price="329")).content_hash())


class NormalizerTests(SimpleTestCase):
    def test_strip_html(self):
        self.assertEqual(strip_html("<p>Fast &amp; <b>light</b></p>"), "Fast & light")

    def test_to_decimal(self):
        self.assertEqual(to_decimal("$1,299.50"), Decimal("1299.50"))
        self.assertEqual(to_decimal("Rs. 1,499"), Decimal("1499"))
        self.assertIsNone(to_decimal(""))
        with self.assertRaises(ValueError):
            to_decimal("free")

    def test_to_bool(self):
        self.assertFalse(to_bool("Out of stock"))
        self.assertTrue(to_bool("yes"))
        self.assertTrue(to_bool(None))

    def test_normalize_currency(self):
        self.assertEqual(normalize_currency(" usd "), "USD")
        self.assertEqual(normalize_currency("₹"), "INR")
        self.assertEqual(normalize_currency("", default="usd"), "USD")

    def test_normalize_features(self):
        self.assertEqual(normalize_features("a; b; a"), ["a", "b"])
        self.assertEqual(normalize_features({"Battery": "30h"}), ["Battery: 30h"])

    def test_derive_brand(self):
        brands = ["Sony", "Apple", "Ray-Ban", "Instant Pot", "Bang & Olufsen", "Nespresso", "De'Longhi"]
        self.assertEqual(derive_brand("Sony WH-1000XM5 Wireless Headphones", brands), "Sony")
        self.assertEqual(derive_brand("Apple Watch Ultra 2", brands), "Apple")
        self.assertEqual(derive_brand("Ray-Ban Classic Aviator", brands), "Ray-Ban")
        self.assertEqual(derive_brand("Instant Pot Duo 7-in-1", brands), "Instant Pot")
        self.assertEqual(derive_brand("Bang & Olufsen Beoplay H95", brands), "Bang & Olufsen")
        self.assertEqual(derive_brand("Nespresso VertuoPlus by De'Longhi", brands), "Nespresso")
        self.assertEqual(derive_brand("Sonya Wireless Headphones", brands), "")
        self.assertEqual(derive_brand("Sony WH-1000XM5 Noise Canceling", brands + ["Noise"]), "Sony")
        self.assertEqual(derive_brand("Wireless Earbuds by Sony", brands), "Sony")
        self.assertEqual(derive_brand("Ceramic Plant Pot Set", brands), "")

    def test_default_brand_list_loads(self):
        self.assertEqual(derive_brand("Logitech MX Master 3S Mouse"), "Logitech")
