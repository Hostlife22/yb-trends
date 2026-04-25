from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.schemas.trends import ClassifiedTrendItem, RawTrendItem
from app.services.classifier import TrendClassifier
from app.services.scoring import compute_final_score, compute_growth_velocity, compute_interest_level


class GeminiClassifier:
    """Gemini-backed classifier with heuristic fallback.

    Falls back to `TrendClassifier` when API key is missing or provider fails.
    """

    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def __init__(self) -> None:
        self._fallback = TrendClassifier()

    def classify(self, item: RawTrendItem) -> ClassifiedTrendItem:
        if not settings.gemini_api_key:
            return self._fallback.classify(item)

        values = [point.interest for point in item.series]
        interest = compute_interest_level(values)
        growth = compute_growth_velocity(values)
        score = compute_final_score(interest, growth)

        prompt = (
            "Classify search query as movie/animation or not. "
            "Respond ONLY valid JSON with fields: "
            "is_movie_or_animation(boolean), confidence(number 0..1), "
            "title(string), content_type(movie|animation|unknown), reason(string). "
            f"Query: {item.query}"
        )
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
        }

        req = Request(
            f"{self.ENDPOINT}?key={settings.gemini_api_key}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=8) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError, KeyError):
            return self._fallback.classify(item)

        try:
            text = raw["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return self._fallback.classify(item)

        return ClassifiedTrendItem(
            query=item.query,
            title_normalized=str(parsed.get("title") or item.query.title()),
            content_type=parsed.get("content_type", "unknown"),
            is_movie_or_animation=bool(parsed.get("is_movie_or_animation", False)),
            confidence=float(parsed.get("confidence", 0.0)),
            reason=str(parsed.get("reason", "gemini response")),
            interest_level=round(interest, 2),
            growth_velocity=round(growth, 2),
            final_score=round(score, 2),
        )
