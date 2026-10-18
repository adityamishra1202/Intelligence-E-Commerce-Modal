import re

from products.models import Product
from assistant.services.requirements_service import (
    ShoppingRequirements,
)


def _word_pattern(text):
    """Whole-word, case-insensitive match that also works for brands like 'Audio-Technica'."""
    return re.compile(r"(?<![a-z0-9])" + re.escape(text.strip().lower()) + r"(?![a-z0-9])")


def brand_matches(product, requested):
    """
    Brand rule (case-insensitive, whole word):
    - if the product has a brand, the requested brand must match it;
    - if the brand field is empty, the requested brand must appear in the title.
    """
    if not requested or not requested.strip():
        return True
    pattern = _word_pattern(requested)
    brand = (product.brand or "").strip().lower()
    if brand:
        return bool(pattern.search(brand))
    return bool(pattern.search((product.title or "").lower()))


def _number(value):
    return float(value) if value is not None else None


def product_to_dict(product):
    """The Product object returned by every API (see the API contract)."""
    return {
        "id": product.id,
        "website_id": product.website_id,
        "website_name": product.website.name,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "price": str(product.price),
        "original_price": str(product.original_price) if product.original_price is not None else None,
        "currency": product.currency,
        "rating": _number(product.rating),
        "review_count": product.review_count,
        "is_available": product.is_available,
        "product_url": product.product_url,
        "image_url": product.image_url,
        "features": product.features,
        "specifications": product.specifications,
        "last_fetched_at": product.last_fetched_at.isoformat() if product.last_fetched_at else None,
    }


