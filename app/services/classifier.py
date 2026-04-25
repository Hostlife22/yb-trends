from app.schemas.trends import ClassifiedTrendItem, RawTrendItem
from app.services.scoring import compute_final_score, compute_growth_velocity, compute_interest_level


class TrendClassifier:
    """Simple heuristic classifier for movie/animation trend detection."""

    MOVIE_TOKENS = {
        "movie",
        "film",
        "trailer",
        "box office",
        "cinema",
        "marvel",
        "disney",
        "pixar",
        "animation",
        "anime",
    }

    EXCLUDED_TOKENS = {"nfl", "nba", "election", "stock", "crypto"}

    def classify(self, item: RawTrendItem) -> ClassifiedTrendItem:
        query = item.query.lower()
        values = [point.interest for point in item.series]

        has_movie_token = any(token in query for token in self.MOVIE_TOKENS)
        has_excluded = any(token in query for token in self.EXCLUDED_TOKENS)

        is_target = has_movie_token and not has_excluded
        confidence = 0.8 if is_target else 0.2

        if "animation" in query or "anime" in query or "pixar" in query or "disney" in query:
            content_type = "animation"
        elif is_target:
            content_type = "movie"
        else:
            content_type = "unknown"

        reason = "matched movie/animation tokens" if is_target else "did not match target category"

        interest_level = compute_interest_level(values)
        growth_velocity = compute_growth_velocity(values)
        final_score = compute_final_score(interest_level, growth_velocity)

        return ClassifiedTrendItem(
            query=item.query,
            title_normalized=item.query.title(),
            content_type=content_type,
            is_movie_or_animation=is_target,
            confidence=confidence,
            reason=reason,
            interest_level=round(interest_level, 2),
            growth_velocity=round(growth_velocity, 2),
            final_score=round(final_score, 2),
        )
