# Testing

```powershell
.\.venv\Scripts\Activate.ps1
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test -v 2                 # everything
python manage.py test assistant -v 2       # one app
python manage.py test assistant.tests.test_multiturn -v 2
```

The test database is created by Django and needs the pgvector extension (see README,
"PostgreSQL and pgvector"). Ollama, Groq and the network are **never** used by tests.

## Test doubles (`assistant/tests/fakes.py`)

- `patch_llm(responses, default)` replaces `LLMService` everywhere with `FakeLLM`.
  Responses are strings, exceptions or callables. `route(extraction_json, answer, advice)`
  answers extraction prompts with JSON and other prompts with prose.
- `extraction(**fields)` builds the JSON the extraction model would return.
- `patch_embeddings(side_effect=None)` replaces the embedding call with `fake_embed`, a
  deterministic vector (texts that share words are similar); pass an exception to
  simulate an outage.
- `assistant/tests/factories.py`: `create_website`, `create_product`, and
  `build_catalog()` (a USD and an INR website with ten products).

## Where things are tested

| Area | Tests |
|---|---|
| Hard filters, brand matching, diagnostics | `assistant/tests/test_product_search.py`, `test_search_diagnostics.py` |
| Extraction, retries, heuristics, memory merge | `test_requirements.py` |
| Hybrid ranking, fallback, embedding text | `test_hybrid_search.py` |
| Currency policy, scope guard | `test_currency_policy.py`, `test_scope_guard.py` |
| Answer validation | `test_answer_validator.py`, `test_grounded_response.py` |
| Chat API (contract, errors, ownership, throttle, freshness) | `test_chat_api.py` |
| Comparison and alternatives | `test_comparison.py` |
| Multi-turn conversations | `test_multiturn.py` |
| Health endpoint | `test_health.py` |
| Website / conversation read APIs | `websites/tests.py`, `conversations/tests.py` |
| Canonical model, normalizers, connectors | `ingestion/tests/test_canonical.py`, `test_connectors.py` |
| Sync service, commands, sync-then-chat | `ingestion/tests/test_sync_service.py`, `test_commands.py`, `test_integration.py` |

## Manual checks

- Frontend build: `cd frontend; npm run build`.
- Browser scenario: run Django and `npm run dev`, select a website, ask
  "Suggest headphones under $350", then "Which has the best rating?", then
  "Actually increase my budget to 400", reload and reopen the conversation.
- API smoke test (PowerShell):

  ```powershell
  $r1 = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat/ -ContentType 'application/json' -Body '{"message":"Suggest headphones under $350","website_ids":[1]}' -SessionVariable s
  $r1.answer
  $r2 = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/chat/ -ContentType 'application/json' -WebSession $s -Body ('{"message":"Which has the best rating?","website_ids":[1],"conversation_id":' + $r1.conversation_id + '}')
  $r2.answer
  ```
