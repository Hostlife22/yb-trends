from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TrendPoint(BaseModel):
    timestamp: datetime
    interest: float = Field(ge=0.0)


class RawTrendItem(BaseModel):
    query: str
    series: list[TrendPoint]


class ClassifiedTrendItem(BaseModel):
    query: str
    title_normalized: str
    content_type: Literal["movie", "animation", "unknown"]
    is_movie_or_animation: bool
    confidence: float = Field(ge=0.0, le=1.0)
    studio: str = Field(default="unknown")
    reason: str
    interest_level: float = Field(ge=0.0)
    growth_velocity: float
    final_score: float

    # TMDB metadata (filled by MetadataEnricher; None when unavailable)
    release_year: int | None = Field(default=None)
    original_language: str | None = Field(default=None)
    origin_country: str | None = Field(default=None)
    genres: list[str] = Field(default_factory=list)
    tmdb_id: int | None = Field(default=None)

    # YouTube Data API stats over a recent lookback window
    youtube_videos_published_14d: int = Field(default=0, ge=0)
    youtube_total_views_14d: int = Field(default=0, ge=0)
    youtube_median_views_14d: int = Field(default=0, ge=0)
    youtube_top_video_views_14d: int = Field(default=0, ge=0)
    youtube_channels_count_14d: int = Field(default=0, ge=0)

    # Normalized sub-scores in [0..1] used to compose final_score
    search_demand: float = Field(default=0.0, ge=0.0, le=1.0)
    search_momentum: float = Field(default=0.0, ge=0.0, le=1.0)
    youtube_demand: float = Field(default=0.0, ge=0.0, le=1.0)
    youtube_freshness: float = Field(default=0.0, ge=0.0, le=1.0)

    # Compact TMDB payload (poster_path, overview, vote_average, runtime, ...)
    # Stored as JSON in trend_items.tmdb_details. None when not resolved.
    tmdb_details: dict[str, Any] | None = Field(default=None)


class TopTrendsResponse(BaseModel):
    region: str
    period: str
    generated_at: datetime
    items: list[ClassifiedTrendItem]


class SummaryResponse(BaseModel):
    region: str
    period: str
    generated_at: datetime
    summary: str
    top_titles: list[str]


class SnapshotInfo(BaseModel):
    created_at: datetime
    item_count: int


class SnapshotsResponse(BaseModel):
    region: str
    period: str
    snapshots: list[SnapshotInfo]


class TrendTimeseriesResponse(BaseModel):
    region: str
    period: str
    query: str
    points: list[TrendPoint]


class SyncRunInfo(BaseModel):
    id: int
    created_at: datetime
    provider: str
    total_items: int
    relevant_items: int
    quality_passed: bool
    reason: str


class SyncRunsResponse(BaseModel):
    region: str
    period: str
    runs: list[SyncRunInfo]


class MetricsResponse(BaseModel):
    region: str
    period: str
    latest_snapshot_age_seconds: int | None
    latest_sync_quality_passed: bool | None
    sync_runs_last_24h: int
    quality_failures_last_24h: int


class AlertItem(BaseModel):
    code: str
    severity: Literal["warning", "critical"]
    message: str


class AlertsResponse(BaseModel):
    region: str
    period: str
    alerts: list[AlertItem]
