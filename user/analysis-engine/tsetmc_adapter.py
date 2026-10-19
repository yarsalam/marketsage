"""Candidate-only TSETMC ingestion with a provider-supplied adjusted-price path.

The endpoints are reverse-engineered and access/terms are not verified. Raw daily
history remains available for audit, but adjusted ingestion never falls back to raw
prices for dates missing from the legacy adjusted chart.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, time, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from temporal_data import PointInTimeStore, TemporalRecord

SOURCE_ID = "iran.tsetmc"
HISTORY_URL = "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{ins_code}/0"
CHART_URL = "https://members.tsetmc.com/tsev2/chart/data/Financial.aspx"
TEHRAN = ZoneInfo("Asia/Tehran")
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
CHART_FIELD_MAPPING = {
    "date": 0,
    "high_adj": 1,
    "low_adj": 2,
    "open_adj": 3,
    "last_adj": 4,
    "chart_volume": 5,
    "close_adj": 6,
}


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


def _nonnegative_finite_number(value: Any, field: str, row_index: int) -> float:
    if isinstance(value, bool):
        raise TSETMCDataError(f"row {row_index}: {field} must be finite and non-negative")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise TSETMCDataError(f"row {row_index}: {field} must be finite and non-negative") from exc
    if not math.isfinite(number) or number < 0:
        raise TSETMCDataError(f"row {row_index}: {field} must be finite and non-negative")
    return number


def parse_daily_history(
    payload: dict[str, Any],
    *,
    ins_code: str,
    retrieved_at: datetime,
) -> list[TemporalRecord]:
    """Parse raw daily history into quarantined records for audit."""
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
        try:
            day = datetime.strptime(str(row.get("dEven")), "%Y%m%d").date()
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
            return _nonnegative_finite_number(value, field, index)

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
            "normalization_status": "candidate_quarantined_raw_history",
            "eligible_for_scoring": False,
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


def parse_adjusted_chart(payload: Any) -> dict[str, dict[str, float]]:
    """Parse the legacy a=1 chart, preserving its empirical positional mapping.

    Positional meaning is inferred from comparing a=0 chart rows to raw daily
    history. It is not an official schema contract and records remain quarantined.
    Accepts either the raw delimited response text or the date -> array JSON object
    saved by validate_tsetmc_adjustments.py.
    """
    rows: list[tuple[str, Any]] = []
    if isinstance(payload, str):
        for item in payload.strip().split(";"):
            if not item.strip():
                continue
            fields = [part.strip() for part in item.split(",")]
            if not fields or not fields[0]:
                continue
            rows.append((fields[0], fields))
    elif isinstance(payload, dict):
        rows = [(str(key), value) for key, value in payload.items()]
    else:
        raise TSETMCDataError("adjusted chart must be delimited text or a date-to-array object")

    parsed: dict[str, dict[str, float]] = {}
    for index, (key, values) in enumerate(rows):
        date_text = str(key).strip()
        if len(date_text) != 8 or not date_text.isdigit():
            date_text = str(values[0]).strip() if isinstance(values, (list, tuple)) and values else ""
        try:
            datetime.strptime(date_text, "%Y%m%d")
        except ValueError as exc:
            raise TSETMCDataError(f"chart row {index}: invalid date") from exc
        if date_text in parsed:
            raise TSETMCDataError(f"chart row {index}: duplicate date {date_text}")

        # Live fetches are normalized before they are joined; saved probe files
        # contain raw positional arrays. Accept both representations explicitly.
        if isinstance(values, dict):
            required = {"high_adj", "low_adj", "open_adj", "last_adj", "chart_volume", "close_adj"}
            if not required.issubset(values):
                raise TSETMCDataError(f"chart row {index}: normalized chart fields are incomplete")
            parsed[date_text] = {
                "high_adj": _positive_finite_number(values["high_adj"], "chart high_adj", index),
                "low_adj": _positive_finite_number(values["low_adj"], "chart low_adj", index),
                "open_adj": _positive_finite_number(values["open_adj"], "chart open_adj", index),
                "last_adj": _positive_finite_number(values["last_adj"], "chart last_adj", index),
                "chart_volume": _nonnegative_finite_number(values["chart_volume"], "chart volume", index),
                "close_adj": _positive_finite_number(values["close_adj"], "chart close_adj", index),
            }
            continue

        if not isinstance(values, (list, tuple)) or len(values) < 7:
            raise TSETMCDataError(f"chart row {index}: expected at least seven positional fields")
        value_date = str(values[0]).strip()
        if value_date and value_date != date_text:
            raise TSETMCDataError(f"chart row {index}: date key and first field disagree")
        parsed[date_text] = {
            "high_adj": _positive_finite_number(values[1], "chart high_adj", index),
            "low_adj": _positive_finite_number(values[2], "chart low_adj", index),
            "open_adj": _positive_finite_number(values[3], "chart open_adj", index),
            "last_adj": _positive_finite_number(values[4], "chart last_adj", index),
            "chart_volume": _nonnegative_finite_number(values[5], "chart volume", index),
            "close_adj": _positive_finite_number(values[6], "chart close_adj", index),
        }
    if not parsed:
        raise TSETMCDataError("adjusted chart returned no usable rows")
    return parsed


def parse_adjusted_history(
    daily_payload: dict[str, Any],
    chart_payload: Any,
    *,
    ins_code: str,
    retrieved_at: datetime,
    daily_response_sha256: str | None = None,
    chart_response_sha256: str | None = None,
) -> list[TemporalRecord]:
    """Create adjusted-price candidates by joining daily history to TSETMC a=1.

    Raw daily prices are retained under raw_* keys. The canonical close_candidate
    is taken only from the adjusted chart; when a chart date is absent it is None,
    never silently replaced with the raw close. Price units, original publication
    time and the chart schema remain unverified.
    """
    chart_rows = parse_adjusted_chart(chart_payload)
    raw_records = parse_daily_history(
        daily_payload, ins_code=ins_code, retrieved_at=retrieved_at
    )
    daily_canonical = json.dumps(
        daily_payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    daily_hash = daily_response_sha256 or hashlib.sha256(
        daily_canonical.encode("utf-8")
    ).hexdigest()
    chart_canonical = json.dumps(
        chart_rows, sort_keys=True, separators=(",", ":")
    )
    chart_hash = chart_response_sha256 or hashlib.sha256(
        chart_canonical.encode("utf-8")
    ).hexdigest()
    combined_hash = hashlib.sha256(
        f"daily:{daily_hash}|adjusted_chart:{chart_hash}".encode("utf-8")
    ).hexdigest()

    records: list[TemporalRecord] = []
    for raw_record in raw_records:
        raw = raw_record.payload
        chart = chart_rows.get(raw["observation_date"].replace("-", ""))
        adjusted_payload = {
            "instrument_code": ins_code,
            "observation_date": raw["observation_date"],
            "close_candidate": chart["close_adj"] if chart else None,
            "last_trade_candidate": chart["last_adj"] if chart else None,
            "open_candidate": chart["open_adj"] if chart else None,
            "high_candidate": chart["high_adj"] if chart else None,
            "low_candidate": chart["low_adj"] if chart else None,
            "previous_close_candidate": None,
            "volume_candidate": raw["volume_candidate"],
            "chart_volume_candidate": chart["chart_volume"] if chart else None,
            "trade_count_candidate": raw["trade_count_candidate"],
            "turnover_candidate": raw["turnover_candidate"],
            "raw_close_candidate": raw["close_candidate"],
            "raw_last_trade_candidate": raw["last_trade_candidate"],
            "raw_open_candidate": raw["open_candidate"],
            "raw_high_candidate": raw["high_candidate"],
            "raw_low_candidate": raw["low_candidate"],
            "raw_previous_close_candidate": raw["previous_close_candidate"],
            "price_unit": "rial_candidate_unverified",
            "adjustment_source": "tsetmc_legacy_chart_a1",
            "adjustment_status": (
                "provider_supplied_unvalidated" if chart
                else "missing_adjusted_chart_row"
            ),
            "adjusted_chart_row_present": chart is not None,
            "chart_field_mapping_zero_based": CHART_FIELD_MAPPING,
            "daily_response_sha256": daily_hash,
            "adjusted_chart_response_sha256": chart_hash,
            "source_response_sha256": combined_hash,
            "source_publication_time": "unknown",
            "normalization_status": "candidate_quarantined_adjusted_series",
            "eligible_for_scoring": False,
        }
        records.append(TemporalRecord(
            record_key=f"{ins_code}:{raw['observation_date']}:adjusted",
            source_id=SOURCE_ID,
            market="iran_candidate",
            data_kind="daily_ohlcv_adjusted_candidate",
            observed_at=raw_record.observed_at,
            retrieved_at=raw_record.retrieved_at,
            published_at=None,
            source_revision=combined_hash,
            payload=adjusted_payload,
        ))
    return records


def fetch_daily_history(ins_code: str, *, timeout: float = 20.0) -> tuple[dict[str, Any], str]:
    """Fetch one instrument's raw history; callers must honor access terms and back off on blocks."""
    if not ins_code.isdigit() or not (10 <= len(ins_code) <= 22):
        raise TSETMCDataError("ins_code must be a numeric TSETMC instrument identifier")
    request = Request(
        HISTORY_URL.format(ins_code=ins_code),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise TSETMCDataError(f"TSETMC daily-history request failed ({type(exc).__name__}); no data ingested") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TSETMCDataError("TSETMC daily history returned non-JSON content; possible block or schema change") from exc
    if not isinstance(payload, dict):
        raise TSETMCDataError("TSETMC daily-history response must be a JSON object")
    return payload, hashlib.sha256(raw).hexdigest()


def fetch_adjusted_chart(ins_code: str, *, timeout: float = 20.0) -> tuple[dict[str, dict[str, float]], str]:
    """Fetch and parse the legacy adjusted chart (a=1) without falling back to raw prices."""
    if not ins_code.isdigit() or not (10 <= len(ins_code) <= 22):
        raise TSETMCDataError("ins_code must be a numeric TSETMC instrument identifier")
    url = CHART_URL + "?" + urlencode({"i": ins_code, "t": "ph", "a": "1"})
    request = Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain, */*"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise TSETMCDataError(f"TSETMC adjusted-chart request failed ({type(exc).__name__}); no data ingested") from exc
    try:
        body = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TSETMCDataError("TSETMC adjusted chart was not UTF-8 text") from exc
    return parse_adjusted_chart(body), hashlib.sha256(raw).hexdigest()


def ingest_daily_history(
    store: PointInTimeStore,
    ins_code: str,
    *,
    retrieved_at: datetime | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Explicit opt-in raw-history capture for reconciliation only; never score-ready."""
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
        "reason": "raw history is retained for reconciliation only; adjusted data and access terms remain unverified",
    }


def ingest_adjusted_history(
    store: PointInTimeStore,
    ins_code: str,
    *,
    retrieved_at: datetime | None = None,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Capture raw history plus provider-adjusted chart rows into a distinct quarantined series.

    Both requests and normalization complete before any records are appended. If
    either endpoint fails or the chart schema changes, no partial series is stored.
    Missing adjusted dates are represented explicitly and never filled from raw prices.
    """
    daily_payload, daily_sha256 = fetch_daily_history(ins_code, timeout=timeout)
    chart_rows, chart_sha256 = fetch_adjusted_chart(ins_code, timeout=timeout)
    captured_at = retrieved_at or datetime.now(timezone.utc)
    records = parse_adjusted_history(
        daily_payload,
        chart_rows,
        ins_code=ins_code,
        retrieved_at=captured_at,
        daily_response_sha256=daily_sha256,
        chart_response_sha256=chart_sha256,
    )
    ids = [store.append(record) for record in records]
    covered = sum(record.payload["close_candidate"] is not None for record in records)
    return {
        "source_id": SOURCE_ID,
        "instrument_code": ins_code,
        "series_data_kind": "daily_ohlcv_adjusted_candidate",
        "ingested_records": len(ids),
        "rows_with_adjusted_close": covered,
        "rows_missing_adjusted_close": len(records) - covered,
        "daily_response_sha256": daily_sha256,
        "adjusted_chart_response_sha256": chart_sha256,
        "publication_time_known": False,
        "eligible_for_production_scoring": False,
        "adjustment_status": "provider_supplied_unvalidated",
        "reason": "adjusted chart is retained as a candidate; units, chart schema, history and rights remain unverified",
    }
