# EcommerceAI — Architecture

## API contract

All endpoints are JSON. Errors always have the shape
`{"error": "<safe message>", "code": "<snake_case>"}` (validation errors add `details`).
Conversations belong to the browser session (Django session cookie); there is no login.
Another browser's conversation is always reported as **404**, never 403.

### POST /api/chat/

Request:

| Field | Type | Rules |
|---|---|---|
| `message` | string | 1–2000 characters |
| `website_ids` | list of int | 1–10 active website ids |
| `conversation_id` | int, optional | must belong to this session and have the same website scope |

Response 200:

| Field | Meaning |
|---|---|
| `conversation_id` | id to send with the next turn |
| `message` | echo of the user message |
| `intent` | `product_search`, `product_comparison`, `general_question`, `out_of_scope` or `clarification_needed` |
| `answer` | text for the UI (`**bold**` and `- ` list lines only) |
| `requirements` | extracted requirements, for debugging; the UI never shows it |
| `total_products` | number of items in `products` |
| `products` | Product objects that satisfy **every** hard requirement |
| `alternatives` | at most 3 near misses: Product object plus `unmet` (list of strings) |
| `comparison` | `null` or `{products: [rows], facts: [...], notes: [...]}` |
| `website_freshness` | `[{website_id, website_name, last_synced_at, stale}]` for the selected websites |
| `notices` | short user-safe strings, e.g. "Semantic ranking was unavailable; results use standard ranking." |

Product object: `id, website_id, website_name, title, brand, category, description,
price (string), original_price (string or null), currency, rating (number or null),
review_count (int or null), is_available, product_url, image_url, features,
specifications, last_fetched_at`.

Comparison fact: `{kind: cheapest|best_rated|most_reviewed, currency, value, product_ids, titles, website_names}`.
Facts are computed only inside one currency.

Errors:

| HTTP | code | When |
|---|---|---|
| 400 | `invalid_request` | bad JSON or field values |
| 400 | `website_unavailable` | an id is unknown or inactive |
| 404 | `conversation_not_found` | not this session's conversation, or scope differs |
| 429 | `rate_limited` | more than `CHAT_RATE_LIMIT` (default `30/min`) |
| 503 | `model_unavailable` | the language model is unreachable or timed out |
| 500 | `internal_error` | anything else (no details are returned) |

### GET /api/websites/

Active websites only: `[{id, name, base_url, default_currency, last_synced_at, stale}]`.
`stale` is true when the website was never synced or its last sync is older than
`STALE_AFTER_HOURS` (default 24). Connector settings are never returned.

### GET /api/conversations/

This session's newest 50 conversations, newest first:
`[{id, title, website_scope, updated_at}]`. A browser without a session gets `[]`
(no session is created by reading).

### GET /api/conversations/<id>/

`{id, title, website_scope, messages: [{role, content, created_at}]}`, messages oldest
first. 404 `conversation_not_found` unless the conversation belongs to this session.

### GET /api/products/

The original product list endpoint (paginated, 10 per page), unchanged apart from `brand`.
