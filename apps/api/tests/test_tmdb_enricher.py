"""Unit tests for TmdbEnricher with a mocked HTTP transport.

We use ``httpx.MockTransport`` so the tests never touch the network. A real
network smoke test lives in ``test_tmdb_smoke.py`` and is gated by an env var.
"""
from __future__ import annotations

import pytest

pytest.importorskip("httpx")
import httpx

from app.services.cache import TTLCache
from app.services.enrichers.base import MovieMetadata
from app.services.enrichers.tmdb import TmdbEnricher, _normalize_query


_SEARCH_RESPONSE = {
    "results": [
        {
            "id": 12345,
            "media_type": "movie",
            "title": "A Minecraft Movie",
            "release_date": "2025-04-04",
            "original_language": "en",
            "origin_country": ["US"],
            "genre_ids": [16, 35],  # 16 = Animation
        }
    ]
}

_DETAILS_RESPONSE = {
    "id": 12345,
    "title": "A Minecraft Movie",
    "release_date": "2025-04-04",
    "original_language": "en",
    "origin_country": ["US"],
    "production_companies": [
        {"id": 1, "name": "Warner Bros. Pictures"},
        {"id": 2, "name": "Legendary Entertainment"},
    ],
    "genres": [
        {"id": 16, "name": "Animation"},
        {"id": 35, "name": "Comedy"},
    ],
}


def _make_client(handler) -> httpx.Client:
    transport = httpx.MockTransport(handler)
    return httpx.Client(
        base_url="https://api.themoviedb.org/3",
        transport=transport,
        headers={"accept": "application/json"},
    )


def test_normalize_query_strips_youtube_noise() -> None:
    assert _normalize_query("Minecraft Movie Trailer") == "Minecraft"
    assert _normalize_query("inside out 2 official trailer HD") == "inside out 2"
    assert _normalize_query("Marvel Film Release Date") == "Marvel"
    # Empty after stripping → fall back to original (avoids empty TMDB queries)
    assert _normalize_query("trailer movie") != ""


def test_tmdb_enricher_resolves_movie() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/search/multi"):
            return httpx.Response(200, json=_SEARCH_RESPONSE)
        if "/movie/" in request.url.path:
            return httpx.Response(200, json=_DETAILS_RESPONSE)
        return httpx.Response(404, json={})

    enricher = TmdbEnricher(
        read_access_token="test-token",
        api_key=None,
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    metadata = enricher.enrich("Minecraft Movie Trailer")

    assert metadata.tmdb_id == 12345
    assert metadata.release_year == 2025
    assert metadata.original_language == "en"
    assert metadata.origin_country == "US"
    assert "Warner Bros. Pictures" in metadata.studios
    assert "Animation" in metadata.genres
    assert metadata.is_animation is True
    # Both endpoints should have been hit exactly once (path includes /3 base prefix)
    assert len(calls) == 2
    assert calls[0].endswith("/search/multi")
    assert calls[1].endswith("/movie/12345")


def test_tmdb_enricher_caches_repeated_requests() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path.endswith("/search/multi"):
            return httpx.Response(200, json=_SEARCH_RESPONSE)
        return httpx.Response(200, json=_DETAILS_RESPONSE)

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    first = enricher.enrich("Minecraft Movie Trailer", region="US")
    second = enricher.enrich("Minecraft Movie Trailer", region="US")

    assert first.tmdb_id == second.tmdb_id == 12345
    # Cache key is deterministic per (region, title) → only one network round trip
    assert len(calls) == 2
    assert calls[0].endswith("/search/multi")
    assert calls[1].endswith("/movie/12345")


def test_tmdb_enricher_caches_empty_results_too() -> None:
    """A title that TMDB doesn't know shouldn't keep retrying every sync."""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return httpx.Response(200, json={"results": []})

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    a = enricher.enrich("Some Random Trend 12345")
    b = enricher.enrich("Some Random Trend 12345")

    assert a == MovieMetadata()
    assert b == MovieMetadata()
    assert len(calls) == 1  # cached on second call
    assert calls[0].endswith("/search/multi")


def test_tmdb_enricher_handles_5xx_gracefully() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "service unavailable"})

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    metadata = enricher.enrich("Inside Out 2")

    assert metadata == MovieMetadata()


def test_tmdb_enricher_handles_timeout_gracefully() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("simulated timeout")

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    metadata = enricher.enrich("Some Title")

    assert metadata == MovieMetadata()


