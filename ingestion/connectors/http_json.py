"""
Reads products from a JSON HTTP API or feed that the website owner provides.

Secrets (API keys, tokens) are never stored in connector_config: 'headers_env'
names environment variables, and their values are read at sync time.
"""
import os
import time

import requests

from ingestion.connectors.base import BaseConnector, ConnectorError, get_path
from ingestion.connectors.registry import register

USER_AGENT = "EcommerceAI-Sync/1.0 (+product catalog synchronisation)"
MAX_RETRIES = 3
MAX_RETRY_WAIT_SECONDS = 60


@register("http_json")
class HttpJsonConnector(BaseConnector):
    """
    connector_config:
      url                 endpoint returning JSON
      params              fixed query parameters
      headers_env         {"Header-Name": "ENV_VARIABLE_NAME"}
      items_key           dotted path to the record list in each response
      field_map, currency, url_template   as for json_file
      pagination          {"type": "none" | "page" | "cursor",
                           "param": "page", "start": 1, "page_size": 50,
                           "page_size_param": "per_page",
                           "cursor_param": "cursor", "cursor_path": "next",
                           "max_pages": 50}
      timeout_seconds     per request (default 30)
      min_interval_seconds  pause between requests (default 1)
    """

    required_config = ("url",)

    def __init__(self, website, config=None):
        super().__init__(website, config)
        self.session = requests.Session()

    def validate_config(self):
        errors = super().validate_config()
        url = self.config.get("url", "")
        if url and not url.lower().startswith(("http://", "https://")):
            errors.append("url must start with http:// or https://")
        for header, env_name in (self.config.get("headers_env") or {}).items():
            if not os.environ.get(env_name):
                errors.append(f"environment variable {env_name} (for header {header}) is not set")
        pagination = self.config.get("pagination") or {}
        if pagination.get("type", "none") not in ("none", "page", "cursor"):
            errors.append("pagination.type must be none, page or cursor")
        if pagination.get("type") == "cursor" and not pagination.get("cursor_path"):
            errors.append("cursor pagination needs pagination.cursor_path")
        return errors

    # -- HTTP --------------------------------------------------------------

    def _headers(self):
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        for header, env_name in (self.config.get("headers_env") or {}).items():
            value = os.environ.get(env_name)
            if not value:
                raise ConnectorError(f"environment variable {env_name} is not set")
            headers[header] = value
        return headers

    def _get_json(self, params):
        timeout = float(self.config.get("timeout_seconds", 30))
        last_problem = "no response"
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    self.config["url"], params=params, headers=self._headers(), timeout=timeout,
                )
            except requests.Timeout:
                last_problem = "request timed out"
            except requests.RequestException as exc:
                last_problem = f"request failed ({type(exc).__name__})"
            else:
                if response.status_code == 429 or response.status_code >= 500:
                    last_problem = f"HTTP {response.status_code}"
                    if attempt < MAX_RETRIES:
                        time.sleep(self._retry_wait(response, attempt))
                    continue
                if response.status_code >= 400:
                    raise ConnectorError(f"HTTP {response.status_code} from source")
                try:
                    return response.json()
                except ValueError as exc:
                    raise ConnectorError("source returned malformed JSON") from exc
            if attempt < MAX_RETRIES:
                time.sleep(min(2 ** attempt, MAX_RETRY_WAIT_SECONDS))
        raise ConnectorError(f"source unavailable after {MAX_RETRIES + 1} attempts: {last_problem}")

    @staticmethod
    def _retry_wait(response, attempt):
        retry_after = response.headers.get("Retry-After") if response is not None else None
        try:
            wait = float(retry_after) if retry_after is not None else 2 ** attempt
        except ValueError:
            wait = 2 ** attempt
        return max(0.0, min(wait, MAX_RETRY_WAIT_SECONDS))

    def _items(self, data):
        items_key = self.config.get("items_key")
        items = get_path(data, items_key) if items_key else data
        if items is None:
            raise ConnectorError(f"items_key '{items_key}' was not found in the response")
        if not isinstance(items, list):
            raise ConnectorError("expected a list of products in the response")
        return items

    # -- fetch ---------------------------------------------------------------

    def fetch(self):
        pagination = self.config.get("pagination") or {}
        kind = pagination.get("type", "none")
        max_pages = int(pagination.get("max_pages", 50))
        interval = float(self.config.get("min_interval_seconds", 1))
        params = dict(self.config.get("params") or {})

        if kind == "none":
            yield from self._items(self._get_json(params))
            return

        if kind == "page":
            param = pagination.get("param", "page")
            page = int(pagination.get("start", 1))
            page_size = pagination.get("page_size")
            if page_size and pagination.get("page_size_param"):
                params[pagination["page_size_param"]] = page_size
            for index in range(max_pages):
                if index:
                    time.sleep(interval)
                items = self._items(self._get_json({**params, param: page}))
                yield from items
                if not items or (page_size and len(items) < int(page_size)):
                    return
                page += 1
            return

        # cursor
        cursor_param = pagination.get("cursor_param", "cursor")
        cursor = None
        for index in range(max_pages):
            if index:
                time.sleep(interval)
            request_params = dict(params)
            if cursor:
                request_params[cursor_param] = cursor
            data = self._get_json(request_params)
            yield from self._items(data)
            cursor = get_path(data, pagination["cursor_path"])
            if not cursor:
                return
