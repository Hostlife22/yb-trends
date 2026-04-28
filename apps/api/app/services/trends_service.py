from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.config import settings
from app.db import SnapshotMeta, SyncRun, TrendRepository
from app.schemas.trends import (
    AlertsResponse,
    ClassifiedTrendItem,
    MetricsResponse,
    SnapshotsResponse,
    SummaryResponse,
    SyncRunsResponse,
    TopTrendsResponse,
    TrendTimeseriesResponse,
)
from app.services.cache import TTLCache
from app.services.classifier import TrendClassifier
from app.services.enrichers import (
    MetadataEnricher,
    YouTubeStatsEnricher,
    build_metadata_enricher,
    build_youtube_stats_enricher,
)
from app.services.llm_classifier import GeminiClassifier
from app.services.providers.base import TrendsProvider
from app.services.scoring import (
    ScoreWeights,
    compute_search_demand,
    compute_search_momentum,
    compute_weighted_final_score,
    compute_youtube_demand,
    compute_youtube_freshness,
)

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
        metadata_enricher: MetadataEnricher | None = None,
        youtube_stats_enricher: YouTubeStatsEnricher | None = None,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.classifier = classifier or GeminiClassifier()
        self.cache = cache or TTLCache(ttl_seconds=600)
        self.metadata_enricher = metadata_enricher or build_metadata_enricher()
        self.youtube_stats_enricher = youtube_stats_enricher or build_youtube_stats_enricher()

    def _score_weights(self) -> ScoreWeights:
        return ScoreWeights(
            search_demand=settings.score_weight_search_demand,
            search_momentum=settings.score_weight_search_momentum,
            youtube_demand=settings.score_weight_youtube_demand,
            youtube_freshness=settings.score_weight_youtube_freshness,
        )

    def _enrich(self, item: ClassifiedTrendItem, *, region: str) -> ClassifiedTrendItem:
        """Run enrichers + recompute sub-scores and final_score.

        Returns a new ClassifiedTrendItem (pydantic ``model_copy``) — never
        mutates the input. Errors from any enricher must NOT abort the whole
        sync; we degrade gracefully to zeroed signals for that one item.
        """
        try:
            metadata = self.metadata_enricher.enrich(item.title_normalized, region=region)
        except Exception:  # noqa: BLE001 — defensive boundary against misbehaving enrichers
            logger.exception("metadata_enricher_failed", extra={"query": item.query})
            from app.services.enrichers import MovieMetadata

            metadata = MovieMetadata()

        try:
            yt_stats = self.youtube_stats_enricher.fetch_stats(item.query, region=region)
        except Exception:  # noqa: BLE001
            logger.exception("youtube_stats_enricher_failed", extra={"query": item.query})
            from app.services.scoring import YouTubeStats

            yt_stats = YouTubeStats()

        search_demand = compute_search_demand(item.interest_level)
        search_momentum = compute_search_momentum(item.growth_velocity)
        youtube_demand = compute_youtube_demand(yt_stats)
        youtube_freshness = compute_youtube_freshness(yt_stats)
        final_score = compute_weighted_final_score(
            search_demand=search_demand,
            search_momentum=search_momentum,
            youtube_demand=youtube_demand,
            youtube_freshness=youtube_freshness,
            weights=self._score_weights(),
        )

        return item.model_copy(
            update={
                "release_year": metadata.release_year,
                "original_language": metadata.original_language,
                "origin_country": metadata.origin_country,
                "genres": list(metadata.genres),
                "tmdb_id": metadata.tmdb_id,
                "tmdb_details": metadata.tmdb_details,
                "youtube_videos_published_14d": yt_stats.videos_published,
                "youtube_total_views_14d": yt_stats.total_views,
                "youtube_median_views_14d": yt_stats.median_views,
                "youtube_top_video_views_14d": yt_stats.top_video_views,
                "youtube_channels_count_14d": yt_stats.channels_count,
                "search_demand": round(search_demand, 4),
                "search_momentum": round(search_momentum, 4),
                "youtube_demand": round(youtube_demand, 4),
                "youtube_freshness": round(youtube_freshness, 4),
                "final_score": round(final_score, 4),
            }
        )

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

            relevant = [i for i in classified if i.is_movie_or_animation and i.confidence >= 0.7]
            enriched_all = [self._enrich(i, region=region) for i in relevant]

            # Phase 4 validation: only persist items the enrichers were able to
            # corroborate. An item with neither a TMDB match nor a non-zero
            # YouTube signal is almost certainly a classifier hallucination or
            # an off-topic query that slipped through.
            validated = [
                i for i in enriched_all
                if i.tmdb_id is not None or i.youtube_videos_published_14d > 0
            ]
            dropped_count = len(enriched_all) - len(validated)
            if dropped_count > 0:
                logger.info(
                    "validation_filter_dropped_items",
                    extra={
                        "region": region,
                        "period": period,
                        "dropped": dropped_count,
                        "kept": len(validated),
                    },
                )

            relevant_queries = {i.query for i in validated}
            relevant_series = {q: s for q, s in raw_series.items() if q in relevant_queries}

            saved = self.repository.save_snapshot(
                region=region,
                period=period,
                items=validated,
                raw_series_by_query=relevant_series,
            )
            if saved > 0:
                self.cache.clear()
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

    def get_sync_runs(self, region: str, period: str, limit: int) -> SyncRunsResponse:
        runs: list[SyncRun] = self.repository.fetch_sync_runs(region=region, period=period, limit=limit)
        return SyncRunsResponse(
            region=region,
            period=period,
            runs=[
                {
                    "id": run.id,
                    "created_at": run.created_at,
                    "provider": run.provider,
                    "total_items": run.total_items,
                    "relevant_items": run.relevant_items,
                    "quality_passed": run.quality_passed,
                    "reason": run.reason,
                }
                for run in runs
            ],
        )

    def get_metrics(self, region: str, period: str) -> MetricsResponse:
        latest_meta = self.repository.fetch_latest_snapshot_meta(region=region, period=period)
        runs = self.repository.fetch_sync_runs(region=region, period=period, limit=1)

        latest_age: int | None = None
        if latest_meta is not None:
            latest_age = int((datetime.now(timezone.utc) - datetime.fromisoformat(latest_meta.created_at)).total_seconds())

        latest_quality = runs[0].quality_passed if runs else None
        since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
        sync_runs_24h, failures_24h = self.repository.count_sync_runs_since(region=region, period=period, since_iso=since)

        return MetricsResponse(
            region=region,
            period=period,
            latest_snapshot_age_seconds=latest_age,
            latest_sync_quality_passed=latest_quality,
            sync_runs_last_24h=sync_runs_24h,
            quality_failures_last_24h=failures_24h,
        )

    def get_alerts(self, region: str, period: str) -> AlertsResponse:
        metrics = self.get_metrics(region=region, period=period)
        alerts: list[dict[str, str]] = []

        if metrics.latest_snapshot_age_seconds is None:
            alerts.append(
                {
                    "code": "snapshot_missing",
                    "severity": "critical",
                    "message": "No snapshots available for selected region/period.",
                }
            )
        elif metrics.latest_snapshot_age_seconds > settings.alert_snapshot_age_seconds:
            alerts.append(
                {
                    "code": "snapshot_stale",
                    "severity": "warning",
                    "message": f"Latest snapshot is stale: {metrics.latest_snapshot_age_seconds}s old.",
                }
            )

        if metrics.quality_failures_last_24h >= settings.alert_quality_failures_24h:
            alerts.append(
                {
                    "code": "quality_failures_high",
                    "severity": "critical",
                    "message": f"Quality failures in last 24h: {metrics.quality_failures_last_24h}.",
                }
            )

        return AlertsResponse(region=region, period=period, alerts=alerts)

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

    def get_top_trends(
        self,
        region: str,
        period: str,
        limit: int,
        *,
        language: str | None = None,
        country: str | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        sort_by: str = "final_score",
    ) -> TopTrendsResponse:
        cache_key = (
            f"top:{region}:{period}:{limit}:"
            f"{(language or '').lower()}:{(country or '').upper()}:"
            f"{min_year or ''}:{max_year or ''}:{sort_by}"
        )
        cached = self.cache.get(cache_key)
        if cached and self._is_snapshot_fresh(region=region, period=period):
            return cached

        self.ensure_fresh_snapshot(region=region, period=period)
        stored = self.repository.fetch_latest_top(
            region=region,
            period=period,
            limit=limit,
            language=language,
            country=country,
            min_year=min_year,
            max_year=max_year,
            sort_by=sort_by,
        )

        items = [
            ClassifiedTrendItem(
                query=row.query,
                title_normalized=row.title_normalized,
                content_type=row.content_type,
                is_movie_or_animation=True,
                confidence=row.confidence,
                studio=row.studio,
                reason="from snapshot",
                interest_level=row.interest_level,
                growth_velocity=row.growth_velocity,
                final_score=row.final_score,
                release_year=row.release_year,
                original_language=row.original_language,
                origin_country=row.origin_country,
                genres=row.genres or [],
                tmdb_id=row.tmdb_id,
                youtube_videos_published_14d=row.youtube_videos_published_14d,
                youtube_total_views_14d=row.youtube_total_views_14d,
                youtube_median_views_14d=row.youtube_median_views_14d,
                youtube_top_video_views_14d=row.youtube_top_video_views_14d,
                youtube_channels_count_14d=row.youtube_channels_count_14d,
                search_demand=row.search_demand,
                search_momentum=row.search_momentum,
                youtube_demand=row.youtube_demand,
                youtube_freshness=row.youtube_freshness,
                tmdb_details=row.tmdb_details,
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
        # Don't cache empty responses — otherwise a transient empty state
        # (e.g. fresh deploy before first sync, or sync that lost a race
        # with provider quota) sticks for the full TTL even after the DB
        # has been populated.
        if items:
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
