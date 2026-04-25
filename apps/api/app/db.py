from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings
from app.schemas.trends import ClassifiedTrendItem, TrendPoint


@dataclass
class StoredTrend:
    query: str
    title_normalized: str
    content_type: str
    confidence: float
    studio: str
    interest_level: float
    growth_velocity: float
    final_score: float
    created_at: str


@dataclass
class SnapshotMeta:
    created_at: str
    item_count: int


@dataclass
class SyncRun:
    created_at: str
    provider: str
    total_items: int
    relevant_items: int
    quality_passed: bool
    reason: str


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
            conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
            applied = {row["version"] for row in conn.execute("SELECT version FROM schema_migrations").fetchall()}

            migrations: list[tuple[int, str]] = [
                (
                    1,
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
                    );
                    """,
                ),
                (
                    2,
                    """
                    CREATE TABLE IF NOT EXISTS sync_locks (
                        lock_key TEXT PRIMARY KEY,
                        owner_id TEXT NOT NULL,
                        acquired_at TEXT NOT NULL,
                        expires_at TEXT NOT NULL
                    );
                    """,
                ),
                (
                    3,
                    """
                    CREATE TABLE IF NOT EXISTS trend_points (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        region TEXT NOT NULL,
                        period TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        interest REAL NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """,
                ),
                (
                    4,
                    """
                    CREATE TABLE IF NOT EXISTS sync_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        region TEXT NOT NULL,
                        period TEXT NOT NULL,
                        provider TEXT NOT NULL,
                        total_items INTEGER NOT NULL,
                        relevant_items INTEGER NOT NULL,
                        quality_passed INTEGER NOT NULL,
                        reason TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    """,
                ),
                (
                    5,
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uix_trend_points_key
                    ON trend_points (query, region, period, timestamp);
                    """,
                ),
                (
                    6,
                    """
                    ALTER TABLE trend_items ADD COLUMN studio TEXT NOT NULL DEFAULT 'unknown';
                    """,
                ),
            ]

            for version, sql in migrations:
                if version in applied:
                    continue
                conn.executescript(sql)
                conn.execute("INSERT INTO schema_migrations(version) VALUES (?)", (version,))

    def record_sync_run(
        self,
        *,
        region: str,
        period: str,
        provider: str,
        total_items: int,
        relevant_items: int,
        quality_passed: bool,
        reason: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_runs(
                    region, period, provider, total_items, relevant_items,
                    quality_passed, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    region,
                    period,
                    provider,
                    total_items,
                    relevant_items,
                    1 if quality_passed else 0,
                    reason,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def fetch_sync_runs(self, region: str, period: str, limit: int = 50) -> list[SyncRun]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT created_at, provider, total_items, relevant_items, quality_passed, reason
                FROM sync_runs
                WHERE region = ? AND period = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (region, period, limit),
            ).fetchall()
        return [
            SyncRun(
                created_at=r["created_at"],
                provider=r["provider"],
                total_items=r["total_items"],
                relevant_items=r["relevant_items"],
                quality_passed=bool(r["quality_passed"]),
                reason=r["reason"],
            )
            for r in rows
        ]

    def count_sync_runs_since(self, region: str, period: str, since_iso: str) -> tuple[int, int]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN quality_passed = 0 THEN 1 ELSE 0 END) AS failures
                FROM sync_runs
                WHERE region = ? AND period = ? AND created_at >= ?
                """,
                (region, period, since_iso),
            ).fetchone()
        total = int(row["total"] or 0)
        failures = int(row["failures"] or 0)
        return total, failures

    def count_sync_runs_total(self, region: str, period: str) -> tuple[int, int]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN quality_passed = 0 THEN 1 ELSE 0 END) AS failures
                FROM sync_runs
                WHERE region = ? AND period = ?
                """,
                (region, period),
            ).fetchone()
        return int(row["total"] or 0), int(row["failures"] or 0)

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

    def save_snapshot(
        self,
        region: str,
        period: str,
        items: list[ClassifiedTrendItem],
        raw_series_by_query: dict[str, list[TrendPoint]] | None = None,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT INTO trend_items (
                        query, region, period, title_normalized, content_type,
                        is_movie_or_animation, confidence, studio, interest_level,
                        growth_velocity, final_score, reason, raw_payload, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.query,
                        region,
                        period,
                        item.title_normalized,
                        item.content_type,
                        1 if item.is_movie_or_animation else 0,
                        item.confidence,
                        item.studio,
                        item.interest_level,
                        item.growth_velocity,
                        item.final_score,
                        item.reason,
                        json.dumps(item.model_dump(), ensure_ascii=False),
                        now,
                    ),
                )

                if raw_series_by_query and item.query in raw_series_by_query:
                    for point in raw_series_by_query[item.query]:
                        day = point.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
                        conn.execute(
                            """
                            INSERT INTO trend_points (query, region, period, timestamp, interest, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(query, region, period, timestamp) DO UPDATE SET
                                interest = excluded.interest,
                                created_at = excluded.created_at
                            """,
                            (item.query, region, period, day.isoformat(), point.interest, now),
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

    def fetch_snapshots(self, region: str, period: str, limit: int = 20) -> list[SnapshotMeta]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT created_at, COUNT(*) AS item_count
                FROM trend_items
                WHERE region = ? AND period = ?
                GROUP BY created_at
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (region, period, limit),
            ).fetchall()
        return [SnapshotMeta(created_at=r["created_at"], item_count=r["item_count"]) for r in rows]

    def fetch_timeseries(self, region: str, period: str, query: str, limit: int = 200) -> list[TrendPoint]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT timestamp, interest
                FROM trend_points
                WHERE region = ? AND period = ? AND query = ?
                ORDER BY timestamp ASC
                LIMIT ?
                """,
                (region, period, query, limit),
            ).fetchall()
        return [TrendPoint(timestamp=r["timestamp"], interest=r["interest"]) for r in rows]

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
                SELECT query, title_normalized, content_type, confidence, studio,
                       interest_level, growth_velocity, final_score, created_at
                FROM trend_items
                WHERE region = ? AND period = ? AND created_at = ? AND is_movie_or_animation = 1
                ORDER BY final_score DESC
                LIMIT ?
                """,
                (region, period, created_at, limit),
            ).fetchall()

        return [StoredTrend(**dict(r)) for r in rows]
