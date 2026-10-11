from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):

    website_name = serializers.CharField(
        source="website.name",
        read_only=True
    )

    class Meta:
        model = Product

        fields = [
            "id",
            "website",
            "website_name",
            "external_product_id",
            "title",
            "description",
            "category",
            "price",
            "currency",
            "original_price",
            "rating",
            "review_count",
            "is_prime",
            "badge",
            "product_url",
            "image_url",
            "images",
            "features",
            "specifications",
            "is_available",
            "source_updated_at",
            "last_fetched_at",
            "last_verified_at",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields