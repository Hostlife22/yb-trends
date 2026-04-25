from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.providers.base import TrendsProvider


class ManagedTrendsProvider(TrendsProvider):
    """Provider for managed trend APIs (e.g. SerpAPI/Apify/DataForSEO proxy endpoint).

    Expected JSON payload shape:
    {
      "items": [
        {
          "query": "inside out 2",
          "series": [{"timestamp": "2026-04-20T00:00:00Z", "interest": 55.0}, ...]
        }
      ]
    }
    """

    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        if not settings.managed_provider_url:
            raise RuntimeError("Managed provider selected but YBT_MANAGED_PROVIDER_URL is not configured")

        req = Request(settings.managed_provider_url, method="GET")
        req.add_header("Accept", "application/json")
        if settings.managed_provider_api_key:
            req.add_header("Authorization", f"Bearer {settings.managed_provider_api_key}")
        req.add_header("X-Region", region)
        req.add_header("X-Period", "7d")

        try:
            with urlopen(req, timeout=10) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Unable to fetch managed provider trends") from exc

        items: list[RawTrendItem] = []
        for entry in payload.get("items", []):
            query = str(entry.get("query", "")).strip()
            series = [TrendPoint(**point) for point in entry.get("series", [])]
            if query and series:
                items.append(RawTrendItem(query=query, series=series))

        return items
