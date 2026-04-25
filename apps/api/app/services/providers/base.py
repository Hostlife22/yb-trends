from abc import ABC, abstractmethod

from app.schemas.trends import RawTrendItem


class TrendsProvider(ABC):
    """Provider contract for collecting trend items."""

    @abstractmethod
    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        """Return trend queries for last 7 days in the given region."""
