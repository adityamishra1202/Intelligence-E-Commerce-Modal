# Connectors — adding and syncing websites

Every website's products enter the database the same way:

```
connector.fetch()  ->  normalize (field_map, brand, URL policy)  ->  CanonicalProduct  ->  SyncService upsert
```

No website-specific code exists outside `ingestion/connectors/` (the ShopZone adapter
is the only one).

## The canonical product

| Field | Notes |
|---|---|
| `external_product_id` | required, unique per website |
| `title` | required |
| `price` | required, >= 0 (strings such as `"$1,299.00"` or `"Rs. 1,499"` are parsed) |
| `currency` | 3 letters; from the record, else `connector_config.currency`, else the website's `default_currency` |
| `brand` | from the record, else derived from the title using `ingestion/data/brands.json` |
| `category`, `description`, `features`, `specifications`, `images`, `image_url` | optional |
| `original_price`, `rating` (0–5), `review_count`, `is_available` | optional |
| `product_url` | source URL if present, else `url_template`, else empty (never invented) |
| `is_prime`, `badge` | optional |

HTML in text fields is stripped; only http(s) URLs are kept.

## Connector types

### `json_file` — a JSON file on disk

```json
{
  "path": "ingestion/fixtures/my-shop.json",
  "items_key": "data.products",
  "field_map": {"external_product_id": "sku", "title": "name", "price": "pricing.amount",
                "rating": "stars", "is_available": "inStock", "product_url": "link"},
  "currency": "USD",
  "url_template": "https://shop.example.com/p/{id}"
}
```

`path` is relative to the project folder. `items_key` and `url_template` are optional.
`field_map` maps canonical names to (dotted) source names; unmapped fields are read
under their canonical name, so a file exported with `export_website_json` needs no map.

### `http_json` — an official API or feed

```json
{
  "url": "https://api.example.com/v1/products",
  "params": {"status": "active"},
  "headers_env": {"Authorization": "MYSHOP_API_TOKEN"},
  "items_key": "items",
  "field_map": {"external_product_id": "id", "title": "name", "price": "price.value"},
  "pagination": {"type": "page", "param": "page", "start": 1, "page_size": 100,
                 "page_size_param": "per_page", "max_pages": 50},
  "timeout_seconds": 30,
  "min_interval_seconds": 1
}
```

- Secrets are never stored in the config: `headers_env` names an environment variable
  (put `MYSHOP_API_TOKEN=...` in `.env`).
- Pagination types: `none`, `page`, or `cursor` (`cursor_param`, `cursor_path`).
- 429 and 5xx responses are retried up to 3 times, honoring `Retry-After` (max 60 s).

### `shopzone` — the ShopZone test store

Reads `products-export.json` with ShopZone's field names; currency from `SHOPZONE_CURRENCY`.

## Adding a website

1. Create the Website in the admin (`/admin/`) — name, base URL, active.
2. Configure it (admin, or the command below):

   ```powershell
   python manage.py configure_website --website-id 4 --connector-type json_file `
     --path ingestion/fixtures/my-shop.json --currency USD --sync-enabled `
     --config-json '{"field_map": {"external_product_id": "sku", "title": "name"}}'
   ```

   In Windows PowerShell 5.1, write inner quotes as `\"` (for example `'{\"field_map\": ...}'`) or set `connector_config` in the admin instead.

3. Preview, then sync:

   ```powershell
   python manage.py sync_website --website-id 4 --dry-run
   python manage.py sync_website --website-id 4
   ```

4. It now appears in the UI's website list and in `sync_all`.

To export an existing website's rows to a canonical JSON file:
`python manage.py export_website_json --website-id 2 --output ingestion/fixtures/website-2.json`.

## Sync behaviour

- Re-running on unchanged data changes nothing (content hash).
- Products missing from a successful fetch become unavailable; they are never deleted
  and come back when they reappear.
- If more than 10 products are active and fewer than half are fetched, nothing is
  deactivated and the run is `partial` (protects against a broken feed).
- A failing website never affects another; each run is a `SyncRun` row in the admin
  with counts and up to 50 error messages.
- `--dry-run` computes everything and writes nothing except the `SyncRun` record.

## Source restrictions

- Use official APIs, feeds or exports provided or permitted by the website owner.
- **No HTML scraping** unless the owner of that specific site has approved it in writing.
- Never bypass logins, CAPTCHAs, rate limits or terms of service.
- Product text is untrusted data; it is never treated as instructions.
