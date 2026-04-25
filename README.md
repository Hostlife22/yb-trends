# yb-trends

`yb-trends` — backend-сервис на FastAPI для сбора, фильтрации и ранжирования поисковых трендов по фильмам/анимации в регионе **US** за период **7d**.

Документ ниже — актуальная техническая документация по запуску, конфигурации, API-контрактам, метрикам и эксплуатации.

---

## 1. Возможности сервиса

- REST API для:
  - получения топа трендов;
  - получения краткого summary;
  - админ-операций (sync/freshness/snapshots/sync-runs/metrics/alerts).
- Провайдеры данных с переключением через env:
  - `mock` (локальные/тестовые данные),
  - `pytrends` (RSS-based best-effort),
  - `managed` (внешний managed API).
- Классификация трендов:
  - Gemini LLM (если задан API key),
  - fallback на эвристический классификатор.
- Scoring модели трендов (`interest_level`, `growth_velocity`, `final_score`).
- Хранение данных в SQLite:
  - `trend_items`,
  - `trend_points`,
  - `sync_locks`,
  - `sync_runs`.
- Quality Gate на этапе sync:
  - минимум найденных элементов,
  - минимум доли релевантных.
- Operational observability:
  - `/api/v1/admin/metrics`,
  - `/api/v1/admin/alerts`,
  - `/metrics` в формате Prometheus.
- Защита API ключом (`YBT_API_KEY`, опционально).

---

## 2. Архитектура

### 2.1 Поток данных

1. **Provider** загружает weekly trends (US).
2. **Classifier** определяет релевантность к movie/animation.
3. **Quality Gate** валидирует качество набора.
4. **Repository** сохраняет snapshot + timeseries.
5. **API layer** отдает данные клиентам.
6. **Scheduler/CLI** инициируют регулярный sync.

### 2.2 Основные модули

- `app/main.py` — инициализация FastAPI, startup/shutdown, `/health`, `/ready`, `/metrics`.
- `app/api/routes_trends.py` — все API маршруты `/api/v1/*`.
- `app/services/trends_service.py` — orchestration sync/read path, quality gate, alerts.
- `app/services/providers/*` — адаптеры провайдеров данных.
- `app/services/llm_classifier.py` и `app/services/classifier.py` — LLM + fallback классификация.
- `app/db.py` — миграции SQLite, доступ к данным, lock/sync-run/snapshot операции.
- `scripts/run_sync.py` — CLI для внешнего cron/CI запуска sync.

---

## 3. Быстрый старт

### 3.1 Требования

- Python 3.11+
- `pip`

### 3.2 Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3.3 Локальный запуск API

```bash
make run
```

После запуска сервис доступен по `http://localhost:8000`.

Проверка:

```bash
curl http://localhost:8000/health
```

---

## 4. Конфигурация (ENV)

Все переменные читаются из окружения с префиксом `YBT_`.

### 4.1 Базовые

- `YBT_APP_NAME` (default: `YB Trends`)
- `YBT_DEFAULT_REGION` (default: `US`)
- `YBT_DEFAULT_PERIOD` (default: `7d`)
- `YBT_DEFAULT_LIMIT` (default: `20`)

### 4.2 Провайдеры

- `YBT_GOOGLE_PROVIDER=mock|pytrends|managed` (default: `mock`)
- `YBT_MANAGED_PROVIDER_URL=<https://...>`
- `YBT_MANAGED_PROVIDER_API_KEY=<optional>`

### 4.3 Классификация

- `YBT_GEMINI_API_KEY=<optional>`

Если ключ не задан или LLM недоступен, сервис использует эвристический классификатор.

### 4.4 Безопасность

- `YBT_API_KEY=<optional>`

Если задана, почти все `/api/v1/*` endpoint’ы требуют заголовок:

```http
x-api-key: <YBT_API_KEY>
```

### 4.5 Хранилище и кэш

- `YBT_SQLITE_PATH=.data/trends.db`
- `YBT_CACHE_TTL_SECONDS=600`

### 4.6 Sync и freshness

- `YBT_SYNC_INTERVAL_SECONDS=21600`
- `YBT_MAX_SNAPSHOT_AGE_SECONDS=43200`
- `YBT_LOCK_TTL_SECONDS=1200`
- `YBT_ENABLE_INPROCESS_SCHEDULER=false`

### 4.7 Quality Gate

- `YBT_QUALITY_MIN_ITEMS=5`
- `YBT_QUALITY_MIN_RELEVANT_RATIO=0.2`

### 4.8 Alert thresholds

- `YBT_ALERT_SNAPSHOT_AGE_SECONDS=21600`
- `YBT_ALERT_QUALITY_FAILURES_24H=3`

