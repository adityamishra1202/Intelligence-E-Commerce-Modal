from pgvector.django import CosineDistance

from assistant.models import ProductEmbedding
from assistant.services.embedding_service import EmbeddingService


class SemanticSearchService:
    """
    Retrieves products by semantic similarity using PostgreSQL
    and pgvector.
    """

    def __init__(self):
        self.embedding_service = EmbeddingService()

    def search(
        self,
        query: str,
        website_ids: list[int] | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return products ranked by cosine similarity.

        If website_ids is provided, results are restricted to
        those websites.
        """

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query must not be empty.")

        if limit < 1:
            raise ValueError("Limit must be greater than zero.")

        query_vector = self.embedding_service.embed(query)

        queryset = ProductEmbedding.objects.select_related(
            "product",
            "product__website",
        ).filter(
            product__website__is_active=True,
        )

        if website_ids is not None:
            if not website_ids:
                return []

            queryset = queryset.filter(
                product__website_id__in=website_ids,
            )

        queryset = queryset.order_by(
            CosineDistance("embedding", query_vector)
        )[:limit]

        results = []

        for record in queryset:
            product = record.product

            results.append({
                "id": product.id,
                "website_id": product.website_id,
                "website_name": product.website.name,
                "title": product.title,
                "brand": product.brand,
                "category": product.category,
                "description": product.description,
                "price": str(product.price),
                "currency": product.currency,
                "rating": (
                    float(product.rating)
                    if product.rating is not None
                    else None
                ),
                "is_available": product.is_available,
                "product_url": product.product_url,
                "image_url": product.image_url,
                "features": product.features,
                "specifications": product.specifications,
            })

        return results