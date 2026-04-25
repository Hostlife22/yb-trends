from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from app.config import settings
from app.services.trends_service import TrendsService

logger = logging.getLogger(__name__)


class SyncScheduler:
    def __init__(self, service: TrendsService) -> None:
        self.service = service
        self._timer: threading.Timer | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._schedule_next(delay=1)

    def stop(self) -> None:
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _schedule_next(self, delay: int | None = None) -> None:
        if not self._running:
            return
        interval = delay if delay is not None else settings.sync_interval_seconds
        self._timer = threading.Timer(interval, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        if not self._running:
            return
        try:
            saved = self.service.sync(region=settings.default_region, period=settings.default_period)
            logger.info(
                "background_sync_completed",
                extra={
                    "saved": saved,
                    "region": settings.default_region,
                    "period": settings.default_period,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:
            logger.exception("background_sync_failed")
        finally:
            self._schedule_next()
