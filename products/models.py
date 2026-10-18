
from django.db import models


class Product(models.Model):

    website = models.ForeignKey(
        "websites.Website",
        on_delete=models.PROTECT,
        related_name="products",
    )

    external_product_id = models.CharField(
        max_length=255,
    )

    title = models.CharField(
        max_length=300,
    )

    description = models.TextField(
        blank=True,
    )

    category = models.CharField(
        max_length=150,
        blank=True,
    )

    brand = models.CharField(
        max_length=150,
        blank=True,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    original_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Required, with no default: every source must state its currency.
    currency = models.CharField(
        max_length=3,
    )

    product_url = models.URLField(max_length=1000, blank=True)

    image_url = models.URLField(
        max_length=1000,
        blank=True,
    )

    images = models.JSONField(
        default=list,
        blank=True,
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
    )

    review_count = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_prime = models.BooleanField(
        null=True,
        blank=True,
    )

    badge = models.CharField(
        max_length=100,
        blank=True,
    )

    features = models.JSONField(
        default=list,
        blank=True,
    )

    specifications = models.JSONField(
        default=dict,
        blank=True,
    )

    is_available = models.BooleanField(
        default=True,
    )

    source_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_fetched_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    last_verified_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # sha256 of the canonical record; a sync only writes when it changes.
    content_hash = models.CharField(
        max_length=64,
        blank=True,
    )

    # Last time a sync saw this product in its source.
    last_seen_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["website", "external_product_id"],
                name="unique_product_per_website",
            )
        ]

    def __str__(self):
        return f"{self.title} - {self.website.name}"



    