from django.contrib import admin
from .models import Website


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "base_url",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "base_url",
    )

    list_filter = (
        "is_active",
    )
    # //Register the models here
