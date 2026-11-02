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
import threading
import time
from contextlib import contextmanager
from typing import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tindex_normalizer import normalize_currency_rates, normalize_indicator_candles
from tindex_provider import SOURCE_ID, TindexClient, TindexRateLimitError, tindex_connection_status


DEFAULT_DB_PATH = "/data/iran-market.sqlite3"
_MIN_REFRESH_INTERVAL_SECONDS = 60
_refresh_slot_lock = threading.Lock()
_last_refresh_monotonic = 0.0


def _reserve_refresh_slot() -> None:
    """Apply a process-wide cooldown across newly constructed API clients."""
    global _last_refresh_monotonic
    with _refresh_slot_lock:
        now = time.monotonic()
        if _last_refresh_monotonic and now - _last_refresh_monotonic < _MIN_REFRESH_INTERVAL_SECONDS:
            raise TindexRateLimitError("Local source refresh cooldown active; wait at least 60 seconds.")
        _last_refresh_monotonic = now


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
        CREATE TABLE IF NOT EXISTS iran_candle_refresh_metadata (
            refresh_id INTEGER PRIMARY KEY REFERENCES iran_source_refreshes(id),
            instrument_key TEXT NOT NULL,
            requested_range TEXT NOT NULL,
            requested_interval TEXT NOT NULL,
            response_slug TEXT
        );
        CREATE TABLE IF NOT EXISTS iran_candle_observations (
            refresh_id INTEGER NOT NULL REFERENCES iran_source_refreshes(id),
            source_id TEXT NOT NULL,
            instrument_key TEXT NOT NULL,
            observation_date TEXT NOT NULL,
            open_raw TEXT NOT NULL,
            high_raw TEXT NOT NULL,
            low_raw TEXT NOT NULL,
            close_raw TEXT NOT NULL,
            unit TEXT,
            partial INTEGER NOT NULL DEFAULT 0,
            provider_source TEXT,
            requested_range TEXT NOT NULL,
            requested_interval TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            eligible_for_scoring INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (refresh_id, instrument_key, observation_date)
        );
        CREATE INDEX IF NOT EXISTS idx_iran_candle_observations_lookup
            ON iran_candle_observations (instrument_key, observation_date, refresh_id);
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
    _reserve_refresh_slot()
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



