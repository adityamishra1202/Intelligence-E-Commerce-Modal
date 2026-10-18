# EcommerceAI — Architecture

## Overview

```
Browser (React, frontend/)  --/api-->  Django REST views (thin)
                                          |
                                ChatOrchestrator (assistant/services)
            scope_guard -> RequirementsService (LLM, JSON) -> merge with memory
            -> currency_policy -> HybridSearchService
                   ProductSearchService (hard filters, ORM + code)
                   SemanticSearchService (pgvector, ranking only)
            -> answer: GroundedResponseService | ComparisonService | SearchDiagnostics
            -> answer_validator -> alternatives -> freshness notices
            -> one short transaction: conversation, 2 messages, memory
PostgreSQL + pgvector  <--  ingestion/ SyncService  <--  connectors (json_file, http_json, shopzone)
```

## Apps

| App | Responsibility |
|---|---|
| `assistant` | chat API, orchestration, search, model calls, embeddings, health check |
| `products` | `Product` model, product list API |
| `websites` | `Website` model (connector settings, sync status), website list API |
| `conversations` | `Conversation` (owner_key, website_scope, memory) and `Message`, read APIs |
| `ingestion` | canonical product model, normalizers, connectors, `SyncService`, `SyncRun`, sync commands |

## Chat flow rules

- **Scope guard first.** Requests for code, essays and the like are redirected and
  greetings answered without any model call. Memory is not changed.
- **Extraction.** The model returns JSON validated by pydantic. Invalid output gets one
  stricter retry, then a deterministic heuristic, then a clarifying question. Provider
  errors become HTTP 503 `model_unavailable`.
- **Memory.** The conversation stores the current requirements; follow-ups are merged
  deterministically (budget changes, brand change/removal, feature removal, "remove
  the budget"). General questions and out-of-scope requests never change memory.
- **Currency.** A stated currency filters; one currency in scope is used; several
  currencies in scope trigger one question listing the codes. Never converted.
- **Hard filters in code.** Website scope, budget, currency, stock, rating, brand
  (whole word; title fallback when brand is empty), product type and required features
  are applied before any ranking. Semantic similarity only reorders for
  `sort_by=relevance`; an explicit sort (price, rating) is never reordered. If the
  embedding model is down, search falls back to standard ranking with a notice.
- **No matches.** `SearchDiagnostics` names the first requirement that removes all
  products and the single easiest change. No model call; no non-matching products.
- **Alternatives.** At most 3, each failing exactly one of min rating, budget (+15% max)
  or one feature; returned separately with `unmet`.
- **Comparison.** Rows and facts (cheapest, best rated, most reviewed) computed in
  code, within one currency, cross-website price facts only for fresh data. The model
  only explains it.
- **Validation.** Every price, rating and URL in a generated answer must come from the
  records (or the user's own budget/rating). Otherwise a deterministic template is used.
- **Persistence.** All model and search work runs outside transactions; one short
  transaction saves the conversation, both messages and memory. A failure saves nothing.
- **Ownership.** `owner_key` is the Django session key. Other sessions get 404.
  `ScopedRateThrottle` scope `chat` limits requests.

## Data and sync

- `Product` is unique per `(website, external_product_id)`; has `content_hash` and
  `last_seen_at`; indexes on `(website, is_available)`, `price`, `rating`.
- `SyncService.run(website, dry_run)` fetches through the website's connector,
  normalizes to `CanonicalProduct`, and upserts: unchanged hash = no write; products
  missing from a successful fetch are marked unavailable (never deleted); a suspicious
  shrink (>10 active products and <50% fetched) deactivates nothing and ends `partial`.
  Embeddings are refreshed only when the embedding text changes (price, currency and
  rating are not part of it). Every run is recorded as a `SyncRun`.
- A website is **stale** when never synced or last synced more than `STALE_AFTER_HOURS` ago.

## Security

- Settings from the environment; `DEBUG` off by default; secret key required in production.
- `nosniff`, `X-Frame-Options: DENY`, HttpOnly + SameSite=Lax cookies, secure cookies,
  SSL redirect and HSTS with `DJANGO_HTTPS=true`. `check --deploy` leaves only the HSTS
  preload warning, which is deliberately left to the operator.
- Product text is treated as data in every prompt. Logs record error types, never request
  bodies, prompts or keys.
- The UI renders answers with its own small renderer (no `dangerouslySetInnerHTML`) and
  links only http(s) URLs.

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

### GET /api/health/

`{status: ok|degraded|error, database: ok|unavailable, ollama: ok|unavailable}`.
`degraded` (HTTP 200) when Ollama is unreachable; `error` (HTTP 503) when the database is.
No URLs, versions or secrets are returned.
