from django.contrib import admin
from .models import Website


@admin.register(Website)
class WebsiteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "base_url",
        "is_active",
        "connector_type",
        "default_currency",
        "sync_enabled",
        "last_synced_at",
        "last_sync_status",
    )

    search_fields = (
        "name",
        "base_url",
    )

    list_filter = (
        "is_active",
        "connector_type",
        "sync_enabled",
    )
    readonly_fields = ("last_synced_at", "last_sync_status")
    # //Register the models here
