from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.db import SnapshotMeta, TrendRepository
from app.schemas.trends import (
    ClassifiedTrendItem,
    SnapshotsResponse,
    SummaryResponse,
    TopTrendsResponse,
    TrendTimeseriesResponse,
)
from app.services.cache import TTLCache
from app.services.classifier import TrendClassifier
from app.services.llm_classifier import GeminiClassifier
from app.services.providers.base import TrendsProvider

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    total_items: int
    relevant_items: int
    relevant_ratio: float
    passed: bool
    reason: str


class TrendsService:
    def __init__(
        self,
        provider: TrendsProvider,
        repository: TrendRepository,
        classifier: TrendClassifier | GeminiClassifier | None = None,
        cache: TTLCache[TopTrendsResponse] | None = None,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.classifier = classifier or GeminiClassifier()
        self.cache = cache or TTLCache(ttl_seconds=600)

    def _run_quality_check(self, classified: list[ClassifiedTrendItem]) -> QualityReport:
        total = len(classified)
        relevant = len([i for i in classified if i.is_movie_or_animation and i.confidence >= 0.7])
        ratio = (relevant / total) if total > 0 else 0.0

        if total < settings.quality_min_items:
            return QualityReport(total, relevant, ratio, False, "total_items_below_threshold")
        if ratio < settings.quality_min_relevant_ratio:
            return QualityReport(total, relevant, ratio, False, "relevant_ratio_below_threshold")

        return QualityReport(total, relevant, ratio, True, "ok")

    def sync(self, region: str, period: str) -> int:
        owner_id = str(uuid.uuid4())
        lock_key = f"sync:{region}:{period}"
        lock_acquired = self.repository.acquire_lock(lock_key=lock_key, owner_id=owner_id, ttl_seconds=settings.lock_ttl_seconds)

        if not lock_acquired:
            logger.warning("sync_skipped_lock_not_acquired", extra={"region": region, "period": period})
            return 0

        start = datetime.now(timezone.utc)
        try:
            raw_items = self.provider.fetch_weekly_trends(region)
            raw_series = {item.query: item.series for item in raw_items}
            classified = [self.classifier.classify(item) for item in raw_items]

            quality = self._run_quality_check(classified)
            self.repository.record_sync_run(
                region=region,
                period=period,
                provider=type(self.provider).__name__,
                total_items=quality.total_items,
                relevant_items=quality.relevant_items,
                quality_passed=quality.passed,
                reason=quality.reason,
            )

            if not quality.passed:
                logger.warning(
                    "sync_rejected_by_quality_gate",
                    extra={
                        "region": region,
                        "period": period,
                        "reason": quality.reason,
                        "total_items": quality.total_items,
                        "relevant_items": quality.relevant_items,
                        "relevant_ratio": quality.relevant_ratio,
                    },
                )
                return 0

            saved = self.repository.save_snapshot(
                region=region,
                period=period,
                items=classified,
                raw_series_by_query=raw_series,
            )
            duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            logger.info(
                "sync_completed",
                extra={
                    "region": region,
                    "period": period,
                    "saved": saved,
                    "duration_ms": duration_ms,
                    "provider": type(self.provider).__name__,
                    "quality_reason": quality.reason,
                    "relevant_ratio": quality.relevant_ratio,
                },
            )
            return saved
        finally:
            self.repository.release_lock(lock_key=lock_key, owner_id=owner_id)

    def _is_snapshot_fresh(self, region: str, period: str) -> bool:
        meta = self.repository.fetch_latest_snapshot_meta(region=region, period=period)
        if meta is None:
            return False
        created_at = datetime.fromisoformat(meta.created_at)
        return created_at >= datetime.now(timezone.utc) - timedelta(seconds=settings.max_snapshot_age_seconds)

    def ensure_fresh_snapshot(self, region: str, period: str) -> bool:
        if self._is_snapshot_fresh(region=region, period=period):
            return True
        self.sync(region=region, period=period)
        return self._is_snapshot_fresh(region=region, period=period)

    def get_snapshots(self, region: str, period: str, limit: int) -> SnapshotsResponse:
        snapshots: list[SnapshotMeta] = self.repository.fetch_snapshots(region=region, period=period, limit=limit)
        return SnapshotsResponse(
            region=region,
            period=period,
            snapshots=[{"created_at": s.created_at, "item_count": s.item_count} for s in snapshots],
        )

    def get_timeseries(self, region: str, period: str, query: str, limit: int) -> TrendTimeseriesResponse:
        points = self.repository.fetch_timeseries(region=region, period=period, query=query, limit=limit)
        return TrendTimeseriesResponse(region=region, period=period, query=query, points=points)

    def get_top_trends(self, region: str, period: str, limit: int) -> TopTrendsResponse:
        cache_key = f"top:{region}:{period}:{limit}"
        cached = self.cache.get(cache_key)
        if cached and self._is_snapshot_fresh(region=region, period=period):
            return cached

        self.ensure_fresh_snapshot(region=region, period=period)
        stored = self.repository.fetch_latest_top(region=region, period=period, limit=limit)

        items = [
            ClassifiedTrendItem(
                query=row.query,
                title_normalized=row.title_normalized,
                content_type=row.content_type,
                is_movie_or_animation=True,
                confidence=row.confidence,
                reason="from snapshot",
                interest_level=row.interest_level,
                growth_velocity=row.growth_velocity,
                final_score=row.final_score,
            )
            for row in stored
            if row.confidence >= 0.7
        ]

        response = TopTrendsResponse(
            region=region,
            period=period,
            generated_at=datetime.now(timezone.utc),
            items=items,
        )
        self.cache.set(cache_key, response)
        return response

    def get_summary(self, region: str, period: str, limit: int) -> SummaryResponse:
        top = self.get_top_trends(region=region, period=period, limit=limit)
        if not top.items:
            text = "No movie or animation trends were detected for the selected period."
            titles: list[str] = []
        else:
            titles = [item.title_normalized for item in top.items[:5]]
            text = (
                f"Top US movie/animation trend is '{top.items[0].title_normalized}'. "
                f"Detected {len(top.items)} relevant queries in the last {period}."
            )

        return SummaryResponse(
            region=region,
            period=period,
            generated_at=datetime.now(timezone.utc),
            summary=text,
            top_titles=titles,
        )
