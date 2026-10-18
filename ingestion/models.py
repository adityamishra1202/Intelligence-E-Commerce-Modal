from django.db import models


class SyncRun(models.Model):
    """One synchronisation of one website's products from its connector."""

    STATUS_CHOICES = [
        ("running", "Running"),
        ("success", "Success"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ]
    MAX_ERRORS = 50

    website = models.ForeignKey(
        "websites.Website",
        on_delete=models.PROTECT,
        related_name="sync_runs",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="running")

    fetched_count = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    unchanged_count = models.PositiveIntegerField(default=0)
    deactivated_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    # Short, user-safe error descriptions (at most MAX_ERRORS entries).
    error_summary = models.JSONField(default=list, blank=True)

    triggered_by = models.CharField(max_length=50)
    dry_run = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Sync {self.id} of {self.website} ({self.status})"

    def add_error(self, message):
        self.error_count += 1
        if len(self.error_summary) < self.MAX_ERRORS:
            self.error_summary.append(str(message)[:300])
