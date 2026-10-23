#!/usr/bin/env python3
"""Offline integrated TSETMC corpus acceptance runner.

Reads local JSON/CSV history, adjusted-chart and event payloads; does not collect
from the network, mutate inputs, infer/apply adjustment factors, forward-fill,
or grant production scoring. Outputs are written to a fresh local run directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

VERSION = "1.0.0"
SOURCE_ID = "iran.tsetmc"
DEFAULT_MIN_HISTORY = 252
DEFAULT_MIN_COVERAGE = 0.95
DEFAULT_FACTOR_MIN = 0.05
DEFAULT_FACTOR_MAX = 20.0

MANIFEST_COLUMNS = [
    "instrument_code", "symbol", "isin", "daily_history_path",
    "adjusted_chart_path", "adjustment_events_path", "history_close_semantics", "rights_status",
    "semantics_verified", "independent_reconciliation_passed",
    "corporate_action_completeness_verified", "identity_match_evidence_ref",
    "rights_evidence_ref", "semantics_evidence_ref",
    "independent_reconciliation_evidence_ref",
    "corporate_action_completeness_evidence_ref",
]
DECISION_COLUMNS = [
    "instrument_code", "symbol", "isin", "price_input_semantics", "identity_verified", "decision_status",
    "decision_reason_codes", "input_hashes_json", "history_rows",
    "valid_history_rows", "unique_history_dates", "invalid_date_rows",
    "invalid_or_nonpositive_close_rows", "invalid_numeric_field_rows",
    "duplicate_history_date_rows", "input_order_inversions", "input_order_status",
    "ohlc_violation_rows", "adjusted_ohlc_violation_rows", "first_date", "last_date", "max_calendar_gap_days",
    "adjusted_chart_rows", "adjusted_close_coverage", "factor_ratio_outlier_rows",
    "factor_step_change_count", "event_rows", "event_dates_unrecognized",
    "event_dates_exact_history_match", "event_dates_exact_adjusted_chart_match", "raw_history_preserved",
    "eligible_for_research", "eligible_for_scoring", "eligible_for_backtest",
]
RAW_COLUMNS = [
    "instrument_code", "symbol", "isin", "date", "close_input_candidate", "last_input_candidate",
    "open_input_candidate", "high_input_candidate", "low_input_candidate", "prev_close_input_candidate",
    "volume_input_candidate", "trade_value_input_candidate", "price_input_semantics",
    "source_response_sha256", "normalization_status", "eligible_for_scoring",
]
QUALITY_COLUMNS = [
    "instrument_code", "symbol", "date", "input_close_candidate", "input_open_candidate", "input_high_candidate",
    "input_low_candidate", "input_volume_candidate", "price_input_semantics", "row_status", "reason_codes",
]
ADJUSTED_COLUMNS = [
    "instrument_code", "symbol", "isin", "date", "close_input_candidate", "last_input_candidate",
    "open_input_candidate", "high_input_candidate", "low_input_candidate", "volume_input_candidate", "turnover_input_candidate",
    "price_input_semantics",
    "adjusted_open_candidate", "adjusted_high_candidate",
    "adjusted_low_candidate", "adjusted_last_candidate",
    "adjusted_close_candidate", "adjusted_chart_volume",
    "adjusted_chart_row_present", "adjusted_ohlc_status", "adjusted_ohlc_reason_codes", "adjusted_to_input_close_ratio",
    "adjustment_source", "adjustment_status", "source_response_sha256",
    "eligible_for_scoring",
]
EVENT_COLUMNS = [
    "instrument_code", "symbol", "event_index", "event_date", "date_field",
    "date_parse_status", "history_date_exact_match", "adjusted_chart_date_match",
    "event_type_candidate", "event_source_hash", "decision_note",
]
FACTOR_COLUMNS = [
    "instrument_code", "symbol", "overlap_count", "factor_min",
    "factor_median", "factor_max", "factor_outlier_count",
    "factor_step_change_count", "factor_min_threshold", "factor_max_threshold",
    "interpretation",
]
QUARANTINE_COLUMNS = [
    "instrument_code", "symbol", "stage", "reason_code", "details",
    "input_hashes_json", "required_action", "resolution_status",
]
QUEUE_COLUMNS = [
    "instrument_code", "symbol", "stage", "reason_code", "required_action",
    "attempt_count", "last_attempt_at", "next_retry_after", "input_hash",
    "pipeline_version", "resolution_status",
]
RESEARCH_COLUMNS = [
    "instrument_code", "symbol", "isin", "daily_history_path",
    "adjusted_chart_path", "adjustment_events_path", "history_close_semantics", "first_date", "last_date",
    "history_rows", "adjusted_close_coverage", "input_hashes_json",
    "identity_match_evidence_ref", "rights_evidence_ref", "semantics_evidence_ref",
    "independent_reconciliation_evidence_ref",
    "corporate_action_completeness_evidence_ref", "eligible_for_scoring",
    "eligibility_scope",
]
FEATURE_COLUMNS = [
    "instrument_code", "symbol", "date", "close_adjusted", "return_1d",
    "return_20d", "return_60d", "return_126d", "volatility_20d",
    "drawdown_126d",
]
LABEL_COLUMNS = [
    "instrument_code", "symbol", "decision_date", "target_date",
    "forward_return_6m_pct", "horizon_calendar_days",
]


class PipelineError(ValueError):
    pass


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value: Any) -> date | None:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{8}(?:\.0)?", text):
        try:
            return datetime.strptime(text[:8], "%Y%m%d").date()
        except ValueError:
            return None
    try:
        result = date.fromisoformat(text[:10])
    except ValueError:
        return None
    return result if result.isoformat() == text[:10] else None


def number(value: Any, *, positive: bool = False, nonnegative: bool = False) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result) or (positive and result <= 0) or (nonnegative and result < 0):
        return None
    return result


def field(row: dict[str, Any], *names: str) -> Any:
    return next((row[n] for n in names if n in row and row[n] not in (None, "")), None)


def row_list(payload: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
    rows = payload
    if isinstance(payload, dict):
        rows = next((payload[k] for k in (
            "closingPriceDaily", "dailyHistory", "daily_history", "rows", "data"
        ) if isinstance(payload.get(k), list)), None)
    if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows[:min(3, len(rows))]):
        return None, None
    code_key = next((k for k in (
        "instrument_code", "insCode", "inscode", "instrumentCode", "instrument_id"
    ) if any(k in r for r in rows[:min(20, len(rows))])), None)
    return rows, code_key


def looks_like_history(payload: Any) -> bool:
    rows, _ = row_list(payload)
    return bool(rows and any(
        field(r, "dEven", "date", "observation_date", "Date", "date_key", "DTYYYYMMDD", "<DTYYYYMMDD>") not in (None, "")
        and field(r, "pClosing", "close_raw", "close", "CLOSE", "<CLOSE>", "close_candidate", "adjusted_close_candidate") not in (None, "")
        for r in rows[:20]
    ))


def classify_price_input_semantics(rows: list[dict[str, Any]], declared: Any) -> str:
    """Return a conservative semantics label; structure never proves raw-vs-adjusted."""
    declared_text = str(declared or "").strip().lower().replace("-", "_").replace(" ", "_")
    if declared_text == "raw_unadjusted":
        return "raw_unadjusted"
    if declared_text in {"provider_adjusted", "adjusted"}:
        return "provider_adjusted"
    if declared_text in {"unknown", "unknown_unverified", ""}:
        pass
    # This is diagnostic only: these names hint at a raw TSETMC contract, but do not
    # constitute proof that the stored series is unadjusted.
    sample = rows[: min(20, len(rows))]
    if sample and any("pClosing" in row for row in sample):
        return "tsetmc_pClosing_candidate_unverified"
    return "unknown_unverified"


def read_payload(path: Path) -> Any:
    try:
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                return [dict(r) for r in csv.DictReader(f)]
        raw = path.read_text(encoding="utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            if ";" in raw and "," in raw:
                return raw
            raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PipelineError(f"cannot parse {path.name} ({type(exc).__name__})") from None


def filter_for_instrument(
    payload: Any, code: str, *, index_cache: dict[str, Any] | None = None,
    cache_key: str | None = None,
) -> Any:
    """Select one instrument efficiently; index a combined file only once."""
    if not code:
        return payload
    indexed: dict[str, list[dict[str, Any]]] | None = None
    if index_cache is not None and cache_key is not None:
        if cache_key not in index_cache:
            rows, code_key = row_list(payload)
            if rows is not None and code_key:
                by_code: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in rows:
                    by_code[str(row.get(code_key, "") or "").strip()].append(row)
                index_cache[cache_key] = (code_key, dict(by_code))
            else:
                index_cache[cache_key] = None
        index_entry = index_cache[cache_key]
        if index_entry is not None:
            _, indexed = index_entry
    if indexed is not None:
        selected = indexed.get(code, [])
        if isinstance(payload, list):
            return selected
        if isinstance(payload, dict):
            cloned = dict(payload)
            for key in (
                "closingPriceDaily", "dailyHistory", "daily_history", "rows", "data",
                "priceAdjust", "priceAdjustment", "priceAdjustList", "price_adjustments", "events",
            ):
                if isinstance(cloned.get(key), list):
                    cloned[key] = selected
                    break
            return cloned
    def filtered(rows: Any) -> Any:
        values, code_key = row_list(rows)
        if values is not None and code_key:
            return [r for r in values if str(r.get(code_key, "")).strip() == code]
        return rows
    if isinstance(payload, list):
        return filtered(payload)
    if isinstance(payload, dict):
        cloned = dict(payload)
        for key in (
            "closingPriceDaily", "dailyHistory", "daily_history", "rows", "data",
            "priceAdjust", "priceAdjustment", "priceAdjustList", "price_adjustments", "events",
        ):
            if isinstance(cloned.get(key), list):
                cloned[key] = filtered(cloned[key])
                break
        return cloned
    return payload


def load_manifest(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not {"instrument_code", "symbol", "isin"}.issubset(set(reader.fieldnames or [])):
            raise PipelineError("manifest must contain instrument_code,symbol,isin columns")
        aliases = {
            "daily_history_path": ("daily_history_path", "history_path", "raw_history_path", "daily_json"),
            "adjusted_chart_path": ("adjusted_chart_path", "chart_adjusted_path", "adjusted_history_path", "chart_path"),
            "adjustment_events_path": ("adjustment_events_path", "price_adjustments_path", "events_path", "event_path"),
        }
        result = []
        for row in reader:
            obj = dict(row)
            for target, names in aliases.items():
                obj[target] = next((row.get(n, "") for n in names if row.get(n, "").strip()), "")
            obj["_base_dir"] = str(path.resolve().parent)
            result.append(obj)
    if not result:
        raise PipelineError("manifest has no instrument rows")
    return result


def discover_manifest(root: Path) -> list[dict[str, Any]]:
    if not root.is_dir():
        raise PipelineError(f"discovery root is not a directory: {root}")
    rows: list[dict[str, Any]] = []
    excluded = ("chart", "adjust", "event", "priceadjust", "manifest", "report", "audit", "quarantine", "candidate")
    allowed_suffixes = {".json", ".csv"}
    for path in sorted([*root.rglob("*.json"), *root.rglob("*.csv")]):
        if any(x in path.name.lower() for x in excluded):
            continue
        payload = None
        try:
            payload = read_payload(path)
        except PipelineError:
            continue
        if path.name.lower() not in {
            "daily_history_raw.json", "daily_history.json", "closing_price_daily_raw.json",
            "closing_price_daily.json", "history_raw.json", "daily_raw.json",
            "daily_history.csv", "normalized_history.csv", "market_prices_daily.csv",
        } and not looks_like_history(payload):
            continue
        if path.suffix.lower() not in allowed_suffixes or not looks_like_history(payload):
            continue
        values, code_key = row_list(payload)
        code_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if values and code_key:
            for item in values:
                code = str(item.get(code_key, "") or "").strip()
                if code:
                    code_groups[code].append(item)
        if code_groups:
            for code, members in sorted(code_groups.items()):
                symbol = next((str(field(r, "symbol", "ticker") or "").strip() for r in members if field(r, "symbol", "ticker")), path.parent.name)
                isin = next((str(field(r, "isin", "ISIN") or "").strip() for r in members if field(r, "isin", "ISIN")), "")
                rows.append({
                    "instrument_code": code, "symbol": symbol, "isin": isin,
                    "daily_history_path": str(path.resolve()),
                    "adjusted_chart_path": _sibling(path, ("chart_adjusted_raw.json", "adjusted_chart_raw.json", "chart_adjusted.json", "adjusted_chart.json", "chart_adjusted.csv", "adjusted_chart.csv", "adjusted_history.csv")),
                    "adjustment_events_path": _sibling(path, ("price_adjustments_raw.json", "price_adjustments.json", "price_adjust_list_raw.json", "events.json", "price_adjustments.csv", "events.csv")),
                    "_base_dir": str(root.resolve()), "_discovered": True,
                })
        else:
            codes = re.findall(r"(?<!\d)\d{10,22}(?!\d)", str(path))
            code = codes[0] if codes else ""
            rows.append({
                "instrument_code": code, "symbol": path.parent.name or path.stem, "isin": "",
                "daily_history_path": str(path.resolve()),
                "adjusted_chart_path": _sibling(path, ("chart_adjusted_raw.json", "adjusted_chart_raw.json", "chart_adjusted.json", "adjusted_chart.json")),
                "adjustment_events_path": _sibling(path, ("price_adjustments_raw.json", "price_adjustments.json", "price_adjust_list_raw.json", "events.json")),
                "_base_dir": str(root.resolve()), "_discovered": True,
            })
    if not rows:
        raise PipelineError("no recognizable daily-history JSON/CSV files found; provide --manifest with explicit input paths")

    # When both raw archives and derived/normalized copies exist, pick one stable
    # primary history per instrument and retain alternatives in the run inventory.
    # Ambiguous peers at the same priority block acceptance instead of silently
    # choosing whichever file happens to sort first.
    def priority(item: dict[str, Any]) -> tuple[int, str]:
        candidate = Path(str(item.get("daily_history_path", "")))
        name = candidate.name.lower()
        raw_exact = {
            "daily_history_raw.json", "closing_price_daily_raw.json",
            "history_raw.json", "daily_raw.json",
        }
        if name in raw_exact:
            rank = 0
        elif candidate.suffix.lower() == ".json" and "raw" in name:
            rank = 1
        elif candidate.suffix.lower() == ".json":
            rank = 2
        elif name in {"daily_history.csv", "market_prices_daily.csv", "normalized_history.csv"}:
            rank = 3
        else:
            rank = 4
        return rank, str(candidate)

    keyed: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unkeyed: list[dict[str, Any]] = []
    for item in rows:
        code = str(item.get("instrument_code", "") or "").strip()
        if code:
            keyed[code].append(item)
        else:
            unkeyed.append(item)
    selected: list[dict[str, Any]] = []
    for code, candidates in sorted(keyed.items()):
        ordered = sorted(candidates, key=priority)
        primary = dict(ordered[0])
        best_rank = priority(ordered[0])[0]
        equal_rank = [entry for entry in ordered if priority(entry)[0] == best_rank]
        # Same-code, same-priority candidate histories are genuinely ambiguous.
        primary["_discovery_ambiguous_history"] = len(equal_rank) > 1
        primary["_alternative_history_paths"] = [
            str(entry.get("daily_history_path", ""))
            for entry in ordered[1:]
            if str(entry.get("daily_history_path", "")) != str(primary.get("daily_history_path", ""))
        ]
        selected.append(primary)
    selected.extend(unkeyed)
    return selected


def _sibling(path: Path, names: tuple[str, ...]) -> str:
    return next((str((path.parent / n).resolve()) for n in names if (path.parent / n).is_file()), "")


def extract_history(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = next((payload[k] for k in ("closingPriceDaily", "dailyHistory", "daily_history", "rows", "data", "history") if isinstance(payload.get(k), list)), None)
    else:
        rows = None
    if not isinstance(rows, list) or not rows or any(not isinstance(r, dict) for r in rows):
        raise PipelineError("history must be a non-empty list of observation objects")
    return rows


def audit_history(rows: list[dict[str, Any]]) -> dict[str, Any]:
    cleaned = []
    dates: dict[date, list[int]] = defaultdict(list)
    order: list[date] = []
    bad_date = bad_close = bad_optional = bad_ohlc = 0
    for i, raw in enumerate(rows):
        d = parse_date(field(raw, "dEven", "date", "observation_date", "Date", "date_key", "DTYYYYMMDD", "<DTYYYYMMDD>"))
        close_raw = field(raw, "pClosing", "close_raw", "close", "CLOSE", "<CLOSE>", "close_candidate")
        open_raw = field(raw, "priceFirst", "open_raw", "open", "OPEN", "<OPEN>", "open_candidate")
        high_raw = field(raw, "priceMax", "high_raw", "high", "HIGH", "<HIGH>", "high_candidate")
        low_raw = field(raw, "priceMin", "low_raw", "low", "LOW", "<LOW>", "low_candidate")
        volume_raw = field(raw, "qTotTran5J", "volume_raw", "volume", "VOL", "<VOL>", "volume", "<VOLUME>", "volume_candidate")
        close, opn = number(close_raw, positive=True), number(open_raw, positive=True)
        high, low = number(high_raw, positive=True), number(low_raw, positive=True)
        volume = number(volume_raw, nonnegative=True)
        last = number(field(raw, "pDrCotVal", "last_raw", "last"), positive=True)
        turnover = number(field(raw, "qTotCap", "trade_value_raw", "turnover"), nonnegative=True)
        reasons: list[str] = []
        if d is None:
            bad_date += 1
            reasons.append("INVALID_DATE")
        else:
            order.append(d)
            dates[d].append(i)
        if close is None:
            bad_close += 1
            reasons.append("INVALID_OR_NONPOSITIVE_CLOSE")
        for raw_value, parsed_value, label in (
            (open_raw, opn, "OPEN"), (high_raw, high, "HIGH"), (low_raw, low, "LOW"),
            (volume_raw, volume, "VOLUME"),
            (field(raw, "pDrCotVal", "last_raw", "last"), last, "LAST"),
            (field(raw, "qTotCap", "trade_value_raw", "turnover"), turnover, "TURNOVER"),
        ):
            if raw_value not in (None, "") and parsed_value is None:
                bad_optional += 1
                reasons.append(f"INVALID_{label}")
        row_bad_ohlc = False
        if high is not None and low is not None and high < low:
            row_bad_ohlc = True
            reasons.append("HIGH_BELOW_LOW")
        if high is not None and any(x is not None and high < x for x in (opn, close)):
            row_bad_ohlc = True
            reasons.append("HIGH_BELOW_OPEN_OR_CLOSE")
        if low is not None and any(x is not None and low > x for x in (opn, close)):
            row_bad_ohlc = True
            reasons.append("LOW_ABOVE_OPEN_OR_CLOSE")
        bad_ohlc += int(row_bad_ohlc)
        cleaned.append({
            "raw": raw, "date_obj": d, "date": d.isoformat() if d else "",
            "close": close, "open": opn, "high": high, "low": low,
            "volume": volume, "last": last, "turnover": turnover, "reasons": reasons,
        })
    unique_dates = sorted(dates)
    gaps = [(b - a).days for a, b in zip(unique_dates, unique_dates[1:])]
    asc = sum(b > a for a, b in zip(order, order[1:]))
    desc = sum(b < a for a, b in zip(order, order[1:]))
    order_status = "non_monotonic" if asc and desc else "monotonic_descending" if desc else "monotonic_ascending_or_constant"
    return {
        "rows": cleaned, "history_rows": len(rows),
        "valid_history_rows": sum(r["date_obj"] is not None and r["close"] is not None for r in cleaned),
        "unique_dates": unique_dates, "dates_seen": dates,
        "invalid_date_rows": bad_date, "invalid_or_nonpositive_close_rows": bad_close,
        "invalid_numeric_field_rows": bad_optional,
        "duplicate_history_date_rows": sum(max(0, len(v) - 1) for v in dates.values()),
        "input_order_inversions": sum(b < a for a, b in zip(order, order[1:])),
        "input_order_status": order_status, "ohlc_violation_rows": bad_ohlc,
        "first_date": unique_dates[0].isoformat() if unique_dates else "",
        "last_date": unique_dates[-1].isoformat() if unique_dates else "",
        "max_calendar_gap_days": max(gaps) if gaps else 0,
        "gaps_gt_7_days": sum(g > 7 for g in gaps),
        "gaps_gt_30_days": sum(g > 30 for g in gaps),
    }


def parse_chart(payload: Any) -> dict[date, dict[str, float | None]]:
    if isinstance(payload, str):
        items = [(None, [p.strip() for p in part.split(",")]) for part in payload.strip().split(";") if part.strip()]
    elif isinstance(payload, dict):
        nested = next((payload[k] for k in ("data", "rows", "chart", "chartData") if isinstance(payload.get(k), (dict, list, str))), payload)
        if isinstance(nested, str):
            return parse_chart(nested)
        items = list(nested.items()) if isinstance(nested, dict) else [(None, r) for r in nested] if isinstance(nested, list) else []
    elif isinstance(payload, list):
        items = [(None, row) for row in payload]
    else:
        items = []
    if not items:
        raise PipelineError("adjusted chart has no recognizable rows")
    result = {}
    for i, (key, values) in enumerate(items):
        if isinstance(values, dict):
            d = parse_date(field(values, "date", "dEven", "observation_date") or key)
            row = {
                "open": number(field(values, "open_adj", "adjusted_open", "OPEN", "<OPEN>", "open"), positive=True),
                "high": number(field(values, "high_adj", "adjusted_high", "HIGH", "<HIGH>", "high"), positive=True),
                "low": number(field(values, "low_adj", "adjusted_low", "LOW", "<LOW>", "low"), positive=True),
                "last": number(field(values, "last_adj", "adjusted_last", "last"), positive=True),
                "volume": number(field(values, "chart_volume", "volume"), nonnegative=True),
                "close": number(field(values, "close_adj", "adjusted_close", "CLOSE", "<CLOSE>", "close"), positive=True),
            }
        elif isinstance(values, (list, tuple)) and len(values) >= 7:
            d = parse_date(key if key not in (None, "") else values[0])
            if d and values[0] not in (None, "") and parse_date(values[0]) != d:
                raise PipelineError(f"chart row {i}: key/date mismatch")
            row = {
                "high": number(values[1], positive=True), "low": number(values[2], positive=True),
                "open": number(values[3], positive=True), "last": number(values[4], positive=True),
                "volume": number(values[5], nonnegative=True), "close": number(values[6], positive=True),
            }
        else:
            raise PipelineError(f"chart row {i}: invalid shape")
        if d is None or row["close"] is None:
            raise PipelineError(f"chart row {i}: invalid date or adjusted close")
        if d in result:
            raise PipelineError(f"duplicate adjusted chart date {d.isoformat()}")
        result[d] = row
    return result


def parse_events(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list) and all(isinstance(r, dict) for r in payload):
        return payload
    if isinstance(payload, dict):
        for key in ("priceAdjust", "priceAdjustment", "priceAdjustList", "price_adjustments", "events", "data"):
            if isinstance(payload.get(key), list):
                return [r for r in payload[key] if isinstance(r, dict)]
    raise PipelineError("unrecognized event payload shape")


def event_date(row: dict[str, Any]) -> tuple[date | None, str, str]:
    event_type = str(field(row, "type", "eventType", "cDesc", "desc", "description", "eventName") or "")[:120]
    for key in ("dEven", "date", "eventDate", "effectiveDate", "dEffective", "date_event", "dEvenDate", "adjustmentDate", "observation_date"):
        if row.get(key) not in (None, ""):
            d = parse_date(row[key])
            if d:
                return d, key, event_type
    return None, "", event_type


def evidence_reference_ok(value: Any, base: Path) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if re.fullmatch(r"sha256:[0-9a-fA-F]{64}", text):
        return True
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return True
    path = Path(text).expanduser()
    path = path.resolve() if path.is_absolute() else (base / path).resolve()
    return path.is_file()


def flag(row: dict[str, Any], key: str) -> bool:
    return str(row.get(key, "false") or "false").strip().lower() in {"true", "1", "yes", "approved", "passed"}


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({c: row.get(c, "") for c in columns} for row in rows)


def add_months(day: date, months: int) -> date:
    index = day.year * 12 + day.month - 1 + months
    year, m = divmod(index, 12)
    month = m + 1
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return date(year, month, min(day.day, (next_month - timedelta(days=1)).day))


def build_features_labels(rows: list[dict[str, Any]], eligible_codes: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[tuple[date, float, str]]] = defaultdict(list)
    for row in rows:
        code = str(row.get("instrument_code", ""))
        if code not in eligible_codes:
            continue
        d = parse_date(row.get("date"))
        close = number(row.get("adjusted_close_candidate"), positive=True)
        if d and close is not None:
            grouped[code].append((d, close, str(row.get("symbol", ""))))
    features, labels = [], []
    for code, series in grouped.items():
        series.sort(key=lambda x: x[0])
        days, closes = [x[0] for x in series], [x[1] for x in series]
        symbol = series[0][2]
        returns: list[float | None] = [None]
        for i in range(1, len(closes)):
            returns.append(closes[i] / closes[i - 1] - 1 if (days[i] - days[i - 1]).days <= 7 else None)
        for i, d in enumerate(days):
            def lagged(n: int) -> float | str:
                if i < n or closes[i - n] <= 0:
                    return ""
                if any((days[k] - days[k - 1]).days > 7 for k in range(i - n + 1, i + 1)):
                    return ""
                return closes[i] / closes[i - n] - 1
            recent = [r for r in returns[max(1, i - 19):i + 1] if r is not None]
            volatility = statistics.stdev(recent) * math.sqrt(252) if len(recent) >= 20 else ""
            peak = max(closes[max(0, i - 125):i + 1])
            features.append({
                "instrument_code": code, "symbol": symbol, "date": d.isoformat(),
                "close_adjusted": closes[i], "return_1d": returns[i] if returns[i] is not None else "",
                "return_20d": lagged(20), "return_60d": lagged(60), "return_126d": lagged(126),
                "volatility_20d": volatility, "drawdown_126d": closes[i] / peak - 1 if peak else "",
            })
        month_last: dict[tuple[int, int], int] = {}
        for i, d in enumerate(days):
            month_last[(d.year, d.month)] = i
        for _, i in sorted(month_last.items()):
            target_cutoff = add_months(days[i], 6)
            target = next((j for j in range(i + 1, len(days)) if days[j] >= target_cutoff), None)
            if target is not None and (days[target] - target_cutoff).days <= 7:
                labels.append({
                    "instrument_code": code, "symbol": symbol,
                    "decision_date": days[i].isoformat(), "target_date": days[target].isoformat(),
                    "forward_return_6m_pct": (closes[target] / closes[i] - 1) * 100,
                    "horizon_calendar_days": (days[target] - days[i]).days,
                })
    return features, labels


def run_pipeline(
    items: list[dict[str, Any]], *, manifest_path: Path | None, output_root: Path,
    min_history: int = DEFAULT_MIN_HISTORY, min_coverage: float = DEFAULT_MIN_COVERAGE,
    factor_min: float = DEFAULT_FACTOR_MIN, factor_max: float = DEFAULT_FACTOR_MAX,
    discovered: bool = False,
) -> dict[str, Any]:
    if min_history < 2 or not 0 <= min_coverage <= 1 or not 0 < factor_min < factor_max < math.inf:
        raise PipelineError("invalid pipeline thresholds")
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%S%fZ")
    out = output_root / run_id
    out.mkdir(parents=True, exist_ok=False)
    decisions, raw_out, quality_out, adjusted_out = [], [], [], []
    event_out, factor_out, quarantine_out, queue_out, research_out, inventory = [], [], [], [], [], []
    cache: dict[str, Any] = {}
    payload_indexes: dict[str, Any] = {}
    hashes_all: dict[str, str] = {}
    codes: defaultdict[str, int] = defaultdict(int)
    for item in items:
        code = str(item.get("instrument_code", "") or "").strip()
        if code:
            codes[code] += 1
    duplicate_codes = {c for c, count in codes.items() if count > 1}

    for item in items:
        base = Path(item.get("_base_dir") or (manifest_path.parent if manifest_path else Path.cwd()))
        code = str(item.get("instrument_code", "") or "").strip()
        symbol = str(item.get("symbol", "") or "").strip()
        isin = str(item.get("isin", "") or "").strip()
        identity_fields = bool(code.isdigit() and 10 <= len(code) <= 22 and symbol and re.fullmatch(r"[A-Za-z0-9]{12}", isin) and code not in duplicate_codes)
        identity_ok = identity_fields and evidence_reference_ok(item.get("identity_match_evidence_ref"), base)
        paths = {k: (Path(str(item.get(k, "")).strip()).expanduser() if str(item.get(k, "")).strip() else None)
                 for k in ("daily_history_path", "adjusted_chart_path", "adjustment_events_path")}
        for k, path in paths.items():
            if path and not path.is_absolute():
                paths[k] = (base / path).resolve()
        payloads, input_hashes, errors = {}, {}, []
        if item.get("_discovery_ambiguous_history"):
            errors.append("discovery:multiple_equal_priority_history_files_for_instrument")
        for alternative in item.get("_alternative_history_paths", []):
            alt_path = Path(str(alternative)).expanduser()
            try:
                alt_hash = file_hash(alt_path) if alt_path.is_file() else ""
                alt_status = "alternative_history_not_selected_lower_priority"
                alt_error = "Primary file selected by deterministic filename priority; reconcile if data differs."
            except OSError as exc:
                alt_hash, alt_status, alt_error = "", "alternative_history_unreadable", type(exc).__name__
            inventory.append({"instrument_code": code, "symbol": symbol,
                              "input_kind": "alternative_history_not_selected",
                              "path": str(alt_path), "sha256": alt_hash,
                              "status": alt_status, "error": alt_error})
        for kind, path in paths.items():
            if path is None:
                continue
            try:
                if not path.is_file():
                    raise PipelineError(f"input file not found: {path}")
                key = str(path)
                if key not in cache:
                    cache[key] = read_payload(path)
                input_hashes[kind] = file_hash(path)
                payloads[kind] = filter_for_instrument(
                    cache[key], code, index_cache=payload_indexes, cache_key=key
                )
                hashes_all[key] = input_hashes[kind]
                inventory.append({"instrument_code": code, "symbol": symbol, "input_kind": kind,
                                  "path": key, "sha256": input_hashes[kind], "status": "read", "error": ""})
            except (PipelineError, OSError) as exc:
                errors.append(f"{kind}:{exc}")
                inventory.append({"instrument_code": code, "symbol": symbol, "input_kind": kind,
                                  "path": str(path), "sha256": "", "status": "error", "error": str(exc)})
        if paths["daily_history_path"] is None:
            errors.append("daily_history_path:not_provided")
        if code in duplicate_codes:
            errors.append("instrument_code:duplicate_manifest_identity")
        hash_json = json.dumps(input_hashes, sort_keys=True, separators=(",", ":"))

        h = None
        raw_history_rows: list[dict[str, Any]] = []
        price_semantics = "unknown_unverified"
        if "daily_history_path" in payloads:
            try:
                raw_history_rows = extract_history(payloads["daily_history_path"])
                price_semantics = classify_price_input_semantics(
                    raw_history_rows, item.get("history_close_semantics")
                )
                h = audit_history(raw_history_rows)
            except PipelineError as exc:
                errors.append(f"history_parse:{exc}")
        chart = {}
        if "adjusted_chart_path" in payloads:
            try:
                chart = parse_chart(payloads["adjusted_chart_path"])
            except PipelineError as exc:
                errors.append(f"chart_parse:{exc}")
        event_list, event_error = [], ""
        if "adjustment_events_path" in payloads:
            try:
                event_list = parse_events(payloads["adjustment_events_path"])
            except PipelineError as exc:
                event_error = str(exc)
                errors.append(f"events_parse:{exc}")

        unique_dates = set(h["unique_dates"]) if h else set()
        coverage = len(unique_dates.intersection(chart)) / len(unique_dates) if unique_dates else 0.0
        ratios = sorted(
            [(d, adj["close"] / row["close"]) for row in (h["rows"] if h else [])
             if price_semantics == "raw_unadjusted"
             and (d := row["date_obj"]) and row["close"] and row["close"] > 0
             and (adj := chart.get(d)) and adj["close"] > 0],
            key=lambda x: x[0],
        )
        vals = [r for _, r in ratios]
        outlier_count = sum(not factor_min <= r <= factor_max for r in vals)
        step_count = sum(r / prev < factor_min or r / prev > factor_max for prev, r in zip(vals, vals[1:]))
        factor_out.append({
            "instrument_code": code, "symbol": symbol, "overlap_count": len(vals),
            "factor_min": min(vals) if vals else "", "factor_median": statistics.median(vals) if vals else "",
            "factor_max": max(vals) if vals else "", "factor_outlier_count": outlier_count,
            "factor_step_change_count": step_count, "factor_min_threshold": factor_min,
            "factor_max_threshold": factor_max, "interpretation": "PRELIMINARY_TRIAGE_ONLY_NOT_FACTOR_VALIDATION",
        })

        event_unrecognized = event_exact = event_chart_exact = 0
        adjusted_ohlc_violation_rows = 0
        if h:
            for row in h["rows"]:
                d = row["date_obj"]
                duplicate = bool(d and len(h["dates_seen"].get(d, [])) > 1)
                row_reasons = row["reasons"] + (["DUPLICATE_HISTORY_DATE"] if duplicate else [])
                raw = row["raw"]
                raw_close = field(raw, "pClosing", "close_raw", "close", "CLOSE", "<CLOSE>", "close_candidate")
                raw_open = field(raw, "priceFirst", "open_raw", "open", "OPEN", "<OPEN>", "open_candidate")
                raw_high = field(raw, "priceMax", "high_raw", "high", "HIGH", "<HIGH>", "high_candidate")
                raw_low = field(raw, "priceMin", "low_raw", "low", "LOW", "<LOW>", "low_candidate")
                raw_vol = field(raw, "qTotTran5J", "volume_raw", "volume", "VOL", "<VOL>", "volume", "<VOLUME>", "volume_candidate")
                raw_last = field(raw, "pDrCotVal", "last_raw", "last")
                raw_prev = field(raw, "priceYesterday", "prev_close_raw", "previous_close")
                raw_turnover = field(raw, "qTotCap", "trade_value_raw", "turnover")
                raw_out.append({
                    "instrument_code": code, "symbol": symbol, "isin": isin, "date": row["date"],
                    "close_input_candidate": raw_close, "last_input_candidate": raw_last,
                    "open_input_candidate": raw_open, "high_input_candidate": raw_high,
                    "low_input_candidate": raw_low, "prev_close_input_candidate": raw_prev,
                    "volume_input_candidate": raw_vol, "trade_value_input_candidate": raw_turnover,
                    "price_input_semantics": price_semantics,
                    "source_response_sha256": input_hashes.get("daily_history_path", ""),
                    "normalization_status": "candidate_quarantined_raw_history" if row_reasons or not identity_ok else "candidate_raw_unapproved",
                    "eligible_for_scoring": False,
                })
                quality_out.append({
                    "instrument_code": code, "symbol": symbol, "date": row["date"],
                    "input_close_candidate": raw_close, "input_open_candidate": raw_open,
                    "input_high_candidate": raw_high, "input_low_candidate": raw_low,
                    "input_volume_candidate": raw_vol, "price_input_semantics": price_semantics,
                    "row_status": "QUARANTINE" if row_reasons else "VALID_STRUCTURAL_CANDIDATE",
                    "reason_codes": ";".join(row_reasons),
                })
                adj = chart.get(d) if d else None
                adj_reasons: list[str] = []
                if adj:
                    adj_high, adj_low = adj.get("high"), adj.get("low")
                    adj_open, adj_close = adj.get("open"), adj.get("close")
                    if adj_high is not None and adj_low is not None and adj_high < adj_low:
                        adj_reasons.append("ADJUSTED_HIGH_BELOW_LOW")
                    if adj_high is not None and any(v is not None and adj_high < v for v in (adj_open, adj_close)):
                        adj_reasons.append("ADJUSTED_HIGH_BELOW_OPEN_OR_CLOSE")
                    if adj_low is not None and any(v is not None and adj_low > v for v in (adj_open, adj_close)):
                        adj_reasons.append("ADJUSTED_LOW_ABOVE_OPEN_OR_CLOSE")
                adjusted_ohlc_violation_rows += int(bool(adj_reasons))
                ratio = adj["close"] / row["close"] if price_semantics == "raw_unadjusted" and adj and row["close"] else ""
                adjusted_out.append({
                    "instrument_code": code, "symbol": symbol, "isin": isin, "date": row["date"],
                    "close_input_candidate": raw_close, "last_input_candidate": raw_last,
                    "open_input_candidate": raw_open, "high_input_candidate": raw_high,
                    "low_input_candidate": raw_low, "volume_input_candidate": raw_vol,
                    "turnover_input_candidate": raw_turnover, "price_input_semantics": price_semantics,
                    "adjusted_open_candidate": adj["open"] if adj else "",
                    "adjusted_high_candidate": adj["high"] if adj else "",
                    "adjusted_low_candidate": adj["low"] if adj else "",
                    "adjusted_last_candidate": adj["last"] if adj else "",
                    "adjusted_close_candidate": adj["close"] if adj else "",
                    "adjusted_chart_volume": adj["volume"] if adj else "",
                    "adjusted_chart_row_present": bool(adj),
                    "adjusted_ohlc_status": ("MISSING_ADJUSTED_CHART_ROW" if not adj else "QUARANTINE" if adj_reasons else "VALID_STRUCTURAL_CANDIDATE"),
                    "adjusted_ohlc_reason_codes": ";".join(adj_reasons),
                    "adjusted_to_input_close_ratio": ratio,
                    "adjustment_source": "tsetmc_legacy_chart_a1",
                    "adjustment_status": "provider_supplied_unvalidated" if adj else "missing_adjusted_chart_row",
                    "source_response_sha256": input_hashes.get("adjusted_chart_path", ""),
                    "eligible_for_scoring": False,
                })
            for idx, event in enumerate(event_list):
                d, date_field, event_type = event_date(event)
                if d is None:
                    event_unrecognized += 1
                else:
                    event_exact += int(d in unique_dates)
                    event_chart_exact += int(d in chart)
                event_out.append({
                    "instrument_code": code, "symbol": symbol, "event_index": idx,
                    "event_date": d.isoformat() if d else "", "date_field": date_field,
                    "date_parse_status": "parsed" if d else "unrecognized",
                    "history_date_exact_match": bool(d and d in unique_dates),
                    "adjusted_chart_date_match": bool(d and d in chart),
                    "event_type_candidate": event_type,
                    "event_source_hash": input_hashes.get("adjustment_events_path", ""),
                    "decision_note": "Exact date overlap is descriptive; event effective-date semantics require verification.",
                })

        bad_adjusted_history = adjusted_ohlc_violation_rows > 0
        bad_history = bool(h and (
            h["invalid_date_rows"] or h["invalid_or_nonpositive_close_rows"]
            or h["invalid_numeric_field_rows"] or h["duplicate_history_date_rows"]
            or h["ohlc_violation_rows"] or h["input_order_status"] == "non_monotonic"
        ))
        short_history = bool(h and h["valid_history_rows"] < min_history)
        low_coverage = not h or not chart or coverage < min_coverage
        ratio_bad = bool(outlier_count or step_count)
        event_payload_missing = paths["adjustment_events_path"] is None or "adjustment_events_path" not in payloads
        event_bad = bool(event_unrecognized or event_payload_missing or event_error)
        rights_ref = evidence_reference_ok(item.get("rights_evidence_ref"), base)
        semantics_ref = evidence_reference_ok(item.get("semantics_evidence_ref"), base)
        independent_ref = evidence_reference_ok(item.get("independent_reconciliation_evidence_ref"), base)
        actions_ref = evidence_reference_ok(item.get("corporate_action_completeness_evidence_ref"), base)
        rights_ok = str(item.get("rights_status", "unreviewed")).lower() in {"approved", "verified", "permitted"} and rights_ref
        semantics_ok = (
            flag(item, "semantics_verified")
            and semantics_ref
            and price_semantics == "raw_unadjusted"
        )
        independent_ok = flag(item, "independent_reconciliation_passed") and independent_ref
        actions_ok = flag(item, "corporate_action_completeness_verified") and actions_ref
        all_evidence = identity_ok and rights_ok and semantics_ok and independent_ok and actions_ok
        reasons = []
        if not identity_fields:
            reasons.append("INSTRUMENT_IDENTITY_FIELDS_INCOMPLETE_OR_DUPLICATE")
        elif not identity_ok:
            reasons.append("INSTRUMENT_IDENTITY_EVIDENCE_REFERENCE_MISSING")
        if errors:
            reasons.append("INPUT_OR_PARSER_ERROR")
        if bad_history:
            reasons.append("RAW_HISTORY_STRUCTURAL_DEFECTS")
        if bad_adjusted_history:
            reasons.append("ADJUSTED_CHART_OHLC_STRUCTURAL_DEFECTS")
        if short_history:
            reasons.append("HISTORY_TOO_SHORT_FOR_SIX_MONTH_RESEARCH")
        if low_coverage:
            reasons.append("ADJUSTED_COVERAGE_BELOW_TRIAGE_THRESHOLD")
        if ratio_bad:
            reasons.append("ADJUSTMENT_RATIO_OUTLIER_OR_STEP_CHANGE")
        if event_payload_missing:
            reasons.append("CORPORATE_ACTION_EVENT_PAYLOAD_MISSING")
        if event_error:
            reasons.append("CORPORATE_ACTION_EVENT_PAYLOAD_PARSE_ERROR")
        if event_unrecognized:
            reasons.append("EVENT_DATE_FIELDS_UNRESOLVED")
        if not rights_ok:
            reasons.append("USAGE_RIGHTS_NOT_VERIFIED_OR_EVIDENCE_REFERENCE_MISSING")
        if price_semantics != "raw_unadjusted":
            reasons.append("PRICE_INPUT_SEMANTICS_NOT_EXPLICITLY_RAW_UNADJUSTED")
        if not semantics_ok:
            reasons.append("PRICE_SEMANTICS_OR_UNITS_NOT_VERIFIED_OR_EVIDENCE_REFERENCE_MISSING")
        if not independent_ok:
            reasons.append("INDEPENDENT_RECONCILIATION_NOT_PASSED_OR_EVIDENCE_REFERENCE_MISSING")
        if not actions_ok:
            reasons.append("CORPORATE_ACTION_COMPLETENESS_NOT_VERIFIED_OR_EVIDENCE_REFERENCE_MISSING")

        if errors or bad_history or bad_adjusted_history:
            status = "needs_reprocessing"
        elif ratio_bad or event_bad or not identity_ok:
            status = "quarantine_needs_independent_evidence"
        elif low_coverage:
            status = "needs_reprocessing"
        elif short_history:
            status = "retain_candidate_insufficient_history"
        elif not all_evidence:
            status = "retain_candidate_pending_evidence"
        else:
            status = "research_eligible_after_explicit_evidence_review"
        eligible = bool(status == "research_eligible_after_explicit_evidence_review" and all_evidence and h and not bad_history and not bad_adjusted_history and not short_history and not low_coverage and not ratio_bad and not errors)

        decision = {
            "instrument_code": code, "symbol": symbol, "isin": isin,
            "price_input_semantics": price_semantics,
            "identity_verified": identity_ok, "decision_status": status,
            "decision_reason_codes": ";".join(reasons or ["TECHNICAL_AND_EVIDENCE_GATES_PASSED"]),
            "input_hashes_json": hash_json, "history_rows": h["history_rows"] if h else 0,
            "valid_history_rows": h["valid_history_rows"] if h else 0,
            "unique_history_dates": len(h["unique_dates"]) if h else 0,
            "invalid_date_rows": h["invalid_date_rows"] if h else 0,
            "invalid_or_nonpositive_close_rows": h["invalid_or_nonpositive_close_rows"] if h else 0,
            "invalid_numeric_field_rows": h["invalid_numeric_field_rows"] if h else 0,
            "duplicate_history_date_rows": h["duplicate_history_date_rows"] if h else 0,
            "input_order_inversions": h["input_order_inversions"] if h else 0,
            "input_order_status": h["input_order_status"] if h else "unknown",
            "ohlc_violation_rows": h["ohlc_violation_rows"] if h else 0,
            "adjusted_ohlc_violation_rows": adjusted_ohlc_violation_rows,
            "first_date": h["first_date"] if h else "", "last_date": h["last_date"] if h else "",
            "max_calendar_gap_days": h["max_calendar_gap_days"] if h else 0,
            "adjusted_chart_rows": len(chart), "adjusted_close_coverage": round(coverage, 6),
            "factor_ratio_outlier_rows": outlier_count, "factor_step_change_count": step_count,
            "event_rows": len(event_list), "event_dates_unrecognized": event_unrecognized,
            "event_dates_exact_history_match": event_exact, "event_dates_exact_adjusted_chart_match": event_chart_exact, "raw_history_preserved": True,
            "eligible_for_research": eligible, "eligible_for_scoring": False,
            "eligible_for_backtest": eligible,
        }
        decisions.append(decision)

        if not eligible:
            reason_text = ";".join(reasons or ["RESEARCH_GATE_NOT_PASSED"])
            quarantine_out.append({
                "instrument_code": code, "symbol": symbol, "stage": "acceptance",
                "reason_code": reason_text, "details": "Candidate retained; no automatic repair or forward-fill.",
                "input_hashes_json": hash_json,
                "required_action": "Resolve reason codes using reviewed evidence; do not retry unless input hash or evidence changes.",
                "resolution_status": "open",
            })
            stage = "history_quality_or_input" if errors or bad_history else "adjusted_history_quality" if bad_adjusted_history else "adjustment_factor_audit" if ratio_bad else "adjusted_history_coverage" if low_coverage else "event_reconciliation" if event_bad else "source_evidence"
            queue_out.append({
                "instrument_code": code, "symbol": symbol, "stage": stage,
                "reason_code": reason_text,
                "required_action": "Resolve reason codes; no automatic retry loop.",
                "attempt_count": 0, "last_attempt_at": "", "next_retry_after": "",
                "input_hash": hashlib.sha256(hash_json.encode()).hexdigest(),
                "pipeline_version": VERSION, "resolution_status": "pending_evidence_or_reprocessing",
            })
        else:
            research_out.append({
                "instrument_code": code, "symbol": symbol, "isin": isin,
                "daily_history_path": str(paths["daily_history_path"]),
                "adjusted_chart_path": str(paths["adjusted_chart_path"]),
                "adjustment_events_path": str(paths["adjustment_events_path"]),
                "first_date": h["first_date"], "last_date": h["last_date"],
                "history_rows": h["history_rows"], "adjusted_close_coverage": round(coverage, 6),
                "input_hashes_json": hash_json,
                "identity_match_evidence_ref": item.get("identity_match_evidence_ref", ""),
                "history_close_semantics": price_semantics,
                "rights_evidence_ref": item.get("rights_evidence_ref", ""),
                "semantics_evidence_ref": item.get("semantics_evidence_ref", ""),
                "independent_reconciliation_evidence_ref": item.get("independent_reconciliation_evidence_ref", ""),
                "corporate_action_completeness_evidence_ref": item.get("corporate_action_completeness_evidence_ref", ""),
                "eligible_for_scoring": False,
                "eligibility_scope": "research only; production source registry still controls scoring",
            })

    if not decisions:
        raise PipelineError("no instruments found")
    eligible_codes = {str(r["instrument_code"]) for r in research_out}
    features, labels = build_features_labels(adjusted_out, eligible_codes)
    write_csv(out / "instrument_decisions.csv", DECISION_COLUMNS, decisions)
    write_csv(out / "input_history_candidate.csv", RAW_COLUMNS, raw_out)
    write_csv(out / "raw_history_quality.csv", QUALITY_COLUMNS, quality_out)
    write_csv(out / "adjusted_candidate_daily.csv", ADJUSTED_COLUMNS, adjusted_out)
    write_csv(out / "event_reconciliation.csv", EVENT_COLUMNS, event_out)
    write_csv(out / "adjustment_factor_audit.csv", FACTOR_COLUMNS, factor_out)
    write_csv(out / "research_eligible_manifest.csv", RESEARCH_COLUMNS, research_out)
    write_csv(out / "quarantine.csv", QUARANTINE_COLUMNS, quarantine_out)
    write_csv(out / "reprocessing_queue.csv", QUEUE_COLUMNS, queue_out)
    write_csv(out / "input_inventory.csv", ["instrument_code", "symbol", "input_kind", "path", "sha256", "status", "error"], inventory)
    if discovered:
        write_csv(out / "discovered_manifest.csv", MANIFEST_COLUMNS, items)
    write_csv(out / "research_features.csv", FEATURE_COLUMNS, features)
    write_csv(out / "forward_labels_6m.csv", LABEL_COLUMNS, labels)

    status_counts: defaultdict[str, int] = defaultdict(int)
    for row in decisions:
        status_counts[row["decision_status"]] += 1
    report = {
        "pipeline_version": VERSION, "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "local_offline_acceptance_pipeline", "source_id": SOURCE_ID,
        "input_manifest": str(manifest_path) if manifest_path else None,
        "input_manifest_sha256": file_hash(manifest_path) if manifest_path and manifest_path.is_file() else None,
        "instrument_count": len(decisions), "input_files_read": sum(r["status"] == "read" for r in inventory),
        "input_file_read_errors": sum(r["status"] == "error" for r in inventory),
        "input_hash_count": len(hashes_all), "decision_status_counts": dict(status_counts),
        "research_eligible_count": len(research_out), "quarantine_count": len(quarantine_out),
        "reprocessing_queue_count": len(queue_out), "aggregate_history_rows": sum(r["history_rows"] for r in decisions),
        "aggregate_adjusted_candidate_rows": len(adjusted_out), "event_rows_audited": len(event_out),
        "research_feature_rows": len(features), "forward_label_rows": len(labels),
        "flags": {"raw_inputs_overwritten": False, "network_requests_made": False,
                  "automatic_adjustment_applied": False, "forward_fill_applied": False,
                  "production_scoring_enabled": False, "backtest_run": False},
        "rules": {"minimum_history_rows_for_six_month_research": min_history,
                  "minimum_adjusted_coverage_triage_only": min_coverage,
                  "adjusted_raw_factor_range_triage_only": [factor_min, factor_max],
                  "research_acceptance_requires_traceable_identity_rights_semantics_independent_reference_and_corporate_action_evidence": True},
        "limitations": [
            "Local payload acceptance only: this pipeline makes no TSETMC requests.",
            "The legacy adjusted-chart mapping is empirical and not an official stable schema contract.",
            "Exact event-date overlap does not by itself establish effective-date or publication-time semantics.",
            "Coverage and ratio thresholds are preliminary triage rules, not proof of corporate-action correctness.",
            "The user must point discovery mode at the data corpus itself, not the whole repository or output directory.",
            "Only series with explicit traceable evidence references can pass research gating; production scoring remains separately disabled.",
            "Chronological strategy backtesting with real transaction costs, liquidity, drawdown and out-of-sample evaluation is not performed by this ingestion/acceptance stage.",
        ],
        "output_dir": str(out),
    }
    (out / "data_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "backtest_gate.json").write_text(json.dumps({
        "status": "BLOCKED_NO_EVIDENCE_ACCEPTED_SERIES" if not research_out else "NOT_RUN_REQUIRES_CHRONOLOGICAL_STRATEGY_REVIEW",
        "research_eligible_series_count": len(research_out), "feature_rows": len(features), "forward_label_rows": len(labels),
        "backtest_run": False, "eligible_for_scoring": False, "eligible_for_backtest": False,
        "reason": "The data pipeline prepares causal features and six-calendar-month forward labels only after evidence gates pass. A separate chronological strategy evaluation with realistic costs, liquidity constraints, drawdown and holdout protocol is required.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "run_manifest.json").write_text(json.dumps({
        "pipeline_version": VERSION, "run_id": run_id, "input_hashes": hashes_all,
        "output_files": sorted(p.name for p in out.iterdir() if p.is_file()),
        "raw_inputs_overwritten": False, "outputs_are_candidate_only": True,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--manifest", help="CSV with instrument_code,symbol,isin and per-instrument local payload paths")
    group.add_argument("--discover-root", help="Discover known raw-history JSON/CSV schemas under a data-only folder")
    parser.add_argument("--output-root", default=str(Path.home() / "marketsage-data" / "tsetmc-acceptance"))
    parser.add_argument("--min-history-rows", type=int, default=DEFAULT_MIN_HISTORY)
    parser.add_argument("--min-adjusted-coverage", type=float, default=DEFAULT_MIN_COVERAGE)
    parser.add_argument("--factor-min", type=float, default=DEFAULT_FACTOR_MIN)
    parser.add_argument("--factor-max", type=float, default=DEFAULT_FACTOR_MAX)
    args = parser.parse_args(argv)
    try:
        manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else None
        items = load_manifest(manifest_path) if manifest_path else discover_manifest(Path(args.discover_root).expanduser().resolve())
        report = run_pipeline(
            items, manifest_path=manifest_path, output_root=Path(args.output_root).expanduser().resolve(),
            min_history=args.min_history_rows, min_coverage=args.min_adjusted_coverage,
            factor_min=args.factor_min, factor_max=args.factor_max, discovered=bool(args.discover_root),
        )
    except (PipelineError, OSError, ValueError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc), "network_requests_made": False}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "COMPLETED_CANDIDATE_ONLY", "run_id": report["run_id"],
        "instrument_count": report["instrument_count"], "decision_status_counts": report["decision_status_counts"],
        "research_eligible_count": report["research_eligible_count"],
        "quarantine_count": report["quarantine_count"], "reprocessing_queue_count": report["reprocessing_queue_count"],
        "research_feature_rows": report["research_feature_rows"], "forward_label_rows": report["forward_label_rows"],
        "network_requests_made": False, "raw_inputs_overwritten": False,
        "production_scoring_enabled": False, "backtest_run": False, "output_dir": report["output_dir"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
