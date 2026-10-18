# EcommerceAI — Project status

Source of truth for what each development session finished. Status values:
`implemented | tested | partial | not_started | blocked`.

## Verification environment used for this work (2026-10-18)

The work was done outside the owner's machine, in a Linux sandbox:

- Python 3.13.16, packages installed from `requirements.txt` at the exact pinned versions.
- PostgreSQL **16** with pgvector **0.6.0** (the owner runs PostgreSQL 18 / pgvector 0.8.7; nothing used is version-specific).
- **Ollama was not reachable** from the sandbox (its download and model registry are blocked there). Automated tests never call a model. Manual HTTP smoke tests used a sandbox-only stand-in server that imitates Ollama's API with canned replies. Those runs prove the HTTP, session, database and pipeline behaviour, **not model quality**. The real-model smoke test must be repeated on the owner's machine (commands in README.md).
- The live `ecommerce_ai` database was not available. ShopZone was loaded with the repository's own importer. GadgetMart and TechGear Store were represented by small **sandbox stand-in rows** (not shipped) because their original source is unknown.

## Phase status

| Phase | Name | Status | Evidence |
|---|---|---|---|
| 0 | Hygiene, configuration, test-database fix | tested | see Phase 0 below |
| 1 | Verify the backend as it is | tested | see Phase 1 below |
| 2 | Test harness and baseline tests | tested | `manage.py test`: 76 tests, OK (expected failures=12) |
| 3 | Backend correctness and reliability | tested | 114 tests OK, 0 expected failures; two-turn smoke test passes |
| 4 | Connector framework and sync | tested | 172 tests OK; `sync_website --dry-run` verified |
| 5 | Onboard existing websites | tested | 177 tests OK; three sandbox websites sync through connectors |
| 6 | Comparison, alternatives, answer quality | tested | 202 tests OK |
| 7 | Read APIs for the UI | not_started | |
| 8 | React + Vite chat UI | not_started | |
| 9 | Production readiness | not_started | |

## Phase 0 — Hygiene, configuration, test database

| Step | Status | Evidence |
|---|---|---|
| 0.1 Git hygiene | tested | `git ls-files` shows no `.env`, `__pycache__`, `db.sqlite3` or `.vscode` (empty output). History not rewritten. |
| 0.2 requirements.txt | tested | `pip install --dry-run -r requirements.txt` resolves; beautifulsoup4 excluded (no import found). |
| 0.3 Settings from environment | tested | `manage.py check` passes; with `DJANGO_DEBUG=false` and no `DJANGO_SECRET_KEY` it stops with a clear ImproperlyConfigured message. |
| 0.4 `__init__.py` renames | tested | `manage.py help` lists `import_shopzone` and `generate_product_embeddings`. |
| 0.5 pgvector for fresh/test DBs | tested | Before: `manage.py test products` failed with `type "vector" does not exist`. After: 6/6 pass with a superuser role on a template without pgvector, and with a non-superuser role after the one-time template1 fix. A non-superuser without the fix gets a clear message naming the fix. |

**Owner action:** `.env` was committed in earlier git history. Rotate `GROQ_API_KEY` and the database password if this repository was ever shared or pushed anywhere.

## Phase 1 — Baseline (before any fixes)

### 1.1 Static checks
`compileall` OK; `manage.py check` no issues; `makemigrations --check --dry-run` no changes; `showmigrations` all applied on a fresh database.

### 1.2 Database inspection (sandbox database)
- ShopZone (id 1): 16 products, currency USD, categories Computers/Electronics/Fashion/Gaming/Home & Kitchen; **16 with empty brand, 16 with empty product_url**, 0 unavailable.
- How GadgetMart and TechGear Store were loaded: **unknown**. No command, fixture, script or git-history line mentions them; they were most likely entered by hand (admin or shell).
- The live database figures (26 products, 26 embeddings) could not be re-checked here.

### 1.3 Two-turn smoke test (baseline code, stand-in model server)
"Suggest headphones under $350" then "Which has the best rating?" on websites 1, 2, 3:

