import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from products.models import Product
from websites.models import Website

FIELDS = [
    "external_product_id", "title", "brand", "category", "description", "price", "original_price",
    "currency", "rating", "review_count", "is_available", "product_url", "image_url", "images",
    "features", "specifications", "is_prime", "badge",
]


def _plain(value):
    return str(value) if value is not None and value.__class__.__name__ == "Decimal" else value


class Command(BaseCommand):
    help = (
        "Write a website's current products to a JSON file using canonical field names, so the "
        "website can be onboarded with the json_file connector."
    )

    def add_arguments(self, parser):
        parser.add_argument("--website-id", type=int, required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        website = Website.objects.filter(id=options["website_id"]).first()
        if website is None:
            raise CommandError(f"Website {options['website_id']} does not exist.")
        rows = [
            {field: _plain(getattr(product, field)) for field in FIELDS}
            for product in Product.objects.filter(website=website).order_by("id")
        ]
        output = Path(options["output"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(rows)} products of {website.name} to {output}"))