def test_tmdb_enricher_skips_person_results() -> None:
    """If TMDB returns a person first, we should not pretend they're a film."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search/multi"):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {"id": 1, "media_type": "person", "name": "Jack Black"},
                        {
                            "id": 12345,
                            "media_type": "movie",
                            "title": "A Minecraft Movie",
                            "release_date": "2025-04-04",
                            "original_language": "en",
                            "origin_country": ["US"],
                            "genre_ids": [],
                        },
                    ]
                },
            )
        return httpx.Response(200, json=_DETAILS_RESPONSE)

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    metadata = enricher.enrich("Jack Black Minecraft")

    assert metadata.tmdb_id == 12345


def test_tmdb_enricher_uses_v3_api_key_when_no_token() -> None:
    """When only the v3 API key is configured, it must end up in the query string."""
    captured_params: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.append(dict(request.url.params))
        if request.url.path.endswith("/search/multi"):
            return httpx.Response(200, json={"results": []})
        return httpx.Response(404)

    enricher = TmdbEnricher(
        read_access_token="",  # explicitly disable Bearer (settings may carry one)
        api_key="v3-key-abc",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )

    enricher.enrich("Whatever")

    assert captured_params, "expected at least one HTTP call"
    assert captured_params[0].get("api_key") == "v3-key-abc"


def test_tmdb_enricher_returns_rich_details_for_ui() -> None:
    """Phase 5: enrich returns a tmdb_details payload with the fields the
    detail page renders (poster, overview, rating, runtime, ...)."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search/multi"):
            return httpx.Response(200, json=_SEARCH_RESPONSE)
        return httpx.Response(
            200,
            json={
                "id": 12345,
                "title": "A Minecraft Movie",
                "original_title": "A Minecraft Movie",
                "overview": "A young miner falls into a cubic world.",
                "tagline": "Block by block.",
                "homepage": "https://example.com/minecraft",
                "release_date": "2025-04-04",
                "runtime": 102,
                "status": "Released",
                "popularity": 1234.5,
                "vote_average": 7.4,
                "vote_count": 1500,
                "poster_path": "/poster.jpg",
                "backdrop_path": "/backdrop.jpg",
                "original_language": "en",
                "origin_country": ["US"],
                "production_companies": [{"id": 1, "name": "Warner Bros. Pictures"}],
                "genres": [{"id": 16, "name": "Animation"}],
                "spoken_languages": [{"iso_639_1": "en", "name": "English"}],
                "production_countries": [{"iso_3166_1": "US", "name": "United States"}],
            },
        )

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )
    metadata = enricher.enrich("Minecraft Movie Trailer")

    details = metadata.tmdb_details
    assert details is not None
    assert details["poster_path"] == "/poster.jpg"
    assert details["backdrop_path"] == "/backdrop.jpg"
    assert details["overview"].startswith("A young miner")
    assert details["tagline"] == "Block by block."
    assert details["homepage"] == "https://example.com/minecraft"
    assert details["runtime"] == 102
    assert details["vote_average"] == 7.4
    assert details["vote_count"] == 1500
    assert details["status"] == "Released"
    assert details["spoken_languages"] == ["en"]
    assert details["production_countries"] == ["US"]
    assert details["media_type"] == "movie"


def test_tmdb_enricher_resolves_tv_show_with_origin_country() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/search/multi"):
            return httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": 999,
                            "media_type": "tv",
                            "name": "Squid Game",
                            "first_air_date": "2021-09-17",
                            "original_language": "ko",
                            "origin_country": ["KR"],
                            "genre_ids": [18],
                        }
                    ]
                },
            )
        return httpx.Response(
            200,
            json={
                "id": 999,
                "first_air_date": "2021-09-17",
                "original_language": "ko",
                "origin_country": ["KR"],
                "production_companies": [{"id": 10, "name": "Netflix"}],
                "genres": [{"id": 18, "name": "Drama"}],
            },
        )

    enricher = TmdbEnricher(
        read_access_token="test-token",
        client=_make_client(handler),
        cache=TTLCache[MovieMetadata](ttl_seconds=60),
    )
    metadata = enricher.enrich("squid game season 2")

    assert metadata.tmdb_id == 999
    assert metadata.release_year == 2021
    assert metadata.original_language == "ko"
    assert metadata.origin_country == "KR"
    assert "Netflix" in metadata.studios
    assert metadata.is_animation is False