| Check | Result |
|---|---|
| Same conversation_id on turn 2 | pass |
| History loaded before the new message saved | pass (code order and 4 messages in order) |
| Budget kept (max_price 350, USD) | pass |
| Category kept (headphones) | pass |
| Rating sort applied | **fail**: sort_by became `rating`, but results were 4.8, 4.7, 4.7, 4.6, **4.2, 4.4** (hybrid blending reorders, API-6) |
| Website scope unchanged | pass |
| 2 user + 2 assistant messages saved | pass |
| Products come from the database | pass |
| Answer is prose | pass (stand-in text) |
| No stack trace on errors | pass (generic 502 message) |

### 1.4 Known defects at baseline

| Id | Baseline result | Evidence |
|---|---|---|
| SEC-1 | confirmed | `.env`, caches, sqlite were tracked; fixed in 0.1 |
| SEC-2 | confirmed | hard-coded key, DEBUG=True, empty ALLOWED_HOSTS (fixed 0.3); no throttling (fix 3.10) |
| SEC-3 | confirmed | a second session continued conversation 1 with HTTP 200 |
| DB-1 | confirmed | fresh test DB: `type "vector" does not exist`; fixed in 0.5 |
| API-1 | confirmed | failure inside the request saved 0 messages (user message lost), and 4 of 10 conversations were left with no messages |
| API-2 | confirmed | embeddings down -> whole chat 502 |
| API-3 | confirmed | "hello" -> fixed canned text; shopping knowledge question treated as product search |
| API-4 | confirmed | "headphones under $10" -> generic "try relaxing" text |
| API-5 | confirmed | "headphones under 350" -> currency null, no currency filter |
| API-6 | confirmed | rating sort diluted (see 1.3) |
| API-7 (new) | confirmed | "write a python script…" -> HTTP 400 "Search query must not be empty." (no search terms reach SemanticSearchService) |
| DATA-1 | confirmed | 16/16 ShopZone brands empty; "only Sony headphones" on ShopZone -> 0 products |
| DATA-2 | confirmed | 16/16 ShopZone product_url empty |
| DATA-3 | confirmed | `Product.currency` default `INR`; seed data USD |
| DATA-4 | confirmed | `ProductTextService` includes price and rating |
| CFG-1 | confirmed | hard-coded `OLLAMA_BASE_URL` override; fixed 0.3 |
| CFG-2 | confirmed | `_init_.py` files; fixed 0.4 |
| REL-1 | not reproduced | needs the real Ollama model; not reachable from the sandbox |

## Phase 2 — Test harness and baseline tests

| Step | Status | Evidence |
|---|---|---|
| 2.1 Test package and helpers | tested | `assistant/tests/` with `factories.py` (2 websites USD/INR, 10 products) and `fakes.py` (FakeLLM, patch_llm, fake_embed, patch_embeddings); 5 harness tests pass |
| 2.2 ProductSearchService tests | tested | 22 tests |
| 2.3 RequirementsService tests | tested | 14 tests (merge rules and extraction with mocked LLM) |
| 2.4 HybridSearchService tests | tested | 6 tests (mocked embeddings) |
| 2.5 GroundedResponseService and API tests | tested | 4 + 19 tests |

No test calls a live model: every model call goes through `FakeLLM`, and embeddings through `fake_embed`.

### expectedFailure tests and the step that flips each

| Flips in | Test module | Behaviour |
|---|---|---|
| 3.1 | test_chat_api | error responses carry codes |
| 3.1 | test_chat_api | a failed request saves nothing |
| 3.2 | test_hybrid_search | semantic failure falls back to structured |
| 3.2 | test_chat_api | request without search terms does not fail (API-7) |
| 3.3 | test_hybrid_search | explicit sort is not reordered |
| 3.4 | test_product_search | brand matches title when brand field is empty |
| 3.4 | test_product_search | results contain the API contract fields |
| 3.6 | test_chat_api | unrelated request redirected without LLM |
| 3.6 | test_chat_api | general shopping question answered |
| 3.8 | test_requirements | invalid JSON recovers |
| 3.8 | test_chat_api | provider unreachable -> 503 model_unavailable |
| 3.10 | test_chat_api | another session cannot continue a conversation |

## Phase 3 — Backend correctness and reliability

