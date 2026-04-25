import pytest

pytest.importorskip("pydantic")

from app.db import TrendRepository
from app.schemas.trends import ClassifiedTrendItem


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

    saved = repo.save_snapshot(region="US", period="7d", items=[item])
    assert saved == 1

    out = repo.fetch_latest_top(region="US", period="7d", limit=10)
    assert len(out) == 1
    assert out[0].query == "minecraft movie trailer"
