# yb-trends: статус реализации и roadmap

Документ фиксирует текущее состояние backend-сервиса и дальнейшие шаги развития.

---

## 1) Цель проекта

Собирать и ранжировать поисковые тренды, связанные с фильмами и анимацией, в регионе **United States** за период **7 days**, чтобы отдавать:

- топ трендов;
- исторический ряд интереса по запросу;
- краткий summary;
- operational/админ-диагностику качества синхронизаций.

---

## 2) Текущее состояние (уже реализовано)

### 2.1 API и операционные endpoint’ы

Реализованы:

- `GET /health`
- `GET /ready`
- `GET /metrics` (Prometheus text)
- `GET /api/v1/trends/top`
- `GET /api/v1/summary`
- `GET /api/v1/trends/{query}/timeseries`
- `POST /api/v1/admin/sync`
- `GET /api/v1/admin/freshness`
- `GET /api/v1/admin/snapshots`
- `GET /api/v1/admin/sync-runs`
- `GET /api/v1/admin/metrics`
- `GET /api/v1/admin/alerts`

### 2.2 Data pipeline

- Провайдерный слой (`mock`, `pytrends`, `managed`) через factory.
- Классификация: Gemini classifier + эвристический fallback.
- Quality Gate перед записью snapshot:
  - `quality_min_items`,
  - `quality_min_relevant_ratio`.
- Расчет ranking (`interest_level`, `growth_velocity`, `final_score`).
- Запись snapshot + timeseries в SQLite.

### 2.3 Надежность и эксплуатация

- Lock/lease в SQLite против конкурентных sync.
- Запись истории sync запусков с quality-результатом.
- Freshness-проверка и auto-sync при чтении top.
- Operational alerts по порогам:
  - устаревший snapshot,
  - отсутствие snapshot,
  - частые quality failures за 24 часа.
- In-memory TTL cache для top endpoint.

### 2.4 Инфраструктура

- CLI sync runner (`python -m scripts.run_sync`).
- Docker + docker-compose.
- CI workflow (tests + smoke sync).
- Набор unit/integration тестов.

---

## 3) Архитектурные решения

### 3.1 Почему provider abstraction

Позволяет:

- использовать `mock` в тестах и CI;
- быстро переключиться между `pytrends` и managed API;
- минимизировать vendor lock-in.

### 3.2 Почему quality gate в sync

Идея: лучше не публиковать «плохой» snapshot, чем сохранять нерелевантный набор.

При провале gate:

- snapshot не записывается;
- в `sync_runs` сохраняется причина отказа;
- `admin/alerts` может сигнализировать о деградации качества.

### 3.3 Почему SQLite на текущем этапе

- минимальные операционные издержки;
- предсказуемость для MVP/раннего production;
- простые миграции и репозитории.

При росте нагрузки возможна миграция на Postgres без смены API-контрактов.

---

## 4) Нефункциональные требования (текущее покрытие)

- **Наблюдаемость:** базовые метрики + admin-диагностика.
- **Безопасность:** API key для `/api/v1/*` (опционально).
- **Тестируемость:** интеграционные и unit тесты ключевых слоев.
- **Операбельность:** ручной и плановый sync, lock, quality-audit trail.

---

## 5) Roadmap развития

### Этап A — стабилизация production-контура

1. Явные SLO/SLI для freshness и sync-success-rate.
2. Расширение alert-политик (например, провалы provider timeout/error-rate).
3. Structured logging с correlation id по sync-run.
4. Ротация/архивация старых snapshot/timeseries.

### Этап B — улучшение качества данных

1. Нормализация title (dedup, alias mapping).
2. Улучшение prompt/валидации LLM-классификации.
3. Post-classification rules для edge-cases (sports/person names).
4. A/B оценка relevance precision/recall на golden-наборе.

### Этап C — масштабирование

1. Переход на Postgres + индексы под чтение топов/таймсерий.
2. Вынос scheduler в отдельный worker/queue.
3. Внешний cache слой (Redis) при росте read-нагрузки.
4. Мультирегиональность и расширение period (1d/30d/90d).

### Этап D — продуктовые возможности

1. Более детальный summary (жанры, франшизы, drivers роста).
2. Экспорт отчетов (CSV/JSON snapshot bundles).
3. Webhook/notification при срабатывании алертов.
4. RBAC для admin endpoint’ов.

---

## 6) Критерии готовности следующего релиза

- Документация покрывает все env/API/операционные сценарии.
- Все текущие тесты проходят в CI и локально.
- Alert endpoint документирован и покрыт контрактным тестом.
- Smoke sync стабильно выполняется на `mock` provider.

---

## 7) Рекомендации по эксплуатации

1. В production использовать **внешний scheduler**, а не in-process.
2. Регулярно мониторить:
   - `yb_latest_snapshot_age_seconds`,
   - `quality_failures_last_24h`,
   - `admin/alerts`.
3. Для инцидентов сначала смотреть `admin/sync-runs` (reason) и provider-конфиг.
4. Для безопасного rollout изменений классификации фиксировать метрики качества до/после.
