from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import re
from urllib.error import URLError
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from app.schemas.trends import RawTrendItem, TrendPoint
from app.services.providers.base import TrendsProvider


_TRAFFIC_RE = re.compile(r"([\d,.]+)")


@dataclass
class TrendingEntry:
    title: str
    approx_traffic: float


class PyTrendsProvider(TrendsProvider):
    """Best-effort provider using Google Trending RSS feed.

    Note: This is still an unofficial integration and should be considered
    a transitional data source.
    """

    RSS_TEMPLATE = "https://trends.google.com/trending/rss?geo={region}"

    def fetch_weekly_trends(self, region: str) -> list[RawTrendItem]:
        entries = self._read_trending_entries(region=region)
        now = datetime.now(timezone.utc)
        dates = [now - timedelta(days=6 - i) for i in range(7)]

        items: list[RawTrendItem] = []
        for idx, entry in enumerate(entries):
            # Synthetic 7-day curve from a daily signal (temporary approach).
            base = max(entry.approx_traffic / 7, 1)
            slope = 1 + (idx % 3) * 0.07
            values = [base * (slope + day * 0.05) for day in range(7)]
            series = [TrendPoint(timestamp=dates[i], interest=round(values[i], 2)) for i in range(7)]
            items.append(RawTrendItem(query=entry.title.lower(), series=series))

        return items

    def _read_trending_entries(self, region: str) -> list[TrendingEntry]:
        url = self.RSS_TEMPLATE.format(region=region)
        try:
            with urlopen(url, timeout=8) as response:
                payload = response.read()
        except URLError as exc:
            raise RuntimeError(f"Unable to fetch trends RSS for region={region}") from exc

        root = ET.fromstring(payload)
        channel = root.find("channel")
        if channel is None:
            return []

        items: list[TrendingEntry] = []
        ns = {"ht": "https://trends.google.com/trending/rss"}
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            approx_traffic_text = item.findtext("ht:approx_traffic", default="", namespaces=ns)
            approx_traffic = self._parse_traffic(approx_traffic_text)
            if title:
                items.append(TrendingEntry(title=title, approx_traffic=approx_traffic))

        return items

    @staticmethod
    def _parse_traffic(traffic_text: str) -> float:
        normalized = traffic_text.replace("+", "").replace("K", "000").replace("M", "000000")
        match = _TRAFFIC_RE.search(normalized)
        if not match:
            return 1.0
        return float(match.group(1).replace(",", ""))
