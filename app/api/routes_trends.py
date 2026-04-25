from fastapi import APIRouter, Depends, Query

from app.config import settings
from app.schemas.trends import SummaryResponse, TopTrendsResponse
from app.services.classifier import TrendClassifier
from app.services.providers.mock_provider import MockTrendsProvider
from app.services.trends_service import TrendsService

router = APIRouter(prefix="/api/v1", tags=["trends"])


def get_trends_service() -> TrendsService:
    provider = MockTrendsProvider()
    classifier = TrendClassifier()
    return TrendsService(provider=provider, classifier=classifier)


@router.get("/trends/top", response_model=TopTrendsResponse)
def get_top_trends(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=settings.default_limit, ge=1, le=100),
    service: TrendsService = Depends(get_trends_service),
) -> TopTrendsResponse:
    return service.get_top_trends(region=region, period=period, limit=limit)


@router.get("/summary", response_model=SummaryResponse)
def get_summary(
    region: str = Query(default=settings.default_region),
    period: str = Query(default=settings.default_period),
    limit: int = Query(default=settings.default_limit, ge=1, le=100),
    service: TrendsService = Depends(get_trends_service),
) -> SummaryResponse:
    return service.get_summary(region=region, period=period, limit=limit)
