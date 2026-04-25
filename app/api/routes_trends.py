from fastapi import APIRouter, Depends, Query

from app.api.deps import verify_api_key
from app.config import settings
from app.db import TrendRepository
from app.schemas.trends import SnapshotsResponse, SummaryResponse, TopTrendsResponse, TrendTimeseriesResponse
from app.services.cache import TTLCache
from app.services.providers.factory import build_trends_provider
from app.services.trends_service import TrendsService

router = APIRouter(prefix="/api/v1", tags=["trends"])


def get_trends_service() -> TrendsService:
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


@router.get("/trends/{query}/timeseries", response_model=TrendTimeseriesResponse, dependencies=[Depends(verify_api_key)])
def get_timeseries(
    query: str,
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=200, ge=1, le=1000),
    service: TrendsService = Depends(get_trends_service),
) -> TrendTimeseriesResponse:
    return service.get_timeseries(region=region, period=period, query=query, limit=limit)


@router.get("/trends/top", response_model=TopTrendsResponse, dependencies=[Depends(verify_api_key)])
def get_top_trends(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=settings.default_limit, ge=1, le=100),
    service: TrendsService = Depends(get_trends_service),
) -> TopTrendsResponse:
    return service.get_top_trends(region=region, period=period, limit=limit)


@router.get("/summary", response_model=SummaryResponse, dependencies=[Depends(verify_api_key)])
def get_summary(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=settings.default_limit, ge=1, le=100),
    service: TrendsService = Depends(get_trends_service),
) -> SummaryResponse:
    return service.get_summary(region=region, period=period, limit=limit)
