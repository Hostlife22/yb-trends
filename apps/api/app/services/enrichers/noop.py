from __future__ import annotations

from app.services.enrichers.base import MetadataEnricher, MovieMetadata, YouTubeStatsEnricher
from app.services.scoring import YouTubeStats


class NoopMetadataEnricher(MetadataEnricher):
    """Returns empty metadata. Used in tests and when no API key is configured."""

    def enrich(self, title: str, *, region: str | None = None) -> MovieMetadata:
        return MovieMetadata()


class NoopYouTubeStatsEnricher(YouTubeStatsEnricher):
    """Returns zeroed stats. Used in tests and when no API key is configured."""

    def fetch_stats(self, query: str, *, region: str, lookback_days: int = 14) -> YouTubeStats:
        return YouTubeStats()
