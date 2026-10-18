import json


class ProductTextService:
    """
    Converts product records into normalized text
    suitable for generating semantic embeddings.
    """

    @staticmethod
    def _clean(value):
        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        return str(value).strip()

    @staticmethod
    def _format_json(value):
        if not value:
            return ""

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return value.strip()

        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
        )

    def build_product_text(self, product):
        sections = []

        fields = [
            ("Title", product.title),
            ("Brand", product.brand),
            ("Category", product.category),
            ("Description", product.description),
            ("Price", f"{product.price} {product.currency}"),
            ("Rating", product.rating),
            ("Features", product.features),
            ("Specifications", product.specifications),
        ]

        for label, value in fields:
            if value is None or value == "":
                continue

            if isinstance(value, (dict, list)):
                value = self._format_json(value)

            cleaned = self._clean(value)

            if cleaned:
                sections.append(f"{label}: {cleaned}")

        return "\n".join(sections)
