"""Reads products from a local JSON file (an export or feed saved to disk)."""
import json
from pathlib import Path

from django.conf import settings

from ingestion.connectors.base import BaseConnector, ConnectorError, get_path
from ingestion.connectors.registry import register


@register("json_file")
class JsonFileConnector(BaseConnector):
    """
    connector_config:
      path         file path (relative paths are resolved from the project root)
      items_key    optional dotted path to the list of records inside the file
      field_map    canonical_field -> dotted source path (unmapped fields use the same name)
      currency     currency for records that do not state one
      url_template optional, e.g. "https://shop.example.com/p/{id}"
    """

    required_config = ("path",)

    def file_path(self):
        path = Path(self.config["path"])
        return path if path.is_absolute() else Path(settings.BASE_DIR) / path

    def fetch(self):
        path = self.file_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ConnectorError(f"File not found: {path.name}") from exc
        except json.JSONDecodeError as exc:
            raise ConnectorError(f"{path.name} is not valid JSON (line {exc.lineno})") from exc

        items_key = self.config.get("items_key")
        items = get_path(data, items_key) if items_key else data
        if items is None:
            raise ConnectorError(f"items_key '{items_key}' was not found in {path.name}")
        if not isinstance(items, list):
            raise ConnectorError(f"Expected a list of products in {path.name}")
        yield from items
