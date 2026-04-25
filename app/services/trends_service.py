from datetime import datetime, timezone

from app.schemas.trends import SummaryResponse, TopTrendsResponse
from app.services.classifier import TrendClassifier
from app.services.providers.base import TrendsProvider


class TrendsService:
    def __init__(self, provider: TrendsProvider, classifier: TrendClassifier | None = None) -> None:
        self.provider = provider
        self.classifier = classifier or TrendClassifier()

    def get_top_trends(self, region: str, period: str, limit: int) -> TopTrendsResponse:
        raw_items = self.provider.fetch_weekly_trends(region)
        classified = [self.classifier.classify(item) for item in raw_items]
        filtered = [item for item in classified if item.is_movie_or_animation and item.confidence >= 0.7]
        ranked = sorted(filtered, key=lambda i: i.final_score, reverse=True)[:limit]

        return TopTrendsResponse(
            region=region,
            period=period,
            generated_at=datetime.now(timezone.utc),
            items=ranked,
        )

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
