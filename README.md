# yb-trends

Backend-сервис для сбора и ранжирования трендов фильмов/мультфильмов в США за 7 дней.

## Что уже реализовано
- FastAPI API: `/health`, `/ready`, `/api/v1/trends/top`, `/api/v1/summary`, `/api/v1/admin/sync`, `/api/v1/admin/freshness`
- Provider interface + выбор провайдера через env (`mock` / `pytrends`)
- `PyTrendsProvider` (RSS-based best-effort интеграция) + fallback на mock
- Gemini classifier с fallback на heuristic classifier
- SQLite storage (`trend_items`) для snapshot-подхода
- In-memory TTL cache для top endpoint
- API key защита для API (опционально)
- Background scheduler для регулярной синхронизации

## Конфигурация (env)
- `YBT_GOOGLE_PROVIDER=mock|pytrends`
- `YBT_GEMINI_API_KEY=<key>`
- `YBT_API_KEY=<optional-api-key>`
- `YBT_SQLITE_PATH=.data/trends.db`
- `YBT_CACHE_TTL_SECONDS=600`
- `YBT_SYNC_INTERVAL_SECONDS=21600`
- `YBT_MAX_SNAPSHOT_AGE_SECONDS=43200`

## Тесты
```bash
pytest -q
```

Подробный roadmap: [`docs/implementation-plan.ru.md`](docs/implementation-plan.ru.md)
