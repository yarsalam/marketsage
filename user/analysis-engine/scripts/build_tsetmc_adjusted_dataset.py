#!/usr/bin/env python3
"""Build a quarantined CSV from saved TSETMC raw history and adjusted-chart payloads.

This tool does not compute adjustment factors. It joins the provider's a=1 chart
prices to raw daily rows and leaves unmatched dates blank instead of falling back
to raw prices.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from tsetmc_adapter import TSETMCDataError, parse_adjusted_chart


COLUMNS = [
    "date", "instrument_code",
    "close_raw", "last_raw", "open_raw", "high_raw", "low_raw",
    "prev_close_raw", "volume_raw", "trade_value_raw",
    "open_adj", "high_adj", "low_adj", "last_adj", "close_adj",
    "chart_volume", "adjustment_source", "adjustment_status",
    "eligible_for_scoring",
]


def read_json(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"Required input file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _iso_day(value: Any, index: int) -> tuple[str, str]:
    raw = str(value).strip()
    try:
        day = datetime.strptime(raw, "%Y%m%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"daily history row {index} has invalid dEven") from exc
    return raw, day.isoformat()


def _ratio_summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None}
    return {
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def build_dataset(
    daily_payload: Any,
    chart_payload: Any,
    *,
    instrument_code: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not instrument_code.isdigit():
        raise ValueError("instrument_code must be numeric")
    if not isinstance(daily_payload, list) or not daily_payload:
        raise ValueError("daily_history_raw.json must contain a non-empty JSON array")

    adjusted = parse_adjusted_chart(chart_payload)
    daily_by_date: dict[str, dict[str, Any]] = {}
    iso_by_date: dict[str, str] = {}
    for index, raw in enumerate(daily_payload):
        if not isinstance(raw, dict):
            raise ValueError(f"daily history row {index} must be an object")
        date_key, iso_day = _iso_day(raw.get("dEven"), index)
        if date_key in daily_by_date:
            raise ValueError(f"duplicate daily-history date: {date_key}")
        daily_by_date[date_key] = raw
        iso_by_date[date_key] = iso_day

    rows: list[dict[str, Any]] = []
    ratios: list[float] = []
    for date_key in sorted(daily_by_date):
        raw = daily_by_date[date_key]
        chart = adjusted.get(date_key)
        raw_close_value = raw.get("pClosing")
        try:
            raw_close = float(raw_close_value)
        except (TypeError, ValueError):
            raw_close = math.nan
        adj_close = chart["close_adj"] if chart else None
        if adj_close is not None and math.isfinite(raw_close) and raw_close > 0:
            ratios.append(adj_close / raw_close)

        rows.append({
            "date": iso_by_date[date_key],
            "instrument_code": instrument_code,
            "close_raw": raw.get("pClosing"),
            "last_raw": raw.get("pDrCotVal"),
            "open_raw": raw.get("priceFirst"),
            "high_raw": raw.get("priceMax"),
            "low_raw": raw.get("priceMin"),
            "prev_close_raw": raw.get("priceYesterday"),
            "volume_raw": raw.get("qTotTran5J"),
            "trade_value_raw": raw.get("qTotCap"),
            "open_adj": chart["open_adj"] if chart else None,
            "high_adj": chart["high_adj"] if chart else None,
            "low_adj": chart["low_adj"] if chart else None,
            "last_adj": chart["last_adj"] if chart else None,
            "close_adj": adj_close,
            "chart_volume": chart["chart_volume"] if chart else None,
            "adjustment_source": "tsetmc_legacy_chart_a1",
            "adjustment_status": (
                "provider_supplied_unvalidated" if chart
                else "missing_adjusted_chart_row"
            ),
            "eligible_for_scoring": False,
        })

    covered = sum(row["close_adj"] is not None for row in rows)
    dates = [row["date"] for row in rows]
    report = {
        "source_id": "iran.tsetmc",
        "instrument_code": instrument_code,
        "status": "candidate_dataset_built",
        "adjustment_source": "tsetmc_legacy_chart_a1",
        "adjustment_status": "provider_supplied_unvalidated",
        "daily_history_rows": len(rows),
        "rows_with_adjusted_close": covered,
        "rows_without_adjusted_close": len(rows) - covered,
        "adjusted_close_coverage_fraction": covered / len(rows),
        "date_range": {"first": min(dates), "last": max(dates)},
        "adjusted_to_raw_close_ratio": _ratio_summary(ratios),
        "missing_adjusted_dates_are_filled": False,
        "raw_prices_preserved": True,
        "eligible_for_scoring": False,
        "limitations": [
            "Adjusted OHLC-like fields use an empirically compared positional mapping of an undocumented legacy endpoint.",
            "This report measures coverage and scale only; it does not prove every corporate action is correct.",
            "Price unit/currency, redistribution rights, suspensions, publication timestamps and point-in-time availability remain unverified.",
            "Rows missing from the adjusted chart remain blank and must not be replaced with unadjusted prices.",
        ],
    }
    return rows, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="/tmp/marketsage-tsetmc-adjustments")
    parser.add_argument("--instrument-code", default="46348559193224090")
    parser.add_argument("--out-csv", default="/tmp/foulad_adjusted.csv")
    parser.add_argument("--out-report", default="/tmp/foulad_adjustment_quality_report.json")
    args = parser.parse_args()

    root = Path(args.data_dir)
    try:
        daily = read_json(root / "daily_history_raw.json")
        chart = read_json(root / "chart_adjusted_raw.json")
        rows, report = build_dataset(daily, chart, instrument_code=args.instrument_code)
        csv_path = Path(args.out_csv)
        report_path = Path(args.out_report)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        report["csv_path"] = str(csv_path)
        report["report_path"] = str(report_path)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, ValueError, TSETMCDataError) as exc:
        print(json.dumps({
            "status": "dataset_build_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "eligible_for_scoring": False,
        }, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
