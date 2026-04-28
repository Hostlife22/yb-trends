from __future__ import annotations

import logging

from app.config import settings
from app.services.enrichers.base import MetadataEnricher, YouTubeStatsEnricher
from app.services.enrichers.noop import NoopMetadataEnricher, NoopYouTubeStatsEnricher

logger = logging.getLogger(__name__)


def build_metadata_enricher() -> MetadataEnricher:
    """Pick a metadata enricher based on settings.

    ``tmdb`` is wired up but degrades to noop if no credentials are present —
    that way a misconfigured deployment still boots and just produces empty
    metadata instead of crashing on every sync.
    """
    provider = (settings.metadata_provider or "noop").lower()
    if provider == "tmdb":
        if not settings.tmdb_read_access_token and not settings.tmdb_api_key:
            logger.warning(
                "tmdb_credentials_missing_falling_back_to_noop",
                extra={"hint": "set YBT_TMDB_READ_ACCESS_TOKEN or YBT_TMDB_API_KEY"},
            )
            return NoopMetadataEnricher()
        from app.services.enrichers.tmdb import TmdbEnricher

        return TmdbEnricher()
    return NoopMetadataEnricher()


def build_youtube_stats_enricher() -> YouTubeStatsEnricher:
    """Pick a YouTube stats enricher based on settings.

    ``youtube_api`` is wired up but degrades to noop when the API key is
    missing — so a misconfigured deployment still boots and just produces
    zeroed YouTube signals (the search-side score still works).
    """
    provider = (settings.youtube_stats_provider or "noop").lower()
    if provider == "youtube_api":
        if not settings.youtube_api_key:
            logger.warning(
                "youtube_credentials_missing_falling_back_to_noop",
                extra={"hint": "set YBT_YOUTUBE_API_KEY"},
            )
            return NoopYouTubeStatsEnricher()
        from app.services.enrichers.youtube import YouTubeDataApiEnricher

        return YouTubeDataApiEnricher()
    return NoopYouTubeStatsEnricher()
