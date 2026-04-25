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
