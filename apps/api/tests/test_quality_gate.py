import pytest

pytest.importorskip("pydantic")

from app.config import settings
from app.db import TrendRepository
from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.classifier import TrendClassifier
from app.services.enrichers.base import YouTubeStatsEnricher
from app.services.enrichers.noop import NoopMetadataEnricher
from app.services.providers.base import TrendsProvider
from app.services.scoring import YouTubeStats
from app.services.trends_service import TrendsService


class _StubYouTube(YouTubeStatsEnricher):
    """Constant non-zero YouTube signal so Phase 4 validation lets items through."""

    def fetch_stats(self, query, *, region, lookback_days=14):  # type: ignore[override]
        return YouTubeStats(videos_published=3, total_views=900, median_views=300, channels_count=2)


def _make_service(provider, repo) -> TrendsService:
    return TrendsService(
        provider=provider,
        repository=repo,
        classifier=TrendClassifier(),
        metadata_enricher=NoopMetadataEnricher(),
        youtube_stats_enricher=_StubYouTube(),
    )


class PoorProvider(TrendsProvider):
    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        return [
            RawTrendItem(
                query="some random politics query",
                series=[TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=10)],
            )
        ]


class GoodProvider(TrendsProvider):
    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        return [
            RawTrendItem(
                query="minecraft movie trailer",
                series=[TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=10)],
            ),
            RawTrendItem(
                query="anime movie 2026",
                series=[TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=12)],
            ),
            RawTrendItem(
                query="marvel film release date",
                series=[TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=9)],
            ),
            RawTrendItem(
                query="new disney animation",
                series=[TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=8)],
            ),
            RawTrendItem(
                query="pixar movie trailer",
                series=[TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=11)],
            ),
        ]


def test_quality_gate_rejects_bad_sync(tmp_path) -> None:
    settings.quality_min_items = 2
    settings.quality_min_relevant_ratio = 0.5

    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    service = _make_service(PoorProvider(), repo)

    saved = service.sync(region="US", period="7d")
    assert saved == 0


def test_quality_gate_accepts_good_sync(tmp_path) -> None:
    settings.quality_min_items = 2
    settings.quality_min_relevant_ratio = 0.5

    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    service = _make_service(GoodProvider(), repo)

    saved = service.sync(region="US", period="7d")
    assert saved > 0
