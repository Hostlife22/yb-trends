"""Scoring primitives.

Two layers live here:

* Legacy ``compute_interest_level`` / ``compute_growth_velocity`` /
  ``compute_final_score`` — used directly by classifiers to populate the raw
  interest/growth fields on ``ClassifiedTrendItem``.
* New normalized sub-scores (``compute_search_demand``,
  ``compute_search_momentum``, ``compute_youtube_demand``,
  ``compute_youtube_freshness``) plus ``compute_weighted_final_score`` — used by
  ``TrendsService`` to combine search-side and YouTube-side signals into the
  final ranking once enrichers run.

All sub-scores live in ``[0, 1]`` so weights from settings produce a stable
``[0, 1]`` final score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ---------- Legacy (kept for classifier compatibility) ---------------------


def compute_interest_level(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def compute_growth_velocity(values: list[float]) -> float:
    if len(values) < 4:
        return 0.0

    head = sum(values[:2]) / 2
    tail = sum(values[-2:]) / 2
    if head <= 0:
        return tail
    return ((tail - head) / head) * 100


def compute_final_score(interest_level: float, growth_velocity: float) -> float:
    return 0.6 * interest_level + 0.4 * growth_velocity


# ---------- Normalized sub-scores ------------------------------------------


def _clip01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def compute_search_demand(interest_level: float, *, scale: float = 100.0) -> float:
    """Compress raw mean-interest into [0, 1] via log scaling.

    ``scale`` is the interest value that maps to ~1.0. For pytrends RSS
    ``approx_traffic`` typical peaks land around 50-100, so 100 is a safe
    default. Negative or zero inputs map to 0.
    """
    if interest_level <= 0 or scale <= 0:
        return 0.0
    return _clip01(math.log1p(interest_level) / math.log1p(scale))


def compute_search_momentum(growth_velocity_pct: float, *, half_life: float = 50.0) -> float:
    """Map % growth into [0, 1] via tanh squashing.

    ``half_life`` is the growth value (in percent) that maps to ~0.76. Decay
    is symmetric, so flat (0%) → 0.5 and very large negative growth → ~0.
    """
    if half_life <= 0:
        return 0.5
    return _clip01(0.5 * (1.0 + math.tanh(growth_velocity_pct / half_life)))


@dataclass(frozen=True)
class YouTubeStats:
    """Subset of YouTube Data API stats used by scoring.

    Lives here (instead of in ``enrichers``) to keep scoring pure and
    importable without external dependencies.
    """

    videos_published: int = 0
    total_views: int = 0
    median_views: int = 0
    top_video_views: int = 0
    channels_count: int = 0


def compute_youtube_demand(stats: YouTubeStats, *, scale_views: float = 1_000_000.0) -> float:
    """Normalize median view count into [0, 1].

    Median is preferred over mean: it resists a single viral video skewing
    the niche signal. ``scale_views`` is the median view count that maps to
    ~1.0 (defaults to 1M which is a strong signal in most niches).
    """
    if stats.median_views <= 0 or scale_views <= 0:
        return 0.0
    return _clip01(math.log1p(stats.median_views) / math.log1p(scale_views))


def compute_youtube_freshness(
    stats: YouTubeStats,
    *,
    target_videos: int = 10,
    target_channels: int = 3,
) -> float:
    """How "alive" is the niche on YouTube right now.

    A niche is fresh if multiple distinct creators are publishing it in
    volume. We take the geometric mean of two clipped ratios so a niche
    needs both volume and diversity to score high.
    """
    if target_videos <= 0 or target_channels <= 0:
        return 0.0
    videos_ratio = _clip01(stats.videos_published / target_videos)
    channels_ratio = _clip01(stats.channels_count / target_channels)
    return math.sqrt(videos_ratio * channels_ratio)


@dataclass(frozen=True)
class ScoreWeights:
    search_demand: float = 0.30
    search_momentum: float = 0.20
    youtube_demand: float = 0.30
    youtube_freshness: float = 0.20


def compute_weighted_final_score(
    *,
    search_demand: float,
    search_momentum: float,
    youtube_demand: float,
    youtube_freshness: float,
    weights: ScoreWeights | None = None,
) -> float:
    """Weighted sum of the four sub-scores.

    Inputs are expected to be already in [0, 1]. Output is also clipped to
    [0, 1] for predictable downstream sorting.
    """
    w = weights or ScoreWeights()
    raw = (
        w.search_demand * search_demand
        + w.search_momentum * search_momentum
        + w.youtube_demand * youtube_demand
        + w.youtube_freshness * youtube_freshness
    )
    return _clip01(raw)
