from functools import lru_cache

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import verify_api_key
from app.config import settings
from app.db import TrendRepository
from app.schemas.trends import (
    AlertsResponse,
    MetricsResponse,
    SnapshotsResponse,
    SummaryResponse,
    SyncRunsResponse,
    TopTrendsResponse,
    TrendTimeseriesResponse,
)
from app.services.cache import TTLCache
from app.services.providers.factory import build_trends_provider
from app.services.trends_service import TrendsService

router = APIRouter(prefix="/api/v1", tags=["trends"])


@lru_cache(maxsize=1)
def get_trends_service() -> TrendsService:
    """Module-level singleton: provider/repository/cache reused across requests."""
    provider = build_trends_provider()
    repository = TrendRepository()
    cache = TTLCache[TopTrendsResponse](ttl_seconds=settings.cache_ttl_seconds)
    return TrendsService(provider=provider, repository=repository, cache=cache)


@router.post("/admin/sync", dependencies=[Depends(verify_api_key)])
def sync_trends(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    service: TrendsService = Depends(get_trends_service),
) -> dict[str, int | str]:
    count = service.sync(region=region, period=period)
    return {"status": "ok", "saved": count}


@router.get("/admin/freshness", dependencies=[Depends(verify_api_key)])
def check_freshness(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    service: TrendsService = Depends(get_trends_service),
) -> dict[str, bool | str]:
    fresh = service.ensure_fresh_snapshot(region=region, period=period)
    return {"region": region, "period": period, "fresh": fresh}


@router.get("/admin/snapshots", response_model=SnapshotsResponse, dependencies=[Depends(verify_api_key)])
def get_snapshots(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=20, ge=1, le=200),
    service: TrendsService = Depends(get_trends_service),
) -> SnapshotsResponse:
    return service.get_snapshots(region=region, period=period, limit=limit)


@router.get("/admin/sync-runs", response_model=SyncRunsResponse, dependencies=[Depends(verify_api_key)])
def get_sync_runs(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=50, ge=1, le=500),
    service: TrendsService = Depends(get_trends_service),
) -> SyncRunsResponse:
    return service.get_sync_runs(region=region, period=period, limit=limit)


@router.get("/admin/metrics", response_model=MetricsResponse, dependencies=[Depends(verify_api_key)])
def get_metrics(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    service: TrendsService = Depends(get_trends_service),
) -> MetricsResponse:
    return service.get_metrics(region=region, period=period)


@router.get("/admin/alerts", response_model=AlertsResponse, dependencies=[Depends(verify_api_key)])
def get_alerts(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    service: TrendsService = Depends(get_trends_service),
) -> AlertsResponse:
    return service.get_alerts(region=region, period=period)


@router.get("/trends/{query}/timeseries", response_model=TrendTimeseriesResponse, dependencies=[Depends(verify_api_key)])
def get_timeseries(
    query: str = Path(..., min_length=1, max_length=200),
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=200, ge=1, le=1000),
    service: TrendsService = Depends(get_trends_service),
) -> TrendTimeseriesResponse:
    return service.get_timeseries(region=region, period=period, query=query, limit=limit)


_ALLOWED_SORT_BY = {
    "final_score",
    "search_demand",
    "search_momentum",
    "youtube_demand",
    "youtube_freshness",
    "interest_level",
    "growth_velocity",
    "youtube_median_views_14d",
    "youtube_total_views_14d",
}


@router.get("/trends/top", response_model=TopTrendsResponse, dependencies=[Depends(verify_api_key)])
def get_top_trends(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=settings.default_limit, ge=1, le=100),
    language: str | None = Query(default=None, min_length=2, max_length=5, description="ISO 639-1, e.g. en, es, ja"),
    country: str | None = Query(default=None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2, e.g. US, JP"),
    min_year: int | None = Query(default=None, ge=1900, le=2100),
    max_year: int | None = Query(default=None, ge=1900, le=2100),
    sort_by: str = Query(default="final_score"),
    service: TrendsService = Depends(get_trends_service),
) -> TopTrendsResponse:
    if sort_by not in _ALLOWED_SORT_BY:
        sort_by = "final_score"
    return service.get_top_trends(
        region=region,
        period=period,
        limit=limit,
        language=language,
        country=country,
        min_year=min_year,
        max_year=max_year,
        sort_by=sort_by,
    )


@router.get("/summary", response_model=SummaryResponse, dependencies=[Depends(verify_api_key)])
def get_summary(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=settings.default_limit, ge=1, le=100),
    service: TrendsService = Depends(get_trends_service),
) -> SummaryResponse:
    return service.get_summary(region=region, period=period, limit=limit)
