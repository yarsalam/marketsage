"""FRED/ALFRED vintage adapter for point-in-time macro research.

Requires a FRED API key in FRED_API_KEY. ALFRED vintage dates are day-level,
not exact intraday publication times; this adapter conservatively treats each
vintage as available at 23:59:59 UTC on that date.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, time, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from temporal_data import PointInTimeStore, TemporalRecord

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"


def _date_utc(value: str) -> datetime:
    return datetime.combine(date.fromisoformat(value), time.min, tzinfo=timezone.utc)


def records_from_fred_vintages(
    series_id: str,
    observations: list[dict[str, Any]],
    *,
    retrieved_at: datetime,
    units: str | None = None,
) -> list[TemporalRecord]:
    """Convert FRED output_type=4 rows into immutable vintage records."""
    if not series_id.strip():
        raise ValueError("series_id must be non-empty")
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")

    records: list[TemporalRecord] = []
    for row in observations:
        observation_date = row.get("date")
        vintage_date = row.get("realtime_start") or row.get("vintage_date")
        value = row.get("value")
        if not observation_date or not vintage_date or value in (None, "", "."):
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue
        if numeric_value != numeric_value or numeric_value in (float("inf"), float("-inf")):
            continue
        # ALFRED gives a vintage date, not a trustworthy intraday release time.
        # End-of-day UTC avoids making the value available too early that day.
        published_at = datetime.combine(
            date.fromisoformat(vintage_date), time(23, 59, 59), tzinfo=timezone.utc
        )
        records.append(TemporalRecord(
            record_key=f"macro:US:{series_id}:{observation_date}",
            source_id=f"fred:{series_id}",
            market="US",
            data_kind="macro_release",
            observed_at=_date_utc(observation_date),
            published_at=published_at,
            retrieved_at=retrieved_at.astimezone(timezone.utc),
            source_revision=vintage_date,
            payload={
                "provider": "FRED/ALFRED",
                "series_id": series_id,
                "observation_date": observation_date,
                "vintage_date": vintage_date,
                "value": numeric_value,
                "units": units,
            },
        ))
    return records


def fetch_fred_vintages(
    series_id: str,
    *,
    api_key: str | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
    retrieved_at: datetime | None = None,
    timeout: float = 20.0,
) -> list[dict[str, Any]]:
    """Fetch all returned observation vintages; page through the FRED API."""
    key = api_key or os.getenv("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY is required; never commit the key")
    if not series_id.strip():
        raise ValueError("series_id must be non-empty")

    retrieved = retrieved_at or datetime.now(timezone.utc)
    if retrieved.tzinfo is None or retrieved.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")

    all_rows: list[dict[str, Any]] = []
    offset = 0
    limit = 100000
    while True:
        params: dict[str, str | int] = {
            "series_id": series_id,
            "api_key": key,
            "file_type": "json",
            "output_type": 4,
            "sort_order": "asc",
            "limit": limit,
            "offset": offset,
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
        request = Request(
            f"{FRED_OBSERVATIONS_URL}?{urlencode(params)}",
            headers={"User-Agent": "MarketSage/0.1 (point-in-time research)"},
        )
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = payload.get("observations")
        if not isinstance(rows, list):
            raise RuntimeError("FRED response missing observations list")
        all_rows.extend(rows)
        count = int(payload.get("count", len(all_rows)))
        offset += len(rows)
        if not rows or offset >= count:
            break
    return all_rows


def ingest_fred_series(
    store: PointInTimeStore,
    series_id: str,
    *,
    units: str | None = None,
    observation_start: str | None = None,
    observation_end: str | None = None,
    api_key: str | None = None,
    retrieved_at: datetime | None = None,
) -> dict[str, int | str]:
    """Fetch and append vintage records; does not overwrite existing revisions."""
    fetched_at = retrieved_at or datetime.now(timezone.utc)
    rows = fetch_fred_vintages(
        series_id,
        api_key=api_key,
        observation_start=observation_start,
        observation_end=observation_end,
        retrieved_at=fetched_at,
    )
    records = records_from_fred_vintages(
        series_id, rows, retrieved_at=fetched_at, units=units
    )
    inserted_ids = [store.append(record) for record in records]
    return {
        "series_id": series_id,
        "rows_received": len(rows),
        "records_appended_or_existing": len(inserted_ids),
        "min_id": min(inserted_ids) if inserted_ids else 0,
        "max_id": max(inserted_ids) if inserted_ids else 0,
    }
