"""Append-only point-in-time record store for MarketSage research inputs.

This is a local SQLite foundation, not yet wired into live ingestion or scoring.
Records are never overwritten: later provider corrections are appended as revisions.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_iso(value: datetime | None, *, required: bool = True) -> str | None:
    if value is None:
        if required:
            raise ValueError("timestamp is required")
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


@dataclass(frozen=True)
class TemporalRecord:
    record_key: str
    source_id: str
    market: str
    data_kind: str
    observed_at: datetime
    retrieved_at: datetime
    payload: dict[str, Any]
    published_at: datetime | None = None
    source_revision: str | None = None


class PointInTimeStore:
    """SQLite append-only store with as-of queries for leakage-safe research."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _initialize(self) -> None:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS temporal_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_key TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    market TEXT NOT NULL,
                    data_kind TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    published_at TEXT,
                    retrieved_at TEXT NOT NULL,
                    source_revision TEXT,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    inserted_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%f+00:00','now')),
                    UNIQUE(record_key, source_id, retrieved_at, payload_sha256)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_temporal_pit
                ON temporal_records(record_key, retrieved_at)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_temporal_market_kind
                ON temporal_records(market, data_kind, observed_at)
            """)

    def append(self, record: TemporalRecord) -> int:
        """Append a source observation or correction without mutating prior history."""
        for field_name in ("record_key", "source_id", "market", "data_kind"):
            if not getattr(record, field_name).strip():
                raise ValueError(f"{field_name} must be non-empty")
        observed_at = _utc_iso(record.observed_at)
        retrieved_at = _utc_iso(record.retrieved_at)
        published_at = _utc_iso(record.published_at, required=False)
        if published_at and published_at > retrieved_at:
            raise ValueError("published_at cannot be later than retrieved_at")
        payload_json = json.dumps(
            record.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        with self._connect() as conn:
            cur = conn.execute("""
                INSERT OR IGNORE INTO temporal_records
                (record_key, source_id, market, data_kind, observed_at, published_at,
                 retrieved_at, source_revision, payload_json, payload_sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_key, record.source_id, record.market, record.data_kind,
                observed_at, published_at, retrieved_at, record.source_revision,
                payload_json, payload_hash,
            ))
            if cur.rowcount == 0:
                row = conn.execute("""
                    SELECT id FROM temporal_records
                    WHERE record_key=? AND source_id=? AND retrieved_at=? AND payload_sha256=?
                """, (record.record_key, record.source_id, retrieved_at, payload_hash)).fetchone()
                return int(row["id"])
            return int(cur.lastrowid)

    def summary(self) -> dict[str, Any]:
        """Summarize persisted coverage and timestamps without exposing price payloads."""
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT source_id, market, data_kind,
                       COUNT(*) AS stored_versions,
                       COUNT(DISTINCT record_key) AS distinct_records,
                       MIN(observed_at) AS first_observed_at,
                       MAX(observed_at) AS latest_observed_at,
                       MIN(retrieved_at) AS first_retrieved_at,
                       MAX(retrieved_at) AS latest_retrieved_at,
                       MAX(published_at) AS latest_published_at
                FROM temporal_records
                GROUP BY source_id, market, data_kind
                ORDER BY source_id, market, data_kind
            """).fetchall()
            total = conn.execute(
                "SELECT COUNT(*) AS count FROM temporal_records"
            ).fetchone()["count"]
        return {
            "record_versions": int(total),
            "series": [
                {
                    "source_id": row["source_id"],
                    "market": row["market"],
                    "data_kind": row["data_kind"],
                    "stored_versions": int(row["stored_versions"]),
                    "distinct_records": int(row["distinct_records"]),
                    "first_observed_at": row["first_observed_at"],
                    "latest_observed_at": row["latest_observed_at"],
                    "first_retrieved_at": row["first_retrieved_at"],
                    "latest_retrieved_at": row["latest_retrieved_at"],
                    "latest_published_at": row["latest_published_at"],
                }
                for row in rows
            ],
        }

    def as_of(
        self,
        *,
        as_of: datetime,
        market: str | None = None,
        data_kind: str | None = None,
        availability_basis: str = "captured",
    ) -> list[dict[str, Any]]:
        """Return latest version available at a cutoff.

        captured reproduces what this system had ingested by the cutoff.
        source replays historical publisher vintages downloaded later and
        therefore requires a trustworthy published_at timestamp.
        """
        if availability_basis not in {"captured", "source"}:
            raise ValueError("availability_basis must be 'captured' or 'source'")
        cutoff = _utc_iso(as_of)
        if availability_basis == "captured":
            filters = ["retrieved_at <= ?", "(published_at IS NULL OR published_at <= ?)"]
            params: list[Any] = [cutoff, cutoff]
            revision_order = "retrieved_at DESC, id DESC"
        else:
            filters = ["published_at IS NOT NULL", "published_at <= ?"]
            params = [cutoff]
            revision_order = "published_at DESC, retrieved_at DESC, id DESC"
        if market is not None:
            filters.append("market = ?")
            params.append(market)
        if data_kind is not None:
            filters.append("data_kind = ?")
            params.append(data_kind)
        where = " AND ".join(filters)
        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT * FROM (
                    SELECT temporal_records.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY record_key, source_id
                            ORDER BY {revision_order}
                        ) AS revision_rank
                    FROM temporal_records
                    WHERE {where}
                ) ranked
                WHERE revision_rank = 1
                ORDER BY observed_at, record_key, source_id
            """, params).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append({
                "id": row["id"],
                "record_key": row["record_key"],
                "source_id": row["source_id"],
                "market": row["market"],
                "data_kind": row["data_kind"],
                "observed_at": row["observed_at"],
                "published_at": row["published_at"],
                "retrieved_at": row["retrieved_at"],
                "source_revision": row["source_revision"],
                "payload": json.loads(row["payload_json"]),
                "payload_sha256": row["payload_sha256"],
            })
        return result
