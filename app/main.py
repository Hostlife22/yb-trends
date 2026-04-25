import logging

from fastapi import FastAPI

from app.api.routes_trends import get_trends_service, router as trends_router
from app.config import settings
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