---

## 5. API контракты

> Ниже показаны основные endpoint’ы и назначение. Формальные Pydantic-схемы находятся в `app/schemas/trends.py`.

### 5.1 Service endpoints

- `GET /health` — liveliness check.
- `GET /ready` — readiness + freshness status.
- `GET /metrics` — метрики в Prometheus text format.

### 5.2 Public/consumer API (`/api/v1`)

- `GET /api/v1/trends/top?region=US&period=7d&limit=20`
- `GET /api/v1/summary?region=US&period=7d&limit=20`
- `GET /api/v1/trends/{query}/timeseries?region=US&period=7d&limit=200`

### 5.3 Admin API (`/api/v1/admin`)

- `POST /api/v1/admin/sync?region=US&period=7d`
- `GET /api/v1/admin/freshness?region=US&period=7d`
- `GET /api/v1/admin/snapshots?region=US&period=7d&limit=20`
- `GET /api/v1/admin/sync-runs?region=US&period=7d&limit=50`
- `GET /api/v1/admin/metrics?region=US&period=7d`
- `GET /api/v1/admin/alerts?region=US&period=7d`

### 5.4 Пример запроса top

```bash
curl -H "x-api-key: $YBT_API_KEY" \
  "http://localhost:8000/api/v1/trends/top?region=US&period=7d&limit=10"
```

### 5.5 Пример запроса alerts

```bash
curl -H "x-api-key: $YBT_API_KEY" \
  "http://localhost:8000/api/v1/admin/alerts?region=US&period=7d"
```

Возможные alert-коды:

- `snapshot_missing` (critical)
- `snapshot_stale` (warning)
- `quality_failures_high` (critical)

---

## 6. Модель данных (SQLite)

### 6.1 `trend_items`

Содержит элементы последнего/исторических snapshot’ов по региону/периоду:

- query/title/content_type/confidence
- scoring: interest/growth/final_score
- snapshot timestamp

### 6.2 `trend_points`

Timeseries точки по каждому query (timestamp + interest).

### 6.3 `sync_locks`

Lease/lock запись для защиты от параллельного sync.

### 6.4 `sync_runs`

История запусков sync:

- провайдер,
- total/relevant,
- quality_passed,
- reason,
- created_at.

---

## 7. Sync-стратегия

### 7.1 Внешний запуск (рекомендуется)

```bash
make sync
# или
python -m scripts.run_sync --region US --period 7d
```

Для production предпочтителен внешний scheduler (cron, CI, orchestrator),
а `YBT_ENABLE_INPROCESS_SCHEDULER=false`.

### 7.2 In-process scheduler

Можно включить для локальной разработки:

```bash
export YBT_ENABLE_INPROCESS_SCHEDULER=true
```

---

## 8. Наблюдаемость и эксплуатация

### 8.1 `/api/v1/admin/metrics`

Возвращает JSON с operational показателями:

- `latest_snapshot_age_seconds`
- `latest_sync_quality_passed`
- `sync_runs_last_24h`
- `quality_failures_last_24h`

### 8.2 `/api/v1/admin/alerts`

Возвращает список активных алертов по порогам из ENV.

### 8.3 `/metrics`

Prometheus-совместимые метрики:

- `yb_sync_runs_total`
- `yb_quality_failures_total`
- `yb_latest_snapshot_age_seconds`

---

## 9. Тестирование

```bash
make test
# или
pytest -q
```

Покрытие включает:

- API integration/contract tests,
- repository tests,
- quality gate tests,
- scoring tests,
- providers parsing tests,
- cache tests.

---

## 10. Docker и CI

### 10.1 Docker

- `Dockerfile` — контейнеризация сервиса.
- `docker-compose.yml` — локальный запуск через compose.

### 10.2 CI

- Workflow: `.github/workflows/ci.yml`
- Проверки в CI:
  - установка зависимостей,
  - `pytest -q`,
  - smoke sync: `python -m scripts.run_sync --region US --period 7d`.

---

## 11. Типовые проблемы и диагностика

1. **Пустой топ трендов**
   - Проверьте `admin/sync-runs` и причины quality gate rejection.
2. **Данные устарели**
   - Проверьте `admin/metrics.latest_snapshot_age_seconds` и `admin/alerts`.
3. **401/403 на API**
   - Проверьте заголовок `x-api-key` и `YBT_API_KEY`.
4. **Нет данных от provider**
   - Для локальной проверки переключитесь на `YBT_GOOGLE_PROVIDER=mock`.

---

## 12. Дополнительная документация

- Технический план и roadmap: [`docs/implementation-plan.ru.md`](docs/implementation-plan.ru.md)
