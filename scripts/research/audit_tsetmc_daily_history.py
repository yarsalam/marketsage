#!/usr/bin/env python3
"""Read-only structural and data-quality audit for imported TSETMC daily histories.

No prices are adjusted, filled, dropped or overwritten. The audit reports raw
record counts, exact identifier tokens, date coverage, duplicate/missing dates,
field coverage/ranges and potential no-trade observations. Calendar gap flags are
diagnostic only; they do not classify closures or missing sessions.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SYMBOLS = {
    "vaghdir": {"ticker": "وغدیر", "primary_inscode": "26014913469567886"},
    "foolad": {"ticker": "فولاد", "primary_inscode": "46348559193224090"},
    "parsian": {"ticker": "پارسیان", "primary_inscode": "9481703061634967"},
}
BASE = Path("data/market-research/iran-equities/adjustment-evidence")
DATE_KEYS = ("dEven", "date", "tradeDate", "tradingDate", "datetime")
FIELDS = (
    "pClosing", "pDrCotVal", "priceYesterday", "priceFirst",
    "priceMax", "priceMin", "qTotTran5J", "qTotCap", "zTotTran",
)


def as_decimal_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float):
        raise ValueError("InsCode decoded as float; precision may be lost")
    return str(value).strip()


def find_object_arrays(value: Any, path: str = "$") -> list[tuple[str, list[dict[str, Any]]]]:
    found: list[tuple[str, list[dict[str, Any]]]] = []
    if isinstance(value, list):
        if value and sum(isinstance(item, dict) for item in value) >= max(1, int(len(value) * 0.8)):
            found.append((path, [item for item in value if isinstance(item, dict)]))
        else:
            for index, item in enumerate(value):
                found.extend(find_object_arrays(item, f"{path}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            found.extend(find_object_arrays(item, f"{path}.{key}"))
    return found


def parse_date(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():
        try:
            return datetime.strptime(text, "%Y%m%d")
        except ValueError:
            return None
    if len(text) >= 10:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def date_value(row: dict[str, Any]) -> tuple[str | None, Any]:
    for key in DATE_KEYS:
        if key in row and row[key] is not None:
            return key, row[key]
    return None, None


def summarize_field(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [row.get(field) for row in rows]
    present = [value for value in values if value is not None]
    numeric: list[Decimal] = []
    invalid_numeric = 0
    for value in present:
        try:
            number = Decimal(str(value).strip())
            if not number.is_finite():
                invalid_numeric += 1
            else:
                numeric.append(number)
        except (TypeError, ValueError, InvalidOperation):
            invalid_numeric += 1
    return {
        "present": len(present),
        "missing": len(values) - len(present),
        "zero": sum(1 for value in present if str(value).strip() in {"0", "0.0"}),
        "invalid_numeric": invalid_numeric,
        "min": str(min(numeric)) if numeric else None,
        "max": str(max(numeric)) if numeric else None,
    }


def summarize_symbol(repo_root: Path, symbol: str) -> dict[str, Any]:
    expected = SYMBOLS[symbol]
    path = repo_root / BASE / symbol / "raw" / "tsetmc" / f"{symbol}_daily_raw.json"
    with path.open("r", encoding="utf-8") as stream:
        payload = json.load(stream)

    arrays = find_object_arrays(payload)
    if not arrays:
        raise ValueError(f"{symbol}: no array of JSON objects found in daily history")
    array_path, rows = max(arrays, key=lambda item: len(item[1]))

    id_counts = Counter()
    id_missing = 0
    for row in rows:
        ins = as_decimal_text(row.get("insCode"))
        if not ins:
            id_missing += 1
        else:
            id_counts[ins] += 1

    date_keys_count = Counter()
    parsed_dates: list[tuple[datetime, int]] = []
    invalid_dates = 0
    for index, row in enumerate(rows):
        key, value = date_value(row)
        if key is None:
            invalid_dates += 1
            continue
        date_keys_count[key] += 1
        parsed = parse_date(value)
        if parsed is None:
            invalid_dates += 1
            continue
        parsed_dates.append((parsed, index))

    sorted_dates = sorted(parsed_dates, key=lambda item: item[0])
    date_counts = Counter(date for date, _ in parsed_dates)
    duplicate_date_rows = sum(count - 1 for count in date_counts.values() if count > 1)
    unique_dates = sorted(date_counts)
    gap_intervals = []
    gaps = []
    for index in range(1, len(unique_dates)):
        delta = (unique_dates[index] - unique_dates[index - 1]).days
        gaps.append(delta)
        if delta >= 5:
            gap_intervals.append({
                "previous_observation": unique_dates[index - 1].strftime("%Y-%m-%d"),
                "next_observation": unique_dates[index].strftime("%Y-%m-%d"),
                "calendar_days_between_observations": delta,
                "calendar_days_without_observation": max(0, delta - 1),
            })
    gap_intervals.sort(key=lambda item: item["calendar_days_between_observations"], reverse=True)
    largest_gaps = sorted(gaps, reverse=True)[:10]

    fields = {field: summarize_field(rows, field) for field in FIELDS if any(field in row for row in rows)}
    zero_activity_samples = []
    for row in rows:
        volume_value = row.get("qTotTran5J")
        trade_count_value = row.get("zTotTran")
        volume = str(volume_value).strip() if volume_value is not None else ""
        trade_count = str(trade_count_value).strip() if trade_count_value is not None else ""
        if volume in {"0", "0.0"} or trade_count in {"0", "0.0"}:
            zero_activity_samples.append({
                "dEven": row.get("dEven"),
                "pClosing": row.get("pClosing"),
                "pDrCotVal": row.get("pDrCotVal"),
                "priceYesterday": row.get("priceYesterday"),
                "qTotTran5J": row.get("qTotTran5J"),
                "zTotTran": row.get("zTotTran"),
                "qTotCap": row.get("qTotCap"),
            })
            if len(zero_activity_samples) >= 20:
                break

    zero_volume_rows = sum(
        1 for row in rows
        if row.get("qTotTran5J") is not None and str(row.get("qTotTran5J")).strip() in {"0", "0.0"}
    )
    zero_trade_count_rows = sum(
        1 for row in rows
        if row.get("zTotTran") is not None and str(row.get("zTotTran")).strip() in {"0", "0.0"}
    )

    first_record = rows[0] if rows else {}
    last_record = rows[-1] if rows else {}
    return {
        "symbol": symbol,
        "ticker": expected["ticker"],
        "source_relative": str(path.relative_to(repo_root)),
        "record_array_path": array_path,
        "row_count": len(rows),
        "row_field_names": sorted({key for row in rows for key in row}),
        "date_field_counts": dict(date_keys_count),
        "valid_date_rows": len(parsed_dates),
        "invalid_or_missing_date_rows": invalid_dates,
        "date_min": unique_dates[0].strftime("%Y-%m-%d") if unique_dates else None,
        "date_max": unique_dates[-1].strftime("%Y-%m-%d") if unique_dates else None,
        "duplicate_date_extra_rows": duplicate_date_rows,
        "unique_date_count": len(unique_dates),
        "descending_date_order": bool(parsed_dates) and all(
            parsed_dates[index][0] >= parsed_dates[index + 1][0]
            for index in range(len(parsed_dates) - 1)
        ),
        "largest_calendar_day_gaps_diagnostic_only": largest_gaps,
        "gap_intervals_ge_5_calendar_days": gap_intervals[:30],
        "zero_activity_sample_records_first_20": zero_activity_samples,
        "primary_insCode": expected["primary_inscode"],
        "insCode_row_counts": dict(id_counts),
        "primary_id_match_rows": id_counts.get(expected["primary_inscode"], 0),
        "unmatched_id_rows": sum(count for code, count in id_counts.items() if code != expected["primary_inscode"]),
        "missing_id_rows": id_missing,
        "zero_volume_rows_qTotTran5J": zero_volume_rows,
        "zero_trade_count_rows_zTotTran": zero_trade_count_rows,
        "fields": fields,
        "first_record": first_record,
        "last_record": last_record,
        "interpretation": [
            "Raw history only; no price adjustment was applied.",
            "Calendar gaps are diagnostics, not proof of missing trading sessions or exchange closures.",
            "Zero trade/volume rows require source-field and market-state interpretation.",
            "Price basis, Rial/Toman unit and stale/no-trade semantics require separate source verification."
        ]
    }


def run_audit(repo_root: Path) -> dict[str, Any]:
    symbols = {symbol: summarize_symbol(repo_root, symbol) for symbol in SYMBOLS}
    return {
        "audit_version": "1.0.0",
        "scope": "three imported Iranian equity pilot daily histories",
        "method": "read-only; exact Python integer/string identifier handling; no fills or adjustments",
        "symbols": symbols,
        "summary": {
            "symbol_count": len(symbols),
            "total_daily_rows": sum(item["row_count"] for item in symbols.values()),
            "all_daily_rows_match_primary_id": all(
                item["primary_id_match_rows"] == item["row_count"]
                and item["unmatched_id_rows"] == 0
                and item["missing_id_rows"] == 0
                for item in symbols.values()
            ),
            "symbols_with_duplicate_date_rows": [
                symbol for symbol, item in symbols.items() if item["duplicate_date_extra_rows"]
            ],
            "symbols_with_invalid_or_missing_dates": [
                symbol for symbol, item in symbols.items() if item["invalid_or_missing_date_rows"]
            ]
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_audit(args.repo_root.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print("DAILY_HISTORY_AUDIT_JSON_BEGIN")
    print(rendered, end="")
    print("DAILY_HISTORY_AUDIT_JSON_END")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
