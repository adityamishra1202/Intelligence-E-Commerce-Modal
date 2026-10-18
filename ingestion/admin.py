from django.contrib import admin

from .models import SyncRun


@admin.register(SyncRun)
class SyncRunAdmin(admin.ModelAdmin):
    list_display = (
        "id", "website", "status", "dry_run", "started_at", "finished_at",
        "fetched_count", "created_count", "updated_count", "unchanged_count",
        "deactivated_count", "error_count", "triggered_by",
    )
    list_filter = ("status", "dry_run", "website")
    readonly_fields = [field.name for field in SyncRun._meta.fields]
