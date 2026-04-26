from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.providers.base import TrendsProvider

logger = logging.getLogger(__name__)

_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


class GeminiTrendsProvider(TrendsProvider):
    """Discovers trending movies/animations via Gemini with Google Search grounding,
    then builds synthetic 7-day interest curves from Google Trends RSS traffic data."""

    GEMINI_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    )
    RSS_URL = "https://trends.google.com/trending/rss?geo={region}"

    PROMPT = (
        "Return a JSON array of up to 20 movies and animated films that are currently "
        "trending in the {region} right now. Include films in theaters, recently released on streaming, "
        "and upcoming films generating significant buzz. "
        'Each item: {{"title": "exact title", "type": "movie" or "animation"}}. '
        "Only real, existing films — no made-up titles. Return ONLY the JSON array, no markdown."
    )

    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        titles = self._discover_titles(region)
        if not titles:
            logger.warning("gemini_provider_no_titles", extra={"region": region})
            return []

        rss_traffic = self._fetch_rss_traffic(region)
        now = datetime.now(timezone.utc)
        dates = [now - timedelta(days=6 - i) for i in range(7)]

        items: list[RawTrendItem] = []
        for idx, entry in enumerate(titles):
            title = entry.get("title", "")
            if not title:
                continue

            base_traffic = rss_traffic.get(title.lower(), 1000.0)
            base = max(base_traffic / 7, 1)
            slope = 1 + (idx % 5) * 0.04
            values = [round(base * (slope + day * 0.06), 2) for day in range(7)]
            series = [TrendPoint(timestamp=dates[i], interest=values[i]) for i in range(7)]
            items.append(RawTrendItem(query=title, series=series))

        logger.info("gemini_provider_fetched", extra={"region": region, "count": len(items)})
        return items

    def _discover_titles(self, region: str) -> list[dict]:
        api_key = settings.gemini_api_key
        if not api_key:
            logger.error("gemini_provider_no_api_key")
            return []

        body = json.dumps({
            "contents": [{"parts": [{"text": self.PROMPT.format(region=region)}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.1},
        }).encode()

        req = Request(
            self.GEMINI_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
        )
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except (URLError, TimeoutError) as exc:
            logger.error("gemini_provider_request_failed", extra={"error": str(exc)})
            return []

        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        md_match = _JSON_BLOCK_RE.search(text)
        raw = md_match.group(1) if md_match else text.strip()

        try:
            titles = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("gemini_provider_parse_failed", extra={"raw": raw[:200]})
            return []

        return titles if isinstance(titles, list) else []

    def _fetch_rss_traffic(self, region: str) -> dict[str, float]:
        """Fetch current RSS traffic as a rough popularity baseline."""
        url = self.RSS_URL.format(region=region)
        try:
            with urlopen(url, timeout=8) as resp:
                payload = resp.read()
        except URLError:
            return {}

        import xml.etree.ElementTree as ET

        root = ET.fromstring(payload)
        channel = root.find("channel")
        if channel is None:
            return {}

        traffic: dict[str, float] = {}
        ns = {"ht": "https://trends.google.com/trending/rss"}
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip().lower()
            text = item.findtext("ht:approx_traffic", default="", namespaces=ns)
            val = text.replace("+", "").replace("K", "000").replace("M", "000000").replace(",", "")
            try:
                traffic[title] = float(re.sub(r"[^\d.]", "", val) or "1")
            except ValueError:
                traffic[title] = 1.0

        return traffic
