"""Phase 1 wiring: enrichers integrate cleanly with the sync pipeline.

These tests verify that the noop enrichers (default for Phase 1) produce a
working pipeline end-to-end and that the new fields land in the snapshot.
Real TMDB/YouTube enrichers ship in Phase 2/3.
"""
from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from app.config import settings
from app.db import TrendRepository
from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.classifier import TrendClassifier
from app.services.enrichers import (
    NoopMetadataEnricher,
    NoopYouTubeStatsEnricher,
)
from app.services.providers.base import TrendsProvider
from app.services.trends_service import TrendsService


class GoodProvider(TrendsProvider):
    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        return [
            RawTrendItem(
                query="minecraft movie trailer",
                series=[
                    TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=10),
                    TrendPoint(timestamp="2026-01-02T00:00:00Z", interest=12),
                    TrendPoint(timestamp="2026-01-03T00:00:00Z", interest=15),
                    TrendPoint(timestamp="2026-01-04T00:00:00Z", interest=20),
                ],
            ),
            RawTrendItem(
                query="anime movie 2026",
                series=[
                    TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=8),
                    TrendPoint(timestamp="2026-01-02T00:00:00Z", interest=9),
                    TrendPoint(timestamp="2026-01-03T00:00:00Z", interest=11),
                    TrendPoint(timestamp="2026-01-04T00:00:00Z", interest=14),
                ],
            ),
            RawTrendItem(
                query="marvel film release date",
                series=[
                    TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=5),
                    TrendPoint(timestamp="2026-01-02T00:00:00Z", interest=6),
                    TrendPoint(timestamp="2026-01-03T00:00:00Z", interest=7),
                    TrendPoint(timestamp="2026-01-04T00:00:00Z", interest=9),
                ],
            ),
            RawTrendItem(
                query="new disney animation",
                series=[
                    TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=4),
                    TrendPoint(timestamp="2026-01-02T00:00:00Z", interest=5),
                    TrendPoint(timestamp="2026-01-03T00:00:00Z", interest=6),
                    TrendPoint(timestamp="2026-01-04T00:00:00Z", interest=7),
                ],
            ),
            RawTrendItem(
                query="pixar movie trailer",
                series=[
                    TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=11),
                    TrendPoint(timestamp="2026-01-02T00:00:00Z", interest=12),
                    TrendPoint(timestamp="2026-01-03T00:00:00Z", interest=13),
                    TrendPoint(timestamp="2026-01-04T00:00:00Z", interest=14),
                ],
            ),
        ]


def _service(tmp_path, *, youtube_enricher=None) -> TrendsService:
    """Factory for a TrendsService with the GoodProvider.

    Phase 4 validation requires either a TMDB id or a non-zero YouTube
    signal, so tests that want items to *land* must inject an enricher that
    provides one. By default we provide a constant low YouTube signal so the
    pipeline produces output in the test cases that need it.
    """
    settings.quality_min_items = 2
    settings.quality_min_relevant_ratio = 0.5
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))

    from app.services.enrichers.base import YouTubeStatsEnricher
    from app.services.scoring import YouTubeStats

    class _ConstantYouTube(YouTubeStatsEnricher):
        def fetch_stats(self, query, *, region, lookback_days=14):  # type: ignore[override]
            return YouTubeStats(videos_published=3, total_views=900, median_views=300, channels_count=2)

    return TrendsService(
        provider=GoodProvider(),
        repository=repo,
        classifier=TrendClassifier(),
        metadata_enricher=NoopMetadataEnricher(),
        youtube_stats_enricher=youtube_enricher or _ConstantYouTube(),
    )


