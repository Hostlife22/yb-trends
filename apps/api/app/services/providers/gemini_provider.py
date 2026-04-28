from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import settings
from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.providers.base import TrendsProvider

logger = logging.getLogger(__name__)

# Retry transient errors (rate-limit + 5xx). 429 is by far the most common
# in practice on free-tier keys.
_RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
_MAX_RETRIES = 2  # total attempts = 1 + _MAX_RETRIES

_JSON_BLOCK_RE = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)


class GeminiTrendsProvider(TrendsProvider):
    """Discovers trending movies/animations via Gemini with Google Search grounding,
    then builds synthetic 7-day interest curves from Google Trends RSS traffic data."""

    GEMINI_URL_TEMPLATE = (
        "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    )
    RSS_URL = "https://trends.google.com/trending/rss?geo={region}"

    @property
    def gemini_url(self) -> str:
        return self.GEMINI_URL_TEMPLATE.format(model=settings.gemini_model)

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
            self.gemini_url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
        )

        data = self._post_with_retry(req)
        if data is None:
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

    def _post_with_retry(self, req: Request) -> dict | None:
        """POST with exponential backoff on 429/5xx.

        Logs the actual HTTP status and a snippet of the error body so failures
        are diagnosable without re-running with breakpoints. Returns parsed
        JSON or None on terminal failure.
        """
        last_error: str | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                with urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read())
            except HTTPError as exc:
                body_snippet = ""
                try:
                    body_snippet = exc.read().decode("utf-8", errors="replace")[:300]
                except Exception:  # noqa: BLE001
                    pass
                last_error = f"HTTP {exc.code} {exc.reason}: {body_snippet}"
                if exc.code not in _RETRY_STATUS_CODES or attempt == _MAX_RETRIES:
                    logger.error(
                        "gemini_provider_request_failed",
                        extra={"status": exc.code, "reason": exc.reason, "body": body_snippet},
                    )
                    return None
            except (URLError, TimeoutError) as exc:
                last_error = f"network: {exc}"
                if attempt == _MAX_RETRIES:
                    logger.error("gemini_provider_request_failed", extra={"error": str(exc)})
                    return None

            backoff_seconds = 2 ** attempt
            logger.warning(
                "gemini_provider_retrying",
                extra={"attempt": attempt + 1, "delay_seconds": backoff_seconds, "last_error": last_error},
            )
            time.sleep(backoff_seconds)

        return None

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