def refresh_tindex_indicator_candles(
    slug: str,
    *,
    requested_range: str = "3m",
    interval: str = "daily",
) -> dict[str, Any]:
    """Fetch one Tindex candle range and persist it as non-scoreable candidate data.

    This function deliberately handles one slug per invocation to respect the
    existing local cooldown. Tindex documents candle history as capped at 100 days.
    Publication timestamps are not invented; the decoded date is stored separately.
    """
    clean_slug = slug.strip() if isinstance(slug, str) else ""
    if not clean_slug or len(clean_slug) > 100 or any(
        not (char.isalnum() or char in "._-") for char in clean_slug
    ):
        raise ValueError("slug must be a single safe Tindex indicator slug")
    if requested_range not in ("1m", "3m"):
        raise ValueError("requested_range must be one of: 1m, 3m")
    if interval not in ("daily", "weekly"):
        raise ValueError("interval must be one of: daily, weekly")

    _reserve_refresh_slot()
    retrieved_at = _utc_now()
    try:
        with TindexClient() as client:
            payload = client.indicator_candles(
                clean_slug, range=requested_range, interval=interval
            )
        normalized = normalize_indicator_candles(payload)
        normalized_slug = normalized[0]["instrument_key"]
        if normalized_slug.casefold() != clean_slug.casefold():
            raise ValueError("provider response slug does not match requested slug")
        returned_range = normalized[0]["requested_range"]
        returned_interval = normalized[0]["interval"]
        if returned_range != requested_range:
            raise ValueError(
                f"provider returned range {returned_range!r}; requested {requested_range!r}"
            )
        if returned_interval != interval:
            raise ValueError(
                f"provider returned interval {returned_interval!r}; requested {interval!r}"
            )
    except Exception as exc:
        with _connect() as db:
            cursor = db.execute(
                """INSERT INTO iran_source_refreshes
                   (source_id, retrieved_at, status, error_code)
                   VALUES (?, ?, 'error', ?)""",
                (SOURCE_ID, retrieved_at, type(exc).__name__[:80]),
            )
            refresh_id = int(cursor.lastrowid)
            db.execute(
                """INSERT INTO iran_candle_refresh_metadata
                   (refresh_id, instrument_key, requested_range, requested_interval, response_slug)
                   VALUES (?, ?, ?, ?, NULL)""",
                (refresh_id, clean_slug, requested_range, interval),
            )
        raise

    payload_json = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
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
        db.execute(
            """INSERT INTO iran_candle_refresh_metadata
               (refresh_id, instrument_key, requested_range, requested_interval, response_slug)
               VALUES (?, ?, ?, ?, ?)""",
            (refresh_id, clean_slug, requested_range, interval, normalized_slug),
        )
        for row in normalized:
            db.execute(
                """INSERT INTO iran_candle_observations
                   (refresh_id, source_id, instrument_key, observation_date,
                    open_raw, high_raw, low_raw, close_raw, unit, partial,
                    provider_source, requested_range, requested_interval,
                    retrieved_at, eligible_for_scoring)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    refresh_id, SOURCE_ID, row["instrument_key"], row["observation_date"],
                    str(row["open"]), str(row["high"]), str(row["low"]), str(row["close"]),
                    row["unit"], int(row["partial"]), row["provider_source"],
                    requested_range, interval, retrieved_at,
                ),
            )
    return {
        "status": "success",
        "source_id": SOURCE_ID,
        "instrument_key": clean_slug,
        "requested_range": requested_range,
        "interval": interval,
        "retrieved_at": retrieved_at,
        "observation_count": len(normalized),
        "first_observation_date": normalized[0]["observation_date"],
        "last_observation_date": normalized[-1]["observation_date"],
        "partial_candle_count": sum(row["partial"] for row in normalized),
        "provider_units": sorted({row["unit"] for row in normalized if row["unit"]}),
        "payload_sha256": checksum,
        "publication_time_known": False,
        "eligible_for_scoring": False,
        "message": "Candles stored as candidate history only; provider unit, venue, rights, timing and independent reconciliation still require approval.",
    }


def get_candidate_indicator_candles(slug: str) -> dict[str, Any]:
    """Read the latest successful Tindex history snapshot for internal candidate use.

    This helper is not a public-display endpoint and returns no scoring approval.
    """
    clean_slug = slug.strip() if isinstance(slug, str) else ""
    if not clean_slug or len(clean_slug) > 100 or any(
        not (char.isalnum() or char in "._-") for char in clean_slug
    ):
        raise ValueError("slug must be a single safe Tindex indicator slug")
    with _connect() as db:
        latest_attempt = db.execute(
            """SELECT r.id, r.retrieved_at, r.status, r.payload_sha256,
                      r.item_count, r.error_code, m.requested_range, m.requested_interval
               FROM iran_candle_refresh_metadata m
               JOIN iran_source_refreshes r ON r.id = m.refresh_id
               WHERE r.source_id = ? AND m.instrument_key = ?
               ORDER BY r.id DESC LIMIT 1""",
            (SOURCE_ID, clean_slug),
        ).fetchone()
        latest_success = db.execute(
            """SELECT r.id, r.retrieved_at, r.status, r.payload_sha256,
                      r.item_count, r.error_code, m.requested_range, m.requested_interval
               FROM iran_candle_refresh_metadata m
               JOIN iran_source_refreshes r ON r.id = m.refresh_id
               WHERE r.source_id = ? AND m.instrument_key = ? AND r.status = 'success'
               ORDER BY r.id DESC LIMIT 1""",
            (SOURCE_ID, clean_slug),
        ).fetchone()
        if not latest_success:
            return {
                "source_id": SOURCE_ID,
                "instrument_key": clean_slug,
                "status": "no_successful_history_refresh",
                "latest_attempt": dict(latest_attempt) if latest_attempt else None,
                "candles": [],
                "eligible_for_scoring": False,
            }
        rows = db.execute(
            """SELECT observation_date, open_raw, high_raw, low_raw, close_raw,
                      unit, partial, provider_source, requested_range,
                      requested_interval, retrieved_at
               FROM iran_candle_observations
               WHERE refresh_id = ? ORDER BY observation_date""",
            (latest_success["id"],),
        ).fetchall()
    return {
        "source_id": SOURCE_ID,
        "instrument_key": clean_slug,
        "status": "candidate_history_available",
        "latest_successful_refresh": dict(latest_success),
        "latest_attempt": dict(latest_attempt) if latest_attempt else None,
        "candles": [
            {
                **dict(row),
                "partial": bool(row["partial"]),
                "eligible_for_scoring": False,
                "observation_precision": "day",
                "source_publication_time": None,
            }
            for row in rows
        ],
        "eligible_for_scoring": False,
        "notice": "Internal candidate data only. Historical ranges are provider-capped and must not be treated as total-return series without instrument-specific reconciliation.",
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
            candle_count = db.execute(
                "SELECT COUNT(*) AS n FROM iran_candle_observations",
            ).fetchone()["n"]
            candle_refreshes = db.execute(
                "SELECT COUNT(*) AS n FROM iran_candle_refresh_metadata",
            ).fetchone()["n"]
            successful = db.execute(
                "SELECT 1 FROM iran_source_refreshes WHERE source_id = ? AND status = 'success' LIMIT 1",
                (SOURCE_ID,),
            ).fetchone()
    except Exception:
        latest, total, count, successful = None, 0, 0, None
        candle_count, candle_refreshes = 0, 0
    return {
        "source_id": SOURCE_ID,
        "provider": "Tindex",
        "configured": status["configured"],
        "refresh_enabled": bool(os.getenv("IRAN_REFRESH_TOKEN", "").strip()),
        "auto_refresh_enabled": os.getenv("IRAN_DATA_AUTO_REFRESH_ENABLED", "false").strip().lower() == "true",
        "public_display_enabled": os.getenv("TINDEX_PUBLIC_DISPLAY_ENABLED", "false").strip().lower() == "true",
        "network_tested": bool(successful),
        "production_approved": False,
        "eligible_for_scoring": False,
        "stored_observation_count": int(count),
        "stored_candle_observation_count": int(candle_count),
        "candle_refresh_attempt_count": int(candle_refreshes),
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
            "The Tindex candle endpoint is capped at recent history (up to 100 days) and is not a long-horizon total-return history.",
            "Currency/price units must be taken from each provider response and independently reconciled; market definitions, publication times, and commercial redistribution rights are not fully verified.",
        ],
        "source_status": status,
        "message": "No ranking is published until the required source and data-quality gates pass.",
    }
