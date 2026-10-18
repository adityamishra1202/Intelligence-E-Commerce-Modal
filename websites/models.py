from django.db import models


class Website(models.Model):
    name = models.CharField(max_length=150)

    base_url = models.URLField(max_length=500, unique=True)

    is_active = models.BooleanField(default=True)

    # How this website's products are fetched (see ingestion/connectors).
    connector_type = models.CharField(max_length=50, default="manual")

    # Connector settings such as a file path or feed URL. Never store secrets
    # here: connectors read secrets from environment variables named in it.
    connector_config = models.JSONField(default=dict, blank=True)

    # ISO 4217 code used when source records do not state a currency.
    default_currency = models.CharField(max_length=3, blank=True)

    sync_enabled = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_stale(self, hours=None):
        """True when the website was never synced or its last sync is older than `hours`."""
        from datetime import timedelta

        from django.conf import settings
        from django.utils import timezone

        if self.last_synced_at is None:
            return True
        hours = settings.STALE_AFTER_HOURS if hours is None else hours
        return timezone.now() - self.last_synced_at > timedelta(hours=hours)
