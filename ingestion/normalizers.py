"""Small, source-independent helpers that turn raw source values into clean values."""
import html
import json
import re
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

BRANDS_FILE = Path(__file__).resolve().parent / "data" / "brands.json"

CURRENCY_SYMBOLS = {"$": "USD", "₹": "INR", "€": "EUR", "£": "GBP", "¥": "JPY"}

_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")


def strip_html(value):
    """Remove HTML tags and entities and collapse whitespace."""
    if value is None:
        return ""
    text = _TAG.sub(" ", str(value))
    return _SPACE.sub(" ", html.unescape(text)).strip()


def to_decimal(value):
    """'1,299.00', '$12', 12, None -> Decimal or None. Raises ValueError for garbage."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise ValueError(f"not a number: {value!r}")
    text = str(value).strip()
    for symbol in CURRENCY_SYMBOLS:
        text = text.replace(symbol, "")
    text = re.sub(r"(?i)\brs\.?|\b(?:inr|usd|eur|gbp)\b", "", text).replace(",", "").strip()
    try:
        number = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"not a number: {value!r}") from exc
    if not number.is_finite():
        raise ValueError(f"not a finite number: {value!r}")
    return number


def to_bool(value, default=True):
    """Interpret common truthy / falsy source values ('yes', 'in stock', 0, ...)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if text in ("true", "yes", "y", "1", "in stock", "instock", "available", "in_stock"):
        return True
    if text in ("false", "no", "n", "0", "out of stock", "outofstock", "unavailable", "sold out", "out_of_stock"):
        return False
    return default


def normalize_currency(value, default=None):
    """'usd', '$', ' INR ' -> 'USD' / 'INR'. Returns `default` (uppercased) when value is empty."""
    text = (str(value).strip() if value is not None else "")
    if not text:
        return (default or "").upper() or None
    if text in CURRENCY_SYMBOLS:
        return CURRENCY_SYMBOLS[text]
    return text.upper()


def normalize_features(value):
    """A list of short feature strings from a list, dict, JSON string or delimited string."""
    if value is None or value == "":
        return []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = re.split(r"[\n;|•]+", value)
        value = parsed
    if isinstance(value, dict):
        value = [f"{key}: {item}" for key, item in value.items()]
    if not isinstance(value, (list, tuple, set)):
        value = [value]
    features = []
    for item in value:
        text = strip_html(item)
        if text and text not in features:
            features.append(text[:300])
    return features


@lru_cache(maxsize=1)
def load_brand_list():
    data = json.loads(BRANDS_FILE.read_text(encoding="utf-8"))
    return tuple(data["brands"])


def derive_brand(title, brand_list=None):
    """
    The longest known brand that appears as a whole word (or phrase) in the
    title; ties go to the brand that appears first. '' when none matches.
    """
    if not title:
        return ""
    brand_list = load_brand_list() if brand_list is None else brand_list
    lower = title.lower()
    best = None
    for brand in brand_list:
        pattern = re.compile(r"(?<![a-z0-9])" + re.escape(brand.lower()) + r"(?![a-z0-9])")
        match = pattern.search(lower)
        if match:
            key = (len(brand), -match.start())
            if best is None or key > best[0]:
                best = (key, brand)
    return best[1] if best else ""
