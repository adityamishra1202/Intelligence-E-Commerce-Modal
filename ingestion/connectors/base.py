"""
Connector contract. A connector knows how to FETCH one kind of source and how
to map its records onto CanonicalProduct. Everything after that (validation,
hashing, upserts, embeddings) is shared and lives in ingestion/sync_service.py.
"""
from abc import ABC, abstractmethod

from ingestion.canonical import CanonicalProduct
from ingestion.normalizers import (
    derive_brand,
    normalize_currency,
    normalize_features,
    to_bool,
    to_decimal,
)

CANONICAL_FIELDS = list(CanonicalProduct.model_fields)


class ConnectorError(Exception):
    """The source could not be read as a whole (network, file, format)."""


def get_path(data, path):
    """Read a dotted path such as 'pricing.amount' or 'images.0.url'; None if missing."""
    current = data
    for part in str(path).split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return None
        if current is None:
            return None
    return current


class BaseConnector(ABC):
    connector_type = None
    required_config = ()

    def __init__(self, website, config=None):
        self.website = website
        self.config = dict(website.connector_config or {}) if config is None else dict(config)

    # -- configuration -------------------------------------------------------

    def default_currency(self):
        return self.config.get("currency") or self.website.default_currency or None

    def validate_config(self):
        """Return a list of human-readable problems (empty when the config is usable)."""
        errors = [f"connector_config is missing '{key}'" for key in self.required_config if not self.config.get(key)]
        field_map = self.config.get("field_map", {})
        if not isinstance(field_map, dict):
            errors.append("connector_config 'field_map' must be an object of canonical_field -> source path")
        else:
            unknown = sorted(set(field_map) - set(CANONICAL_FIELDS))
            if unknown:
                errors.append(f"field_map has unknown canonical fields: {', '.join(unknown)}")
        if not self.default_currency() and "currency" not in field_map:
            errors.append("no currency: set connector_config 'currency', the website's default_currency, "
                          "or map a 'currency' field")
        return errors

    # -- the three stages ----------------------------------------------------

    @abstractmethod
    def fetch(self):
        """Yield raw records. Raise ConnectorError if the source cannot be read."""

    def parse(self, raw):
        """Turn one raw record into a dict. Raise ValueError for a bad record."""
        if not isinstance(raw, dict):
            raise ValueError("record is not an object")
        return raw

    def normalize(self, parsed):
        """Map a parsed record onto CanonicalProduct using config['field_map']."""
        field_map = self.config.get("field_map", {}) or {}
        value = {field: get_path(parsed, field_map.get(field, field)) for field in CANONICAL_FIELDS}

        value["external_product_id"] = str(value["external_product_id"]).strip() if value["external_product_id"] is not None else ""
        value["price"] = to_decimal(value["price"])
        value["original_price"] = to_decimal(value["original_price"])
        value["rating"] = to_decimal(value["rating"])
        if value["review_count"] not in (None, ""):
            value["review_count"] = int(to_decimal(value["review_count"]))
        value["is_available"] = to_bool(value["is_available"], default=True)
        value["currency"] = normalize_currency(value["currency"], default=self.default_currency())
        value["features"] = normalize_features(value["features"])
        if value["is_prime"] is not None:
            value["is_prime"] = to_bool(value["is_prime"], default=None)

        for key in ("title", "brand", "category", "description", "product_url", "image_url", "badge"):
            if value[key] is None:
                value[key] = ""
        if value["images"] is None:
            value["images"] = []
        if value["specifications"] is None:
            value["specifications"] = {}

        # Brand: from the source when present, otherwise from the title.
        if not str(value["brand"]).strip():
            value["brand"] = derive_brand(str(value["title"]))

        # Product URL policy: source URL, else the configured template, else empty.
        template = self.config.get("url_template")
        if not value["product_url"] and template and value["external_product_id"]:
            value["product_url"] = template.format(id=value["external_product_id"])

        return CanonicalProduct(**value)
