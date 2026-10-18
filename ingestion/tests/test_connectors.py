"""Connectors: JSON file, HTTP JSON (requests mocked) and the ShopZone adapter."""
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

import requests
from django.test import TestCase

from ingestion.connectors import ConnectorError, get_connector
from ingestion.connectors.http_json import HttpJsonConnector
from ingestion.connectors.json_file import JsonFileConnector
from ingestion.connectors.shopzone import ShopZoneConnector
from websites.models import Website


def response(status=200, payload=None, headers=None, bad_json=False):
    r = mock.Mock()
    r.status_code = status
    r.headers = headers or {}
    if bad_json:
        r.json.side_effect = ValueError("bad json")
    else:
        r.json.return_value = payload
    return r


class ConnectorTestBase(TestCase):
    def website(self, connector_type, config, currency="USD"):
        return Website.objects.create(
            name=f"Site {connector_type} {Website.objects.count()}",
            base_url=f"https://site{Website.objects.count()}.example.com",
            connector_type=connector_type, connector_config=config, default_currency=currency,
        )

    def write_json(self, data):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(data, handle)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name


class RegistryTests(ConnectorTestBase):
    def test_manual_website_cannot_sync(self):
        with self.assertRaises(ConnectorError):
            get_connector(self.website("manual", {}))

    def test_known_type(self):
        self.assertIsInstance(get_connector(self.website("json_file", {"path": "x.json"})), JsonFileConnector)


class JsonFileConnectorTests(ConnectorTestBase):
    def test_reads_items_with_field_map_and_url_template(self):
        path = self.write_json({"data": {"items": [{"sku": "A1", "name": "Sony WH-CH520 Headphones",
                                                     "cost": "58.00", "stars": 4.3}]}})
        site = self.website("json_file", {
            "path": path, "items_key": "data.items",
            "field_map": {"external_product_id": "sku", "title": "name", "price": "cost", "rating": "stars"},
            "url_template": "https://shop.example.com/p/{id}",
        })
        connector = get_connector(site)
        self.assertEqual(connector.validate_config(), [])
        product = connector.normalize(connector.parse(next(iter(connector.fetch()))))
        self.assertEqual(product.external_product_id, "A1")
        self.assertEqual(product.brand, "Sony")          # derived from the title
        self.assertEqual(product.currency, "USD")        # website default
        self.assertEqual(product.product_url, "https://shop.example.com/p/A1")

    def test_missing_file(self):
        connector = get_connector(self.website("json_file", {"path": "/no/such/file.json"}))
        with self.assertRaises(ConnectorError):
            list(connector.fetch())

    def test_invalid_json_file(self):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        handle.write("{not json")
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        with self.assertRaises(ConnectorError):
            list(get_connector(self.website("json_file", {"path": handle.name})).fetch())

    def test_missing_items_key(self):
        path = self.write_json({"products": []})
        with self.assertRaises(ConnectorError):
            list(get_connector(self.website("json_file", {"path": path, "items_key": "items"})).fetch())

    def test_config_errors(self):
        connector = get_connector(self.website("json_file", {"field_map": {"nonsense": "x"}}, currency=""))
        errors = " ".join(connector.validate_config())
        self.assertIn("path", errors)
        self.assertIn("nonsense", errors)
        self.assertIn("currency", errors)


class ShopZoneConnectorTests(ConnectorTestBase):
    def test_maps_shopzone_export(self):
        connector = get_connector(self.website("shopzone", {}))
        self.assertIsInstance(connector, ShopZoneConnector)
        records = list(connector.fetch())
        self.assertEqual(len(records), 16)
        product = connector.normalize(records[1])
        self.assertEqual(product.external_product_id, "2")
        self.assertEqual(product.brand, "Sony")
        self.assertEqual(product.original_price is not None, True)
        self.assertTrue(product.is_available)
        self.assertEqual(product.product_url, "")  # the export has no product URLs; none invented


@mock.patch("ingestion.connectors.http_json.time.sleep")
class HttpJsonConnectorTests(ConnectorTestBase):
    def connector(self, **config):
        config.setdefault("url", "https://api.example.com/products")
        config.setdefault("field_map", {"external_product_id": "id", "title": "name", "price": "price"})
        return get_connector(self.website("http_json", config))

    def test_page_pagination(self, _sleep):
        connector = self.connector(items_key="items", pagination={"type": "page", "page_size": 2})
        pages = [response(payload={"items": [{"id": 1}, {"id": 2}]}),
                 response(payload={"items": [{"id": 3}]})]
        with mock.patch.object(connector.session, "get", side_effect=pages) as get:
            records = list(connector.fetch())
        self.assertEqual([r["id"] for r in records], [1, 2, 3])
        self.assertEqual([c.kwargs["params"]["page"] for c in get.call_args_list], [1, 2])
        self.assertIn("EcommerceAI", get.call_args.kwargs["headers"]["User-Agent"])

    def test_cursor_pagination(self, _sleep):
        connector = self.connector(items_key="data", pagination={"type": "cursor", "cursor_path": "next"})
        pages = [response(payload={"data": [{"id": 1}], "next": "abc"}),
                 response(payload={"data": [{"id": 2}], "next": None})]
        with mock.patch.object(connector.session, "get", side_effect=pages) as get:
            records = list(connector.fetch())
        self.assertEqual([r["id"] for r in records], [1, 2])
        self.assertEqual(get.call_args_list[1].kwargs["params"]["cursor"], "abc")

    def test_429_honours_retry_after(self, sleep):
        connector = self.connector()
        replies = [response(429, headers={"Retry-After": "7"}), response(payload=[{"id": 1}])]
        with mock.patch.object(connector.session, "get", side_effect=replies):
            self.assertEqual(len(list(connector.fetch())), 1)
        sleep.assert_any_call(7.0)

    def test_repeated_429_gives_up(self, _sleep):
        connector = self.connector()
        with mock.patch.object(connector.session, "get", return_value=response(429)) as get:
            with self.assertRaises(ConnectorError):
                list(connector.fetch())
        self.assertEqual(get.call_count, 4)  # first try + 3 bounded retries

    def test_timeout(self, _sleep):
        connector = self.connector()
        with mock.patch.object(connector.session, "get", side_effect=requests.Timeout()):
            with self.assertRaises(ConnectorError):
                list(connector.fetch())

    def test_malformed_json(self, _sleep):
        connector = self.connector()
        with mock.patch.object(connector.session, "get", return_value=response(bad_json=True)):
            with self.assertRaises(ConnectorError):
                list(connector.fetch())

    def test_missing_items_key(self, _sleep):
        connector = self.connector(items_key="items")
        with mock.patch.object(connector.session, "get", return_value=response(payload={"rows": []})):
            with self.assertRaises(ConnectorError):
                list(connector.fetch())

    def test_header_secret_comes_from_environment(self, _sleep):
        connector = self.connector(headers_env={"Authorization": "TEST_SHOP_TOKEN"})
        os.environ.pop("TEST_SHOP_TOKEN", None)
        self.assertTrue(any("TEST_SHOP_TOKEN" in e for e in connector.validate_config()))
        with self.assertRaises(ConnectorError):
            list(connector.fetch())
        with mock.patch.dict(os.environ, {"TEST_SHOP_TOKEN": "Bearer secret"}):
            with mock.patch.object(connector.session, "get", return_value=response(payload=[])) as get:
                list(connector.fetch())
            self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertNotIn("secret", json.dumps(connector.website.connector_config))