| Step | Defect | Status | Evidence |
|---|---|---|---|
| 3.1 ChatOrchestrator, short transaction | API-1 | tested | `test_failure_saves_nothing` (no conversation or message written when the model fails); thin view; `{error, code}` everywhere |
| 3.2 Semantic fallback | API-2, API-7 | tested | embeddings down -> structured results + notice; empty search terms no longer return 400 |
| 3.3 Explicit sort wins | API-6 | tested | smoke test turn 2 now 4.8, 4.7, 4.7, 4.6, 4.4, 4.2 |
| 3.4 Brand matching, product fields | DATA-1 (part 1) | tested | whole-word brand, title fallback for empty brand; `brand` in ProductSerializer; results carry description, original_price, review_count, last_fetched_at |
| 3.5 Currency policy | API-5 | tested | mixed currencies -> one question listing codes; the reply ("USD") resumes the search without a model call |
| 3.6 Intent handling | API-3 | tested | scope guard before any model call; greeting needs no model; general shopping questions answered as labelled general advice; out_of_scope redirect |
| 3.7 No-match diagnostics | API-4 | tested | e.g. "23 products are in your selected websites; 6 match "headphones"; ...; none costs 10.00 USD or less. The lowest price for headphones is 39.95 USD. Raise your budget to at least 39.95 USD." |
| 3.8 LLM reliability | REL-1 | tested (mocked) | invalid JSON -> one strict retry -> heuristic extractor -> clarification; provider errors -> HTTP 503 `model_unavailable` |
| 3.9 Answer validation | grounding | tested | invented price/URL replaced by a deterministic template |
| 3.10 Ownership and throttling | SEC-3, SEC-2 | tested | another session gets 404; `ScopedRateThrottle` scope `chat` -> 429 `rate_limited` |

Decisions and notes:
- **Currency "in scope"** is read as the products that match the request's other hard filters. A laptop search across a USD and an INR site where only the USD site sells laptops is therefore not interrupted.
- **No-match wording order.** The message checks product type, brand and features before stock, currency, price and rating. That gives the reading "N products; K are headphones; none is under 350 USD" from the example.
- **New defects found and fixed:** API-7 (empty search terms gave HTTP 400), and the feature alias "anc" matching inside words such as "performance", so a mouse counted as noise-cancelling.
- **Conversation owners.** Conversations created before 3.10 have `owner_key = ''` and are reachable only through the Django admin.
- **Model size.** `qwen2.5:0.5b-instruct` is very small, and REL-1 could not be re-tested against it here. If extraction quality stays poor, try `LLM_PROVIDER=groq` or a larger Ollama model (for example `qwen2.5:3b-instruct`). The provider was not changed.
- **Prompt size.** The answer prompt now holds at most 8 products (all matches are still returned as product cards). This speeds up the answer call.

## Phase 4 — Connector framework and sync

| Step | Status | Evidence |
|---|---|---|
| 4.1 Website/Product sync fields, SyncRun | tested | migrations `websites.0002`, `products.0004`, `ingestion.0001` (dry-run reviewed first); `Product.currency` no longer defaults to INR (DATA-3) |
| 4.2 CanonicalProduct and normalizers | tested | pydantic model; http(s) URLs only; `content_hash`; brand derived from `ingestion/data/brands.json` |
| 4.3 Connectors | tested | `json_file`, `http_json` (page/cursor pagination, bounded retries with Retry-After, secrets from env var names), `shopzone` adapter; registry |
| 4.4 SyncService | tested | idempotent upsert by `(website, external_product_id)`; unchanged hash -> no write; missing products deactivated, never deleted; shrink guard (>10 active and <50% fetched -> `partial`, nothing deactivated); one website's failure never touches another |
| 4.5 Embedding text | tested | price, currency and rating removed from embedding text (DATA-4); a price change does not re-embed |
| 4.6 Commands and freshness | tested | `sync_website --website-id N [--dry-run]`, `sync_all`, `export_website_json`; `import_shopzone` now calls SyncService; chat response carries `website_freshness` and a notice for stale or never-synced websites |

