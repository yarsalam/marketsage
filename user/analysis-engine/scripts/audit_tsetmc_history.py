#!/usr/bin/env python3
"""Audit a TSETMC daily-history sample without approving it for investment scoring.

By default fetches one instrument history. Use --input for an already saved JSON
fixture. The report contains aggregate metadata/anomaly flags only, not raw rows.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from tsetmc_provider import TsetmcClient


DEFAULT_INSTRUMENT_CODE = "46348559193224090"  # فولاد; override with --ins-code
DEFAULT_OUTLIER_THRESHOLD = 0.30


def _date_value(row: dict[str, Any]) -> datetime.date | None:
    raw = row.get("dEven")
    if isinstance(raw, bool) or not isinstance(raw, (int, str)):
        return None
    try:
        return datetime.strptime(str(raw), "%Y%m%d").date()
    except ValueError:
        return None


def _number(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def audit_history(
    rows: Any,
    *,
    expected_ins_code: str | None = None,
    outlier_threshold: float = DEFAULT_OUTLIER_THRESHOLD,
) -> dict[str, Any]:
    """Return an aggregate audit. Findings are flags for review, not silent fixes."""
    if not isinstance(rows, list):
        raise ValueError("history rows must be a JSON array")
    if not math.isfinite(outlier_threshold) or not 0 < outlier_threshold <= 5:
        raise ValueError("outlier_threshold must be finite and in (0, 5]")

    valid_rows: list[tuple[datetime.date, dict[str, Any]]] = []
    invalid_date_rows = 0
    instrument_mismatches = 0
    date_counts: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            invalid_date_rows += 1
            continue
        day = _date_value(row)
        if day is None:
            invalid_date_rows += 1
            continue
        valid_rows.append((day, row))
        date_counts[day.isoformat()] += 1
        if expected_ins_code and str(row.get("insCode", "")).strip() != expected_ins_code:
            instrument_mismatches += 1

    dates_in_source_order = [day for day, _ in valid_rows]
    sorted_rows = sorted(valid_rows, key=lambda item: item[0])
    duplicate_dates = sorted(day for day, count in date_counts.items() if count > 1)
    date_order = (
        "ascending" if dates_in_source_order == sorted(dates_in_source_order)
        else "descending" if dates_in_source_order == sorted(dates_in_source_order, reverse=True)
        else "mixed"
    )

    positive_close = 0
    missing_counts: Counter[str] = Counter()
    invalid_numeric_counts: Counter[str] = Counter()
    zero_or_negative_counts: Counter[str] = Counter()
    ohlc_violations: list[dict[str, Any]] = []
    returns: list[tuple[str, float]] = []
    gap_flags: list[dict[str, Any]] = []
    numeric_fields = {
        "open": "priceFirst",
        "high": "priceMax",
        "low": "priceMin",
        "close": "pClosing",
        "last": "pDrCotVal",
        "previous_close": "priceYesterday",
        "volume": "qTotTran5J",
        "turnover": "qTotCap",
    }
    previous_day = None
    previous_close = None

    for day, row in sorted_rows:
        day_text = day.isoformat()
        numbers: dict[str, float | None] = {}
        for name, field in numeric_fields.items():
            if row.get(field) is None:
                missing_counts[field] += 1
                numbers[name] = None
                continue
            number = _number(row, field)
            if number is None:
                invalid_numeric_counts[field] += 1
                numbers[name] = None
                continue
            numbers[name] = number
            if name in {"open", "high", "low", "close", "last", "previous_close"} and number <= 0:
                zero_or_negative_counts[field] += 1
        close = numbers["close"]
        if close is not None and close > 0:
            positive_close += 1

        low, high = numbers["low"], numbers["high"]
        open_price = numbers["open"]
        if low is not None and high is not None:
            violations = []
            if low > high:
                violations.append("low_above_high")
            if low <= high and open_price is not None and not low <= open_price <= high:
                violations.append("open_outside_low_high")
            if low <= high and close is not None and not low <= close <= high:
                violations.append("close_outside_low_high")
            if violations and len(ohlc_violations) < 50:
                ohlc_violations.append({"date": day_text, "flags": violations})

        if previous_day is not None:
            gap_days = (day - previous_day).days
            if gap_days > 4 and len(gap_flags) < 50:
                gap_flags.append({
                    "from_date": previous_day.isoformat(),
                    "to_date": day_text,
                    "calendar_days_between": gap_days,
                    "note": "Review against the Iranian trading calendar; weekends/holidays are not inferred.",
                })
        if close is not None and close > 0 and previous_close is not None and previous_close > 0:
            daily_return = close / previous_close - 1
            if abs(daily_return) >= outlier_threshold and len(returns) < 100:
                returns.append((day_text, daily_return))
        previous_day = day
        previous_close = close if close is not None and close > 0 else None

    return {
        "schema_version": 1,
        "source_id": "iran.tsetmc",
        "instrument_code": expected_ins_code,
        "purpose": "historical_sample_quality_audit_only",
        "eligible_for_production_scoring": False,
        "approval_status": "not_approved",
        "row_count": len(rows),
        "valid_date_rows": len(valid_rows),
        "invalid_date_rows": invalid_date_rows,
        "duplicate_date_count": len(duplicate_dates),
        "duplicate_dates_sample": duplicate_dates[:20],
        "source_date_order": date_order,
        "date_range": {
            "first": sorted_rows[0][0].isoformat() if sorted_rows else None,
            "last": sorted_rows[-1][0].isoformat() if sorted_rows else None,
        },
        "instrument_mismatch_rows": instrument_mismatches,
        "positive_close_rows": positive_close,
        "missing_value_counts": dict(sorted(missing_counts.items())),
        "invalid_numeric_counts": dict(sorted(invalid_numeric_counts.items())),
        "zero_or_negative_price_counts": dict(sorted(zero_or_negative_counts.items())),
        "ohlc_consistency_flag_count": sum(
            len(item["flags"]) for item in ohlc_violations
        ),
        "ohlc_consistency_flags_sample": ohlc_violations,
        "large_return_threshold": outlier_threshold,
        "large_return_flag_count_sample_capped": len(returns),
        "large_return_flags": [
            {"date": day, "return": round(value, 6)} for day, value in returns
        ],
        "calendar_gap_flag_count_sample_capped": len(gap_flags),
        "calendar_gap_flags": gap_flags,
        "limitations": [
            "A clean sample does not establish provider authorization or commercial reuse rights.",
            "Price units, corporate-action adjustment, field semantics and publication timestamps remain unverified.",
            "Calendar gaps and large returns are review flags, not automatic errors.",
            "This report does not change the source registry or scoring gate.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Path to a saved TSETMC JSON response; skips network access.")
    parser.add_argument("--ins-code", default=DEFAULT_INSTRUMENT_CODE)
    parser.add_argument("--output", default="/tmp/marketsage-tsetmc-history-audit.json")
    parser.add_argument("--outlier-threshold", type=float, default=DEFAULT_OUTLIER_THRESHOLD)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args(argv)
    try:
        if args.input:
            payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            with TsetmcClient(timeout=args.timeout) as client:
                rows = client.daily_history(args.ins_code)
            payload = {"closingPriceDaily": rows}
        if not isinstance(payload, dict) or not isinstance(payload.get("closingPriceDaily"), list):
            raise ValueError("input must contain a closingPriceDaily array")
        report = audit_history(
            payload["closingPriceDaily"],
            expected_ins_code=args.ins_code,
            outlier_threshold=args.outlier_threshold,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        # Avoid printing exception text from HTTP libraries, which can include URLs.
        print(json.dumps({
            "status": "failed",
            "error_type": type(exc).__name__,
            "details_redacted": True,
        }, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({
        "status": "completed",
        "output": str(output),
        "instrument_code": args.ins_code,
        "row_count": report["row_count"],
        "date_range": report["date_range"],
        "source_date_order": report["source_date_order"],
        "duplicate_date_count": report["duplicate_date_count"],
        "invalid_date_rows": report["invalid_date_rows"],
        "instrument_mismatch_rows": report["instrument_mismatch_rows"],
        "large_return_flag_count_sample_capped": report["large_return_flag_count_sample_capped"],
        "ohlc_consistency_flag_count": report["ohlc_consistency_flag_count"],
        "eligible_for_production_scoring": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
