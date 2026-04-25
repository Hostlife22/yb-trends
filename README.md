# yb-trends

Backend-сервис для сбора и ранжирования трендов фильмов/мультфильмов в США за 7 дней.

## Что уже реализовано
- FastAPI API: `/health`, `/ready`, `/api/v1/trends/top`, `/api/v1/summary`, `/api/v1/admin/sync`, `/api/v1/admin/freshness`
- Дополнительные аналитические API: `/api/v1/admin/snapshots`, `/api/v1/trends/{query}/timeseries`
- Provider interface + выбор провайдера через env (`mock` / `pytrends` / `managed`)
- `PyTrendsProvider` (RSS-based best-effort интеграция) + `ManagedTrendsProvider` (production API adapter)
- Gemini classifier с fallback на heuristic classifier
- SQLite storage (`trend_items`, `trend_points`, `sync_locks`) + schema migrations
- In-memory TTL cache для top endpoint
- API key защита для API (опционально)
- In-process scheduler (опционально, по флагу)
- External sync runner (`python -m scripts.run_sync`) для cron/CI
- Lock/lease в SQLite для защиты от параллельного sync

## Конфигурация (env)
- `YBT_GOOGLE_PROVIDER=mock|pytrends|managed`
- `YBT_MANAGED_PROVIDER_URL=https://...`
- `YBT_MANAGED_PROVIDER_API_KEY=<optional>`
- `YBT_GEMINI_API_KEY=<key>`
- `YBT_API_KEY=<optional-api-key>`
- `YBT_SQLITE_PATH=.data/trends.db`
- `YBT_CACHE_TTL_SECONDS=600`
- `YBT_SYNC_INTERVAL_SECONDS=21600`
- `YBT_MAX_SNAPSHOT_AGE_SECONDS=43200`
- `YBT_LOCK_TTL_SECONDS=1200`
- `YBT_ENABLE_INPROCESS_SCHEDULER=false`

## Локальный запуск
```bash
make run
```

## Запуск sync вручную
```bash
make sync
```

## Тесты
```bash
make test
```

## CI/CD
- GitHub Actions workflow: `.github/workflows/ci.yml`
- Docker image: `Dockerfile`
- Локальный compose: `docker-compose.yml`

Подробный roadmap: [`docs/implementation-plan.ru.md`](docs/implementation-plan.ru.md)
