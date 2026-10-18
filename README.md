# EcommerceAI

A shopping assistant that answers questions about the products of the websites you
select. It searches your own product database (PostgreSQL + pgvector), enforces every
hard requirement (website, budget, currency, stock, rating, brand, product type,
required features) in code, and uses a language model only to understand the request
and explain verified results. It never invents prices, ratings or links.

- Backend: Django 6.1 + Django REST Framework, PostgreSQL with the pgvector extension
- Models: Ollama (chat and `nomic-embed-text` embeddings) or Groq for chat
- Frontend: React + Vite (plain JSX, `fetch`, plain CSS) in `frontend/`
- Product data: synced from each website through connectors (`ingestion/`)

The static ShopZone demo store (`index.html`, `js/`, `css/`) is test data; its old
README is in `docs/SHOPZONE_README.md`.

More detail: [ARCHITECTURE.md](ARCHITECTURE.md) (design and API),
[CONNECTORS.md](CONNECTORS.md) (adding websites), [TESTING.md](TESTING.md),
[PROJECT_STATUS.md](PROJECT_STATUS.md) (what was done and verified).

## 1. Requirements

- Windows 10/11 with PowerShell (the commands below), Python 3.12+, Node.js 18+
- PostgreSQL 16+ with the **pgvector** extension installed
- Ollama with the chat model and `nomic-embed-text` pulled (or a Groq API key for chat)

## 2. Setup (PowerShell)

```powershell
cd D:\AImodalW
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env      # only if you do not have a .env yet
notepad .env                     # fill in the values (see below)
```

### Environment variables (`.env`)

| Name | Purpose |
|---|---|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL connection |
| `DJANGO_SECRET_KEY` | required when `DJANGO_DEBUG` is false |
| `DJANGO_DEBUG` | `true` for local development (default false) |
| `DJANGO_ALLOWED_HOSTS` | comma-separated host names |
| `DJANGO_HTTPS`, `DJANGO_SSL_REDIRECT`, `DJANGO_HSTS_SECONDS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | production HTTPS settings |
| `DJANGO_LOG_LEVEL` | console log level (default `INFO`) |
| `LLM_PROVIDER` | `ollama` (default) or `groq` |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_EMBEDDING_MODEL` | Ollama settings |
| `GROQ_API_KEY`, `GROQ_MODEL` | Groq settings (only for `LLM_PROVIDER=groq`) |
| `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES` | model call limits |
| `STALE_AFTER_HOURS` | when a website's data counts as out of date (default 24) |
| `CHAT_RATE_LIMIT` | chat requests per client (default `30/min`) |
| `SHOPZONE_BASE_URL`, `SHOPZONE_CURRENCY` | the ShopZone test website |

Never commit `.env`. If this repository was ever shared, rotate `GROQ_API_KEY` and the
database password: an old commit contains a `.env`.

### PostgreSQL and pgvector

```powershell
psql -U postgres -c "CREATE DATABASE ecommerce_ai;"
```

`migrate` creates the `vector` extension automatically. If your database user is not a
superuser and migrate (or the test run) says the extension cannot be created, run this
once as a superuser, which also makes it available to the test database:

```powershell
psql -U postgres -d template1 -c "CREATE EXTENSION IF NOT EXISTS vector;"
psql -U postgres -d ecommerce_ai -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Then:

```powershell
python manage.py migrate
python manage.py createsuperuser        # for /admin/
```

## 3. Run

Two terminals:

```powershell
# Terminal 1 — backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2 — frontend
cd frontend
npm install        # first time only
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` to Django on 127.0.0.1:8000, so no CORS
setup is needed. Health check: http://127.0.0.1:8000/api/health/ returns
`{status, database, ollama}`.

For a production build of the UI: `cd frontend; npm run build` (output in `frontend/dist/`).

## 4. Product data

Every website is synced by a connector. Typical commands:

```powershell
python manage.py sync_website --website-id 1 --dry-run   # show what would change
python manage.py sync_website --website-id 1             # apply
python manage.py sync_all                                # every active website with sync enabled
python manage.py generate_product_embeddings             # (re)create missing or outdated embeddings
```

The ShopZone test website: `python manage.py import_shopzone` (same as syncing it).
To onboard a website, see [CONNECTORS.md](CONNECTORS.md). For websites whose original
source is unknown, see `ingestion/fixtures/README.md`.

### Scheduling sync with Windows Task Scheduler

There is no scheduler inside the project. Create a daily task (example: 06:00):

```powershell
schtasks /Create /TN "EcommerceAI sync" /SC DAILY /ST 06:00 `
  /TR "cmd /c cd /d D:\AImodalW && .venv\Scripts\python.exe manage.py sync_all >> sync.log 2>&1"
```

Run it once by hand with `schtasks /Run /TN "EcommerceAI sync"`; results are also stored
as Sync runs in the admin.

## 5. Tests

```powershell
python manage.py test -v 2
```

Tests never call Ollama or Groq; see [TESTING.md](TESTING.md).

## 6. Backup

```powershell
pg_dump -U postgres -F c -f ecommerce_ai_backup.dump ecommerce_ai
# restore into an empty database:
pg_restore -U postgres -d ecommerce_ai ecommerce_ai_backup.dump
```

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `ImproperlyConfigured: Set DJANGO_SECRET_KEY…` | add `DJANGO_DEBUG=true` (local) or a `DJANGO_SECRET_KEY` to `.env` |
| `type "vector" does not exist` / cannot create extension | run the template1 command in section 2 |
| Chat answers "The assistant's language model is not reachable" (503 `model_unavailable`) | start Ollama (`ollama serve`) or check `OLLAMA_BASE_URL` / Groq key |
| Notice "Semantic ranking was unavailable" | the embedding model is not reachable; results still come from the database |
| "Data for … has never been synced" | run `sync_website` for that website |
| UI shows "Cannot reach the server" | start `python manage.py runserver` on port 8000 |
| Poor understanding of requests | the default `qwen2.5:0.5b-instruct` is very small; try a larger Ollama model or `LLM_PROVIDER=groq` |
