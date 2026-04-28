"""Optional smoke test against the real YouTube Data API v3.

Skipped by default. To run:

    YBT_YOUTUBE_API_KEY=... PYTEST_RUN_NETWORK=1 pytest -m network -v
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("httpx")

from app.config import settings
from app.services.enrichers.youtube import YouTubeDataApiEnricher


pytestmark = [
    pytest.mark.network,
    pytest.mark.skipif(
        os.environ.get("PYTEST_RUN_NETWORK") != "1",
        reason="set PYTEST_RUN_NETWORK=1 to run network-dependent tests",
    ),
    pytest.mark.skipif(
        not settings.youtube_api_key,
        reason="YBT_YOUTUBE_API_KEY not configured",
    ),
]


def test_real_youtube_returns_nonzero_stats_for_popular_query() -> None:
    enricher = YouTubeDataApiEnricher()
    try:
        stats = enricher.fetch_stats("minecraft movie", region="US", lookback_days=30)
    finally:
        enricher.close()

    assert stats.videos_published > 0, "expected at least one video for a popular query"
    assert stats.total_views > 0
    assert stats.channels_count > 0
