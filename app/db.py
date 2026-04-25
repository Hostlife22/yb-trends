from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
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


@dataclass
class SnapshotMeta:
    created_at: str
    item_count: int


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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sync_locks (
                    lock_key TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )

    def acquire_lock(self, lock_key: str, owner_id: str, ttl_seconds: int) -> bool:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)

        with self._connect() as conn:
            row = conn.execute(
                "SELECT owner_id, expires_at FROM sync_locks WHERE lock_key = ?",
                (lock_key,),
            ).fetchone()

            if row is not None:
                existing_expires = datetime.fromisoformat(row["expires_at"])
                if existing_expires > now:
                    return False
                conn.execute("DELETE FROM sync_locks WHERE lock_key = ?", (lock_key,))

            conn.execute(
                """
                INSERT INTO sync_locks (lock_key, owner_id, acquired_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (lock_key, owner_id, now.isoformat(), expires_at.isoformat()),
            )
            return True

    def release_lock(self, lock_key: str, owner_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM sync_locks WHERE lock_key = ? AND owner_id = ?",
                (lock_key, owner_id),
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

    def fetch_latest_snapshot_meta(self, region: str, period: str) -> SnapshotMeta | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT created_at, COUNT(*) AS item_count
                FROM trend_items
                WHERE region = ? AND period = ?
                  AND created_at = (
                    SELECT MAX(created_at) FROM trend_items WHERE region = ? AND period = ?
                  )
                GROUP BY created_at
                """,
                (region, period, region, period),
            ).fetchone()
            if row is None:
                return None
            return SnapshotMeta(created_at=row["created_at"], item_count=row["item_count"])

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