Verification: `manage.py sync_website --website-id 1 --dry-run` on the sandbox ShopZone row (still `connector_type=manual` before Phase 5) ends with a clear message: "connector_type 'manual', which cannot be synced. Available types: http_json, json_file, shopzone." No product was written and `last_sync_status` was not changed by the dry run.

Notes:
- **One-time re-embed needed.** Because the embedding text changed (4.5), run `python manage.py generate_product_embeddings` once (or a real sync) on your own database so stored vectors match the new text.
- **Scheduling.** There is no scheduler in the project. Use Windows Task Scheduler to run `python manage.py sync_all` (see CONNECTORS.md).

## Phase 5 — Onboard existing websites

| Step | Status | Evidence |
|---|---|---|
| 5.1 ShopZone | tested (sandbox DB) | `configure_website --website-id 1 --connector-type shopzone --path products-export.json --currency <SHOPZONE_CURRENCY> --sync-enabled`; dry run: updated 12, unchanged 4, created 0; real run the same; second run: unchanged 16. 16 rows, 0 duplicate ids. Brands filled for 12/16 (DATA-1); the 4 left empty have no brand word in the title (PlayStation 5, Kindle, a watch, a plant pot) and are not guessed. product_url stays empty (DATA-2): products-export.json has no URL field and the ShopZone page opens products in a quick-view modal, so there is no real product page scheme and no `url_template` was set. |
| 5.2 GadgetMart, TechGear Store | tested (sandbox stand-ins) | `export_website_json` -> `ingestion/fixtures/website-<id>.json`, `configure_website ... --connector-type json_file`; GadgetMart dry run and real run: unchanged 4. TechGear: 1 updated (empty brand filled with "Sennheiser" from the title), then unchanged 3. Embedding count unchanged (23). |
| 5.3 Multi-site chat | tested | All three selected, "Suggest Sony headphones under $350": 3 Sony results, one per site (ShopZone's Sony now matches, DATA-1). Only GadgetMart selected: 1 result. Currency inferred as USD because every in-scope product is USD; mixed-currency clarification is covered by tests (USD + INR catalog). `website_freshness` lists each selected site. Integration tests: sync from a temporary JSON file then chat; a price change in the source reaches the next chat with no re-embed; scope isolation. |

Done-when evidence: `test_fourth_json_website_needs_only_configuration` creates a new website with only a Website row and a `field_map`, syncs it and finds its products through chat.

**Your database:** the sandbox GadgetMart and TechGear rows are stand-ins, so their fixture files are not shipped. Run the commands in `ingestion/fixtures/README.md` on your own database.
New command `configure_website` sets connector settings without the admin (generic; no site names in code).

## Phase 6 — Comparison, alternatives and answer quality

| Step | Status | Evidence |
|---|---|---|
| 6.1 ComparisonService | tested | `comparison_service.build_comparison`: rows (price, currency, rating, review_count, availability, key features, website) and facts (cheapest, best rated, most reviewed) computed only inside one currency; ties name every winner; a cross-website cheapest fact is dropped when one of those websites is stale (with a note). Used for intent `product_comparison` and questions such as "which is cheapest" / "which has the best rating" / "compare". The model only explains the object; the explanation goes through the answer validator and must name a compared product, otherwise a deterministic comparison text is used. |
| 6.2 Alternatives | tested | `alternatives_service.find_alternatives`: at most 3, each fails exactly one of min_rating, max_price (up to +15%), one must-have feature; scope, currency, availability, brand and category never relaxed. Looked for when fewer than 3 products match. Returned in `alternatives` with `unmet`; the answer adds them under "These do not fully match your request:". `test_strict_budget_miss_is_an_alternative_not_a_match` proves a budget miss never appears in `products`. |
| 6.3 Follow-up quality | tested | `test_multiturn.py`: budget change, brand change and removal, rating question, comparison of previous results, constraint removal, unrelated request mid-conversation (memory kept), new conversation starts clean. |

Sandbox check (stand-in model): "Which headphones under $350 are cheapest?" across three websites -> cheapest fact JBL 39.95 USD; best rated lists both 4.7 Sony listings with their websites. "Sennheiser headphones under $140" -> Sennheiser HD 450BT (149.99 USD) offered as an alternative with "Price 149.99 USD is above your budget of 140.00 USD".
