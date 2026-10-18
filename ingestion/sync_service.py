"""
SyncService: bring one website's products in line with its source.

    connector.fetch() -> parse() -> normalize() -> CanonicalProduct -> upsert

- Upsert by (website, external_product_id): create new products, update
  products whose content changed, otherwise only record that they were seen.
- Bad records are counted in the SyncRun and skipped; they never stop a sync.
- Products missing from the source are marked unavailable only after a
  complete, successful fetch, and never when the source suddenly shrank
  (fewer than half of the active products, when there are more than 10).
- Embeddings are refreshed only for created or changed products; a failed
  embedding is recorded and does not fail the sync.
- dry_run computes the counts and writes nothing except the SyncRun.
- Nothing outside the given website is ever written.
"""
import logging

from django.utils import timezone
from pydantic import ValidationError

from ingestion.connectors import ConnectorError, get_connector
from ingestion.models import SyncRun
from products.models import Product

logger = logging.getLogger(__name__)

SHRINK_GUARD_MIN_PRODUCTS = 10
SHRINK_GUARD_RATIO = 0.5


def _record_error(exc):
    """A short description of why a record was rejected (no stack traces)."""
    if isinstance(exc, ValidationError):
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first.get("loc", ())) or "record"
        return f"{location}: {first.get('msg', 'invalid value')}"
    return f"{type(exc).__name__}: {str(exc)[:200]}"


class SyncService:

    def __init__(self, embedding_service=None):
        self._embedding_service = embedding_service

    @property
    def embedding_service(self):
        if self._embedding_service is None:
            from assistant.services.product_embedding_service import ProductEmbeddingService

            self._embedding_service = ProductEmbeddingService()
        return self._embedding_service

    # ------------------------------------------------------------------

    def run(self, website, dry_run=False, triggered_by="manual"):
        run = SyncRun.objects.create(website=website, status="running", triggered_by=triggered_by, dry_run=dry_run)
        run.embedded_count = 0
        run.embedding_reused_count = 0
        try:
            status = self._sync(website, run, dry_run)
        except Exception as exc:  # unexpected bug or database problem
            logger.exception("Sync of website %s failed unexpectedly.", website.pk)
            run.add_error(f"internal error: {type(exc).__name__}")
            status = "failed"
        return self._finish(run, website, status, dry_run)

    def _sync(self, website, run, dry_run):
        try:
            connector = get_connector(website)
        except ConnectorError as exc:
            run.add_error(str(exc))
            return "failed"

        config_errors = connector.validate_config()
        if config_errors:
            for error in config_errors:
                run.add_error(f"config: {error}")
            return "failed"

        now = timezone.now()
        existing = {p.external_product_id: p for p in Product.objects.filter(website=website)}
        active_before = sum(1 for p in existing.values() if p.is_available)
        seen, changed, unchanged_ids = set(), [], []
        fetch_failed = False

        try:
            for raw in connector.fetch():
                run.fetched_count += 1
                try:
                    canonical = connector.normalize(connector.parse(raw))
                except (ValueError, TypeError, ValidationError) as exc:
                    run.add_error(f"record {run.fetched_count}: {_record_error(exc)}")
                    continue

                external_id = canonical.external_product_id
                if external_id in seen:
                    run.add_error(f"record {run.fetched_count}: duplicate id {external_id}")
                    continue
                seen.add(external_id)

                product = existing.get(external_id)
                fields = canonical.model_fields_for_db()
                digest = canonical.content_hash()

                if product is None:
                    run.created_count += 1
                    if not dry_run:
                        product = Product.objects.create(
                            website=website, external_product_id=external_id, **fields,
                            content_hash=digest, last_seen_at=now, last_fetched_at=now,
                        )
                        changed.append(product)
                    continue

                if product.content_hash == digest or self._same_values(product, fields):
                    run.unchanged_count += 1
                    if not dry_run:
                        unchanged_ids.append(product.id)
                        if product.content_hash != digest:
                            Product.objects.filter(id=product.id, website=website).update(content_hash=digest)
                    continue

                run.updated_count += 1
                if not dry_run:
                    for name, value in fields.items():
                        setattr(product, name, value)
                    product.content_hash = digest
                    product.last_seen_at = now
                    product.last_fetched_at = now
                    product.save()
                    changed.append(product)
        except ConnectorError as exc:
            fetch_failed = True
            run.add_error(f"fetch failed: {exc}")

        if unchanged_ids:
            Product.objects.filter(id__in=unchanged_ids, website=website).update(last_seen_at=now, last_fetched_at=now)

        shrink = self._apply_missing_rule(website, run, existing, seen, active_before, fetch_failed, dry_run)

        if not dry_run:
            self._refresh_embeddings(run, changed)

        if fetch_failed:
            return "partial" if seen else "failed"
        if run.error_count or shrink:
            return "partial"
        return "success"

    # ------------------------------------------------------------------

    @staticmethod
    def _same_values(product, fields):
        return all(getattr(product, name) == value for name, value in fields.items())

    def _apply_missing_rule(self, website, run, existing, seen, active_before, fetch_failed, dry_run):
        """Mark products missing from a complete fetch as unavailable. Returns True on a suspicious shrink."""
        if fetch_failed or run.fetched_count == 0:
            return False
        if active_before > SHRINK_GUARD_MIN_PRODUCTS and run.fetched_count < active_before * SHRINK_GUARD_RATIO:
            run.add_error(
                f"suspicious_shrink: source returned {run.fetched_count} products but "
                f"{active_before} are active; nothing was marked unavailable"
            )
            return True
        missing = [p.id for ext, p in existing.items() if ext not in seen and p.is_available]
        run.deactivated_count = len(missing)
        if missing and not dry_run:
            # Clearing content_hash makes a product that reappears unchanged
            # be compared field by field (and so become available again).
            Product.objects.filter(id__in=missing, website=website).update(is_available=False, content_hash="")
        return False

    def _refresh_embeddings(self, run, products):
        for product in products:
            try:
                if self.embedding_service.needs_embedding(product):
                    self.embedding_service.generate_for_product(product)
                    run.embedded_count += 1
                else:
                    run.embedding_reused_count += 1
            except Exception as exc:  # embedding problems never fail a sync
                run.add_error(f"embedding for product {product.external_product_id}: {type(exc).__name__}")

    @staticmethod
    def _finish(run, website, status, dry_run):
        run.status = status
        run.finished_at = timezone.now()
        run.save()
        if not dry_run:
            website.last_sync_status = status
            update = ["last_sync_status", "updated_at"]
            if status in ("success", "partial"):
                website.last_synced_at = run.finished_at
                update.append("last_synced_at")
            website.save(update_fields=update)
        return run
