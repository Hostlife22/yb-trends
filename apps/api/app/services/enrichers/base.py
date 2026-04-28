from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.services.scoring import YouTubeStats


@dataclass(frozen=True)
class MovieMetadata:
    """Validated metadata about a film/animation title.

    All fields are optional: enrichers return an empty instance when they
    can't confidently identify the title (rather than guessing).

    ``tmdb_details`` carries an immutable mapping of the rich TMDB fields the
    UI needs (poster_path, overview, vote_average, runtime, release_date,
    tagline, homepage, popularity, ...). It is None when the enricher
    couldn't resolve the title.
    """

    tmdb_id: int | None = None
    release_year: int | None = None
    original_language: str | None = None
    origin_country: str | None = None
    studios: tuple[str, ...] = ()
    genres: tuple[str, ...] = ()
    is_animation: bool | None = None
    tmdb_details: dict[str, Any] | None = None

    @property
    def is_resolved(self) -> bool:
        return self.tmdb_id is not None


class MetadataEnricher(ABC):
    """Resolves a title (e.g. from a Google Trends query) to validated movie metadata."""

    @abstractmethod
    def enrich(self, title: str, *, region: str | None = None) -> MovieMetadata:
        """Return metadata for the given title, or an empty MovieMetadata if unknown."""


class YouTubeStatsEnricher(ABC):
    """Returns recent YouTube activity stats for a query in a given region."""

    @abstractmethod
    def fetch_stats(self, query: str, *, region: str, lookback_days: int = 14) -> YouTubeStats:
        """Return aggregate stats over the recent lookback window."""


# Re-export YouTubeStats here as a convenience so callers don't have to know
# whether the dataclass lives in scoring or enrichers.
__all__ = [
    "MetadataEnricher",
    "MovieMetadata",
    "YouTubeStatsEnricher",
    "YouTubeStats",
    "field",
]
