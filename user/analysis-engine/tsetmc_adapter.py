"""Candidate-only parser/ingestor for TSETMC daily closing-price history.

The endpoint/schema is reverse-engineered and access/terms are not verified. This
module deliberately marks records as candidate data, leaves published_at unknown,
and does not change the production source-scoring approval gate.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, time, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from temporal_data import PointInTimeStore, TemporalRecord

SOURCE_ID = "iran.tsetmc"
HISTORY_URL = "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{ins_code}/0"
TEHRAN = ZoneInfo("Asia/Tehran")
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class TSETMCDataError(ValueError):
    """Raised when a response cannot safely be normalized."""


def _positive_finite_number(value: Any, field: str, row_index: int) -> float:
    if isinstance(value, bool):
        raise TSETMCDataError(f"row {row_index}: {field} must be a finite positive number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TSETMCDataError(f"row {row_index}: {field} must be a finite positive number") from exc
    if not math.isfinite(number) or number <= 0:
        raise TSETMCDataError(f"row {row_index}: {field} must be a finite positive number")
    return number


def parse_daily_history(
    payload: dict[str, Any],
    *,
    ins_code: str,
    retrieved_at: datetime,
) -> list[TemporalRecord]:
    """Parse the candidate JSON response into quarantined point-in-time records.

    The observation date is not proof of when the provider originally published
    the row. Price units are recorded as a candidate Rial convention and remain
    unverified until independently reconciled.
    """
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise TSETMCDataError("retrieved_at must be timezone-aware")
    if not ins_code.isdigit() or not (10 <= len(ins_code) <= 22):
        raise TSETMCDataError("ins_code must be a numeric TSETMC instrument identifier")

    rows = payload.get("closingPriceDaily")
    if not isinstance(rows, list) or not rows:
        raise TSETMCDataError("response must contain a non-empty closingPriceDaily list")

    canonical_raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    raw_sha256 = hashlib.sha256(canonical_raw.encode("utf-8")).hexdigest()
    records: list[TemporalRecord] = []
    seen_dates: set[date] = set()

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise TSETMCDataError(f"row {index}: expected object")
        raw_date = row.get("dEven")
        try:
            day = datetime.strptime(str(raw_date), "%Y%m%d").date()
        except (TypeError, ValueError) as exc:
            raise TSETMCDataError(f"row {index}: invalid dEven date") from exc
        if day in seen_dates:
            raise TSETMCDataError(f"row {index}: duplicate observation date {day.isoformat()}")
        seen_dates.add(day)

        close = _positive_finite_number(row.get("pClosing"), "pClosing", index)
        last = row.get("pDrCotVal")
        if last is not None:
            last = _positive_finite_number(last, "pDrCotVal", index)

        def optional_nonnegative(field: str) -> float | None:
            value = row.get(field)
            if value is None:
                return None
            if isinstance(value, bool):
                raise TSETMCDataError(f"row {index}: {field} must be non-negative")
            try:
                number = float(value)
            except (TypeError, ValueError) as exc:
                raise TSETMCDataError(f"row {index}: {field} must be non-negative") from exc
            if not math.isfinite(number) or number < 0:
                raise TSETMCDataError(f"row {index}: {field} must be non-negative")
            return number

        observed_at = datetime.combine(day, time(23, 59, 59), tzinfo=TEHRAN)
        payload_record = {
            "instrument_code": ins_code,
            "observation_date": day.isoformat(),
            "close_candidate": close,
            "last_trade_candidate": last,
            "open_candidate": optional_nonnegative("priceFirst"),
            "high_candidate": optional_nonnegative("priceMax"),
            "low_candidate": optional_nonnegative("priceMin"),
            "previous_close_candidate": optional_nonnegative("priceYesterday"),
            "volume_candidate": optional_nonnegative("qTotTran5J"),
            "trade_count_candidate": optional_nonnegative("zTotTran"),
            "turnover_candidate": optional_nonnegative("qTotCap"),
            "price_unit": "rial_candidate_unverified",
            "source_response_sha256": raw_sha256,
            "source_publication_time": "unknown",
            "normalization_status": "candidate_quarantined",
        }
        records.append(TemporalRecord(
            record_key=f"{ins_code}:{day.isoformat()}",
            source_id=SOURCE_ID,
            market="iran_candidate",
            data_kind="daily_ohlcv_candidate",
            observed_at=observed_at,
            retrieved_at=retrieved_at.astimezone(timezone.utc),
            published_at=None,
            source_revision=raw_sha256,
            payload=payload_record,
        ))

    return records


def fetch_daily_history(ins_code: str, *, timeout: float = 20.0) -> tuple[dict[str, Any], str]:
    """Fetch one instrument history; callers must honor access terms and back off on blocks."""
    if not ins_code.isdigit() or not (10 <= len(ins_code) <= 22):
        raise TSETMCDataError("ins_code must be a numeric TSETMC instrument identifier")
    request = Request(
        HISTORY_URL.format(ins_code=ins_code),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TSETMCDataError(f"TSETMC request failed ({type(exc).__name__}); no data ingested") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TSETMCDataError("TSETMC returned non-JSON content; possible block or schema change") from exc
    if not isinstance(payload, dict):
        raise TSETMCDataError("TSETMC response must be a JSON object")
    return payload, hashlib.sha256(raw).hexdigest()


def ingest_daily_history(
    store: PointInTimeStore,
    ins_code: str,
    *,
    retrieved_at: datetime | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Explicit opt-in ingestion; returns counts and never grants scoring approval."""
    payload, raw_sha256 = fetch_daily_history(ins_code, timeout=timeout)
    captured_at = retrieved_at or datetime.now(timezone.utc)
    records = parse_daily_history(payload, ins_code=ins_code, retrieved_at=captured_at)
    ids = [store.append(record) for record in records]
    return {
        "source_id": SOURCE_ID,
        "instrument_code": ins_code,
        "ingested_records": len(ids),
        "raw_response_sha256": raw_sha256,
        "publication_time_known": False,
        "eligible_for_production_scoring": False,
        "reason": "candidate endpoint/access/terms/units/timestamps/history remain unverified",
    }
