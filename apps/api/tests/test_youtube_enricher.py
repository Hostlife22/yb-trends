"""Unit tests for YouTubeDataApiEnricher with a mocked httpx transport.

A real network smoke test lives in ``test_youtube_smoke.py`` and is gated by
``PYTEST_RUN_NETWORK=1``.
"""
from __future__ import annotations

import pytest

pytest.importorskip("httpx")
import httpx

from app.services.cache import TTLCache
from app.services.enrichers.youtube import YouTubeDataApiEnricher
from app.services.scoring import YouTubeStats


_SEARCH_RESPONSE = {
    "items": [
        {"id": {"kind": "youtube#video", "videoId": "vid1"}},
        {"id": {"kind": "youtube#video", "videoId": "vid2"}},
        {"id": {"kind": "youtube#video", "videoId": "vid3"}},
        {"id": {"kind": "youtube#channel", "channelId": "ch1"}},  # must be skipped
    ]
}

_VIDEOS_RESPONSE = {
    "items": [
        {
            "id": "vid1",
            "snippet": {"channelId": "ch_a", "title": "video 1"},
            "statistics": {"viewCount": "100000"},
        },
        {
            "id": "vid2",
            "snippet": {"channelId": "ch_b", "title": "video 2"},
            "statistics": {"viewCount": "500000"},
        },
        {
            "id": "vid3",
            "snippet": {"channelId": "ch_a", "title": "video 3"},
            "statistics": {"viewCount": "20000"},
        },
    ]
}


def _make_client(handler) -> httpx.Client:
    transport = httpx.MockTransport(handler)
    return httpx.Client(
        base_url="https://www.googleapis.com/youtube/v3",
        transport=transport,
        headers={"accept": "application/json"},
    )


def test_youtube_enricher_aggregates_basic_stats() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json=_SEARCH_RESPONSE)
        if request.url.path.endswith("/videos"):
            return httpx.Response(200, json=_VIDEOS_RESPONSE)
        return httpx.Response(404)

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    stats = enricher.fetch_stats("minecraft movie", region="US")

    assert stats.videos_published == 3
    assert stats.total_views == 620_000
    assert stats.median_views == 100_000  # median of [100k, 500k, 20k] = 100k
    assert stats.top_video_views == 500_000
    assert stats.channels_count == 2  # ch_a appears twice → 1 distinct
    assert len(calls) == 2
    assert calls[0].endswith("/search")
    assert calls[1].endswith("/videos")


def test_youtube_enricher_caches_repeated_requests() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json=_SEARCH_RESPONSE)
        return httpx.Response(200, json=_VIDEOS_RESPONSE)

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    a = enricher.fetch_stats("minecraft movie", region="US")
    b = enricher.fetch_stats("minecraft movie", region="US")

    assert a == b
    assert len(calls) == 2  # only the first call hit the network


def test_youtube_enricher_caches_empty_results() -> None:
    """Empty search must be cached too — otherwise we burn quota retrying nothing."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"items": []})

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    a = enricher.fetch_stats("nonsense xyzqq", region="US")
    b = enricher.fetch_stats("nonsense xyzqq", region="US")

    assert a == YouTubeStats()
    assert b == YouTubeStats()
    assert len(calls) == 1


def test_youtube_enricher_handles_quota_exceeded() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "quotaExceeded"}})

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    stats = enricher.fetch_stats("anything", region="US")
    assert stats == YouTubeStats()


def test_youtube_enricher_handles_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("simulated timeout")

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    stats = enricher.fetch_stats("anything", region="US")
    assert stats == YouTubeStats()


def test_youtube_enricher_returns_empty_without_api_key() -> None:
    """No API key → don't even hit the network."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"items": []})

    enricher = YouTubeDataApiEnricher(
        api_key="",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    stats = enricher.fetch_stats("anything", region="US")
    assert stats == YouTubeStats()
    assert calls == []


def test_youtube_enricher_skips_videos_call_when_search_empty() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": []})
        return httpx.Response(500)

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    stats = enricher.fetch_stats("anything", region="US")

    assert stats == YouTubeStats()
    assert len(calls) == 1
    assert calls[0].endswith("/search")


def test_youtube_enricher_handles_missing_view_count() -> None:
    """Some videos hide their view counts — those should be treated as 0, not crash."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search"):
            return httpx.Response(
                200,
                json={"items": [{"id": {"videoId": "v1"}}, {"id": {"videoId": "v2"}}]},
            )
        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "v1",
                        "snippet": {"channelId": "ch_a"},
                        "statistics": {"viewCount": "1000"},
                    },
                    {
                        "id": "v2",
                        "snippet": {"channelId": "ch_b"},
                        "statistics": {},  # no viewCount
                    },
                ]
            },
        )

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    stats = enricher.fetch_stats("something", region="US")

    assert stats.videos_published == 2
    assert stats.total_views == 1000
    assert stats.top_video_views == 1000
    assert stats.channels_count == 2


def test_youtube_enricher_passes_region_and_lookback_window() -> None:
    """search.list must be called with regionCode and a non-empty publishedAfter."""
    captured_params: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.append(dict(request.url.params))
        if request.url.path.endswith("/search"):
            return httpx.Response(200, json={"items": []})
        return httpx.Response(200, json={"items": []})

    enricher = YouTubeDataApiEnricher(
        api_key="test-key",
        client=_make_client(handler),
        cache=TTLCache[YouTubeStats](ttl_seconds=60),
    )
    enricher.fetch_stats("a query", region="GB", lookback_days=7)

    assert captured_params, "expected at least one HTTP call"
    params = captured_params[0]
    assert params.get("regionCode") == "GB"
    assert params.get("type") == "video"
    assert params.get("q") == "a query"
    assert "publishedAfter" in params
    # ISO-ish timestamp ending in Z
    assert params["publishedAfter"].endswith("Z")
