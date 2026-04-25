import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api.routes_trends import get_trends_service, router as trends_router
from app.config import settings
from app.db import TrendRepository
from app.services.sync_scheduler import SyncScheduler

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)

app = FastAPI(title=settings.app_name)
app.include_router(trends_router)

scheduler = SyncScheduler(service=get_trends_service())


@app.on_event("startup")
def on_startup() -> None:
    if settings.enable_inprocess_scheduler:
        scheduler.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    if settings.enable_inprocess_scheduler:
        scheduler.stop()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def readiness() -> dict[str, bool | str]:
    service = get_trends_service()
    fresh = service.ensure_fresh_snapshot(region=settings.default_region, period=settings.default_period)
    return {"status": "ready" if fresh else "degraded", "fresh": fresh}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    repo = TrendRepository()
    region = settings.default_region
    period = settings.default_period

    latest = repo.fetch_latest_snapshot_meta(region=region, period=period)
    total_runs, failures = repo.count_sync_runs_total(region=region, period=period)

    latest_age = -1
    if latest is not None:
        latest_age = int((datetime.now(timezone.utc) - datetime.fromisoformat(latest.created_at)).total_seconds())

    lines = [
        "# HELP yb_sync_runs_total Total number of sync runs",
        "# TYPE yb_sync_runs_total gauge",
        f'yb_sync_runs_total{{region="{region}",period="{period}"}} {total_runs}',
        "# HELP yb_quality_failures_total Total number of quality-gate failures",
        "# TYPE yb_quality_failures_total gauge",
        f'yb_quality_failures_total{{region="{region}",period="{period}"}} {failures}',
        "# HELP yb_latest_snapshot_age_seconds Age of latest snapshot in seconds (-1 if missing)",
        "# TYPE yb_latest_snapshot_age_seconds gauge",
        f'yb_latest_snapshot_age_seconds{{region="{region}",period="{period}"}} {latest_age}',
    ]
    return "\n".join(lines) + "\n"
