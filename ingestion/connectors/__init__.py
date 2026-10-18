"""Built-in connectors register themselves on import."""
from ingestion.connectors import http_json, json_file, shopzone  # noqa: F401
from ingestion.connectors.base import BaseConnector, ConnectorError  # noqa: F401
from ingestion.connectors.registry import available_types, get_connector, register  # noqa: F401
