import json

from django.core.management.base import BaseCommand, CommandError

from ingestion.connectors.registry import available_types
from websites.models import Website


class Command(BaseCommand):
    help = (
        "Set a website's connector settings without the admin. Only the options you pass are changed. "
        "Example: configure_website --website-id 2 --connector-type json_file "
        "--path ingestion/fixtures/site-2.json --currency USD --sync-enabled"
    )

    def add_arguments(self, parser):
        parser.add_argument("--website-id", type=int, required=True)
        parser.add_argument("--connector-type")
        parser.add_argument("--path", help="Sets connector_config.path (relative to the project folder).")
        parser.add_argument("--config-json", help="JSON object merged into connector_config.")
        parser.add_argument("--currency", help="Three-letter default currency.")
        parser.add_argument("--sync-enabled", action="store_true")
        parser.add_argument("--sync-disabled", action="store_true")

    def handle(self, *args, **o):
        website = Website.objects.filter(id=o["website_id"]).first()
        if website is None:
            raise CommandError(f"Website {o['website_id']} does not exist.")
        changed = []
        if o["connector_type"]:
            if o["connector_type"] not in available_types() and o["connector_type"] != "manual":
                raise CommandError(f"Unknown connector type. Available: {', '.join(available_types())}, manual.")
            website.connector_type = o["connector_type"]
            changed.append("connector_type")
        config = dict(website.connector_config or {})
        if o["config_json"]:
            try:
                extra = json.loads(o["config_json"])
            except json.JSONDecodeError as exc:
                raise CommandError(f"--config-json is not valid JSON: {exc}")
            if not isinstance(extra, dict):
                raise CommandError("--config-json must be a JSON object.")
            config.update(extra)
        if o["path"]:
            config["path"] = o["path"]
        if config != (website.connector_config or {}):
            website.connector_config = config
            changed.append("connector_config")
        if o["currency"]:
            if len(o["currency"]) != 3 or not o["currency"].isalpha():
                raise CommandError("--currency must be a three-letter code.")
            website.default_currency = o["currency"].upper()
            changed.append("default_currency")
        if o["sync_enabled"] or o["sync_disabled"]:
            website.sync_enabled = bool(o["sync_enabled"])
            changed.append("sync_enabled")
        if changed:
            website.save(update_fields=changed + ["updated_at"])
        self.stdout.write(
            f"{website.name}: connector_type={website.connector_type}, connector_config={website.connector_config}, "
            f"default_currency={website.default_currency or '-'}, sync_enabled={website.sync_enabled}"
        )
