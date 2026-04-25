from datetime import datetime
from typing import Literal

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
    reason: str
    interest_level: float = Field(ge=0.0)
    growth_velocity: float
    final_score: float


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
