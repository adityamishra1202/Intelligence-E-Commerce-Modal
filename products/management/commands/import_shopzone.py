import json
import os
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from websites.models import Website
from products.models import Product


class Command(BaseCommand):
    help = "Import ShopZone products from products-export.json"

    def handle(self, *args, **options):
        file_path = Path("products-export.json")

        if not file_path.exists():
            raise CommandError(
                "products-export.json was not found in the project root."
            )

        with file_path.open("r", encoding="utf-8") as file:
            products = json.load(file)

        if not isinstance(products, list):
            raise CommandError("The JSON file must contain a list of products.")

        # Configure these environment variables before importing.
        base_url = os.environ.get("SHOPZONE_BASE_URL")
        currency = os.environ.get("SHOPZONE_CURRENCY")

        if not base_url or not currency:
            raise CommandError(
                "Set SHOPZONE_BASE_URL and SHOPZONE_CURRENCY before importing."
            )

        currency = currency.upper()

        if len(currency) != 3:
            raise CommandError(
                "SHOPZONE_CURRENCY must be a three-letter currency code."
            )

        website, _ = Website.objects.get_or_create(
            base_url=base_url,
            defaults={
                "name": "ShopZone",
                "is_active": True,
            },
        )

        imported = 0

        for item in products:
            external_id = str(item["id"])

            defaults = {
                "title": item["title"],
                "description": item.get("description", ""),
                "category": item.get("category", ""),
                "price": Decimal(str(item["price"])),
                "currency": currency,
                "product_url": item.get("productUrl", ""),
                "image_url": item.get("image", ""),
                "rating": (
                    Decimal(str(item["rating"]))
                    if item.get("rating") is not None
                    else None
                ),
                "original_price": (
                    Decimal(str(item["originalPrice"]))
                    if item.get("originalPrice") is not None
                    else None
                ),
                "review_count": item.get("reviewsCount"),
                "is_prime": item.get("isPrime"),
                "badge": item.get("badge", ""),
                "images": item.get("images", []),
                "features": item.get("features", []),
                "specifications": {},
                "is_available": bool(item.get("inStock", True)),
                "last_fetched_at": timezone.now(),
            }

            Product.objects.update_or_create(
                website=website,
                external_product_id=external_id,
                defaults=defaults,
            )

            imported += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {imported} ShopZone products."
            )
        )