class ProductSearchService:

    def search(self, requirements, website_ids, limit=20):

        # --------------------------------------------------
        # 1. Validate website scope
        # --------------------------------------------------

        if not website_ids:
            raise ValueError(
                "At least one website ID must be supplied."
            )

        if isinstance(website_ids, int):
            website_ids = [website_ids]
        else:
            website_ids = list(website_ids)

        if not website_ids:
            raise ValueError(
                "Website scope cannot be empty."
            )

        website_ids = list(set(website_ids))
        limit = max(1, min(limit, 100))

        # --------------------------------------------------
        # 2. Retrieve products from selected active websites
        # --------------------------------------------------

        queryset = Product.objects.filter(
            website_id__in=website_ids,
            website__is_active=True,
        ).select_related("website")

        if isinstance(requirements, dict):
            requirements = ShoppingRequirements.model_validate(
                requirements
            )

        # --------------------------------------------------
        # 3. Apply hard constraints
        #
        # These filters must never be silently relaxed.
        # --------------------------------------------------

        if requirements.only_available:
            queryset = queryset.filter(is_available=True)

        if requirements.min_price is not None:
            queryset = queryset.filter(
                price__gte=requirements.min_price
            )

        if requirements.max_price is not None:
            queryset = queryset.filter(
                price__lte=requirements.max_price
            )

        if requirements.min_rating is not None:
            queryset = queryset.filter(
                rating__gte=requirements.min_rating
            )

        # Never compare prices in different currencies.
        if requirements.currency:
            queryset = queryset.filter(
                currency__iexact=requirements.currency
            )

        # --------------------------------------------------
        # 4. Load products that satisfy hard constraints
        # --------------------------------------------------

        products = list(queryset)

        # --------------------------------------------------
        # 5. Prepare search terms
        # --------------------------------------------------

        keywords = [
            keyword.strip().lower()
            for keyword in requirements.keywords
            if keyword and keyword.strip()
        ]

        features = [
            feature.strip().lower()
            for feature in requirements.must_have_features
            if feature and feature.strip()
        ]

        requested_brand = (
            requirements.brand.strip().lower()
            if requirements.brand
            else None
        )

        requested_category = (
            requirements.category.strip().lower()
            if requirements.category
            else None
        )

        # --------------------------------------------------
        # 6. Feature aliases
        #
        # Normalize common variations of feature names.
        # --------------------------------------------------

        feature_aliases = {
    "wireless connectivity": [
        "wireless",
        "bluetooth",
    ],
    "wireless": [
        "wireless",
        "bluetooth",
    ],
    "bluetooth connectivity": [
        "bluetooth",
    ],
    "noise cancellation": [
        "noise cancellation",
        "noise cancelling",
        "noise-cancelling",
        "noise canceling",
        "noise-canceling",
        "active noise cancellation",
        "active noise cancelling",
        "active noise canceling",
        "anc",
    ],
    "noise cancelling": [
        "noise cancellation",
        "noise cancelling",
        "noise-cancelling",
        "noise canceling",
        "noise-canceling",
        "active noise cancellation",
        "active noise cancelling",
        "active noise canceling",
        "anc",
    ],
    "water resistant": [
        "water resistant",
        "water-resistant",
        "water resistance",
    ],
    "waterproof": [
        "waterproof",
        "water proof",
    ],
    "long battery life": [
        "long battery life",
        "extended battery life",
        "longer battery life",
        "hours of battery life",
    ],
    "fast charging": [
        "fast charging",
        "quick charging",
        "rapid charging",
    ],
    "portable": [
        "portable",
        "compact",
    ],
    "high battery capacity": [
        "high battery capacity",
        "large battery capacity",
        "huge battery capacity",
        "high capacity",
        "large capacity",
        "huge capacity",
        "mah capacity",
    ],
    "high capacity": [
        "high capacity",
        "large capacity",
        "huge capacity",
        "mah capacity",
    ],
    "multi-device connectivity": [
        "multipoint",
        "multi-device",
        "multiple devices",
        "multiple-device",
    ],
}

        # --------------------------------------------------
        # 7. Score and filter products
        # --------------------------------------------------

        scored_products = []

        for product in products:

            title = (product.title or "").lower()
            category = (product.category or "").lower()
            brand = (product.brand or "").lower()
            description = (product.description or "").lower()

            product_features = getattr(
                product,
                "features",
                None,
            ) or []

            specifications = getattr(
                product,
                "specifications",
                None,
            ) or {}

            # Convert structured metadata into searchable text.
            if isinstance(product_features, dict):
                feature_text = " ".join(
                    str(key) + " " + str(value)
                    for key, value in product_features.items()
                )

            elif isinstance(
                product_features,
                (list, tuple, set),
            ):
                feature_text = " ".join(
                    str(value)
                    for value in product_features
                )

            else:
                feature_text = str(product_features)

            if isinstance(specifications, dict):
                specification_text = " ".join(
                    str(key) + " " + str(value)
                    for key, value in specifications.items()
                )

            elif isinstance(
                specifications,
                (list, tuple, set),
            ):
                specification_text = " ".join(
                    str(value)
                    for value in specifications
                )

            else:
                specification_text = str(specifications)

            product_text = " ".join([
                title,
                category,
                brand,
                description,
                feature_text.lower(),
                specification_text.lower(),
            ])

            # ----------------------------------------------
            # Brand is a hard constraint when explicitly asked
            # ----------------------------------------------

            if requested_brand and not brand_matches(product, requested_brand):
                continue

            # ----------------------------------------------
            # Category matching
            #
            # The requested category can match the title,
            # stored category, description, or metadata.
            # ----------------------------------------------

            category_match = False

            if requested_category:
                category_match = (
                    requested_category in category
                    or requested_category in title
                    or requested_category in description
                    or requested_category in feature_text.lower()
                    or requested_category in specification_text.lower()
                )

                # Exclude unrelated products.
                if not category_match:
                    continue

            # ----------------------------------------------
            # Required feature filtering
            #
            # Every requested feature must match.
            # ----------------------------------------------

            features_match = all(
                any(
                    alias in product_text
                    for alias in feature_aliases.get(
                        feature,
                        [feature],
                    )
                )
                for feature in features
            )

            if features and not features_match:
                continue

            # ----------------------------------------------
            # Initialize relevance score
            # ----------------------------------------------

            score = 0

            # ----------------------------------------------
            # Keyword relevance
            # ----------------------------------------------

            for keyword in keywords:

                if keyword in title:
                    score += 5

                elif keyword in category:
                    score += 4

                elif keyword in brand:
                    score += 3

                elif keyword in description:
                    score += 2

                elif keyword in product_text:
                    score += 1

                else:
                    # Partial phrase match.
                    words = keyword.split()

                    matched_words = sum(
                        1
                        for word in words
                        if word in product_text
                    )

                    if words:
                        score += matched_words / len(words)

            # ----------------------------------------------
            # Required feature relevance bonus
            #
            # Features have already been validated above.
            # ----------------------------------------------

            if features:
                score += 3 * len(features)

            # ----------------------------------------------
            # Category relevance bonus
            # ----------------------------------------------

            if category_match:
                score += 4

            # ----------------------------------------------
            # Rating bonus for relevance searches
            # ----------------------------------------------

            if (
                requirements.sort_by == "relevance"
                and product.rating is not None
            ):
                score += float(product.rating) * 0.2

            scored_products.append((score, product))

        # --------------------------------------------------
        # 8. Remove products with no query relevance
        # --------------------------------------------------

        if keywords or features or requested_category:
            scored_products = [
                (score, product)
                for score, product in scored_products
                if score > 0
            ]

        # --------------------------------------------------
        # 9. Sort results
        # --------------------------------------------------

        if requirements.sort_by == "price_ascending":

            scored_products.sort(
                key=lambda item: (
                    item[1].price,
                    -(float(item[1].rating or 0)),
                )
            )

        elif requirements.sort_by == "price_descending":

            scored_products.sort(
                key=lambda item: (
                    -item[1].price,
                    -(float(item[1].rating or 0)),
                )
            )

        elif requirements.sort_by == "rating":

            scored_products.sort(
                key=lambda item: (
                    -(float(item[1].rating or 0)),
                    -item[0],
                )
            )

        else:

            scored_products.sort(
                key=lambda item: (
                    -item[0],
                    -float(item[1].rating or 0),
                )
            )

        # --------------------------------------------------
        # 10. Return actual database records
        # --------------------------------------------------

        return [
            product_to_dict(product)
            for score, product in scored_products[:limit]
        ]