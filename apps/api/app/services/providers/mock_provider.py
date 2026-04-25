from datetime import datetime, timedelta, timezone

from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.providers.base import TrendsProvider


class MockTrendsProvider(TrendsProvider):
    """Local deterministic provider for MVP/dev without external API calls."""

    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        now = datetime.now(timezone.utc)
        base = [now - timedelta(days=6 - i) for i in range(7)]

        samples: dict[str, list[float]] = {
            "minecraft movie trailer": [40, 45, 50, 58, 64, 72, 80],
            "inside out 2": [52, 54, 55, 57, 60, 64, 68],
            "new disney animation": [20, 26, 28, 36, 45, 49, 56],
            "nba playoffs": [80, 82, 86, 90, 92, 93, 95],
            "marvel film release date": [30, 34, 33, 39, 42, 46, 50],
            "anime movie 2026": [22, 25, 29, 33, 39, 47, 59],
        }

        items: list[RawTrendItem] = []
        for query, values in samples.items():
            points = [TrendPoint(timestamp=base[idx], interest=value) for idx, value in enumerate(values)]
            items.append(RawTrendItem(query=query, series=points))

        return items
