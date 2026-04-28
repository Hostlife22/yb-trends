import pytest

pytest.importorskip("pydantic")

from app.db import TrendRepository
from app.schemas.trends import ClassifiedTrendItem, TrendPoint


def test_repository_save_and_fetch(tmp_path) -> None:
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    item = ClassifiedTrendItem(
        query="minecraft movie trailer",
        title_normalized="Minecraft Movie Trailer",
        content_type="movie",
        is_movie_or_animation=True,
        confidence=0.91,
        reason="test",
        interest_level=50,
        growth_velocity=40,
        final_score=46,
    )

    saved = repo.save_snapshot(
        region="US",
        period="7d",
        items=[item],
        raw_series_by_query={
            "minecraft movie trailer": [TrendPoint(timestamp="2026-01-01T00:00:00Z", interest=10)]
        },
    )
    assert saved == 1

    out = repo.fetch_latest_top(region="US", period="7d", limit=10)
    assert len(out) == 1
    assert out[0].query == "minecraft movie trailer"

    points = repo.fetch_timeseries(region="US", period="7d", query="minecraft movie trailer")
    assert len(points) == 1
    assert points[0].interest == 10


def test_repository_snapshot_meta(tmp_path) -> None:
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    meta = repo.fetch_latest_snapshot_meta(region="US", period="7d")
    assert meta is None


def test_repository_persists_tmdb_details(tmp_path) -> None:
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    item = ClassifiedTrendItem(
        query="kpop demon hunters",
        title_normalized="KPop Demon Hunters",
        content_type="animation",
        is_movie_or_animation=True,
        confidence=0.95,
        reason="test",
        interest_level=185.71,
        growth_velocity=26.1,
        final_score=0.9,
        tmdb_id=803796,
        release_year=2025,
        original_language="en",
        tmdb_details={
            "media_type": "movie",
            "poster_path": "/poster.jpg",
            "overview": "Demon-hunting K-pop idols.",
            "vote_average": 8.1,
            "vote_count": 2300,
            "runtime": 99,
            "release_date": "2025-06-20",
            "tagline": "Save the world.",
            "spoken_languages": ["ko", "en"],
            "production_countries": ["US", "KR"],
        },
        # Must satisfy Phase 4 validation
        youtube_videos_published_14d=10,
    )
    repo.save_snapshot(region="US", period="7d", items=[item])

    out = repo.fetch_latest_top(region="US", period="7d", limit=10)
    assert len(out) == 1
    assert out[0].tmdb_details is not None
    assert out[0].tmdb_details["poster_path"] == "/poster.jpg"
    assert out[0].tmdb_details["overview"].startswith("Demon-hunting")
    assert out[0].tmdb_details["runtime"] == 99
    assert out[0].tmdb_details["spoken_languages"] == ["ko", "en"]


def test_lock_acquire_release(tmp_path) -> None:
    repo = TrendRepository(db_path=str(tmp_path / "trends.db"))
    assert repo.acquire_lock("sync:US:7d", "owner-a", ttl_seconds=60)
    assert not repo.acquire_lock("sync:US:7d", "owner-b", ttl_seconds=60)
    repo.release_lock("sync:US:7d", "owner-a")
    assert repo.acquire_lock("sync:US:7d", "owner-b", ttl_seconds=60)
