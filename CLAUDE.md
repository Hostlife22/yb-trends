# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Monorepo Structure

```
yb-trends/
├── apps/
│   ├── api/          # Python backend (FastAPI)
│   └── dashboard/    # Frontend dashboard (Next.js)
├── docker-compose.yml
└── Makefile
```

## Build & Run Commands

```bash
# ── API (from root) ──────────────────────────────
make api-run          # uvicorn on :8000
make api-test         # pytest -q
make api-sync         # one-shot sync

# ── API (from apps/api/) ────────────────────────
cd apps/api
uvicorn app.main:app --reload
pytest tests/test_api_integration.py -v

# ── Dashboard (from root) ───────────────────────
make dash-dev         # dev server on :3000
make dash-build       # production build

# ── Docker ──────────────────────────────────────
docker compose up api dashboard    # run both services
docker compose run --rm sync       # one-shot sync
```

## API (apps/api/)

**Python 3.11 / FastAPI / SQLite** service that aggregates Google Trends data, classifies items as movie/animation, scores them, and serves ranked results via REST API.

### Environment Variables

All prefixed with `YBT_`. Key ones:

- `YBT_GOOGLE_PROVIDER` — `mock` (default/tests), `pytrends` (RSS), `gemini` (Gemini + grounding), `managed` (external API)
- `YBT_GEMINI_API_KEY` — required for `gemini` provider and LLM classifier
- `YBT_API_KEY` — protects all `/api/v1/*` endpoints via `x-api-key` header
- `YBT_SQLITE_PATH` — database location (default: `.data/trends.db`)

Full config with defaults: `apps/api/app/config.py` (Pydantic Settings).

### Data Flow

```
Provider (mock|pytrends|gemini|managed)
  → Classifier (Gemini LLM with grounding → heuristic fallback)
    → Quality Gate (min items + relevant ratio)
      → Scoring (interest_level, growth_velocity, final_score)
        → SQLite Repository (snapshot + timeseries with UPSERT dedup)
          → API (cached, with freshness checks)
```

### Layer Responsibilities

- **`app/main.py`** — FastAPI app, startup/shutdown hooks, health/ready/metrics endpoints
- **`app/api/routes_trends.py`** — All `/api/v1/` routes (public trends + admin sync/alerts)
- **`app/api/deps.py`** — API key dependency injection
- **`app/services/trends_service.py`** — Core orchestrator: sync, freshness, top trends, alerts
- **`app/services/providers/`** — Pluggable data sources behind `TrendsProvider` ABC
- **`app/services/providers/gemini_provider.py`** — Discovers movies via Gemini + Google Search grounding
- **`app/services/classifier.py`** — Heuristic token-based classifier
- **`app/services/llm_classifier.py`** — Gemini classifier with grounding (returns studio field)
- **`app/services/scoring.py`** — Ranking formulas (0.6 × interest + 0.4 × growth)
- **`app/db.py`** — SQLite repository, schema migrations (6 versions), sync locking

### Database (SQLite, 5 tables)

`trend_items` (snapshot data with studio field) → `trend_points` (timeseries, UPSERT dedup by day) → `sync_runs` (execution log) → `sync_locks` (lease-based locking) → `schema_migrations` (version tracking).

### Key Design Decisions

- **Provider abstraction**: swap data sources via `YBT_GOOGLE_PROVIDER` without code changes
- **Gemini provider**: uses Google Search grounding to find real trending movies
- **Classifier chain**: Gemini LLM with grounding → heuristic fallback
- **Studio detection**: Gemini identifies production company (Disney, Netflix, A24, etc.)
- **Only movies saved**: non-movie trends filtered before DB write
- **UPSERT dedup**: trend_points deduplicated by (query, region, period, day)
- **Confidence threshold**: API filters items with `confidence >= 0.7`

## CI

GitHub Actions (`ci.yml`): job per app. API job runs in `apps/api/` working directory.

## Testing (API)

Tests use `tmp_path` fixtures for DB isolation and mock provider for deterministic data. The `TestClient` from FastAPI is used for integration tests. No external services needed — all tests run offline.

```bash
cd apps/api && pytest -v
```
