"""
CanonicalProduct: the one validated shape every connector produces before a
product is written to the database.
"""
import hashlib
import json
import re
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from ingestion.normalizers import normalize_features, strip_html

_URL = re.compile(r"^https?://\S+$", re.IGNORECASE)


def _clean_url(value):
    """Keep real http(s) URLs only; anything else becomes '' (never invent URLs)."""
    text = (value or "").strip() if isinstance(value, str) else ""
    return text if _URL.match(text) and len(text) <= 1000 else ""


class CanonicalProduct(BaseModel):
    external_product_id: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1)
    brand: str = ""
    category: str = ""
    description: str = ""
    price: Decimal = Field(ge=0)
    original_price: Decimal | None = Field(default=None, ge=0)
    currency: str
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    is_available: bool = True
    product_url: str = ""
    image_url: str = ""
    images: list[str] = Field(default_factory=list)
    features: list[str] = Field(default_factory=list)
    specifications: dict = Field(default_factory=dict)

    @field_validator("external_product_id", "title", mode="before")
    @classmethod
    def _required_text(cls, value):
        return strip_html(value) if value is not None else value

    @field_validator("title")
    @classmethod
    def _title_length(cls, value):
        return value[:300]

    @field_validator("brand", "category", mode="before")
    @classmethod
    def _short_text(cls, value):
        return strip_html(value)[:150]

    @field_validator("description", mode="before")
    @classmethod
    def _description(cls, value):
        return strip_html(value)

    @field_validator("currency", mode="before")
    @classmethod
    def _currency(cls, value):
        text = str(value or "").strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", text):
            raise ValueError("currency must be a three-letter ISO 4217 code")
        return text

    @field_validator("price", "original_price")
    @classmethod
    def _money(cls, value):
        return value.quantize(Decimal("0.01")) if value is not None else value

    @field_validator("rating")
    @classmethod
    def _rating(cls, value):
        return value.quantize(Decimal("0.01")) if value is not None else value

    @field_validator("product_url", "image_url", mode="before")
    @classmethod
    def _url(cls, value):
        return _clean_url(value)

    @field_validator("images", mode="before")
    @classmethod
    def _images(cls, value):
        items = value if isinstance(value, (list, tuple)) else ([value] if value else [])
        return [url for url in (_clean_url(item) for item in items) if url]

    @field_validator("features", mode="before")
    @classmethod
    def _features(cls, value):
        return normalize_features(value)

    @field_validator("specifications", mode="before")
    @classmethod
    def _specifications(cls, value):
        return value if isinstance(value, dict) else {}

    def content_hash(self):
        """sha256 of the sorted JSON of every field; changes when any field changes."""
        payload = json.dumps(self.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def model_fields_for_db(self):
        """Values for products.Product (excluding website and sync bookkeeping)."""
        data = self.model_dump()
        data.pop("external_product_id")
        return data