def test_pipeline_writes_new_fields_with_enrichers(tmp_path) -> None:
    service = _service(tmp_path)

    saved = service.sync(region="US", period="7d")
    assert saved > 0

    top = service.repository.fetch_latest_top(region="US", period="7d", limit=10)
    assert len(top) > 0

    row = top[0]
    # Metadata is None under noop metadata enricher
    assert row.release_year is None
    assert row.tmdb_id is None
    assert row.original_language is None
    # YouTube stats come from the constant stub
    assert row.youtube_videos_published_14d == 3
    assert row.youtube_total_views_14d == 900
    assert row.youtube_median_views_14d == 300
    # All sub-scores in [0, 1]
    assert 0.0 <= row.search_demand <= 1.0
    assert 0.0 <= row.search_momentum <= 1.0
    assert 0.0 <= row.youtube_demand <= 1.0
    assert 0.0 <= row.youtube_freshness <= 1.0
    assert 0.0 <= row.final_score <= 1.0


def test_pipeline_orders_by_score_descending(tmp_path) -> None:
    service = _service(tmp_path)
    service.sync(region="US", period="7d")

    top = service.repository.fetch_latest_top(region="US", period="7d", limit=10)
    scores = [r.final_score for r in top]
    assert scores == sorted(scores, reverse=True)


def test_validation_filter_drops_unverifiable_items(tmp_path) -> None:
    """Phase 4: items with no TMDB id and no YouTube signal must be dropped."""
    settings.quality_min_items = 2
    settings.quality_min_relevant_ratio = 0.5
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))

    service = TrendsService(
        provider=GoodProvider(),
        repository=repo,
        classifier=TrendClassifier(),
        # Both noop → every enriched item has tmdb_id=None and yt_videos=0
        metadata_enricher=NoopMetadataEnricher(),
        youtube_stats_enricher=NoopYouTubeStatsEnricher(),
    )
    saved = service.sync(region="US", period="7d")
    # All items got dropped by the validation filter
    assert saved == 0
    top = repo.fetch_latest_top(region="US", period="7d", limit=10)
    assert top == []


def test_validation_filter_keeps_items_with_youtube_signal(tmp_path) -> None:
    """Items with no TMDB id but with YouTube videos should still be kept."""
    settings.quality_min_items = 2
    settings.quality_min_relevant_ratio = 0.5
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))

    from app.services.enrichers.base import YouTubeStatsEnricher
    from app.services.scoring import YouTubeStats

    class FakeYouTube(YouTubeStatsEnricher):
        def fetch_stats(self, query, *, region, lookback_days=14):  # type: ignore[override]
            return YouTubeStats(videos_published=5, total_views=10_000, median_views=2000, channels_count=3)

    service = TrendsService(
        provider=GoodProvider(),
        repository=repo,
        classifier=TrendClassifier(),
        metadata_enricher=NoopMetadataEnricher(),
        youtube_stats_enricher=FakeYouTube(),
    )
    saved = service.sync(region="US", period="7d")
    assert saved > 0


def test_enricher_failure_does_not_break_sync(tmp_path) -> None:
    """A misbehaving enricher must not abort the whole sync — degrade gracefully."""
    settings.quality_min_items = 2
    settings.quality_min_relevant_ratio = 0.5
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))

    from app.services.enrichers.base import YouTubeStatsEnricher
    from app.services.scoring import YouTubeStats

    class BoomMetadata(NoopMetadataEnricher):
        def enrich(self, title, *, region=None):  # type: ignore[override]
            raise RuntimeError("simulated TMDB failure")

    class StubYouTube(YouTubeStatsEnricher):
        def fetch_stats(self, query, *, region, lookback_days=14):  # type: ignore[override]
            # Provides a YouTube signal so items pass the Phase 4 validation
            # filter even though the metadata enricher blew up.
            return YouTubeStats(videos_published=3, total_views=1000, median_views=300, channels_count=2)

    service = TrendsService(
        provider=GoodProvider(),
        repository=repo,
        classifier=TrendClassifier(),
        metadata_enricher=BoomMetadata(),
        youtube_stats_enricher=StubYouTube(),
    )
    saved = service.sync(region="US", period="7d")
    assert saved > 0
