# Fixtures for websites whose original source is unknown

Some websites (for example the ones that were entered by hand before the
connector framework existed) have no known feed or API. Their current
database rows are exported here once and then synced with the `json_file`
connector, so they flow through the same pipeline as every other website.

Run these on **your own** database (the website ids may differ; check them in
the admin or with `GET /api/websites/`):

```
python manage.py export_website_json --website-id 2 --output ingestion/fixtures/website-2.json
python manage.py configure_website --website-id 2 --connector-type json_file --path ingestion/fixtures/website-2.json --currency USD --sync-enabled
python manage.py sync_website --website-id 2 --dry-run
python manage.py sync_website --website-id 2
```

The dry run should report `created 0` and `deactivated 0`. A few `updated`
rows are expected only where the brand was empty and could be read from the
title.

The exported files use the canonical field names, so no `field_map` is
needed. To change a product, edit the JSON file and run `sync_website` again.
If a site later gets an official API or feed, configure it with
`connector_type http_json` instead; no code change is needed.

The JSON files are not shipped with the project because they are your data.
