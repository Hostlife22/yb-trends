# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
make run          # uvicorn app.main:app --reload (dev server on :8000)
make test         # pytest -q
make sync         # python -m scripts.run_sync --region US --period 7d

# Run a single test file or test
pytest tests/test_api_integration.py -v
pytest tests/test_scoring.py::test_compute_final_score -v

# Docker
docker compose up api              # run API service
docker compose run --rm sync       # one-shot sync
```

## Environment Variables

All prefixed with `YBT_`. Key ones:

- `YBT_GOOGLE_PROVIDER` — `mock` (default/tests), `pytrends` (RSS), `managed` (external API)
- `YBT_GEMINI_API_KEY` — enables Gemini LLM classifier (falls back to heuristic)
- `YBT_API_KEY` — protects `/api/v1/admin/*` endpoints via `x-api-key` header
- `YBT_SQLITE_PATH` — database location (default: `.data/trends.db`)
- `YBT_ENABLE_INPROCESS_SCHEDULER` — `false` in production; use external cron

Full config with defaults: `app/config.py` (Pydantic Settings).

## Architecture

**Python 3.11 / FastAPI / SQLite** service that aggregates Google Trends data, classifies items as movie/animation, scores them, and serves ranked results via REST API.

### Data Flow

```
Provider (mock|pytrends|managed)
  → Classifier (Gemini LLM → heuristic fallback)
    → Quality Gate (min items + relevant ratio)
      → Scoring (interest_level, growth_velocity, final_score)
        → SQLite Repository (snapshot + timeseries)
          → API (cached, with freshness checks)
```

### Layer Responsibilities

- **`app/main.py`** — FastAPI app, startup/shutdown hooks, health/ready/metrics endpoints
- **`app/api/routes_trends.py`** — All `/api/v1/` routes (public trends + admin sync/alerts)
- **`app/api/deps.py`** — API key dependency injection
- **`app/services/trends_service.py`** — Core orchestrator: sync, freshness, top trends, alerts
- **`app/services/providers/`** — Pluggable data sources behind `TrendsProvider` ABC
- **`app/services/classifier.py`** — Heuristic token-based classifier
- **`app/services/llm_classifier.py`** — Gemini classifier with automatic fallback
- **`app/services/scoring.py`** — Ranking formulas (0.6 × interest + 0.4 × growth)
- **`app/db.py`** — SQLite repository, schema migrations, distributed sync locking
- **`app/schemas/trends.py`** — Pydantic request/response models

### Database (SQLite, 5 tables)

`trend_items` (snapshot data) → `trend_points` (timeseries) → `sync_runs` (execution log) → `sync_locks` (lease-based locking) → `schema_migrations` (version tracking). Schema and migrations live in `app/db.py`.

### Key Design Decisions

- **Provider abstraction**: swap data sources via `YBT_GOOGLE_PROVIDER` without code changes
- **Classifier chain**: Gemini LLM → heuristic fallback ensures classification always succeeds
- **Quality gate**: rejects snapshots with `total < 5` or `relevant_ratio < 0.2`
- **Lease-based locking**: prevents concurrent syncs (TTL 20min)
- **Confidence threshold**: API filters items with `confidence >= 0.7`

## CI

GitHub Actions (`ci.yml`): installs deps → runs pytest → smoke-tests sync with mock provider against `.data/ci-smoke.db`.

## Testing

Tests use `tmp_path` fixtures for DB isolation and mock provider for deterministic data. The `TestClient` from FastAPI is used for integration tests. No external services needed — all tests run offline.
