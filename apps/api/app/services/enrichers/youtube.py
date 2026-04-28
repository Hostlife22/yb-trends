"""YouTube Data API v3-backed stats enricher.

For each query we run two endpoints:

1. ``search.list`` — find videos matching the query, filtered by recency
   (``publishedAfter``) and ``regionCode``. This is the expensive call
   (100 quota units).
2. ``videos.list`` — fetch ``snippet`` + ``statistics`` for the IDs returned
   above (1 quota unit, batched up to 50 IDs).

We then aggregate into a ``YouTubeStats`` instance: total/median/top views,
videos_published count, and distinct channels count. The aggregate is what
scoring consumes; we never store individual video stats.

Cost per query: ~101 quota units. Default daily quota is 10,000, so this
caps us around ~99 queries/day before throttling. Caching for 6h means we
typically call once per query per cycle.

Errors degrade to empty stats — the pipeline already protects against
exceptions but a quiet warning helps debugging.
"""

from __future__ import annotations

import logging
import statistics as stdstat
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from app.config import settings
from app.services.cache import TTLCache
from app.services.enrichers.base import YouTubeStatsEnricher
from app.services.scoring import YouTubeStats

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeDataApiEnricher(YouTubeStatsEnricher):
    """Enriches a query with aggregate YouTube statistics over a recent window."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        cache: TTLCache[YouTubeStats] | None = None,
        max_results: int | None = None,
    ) -> None:
        api = api_key if api_key is not None else settings.youtube_api_key
        self._api_key = api or None
        self._cache = cache or TTLCache[YouTubeStats](ttl_seconds=settings.youtube_cache_ttl_seconds)
        self._max_results = max_results or settings.youtube_search_max_results
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=_BASE_URL,
            timeout=settings.youtube_request_timeout_seconds,
            headers={"accept": "application/json"},
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def fetch_stats(self, query: str, *, region: str, lookback_days: int = 14) -> YouTubeStats:
        if not query or not self._api_key:
            return YouTubeStats()

        cache_key = f"{region.upper()}::{lookback_days}::{query.strip().lower()}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        published_after = (
            datetime.now(timezone.utc) - timedelta(days=max(lookback_days, 1))
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        try:
            ids = self._search_video_ids(query=query, region=region, published_after=published_after)
        except Exception:  # noqa: BLE001 — boundary
            logger.warning("youtube_search_failed", extra={"query": query, "region": region}, exc_info=True)
            return YouTubeStats()

        if not ids:
            empty = YouTubeStats()
            self._cache.set(cache_key, empty)
            return empty

        try:
            videos = self._fetch_videos(ids)
        except Exception:  # noqa: BLE001 — boundary
            logger.warning("youtube_videos_failed", extra={"query": query, "count": len(ids)}, exc_info=True)
            return YouTubeStats()

        stats = _aggregate(videos)
        self._cache.set(cache_key, stats)
        return stats

    def _search_video_ids(self, *, query: str, region: str, published_after: str) -> list[str]:
        params: dict[str, Any] = {
            "key": self._api_key,
            "part": "id",
            "q": query,
            "type": "video",
            "regionCode": region,
            "maxResults": self._max_results,
            "publishedAfter": published_after,
            "order": "relevance",
        }
        response = self._client.get("/search", params=params)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items") or []
        ids: list[str] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            video_id = (item.get("id") or {}).get("videoId") if isinstance(item.get("id"), dict) else None
            if isinstance(video_id, str) and video_id:
                ids.append(video_id)
        return ids

    def _fetch_videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        if not video_ids:
            return []
        params = {
            "key": self._api_key,
            "part": "snippet,statistics",
            "id": ",".join(video_ids),
            "maxResults": min(50, len(video_ids)),
        }
        response = self._client.get("/videos", params=params)
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items") or []
        return [v for v in items if isinstance(v, dict)]


def _aggregate(videos: list[dict[str, Any]]) -> YouTubeStats:
    if not videos:
        return YouTubeStats()

    views: list[int] = []
    channels: set[str] = set()

    for video in videos:
        stats = video.get("statistics") or {}
        view_count_raw = stats.get("viewCount")
        try:
            view_count = int(view_count_raw) if view_count_raw is not None else 0
        except (TypeError, ValueError):
            view_count = 0
        views.append(view_count)

        snippet = video.get("snippet") or {}
        channel_id = snippet.get("channelId")
        if isinstance(channel_id, str) and channel_id:
            channels.add(channel_id)

    total = sum(views)
    top = max(views) if views else 0
    median = int(stdstat.median(views)) if views else 0

    return YouTubeStats(
        videos_published=len(videos),
        total_views=total,
        median_views=median,
        top_video_views=top,
        channels_count=len(channels),
    )
