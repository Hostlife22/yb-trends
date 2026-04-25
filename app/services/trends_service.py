from datetime import datetime, timezone

from app.db import TrendRepository
from app.schemas.trends import ClassifiedTrendItem, SummaryResponse, TopTrendsResponse
from app.services.cache import TTLCache
from app.services.classifier import TrendClassifier
from app.services.llm_classifier import GeminiClassifier
from app.services.providers.base import TrendsProvider


class TrendsService:
    def __init__(
        self,
        provider: TrendsProvider,
        repository: TrendRepository,
        classifier: TrendClassifier | GeminiClassifier | None = None,
        cache: TTLCache[TopTrendsResponse] | None = None,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.classifier = classifier or GeminiClassifier()
        self.cache = cache or TTLCache(ttl_seconds=600)

    def sync(self, region: str, period: str) -> int:
        raw_items = self.provider.fetch_weekly_trends(region)
        classified = [self.classifier.classify(item) for item in raw_items]
        return self.repository.save_snapshot(region=region, period=period, items=classified)

    def get_top_trends(self, region: str, period: str, limit: int) -> TopTrendsResponse:
        cache_key = f"top:{region}:{period}:{limit}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        stored = self.repository.fetch_latest_top(region=region, period=period, limit=limit)
        if not stored:
            self.sync(region=region, period=period)
            stored = self.repository.fetch_latest_top(region=region, period=period, limit=limit)

        items = [
            ClassifiedTrendItem(
                query=row.query,
                title_normalized=row.title_normalized,
                content_type=row.content_type,
                is_movie_or_animation=True,
                confidence=row.confidence,
                reason="from snapshot",
                interest_level=row.interest_level,
                growth_velocity=row.growth_velocity,
                final_score=row.final_score,
            )
            for row in stored
            if row.confidence >= 0.7
        ]

        response = TopTrendsResponse(
            region=region,
            period=period,
            generated_at=datetime.now(timezone.utc),
            items=items,
        )
        self.cache.set(cache_key, response)
        return response

    def get_summary(self, region: str, period: str, limit: int) -> SummaryResponse:
        top = self.get_top_trends(region=region, period=period, limit=limit)
        if not top.items:
            text = "No movie or animation trends were detected for the selected period."
            titles: list[str] = []
        else:
            titles = [item.title_normalized for item in top.items[:5]]
            text = (
                f"Top US movie/animation trend is '{top.items[0].title_normalized}'. "
                f"Detected {len(top.items)} relevant queries in the last {period}."
            )

        return SummaryResponse(
            region=region,
            period=period,
            generated_at=datetime.now(timezone.utc),
            summary=text,
            top_titles=titles,
        )
