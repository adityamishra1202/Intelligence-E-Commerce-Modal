"""
Adapter for the ShopZone test store's products-export.json. ShopZone is seed
data; this file is the only place that knows its field names.
"""
import os

from ingestion.connectors.json_file import JsonFileConnector
from ingestion.connectors.registry import register

SHOPZONE_FIELD_MAP = {
    "external_product_id": "id",
    "title": "title",
    "category": "category",
    "price": "price",
    "original_price": "originalPrice",
    "rating": "rating",
    "review_count": "reviewsCount",
    "is_prime": "isPrime",
    "badge": "badge",
    "image_url": "image",
    "images": "images",
    "description": "description",
    "features": "features",
    "is_available": "inStock",
    "product_url": "productUrl",
}


@register("shopzone")
class ShopZoneConnector(JsonFileConnector):
    required_config = ()

    def __init__(self, website, config=None):
        super().__init__(website, config)
        self.config.setdefault("path", "products-export.json")
        self.config.setdefault("field_map", SHOPZONE_FIELD_MAP)
        if os.environ.get("SHOPZONE_CURRENCY"):
            self.config.setdefault("currency", os.environ["SHOPZONE_CURRENCY"])
