"""Phase 4: filtering and sorting in fetch_latest_top + /api/v1/trends/top."""
from __future__ import annotations

import pytest

pytest.importorskip("pydantic")

from app.db import TrendRepository
from app.schemas.trends import ClassifiedTrendItem


def _item(
    *,
    query: str,
    title: str,
    final_score: float,
    search_demand: float = 0.0,
    youtube_demand: float = 0.0,
    youtube_median_views_14d: int = 0,
    release_year: int | None = None,
    original_language: str | None = None,
    origin_country: str | None = None,
    tmdb_id: int | None = None,
    youtube_videos_published_14d: int = 0,
) -> ClassifiedTrendItem:
    return ClassifiedTrendItem(
        query=query,
        title_normalized=title,
        content_type="movie",
        is_movie_or_animation=True,
        confidence=0.9,
        reason="test",
        interest_level=10.0,
        growth_velocity=20.0,
        final_score=final_score,
        release_year=release_year,
        original_language=original_language,
        origin_country=origin_country,
        tmdb_id=tmdb_id,
        youtube_videos_published_14d=youtube_videos_published_14d,
        youtube_median_views_14d=youtube_median_views_14d,
        search_demand=search_demand,
        youtube_demand=youtube_demand,
    )


@pytest.fixture
def repo_with_mixed_items(tmp_path):
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    items = [
        _item(query="en2025", title="EN 2025 Film", final_score=0.9,
              search_demand=0.5, youtube_demand=0.9, youtube_median_views_14d=1_000_000,
              release_year=2025, original_language="en", origin_country="US",
              tmdb_id=1, youtube_videos_published_14d=20),
        _item(query="es2010", title="ES 2010 Film", final_score=0.7,
              search_demand=0.9, youtube_demand=0.3, youtube_median_views_14d=50_000,
              release_year=2010, original_language="es", origin_country="ES",
              tmdb_id=2, youtube_videos_published_14d=10),
        _item(query="ja2024", title="JA 2024 Anime", final_score=0.85,
              search_demand=0.7, youtube_demand=0.85, youtube_median_views_14d=500_000,
              release_year=2024, original_language="ja", origin_country="JP",
              tmdb_id=3, youtube_videos_published_14d=18),
        _item(query="en1990", title="EN 1990 Classic", final_score=0.5,
              search_demand=0.4, youtube_demand=0.5, youtube_median_views_14d=80_000,
              release_year=1990, original_language="en", origin_country="US",
              tmdb_id=4, youtube_videos_published_14d=8),
    ]
    repo.save_snapshot(region="US", period="7d", items=items)
    return repo


def test_filter_by_language(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(region="US", period="7d", limit=10, language="en")
    assert {r.query for r in rows} == {"en2025", "en1990"}


def test_filter_by_country(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(region="US", period="7d", limit=10, country="JP")
    assert [r.query for r in rows] == ["ja2024"]


def test_filter_by_year_range(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, min_year=2020
    )
    assert {r.query for r in rows} == {"en2025", "ja2024"}


def test_filter_combined(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, language="en", min_year=2000, max_year=2024
    )
    assert {r.query for r in rows} == set()
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, language="en", min_year=2025
    )
    assert {r.query for r in rows} == {"en2025"}


def test_sort_by_search_demand(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, sort_by="search_demand"
    )
    # ES has highest search_demand=0.9
    assert rows[0].query == "es2010"


def test_sort_by_youtube_demand(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, sort_by="youtube_demand"
    )
    # EN 2025 has highest youtube_demand=0.9
    assert rows[0].query == "en2025"


def test_sort_by_youtube_median_views(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, sort_by="youtube_median_views_14d"
    )
    assert [r.query for r in rows[:2]] == ["en2025", "ja2024"]


def test_sort_by_unknown_falls_back_to_final_score(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(
        region="US", period="7d", limit=10, sort_by="DROP TABLE; --"
    )
    # Falls back to final_score → EN 2025 (0.9) wins
    assert rows[0].query == "en2025"


def test_default_sort_is_final_score(repo_with_mixed_items) -> None:
    rows = repo_with_mixed_items.fetch_latest_top(region="US", period="7d", limit=10)
    scores = [r.final_score for r in rows]
    assert scores == sorted(scores, reverse=True)
