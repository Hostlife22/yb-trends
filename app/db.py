from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.schemas.trends import ClassifiedTrendItem


@dataclass
class StoredTrend:
    query: str
    title_normalized: str
    content_type: str
    confidence: float
    interest_level: float
    growth_velocity: float
    final_score: float
    created_at: str


class TrendRepository:
    def __init__(self, db_path: str | None = None) -> None:
        path = db_path or settings.sqlite_path
        self.db_path = Path(path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trend_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    region TEXT NOT NULL,
                    period TEXT NOT NULL,
                    title_normalized TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    is_movie_or_animation INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    interest_level REAL NOT NULL,
                    growth_velocity REAL NOT NULL,
                    final_score REAL NOT NULL,
                    reason TEXT NOT NULL,
                    raw_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def save_snapshot(self, region: str, period: str, items: list[ClassifiedTrendItem]) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT INTO trend_items (
                        query, region, period, title_normalized, content_type,
                        is_movie_or_animation, confidence, interest_level,
                        growth_velocity, final_score, reason, raw_payload, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.query,
                        region,
                        period,
                        item.title_normalized,
                        item.content_type,
                        1 if item.is_movie_or_animation else 0,
                        item.confidence,
                        item.interest_level,
                        item.growth_velocity,
                        item.final_score,
                        item.reason,
                        json.dumps(item.model_dump(), ensure_ascii=False),
                        now,
                    ),
                )
        return len(items)

    def fetch_latest_top(self, region: str, period: str, limit: int) -> list[StoredTrend]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT MAX(created_at) AS created_at FROM trend_items WHERE region = ? AND period = ?",
                (region, period),
            ).fetchone()
            if row is None or row["created_at"] is None:
                return []

            created_at = row["created_at"]
            rows = conn.execute(
                """
                SELECT query, title_normalized, content_type, confidence,
                       interest_level, growth_velocity, final_score, created_at
                FROM trend_items
                WHERE region = ? AND period = ? AND created_at = ? AND is_movie_or_animation = 1
                ORDER BY final_score DESC
                LIMIT ?
                """,
                (region, period, created_at, limit),
            ).fetchall()

        return [StoredTrend(**dict(r)) for r in rows]
