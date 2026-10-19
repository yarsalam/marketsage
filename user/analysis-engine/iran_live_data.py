"""Persistent, opt-in Tindex ingestion for the Iranian-market dashboard.

Raw payloads and normalized observations are stored separately. Provider-reported
rates retain unknown units/market definitions and are never eligible for scoring
until legal, semantic, and historical acceptance gates are explicitly satisfied.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tindex_normalizer import normalize_currency_rates
from tindex_provider import SOURCE_ID, TindexClient, tindex_connection_status


DEFAULT_DB_PATH = "/data/iran-market.sqlite3"


def _db_path() -> Path:
    return Path(os.getenv("IRAN_DATA_DB_PATH", DEFAULT_DB_PATH))


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS iran_source_refreshes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            status TEXT NOT NULL,
            payload_sha256 TEXT,
            item_count INTEGER NOT NULL DEFAULT 0,
            error_code TEXT
        );
        CREATE TABLE IF NOT EXISTS iran_raw_payloads (
            refresh_id INTEGER PRIMARY KEY REFERENCES iran_source_refreshes(id),
            payload_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS iran_currency_observations (
            refresh_id INTEGER NOT NULL REFERENCES iran_source_refreshes(id),
            source_id TEXT NOT NULL,
            instrument_key TEXT NOT NULL,
            display_name TEXT NOT NULL,
            raw_rate TEXT NOT NULL,
            provider_decimals INTEGER NOT NULL,
            unit TEXT,
            market_definition TEXT,
            observed_at TEXT,
            retrieved_at TEXT NOT NULL,
            eligible_for_scoring INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (refresh_id, instrument_key)
        );
        """
    )
    connection.commit()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def refresh_tindex_currency_rates() -> dict[str, Any]:
    """Fetch one explicitly requested endpoint and persist raw plus normalized data."""
    retrieved_at = _utc_now()
    try:
        with TindexClient() as client:
            payload = client.currency_rates()
        normalized = normalize_currency_rates(payload)
    except Exception as exc:
        # Persist a sanitized failure event; never store exception text or credentials.
        with _connect() as db:
            db.execute(
                """INSERT INTO iran_source_refreshes
                   (source_id, retrieved_at, status, error_code)
                   VALUES (?, ?, 'error', ?)""",
                (SOURCE_ID, retrieved_at, type(exc).__name__[:80]),
            )
        raise

    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    checksum = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    with _connect() as db:
        cursor = db.execute(
            """INSERT INTO iran_source_refreshes
               (source_id, retrieved_at, status, payload_sha256, item_count)
               VALUES (?, ?, 'success', ?, ?)""",
            (SOURCE_ID, retrieved_at, checksum, len(normalized)),
        )
        refresh_id = int(cursor.lastrowid)
        db.execute(
            "INSERT INTO iran_raw_payloads (refresh_id, payload_json) VALUES (?, ?)",
            (refresh_id, payload_json),
        )
        for row in normalized:
            db.execute(
                """INSERT INTO iran_currency_observations
                   (refresh_id, source_id, instrument_key, display_name, raw_rate,
                    provider_decimals, unit, market_definition, observed_at,
                    retrieved_at, eligible_for_scoring)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    refresh_id, row["source_id"], row["instrument_key"],
                    row["display_name"], str(row["raw_rate"]),
                    row["provider_decimals"], row["unit"], row["market_definition"],
                    row["observed_at"], retrieved_at,
                ),
            )
    return {
        "status": "success",
        "source_id": SOURCE_ID,
        "retrieved_at": retrieved_at,
        "item_count": len(normalized),
        "payload_sha256": checksum,
        "eligible_for_scoring": False,
        "message": "Fetched and stored. Units, market definitions, and commercial use are not yet approved.",
    }


def get_iran_data_status() -> dict[str, Any]:
    """Return safe configuration and persisted coverage metadata."""
    status = tindex_connection_status()
    try:
        with _connect() as db:
            latest = db.execute(
                """SELECT id, retrieved_at, status, payload_sha256, item_count, error_code
                   FROM iran_source_refreshes WHERE source_id = ?
                   ORDER BY id DESC LIMIT 1""",
                (SOURCE_ID,),
            ).fetchone()
            total = db.execute(
                "SELECT COUNT(*) AS n FROM iran_source_refreshes WHERE source_id = ?",
                (SOURCE_ID,),
            ).fetchone()["n"]
            count = db.execute(
                "SELECT COUNT(*) AS n FROM iran_currency_observations",
            ).fetchone()["n"]
            successful = db.execute(
                "SELECT 1 FROM iran_source_refreshes WHERE source_id = ? AND status = 'success' LIMIT 1",
                (SOURCE_ID,),
            ).fetchone()
    except Exception:
        latest, total, count, successful = None, 0, 0, None
    return {
        "source_id": SOURCE_ID,
        "provider": "Tindex",
        "configured": status["configured"],
        "refresh_enabled": bool(os.getenv("IRAN_REFRESH_TOKEN", "").strip()),
        "public_display_enabled": os.getenv("TINDEX_PUBLIC_DISPLAY_ENABLED", "false").strip().lower() == "true",
        "network_tested": bool(successful),
        "production_approved": False,
        "eligible_for_scoring": False,
        "stored_observation_count": int(count),
        "refresh_attempt_count": int(total),
        "latest_refresh": dict(latest) if latest else None,
        "storage": "SQLite; raw provider payload and normalized rows retained separately",
        "notes": [
            "A refresh is manual and makes one provider request.",
            "Rate units, market definition, observation timestamp, history depth, and redistribution rights are not inferred.",
            "No rates from this source enter opportunity scoring until source acceptance is completed.",
            "Public display is disabled by default and requires explicit Tindex contract approval.",
        ],
    }


def get_latest_currency_rates() -> dict[str, Any]:
    """Return latest permitted display data without inventing semantics."""
    display_enabled = os.getenv("TINDEX_PUBLIC_DISPLAY_ENABLED", "false").strip().lower() == "true"
    with _connect() as db:
        latest_attempt = db.execute(
            """SELECT id, retrieved_at, status, payload_sha256, item_count, error_code
               FROM iran_source_refreshes WHERE source_id = ?
               ORDER BY id DESC LIMIT 1""",
            (SOURCE_ID,),
        ).fetchone()
        refresh = db.execute(
            """SELECT id, retrieved_at, status, payload_sha256, item_count, error_code
               FROM iran_source_refreshes WHERE source_id = ? AND status = 'success'
               ORDER BY id DESC LIMIT 1""",
            (SOURCE_ID,),
        ).fetchone()
        if not display_enabled:
            return {
                "source_id": SOURCE_ID,
                "status": "public_display_disabled",
                "latest_refresh": dict(refresh) if refresh else None,
                "latest_attempt": dict(latest_attempt) if latest_attempt else None,
                "rates": [],
                "eligible_for_scoring": False,
                "notice": "Public display is disabled until the provider contract explicitly permits it.",
            }
        if not refresh:
            return {
                "source_id": SOURCE_ID,
                "status": "no_successful_refresh",
                "latest_refresh": None,
                "latest_attempt": dict(latest_attempt) if latest_attempt else None,
                "rates": [],
                "eligible_for_scoring": False,
            }
        rows = db.execute(
            """SELECT instrument_key, display_name, raw_rate, provider_decimals,
                      unit, market_definition, observed_at, retrieved_at,
                      eligible_for_scoring
               FROM iran_currency_observations WHERE refresh_id = ?
               ORDER BY instrument_key""",
            (refresh["id"],),
        ).fetchall()
    return {
        "source_id": SOURCE_ID,
        "status": "data_available",
        "latest_refresh": dict(refresh),
        "latest_attempt": dict(latest_attempt) if latest_attempt else None,
        "rates": [
            {**dict(row), "eligible_for_scoring": bool(row["eligible_for_scoring"])}
            for row in rows
        ],
        "eligible_for_scoring": False,
        "notice": "raw_rate is the provider-reported number; its currency unit and market definition are not confirmed.",
    }


def get_iran_opportunities() -> dict[str, Any]:
    """Fail-closed opportunity contract until comparable approved series exist."""
    status = get_iran_data_status()
    return {
        "market_scope": "iran",
        "status": "blocked_insufficient_approved_data",
        "generated_at": _utc_now(),
        "opportunities": [],
        "eligible_sources": [],
        "blocked_reasons": [
            "No Iranian source is currently approved for production scoring.",
            "The available Tindex currency-rate endpoint is a quote snapshot, not comparable historical total-return series.",
            "Currency units, market definitions, publication/observation times, and commercial redistribution rights are not fully verified.",
        ],
        "source_status": status,
        "message": "No ranking is published until the required source and data-quality gates pass.",
    }
