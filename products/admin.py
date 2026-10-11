

# Register your models here.
from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "website",
        "price",
        "currency",
        "is_available",
        "last_verified_at",
    )

    search_fields = (
        "title",
        "external_product_id",
    )

    list_filter = (
        "website",
        "category",
        "is_available",
    )
