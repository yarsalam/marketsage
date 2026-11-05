#!/usr/bin/env python3
"""Audit a local Yahoo research download without printing market values.

This is a structural/quality screen, not source approval or a backtest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

PRICE_COLUMNS = ("Close", "Adj Close", "Open", "High", "Low")
ACTION_COLUMNS = ("Dividends", "Stock Splits", "Capital Gains")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_file(path: Path) -> dict:
    result = {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "status": "unknown",
        "issues": [],
    }
    try:
        frame = pd.read_csv(path)
        if frame.empty:
            raise ValueError("empty_table")
        date_col = "Date" if "Date" in frame.columns else frame.columns[0]
        dates = pd.to_datetime(frame[date_col], errors="coerce", utc=True)
        result.update({
            "status": "inspected",
            "row_count": int(len(frame)),
            "columns": [str(c) for c in frame.columns],
            "date_column": str(date_col),
            "invalid_dates": int(dates.isna().sum()),
            "first_date_utc": dates.min().isoformat() if dates.notna().any() else None,
            "last_date_utc": dates.max().isoformat() if dates.notna().any() else None,
            "duplicate_dates": int(dates[dates.notna()].duplicated().sum()),
            "monotonic_dates": bool(dates.dropna().is_monotonic_increasing),
            "missing_by_column": {str(c): int(n) for c, n in frame.isna().sum().items()},
            "price_checks": {},
            "action_columns_present": [c for c in ACTION_COLUMNS if c in frame.columns],
        })
        for column in PRICE_COLUMNS:
            if column not in frame.columns:
                continue
            values = pd.to_numeric(frame[column], errors="coerce")
            finite = np.isfinite(values.to_numpy(dtype=float, na_value=np.nan))
            result["price_checks"][column] = {
                "non_numeric_or_nonfinite": int((~finite).sum()),
                "non_positive": int((values[values.notna()] <= 0).sum()),
            }
        for column in ("Close", "Adj Close"):
            if column in frame.columns and frame[column].notna().sum() == 0:
                result["issues"].append(f"{column}_entirely_missing")
        if result["invalid_dates"]:
            result["issues"].append("invalid_dates")
        if result["duplicate_dates"]:
            result["issues"].append("duplicate_dates")
        if not result["monotonic_dates"]:
            result["issues"].append("dates_not_monotonic")
        if "Close" not in frame.columns:
            result["issues"].append("close_column_missing")
        if "Adj Close" not in frame.columns:
            result["issues"].append("adjusted_close_column_missing")
        for column, checks in result["price_checks"].items():
            if checks["non_numeric_or_nonfinite"]:
                result["issues"].append(f"{column}_invalid_values")
            if checks["non_positive"]:
                result["issues"].append(f"{column}_non_positive_values")
    except Exception as exc:
        result["status"] = "error"
        result["error_type"] = type(exc).__name__
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("/tmp/marketsage-yahoo-stage4"))
    parser.add_argument("--output", type=Path, default=Path("/tmp/marketsage-yahoo-quality-audit.json"))
    args = parser.parse_args()
    data_dir = args.data_dir.expanduser().resolve()
    manifest_path = data_dir / "manifest.json"
    if not manifest_path.is_file():
        parser.error(f"manifest.json not found in {data_dir}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        parser.error(f"manifest.json is unreadable ({type(exc).__name__})")

    symbol_results = []
    for symbol, info in manifest.get("symbols", {}).items():
        filename = info.get("file")
        if info.get("status") != "downloaded_unapproved" or not filename:
            symbol_results.append({"symbol": symbol, "status": info.get("status", "unknown"), "issues": ["not_downloaded"]})
            continue
        path = (data_dir / filename).resolve()
        if path.parent != data_dir or not path.is_file():
            symbol_results.append({"symbol": symbol, "status": "error", "issues": ["file_missing_or_outside_data_dir"]})
            continue
        audited = audit_file(path)
        audited["symbol"] = symbol
        audited["manifest_row_count_matches"] = audited.get("row_count") == info.get("row_count")
        if not audited["manifest_row_count_matches"]:
            audited["issues"].append("manifest_row_count_mismatch")
        symbol_results.append(audited)

    report = {
        "schema_version": 1,
        "purpose": "research_only_quality_screen_not_source_approval",
        "data_dir": str(data_dir),
        "provider": manifest.get("provider"),
        "retrieved_at_utc": manifest.get("retrieved_at_utc"),
        "symbols": symbol_results,
        "approval_gates": {
            "provenance_and_terms": "unknown",
            "currency_and_units": "unknown",
            "adjusted_price_semantics": "unknown_pending_review",
            "point_in_time_availability_and_revisions": "unknown",
            "survivorship_bias": "unknown",
            "representative_of_iranian_market": "fail",
            "eligible_for_production_scoring": False,
        },
    }
    args.output.expanduser().resolve().write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Symbols inspected: {len(symbol_results)}")
    print(f"File errors: {sum(s.get('status') == 'error' for s in symbol_results)}")
    print(f"Symbols with structural issues: {sum(bool(s.get('issues')) for s in symbol_results)}")
    for item in symbol_results:
        if item.get("issues"):
            print(f"- {item.get('symbol', item.get('file'))}: {', '.join(item['issues'])}")
        elif item.get("status") == "inspected":
            print(f"- {item['symbol']}: rows={item['row_count']}; duplicate_dates={item['duplicate_dates']}; invalid_dates={item['invalid_dates']}; missing_close={item['missing_by_column'].get('Close', 0)}; missing_adj_close={item['missing_by_column'].get('Adj Close', 0)}")
    print(f"Report: {args.output.expanduser().resolve()}")
    print("Approval remains unknown/fail-closed; no investment ranking is enabled.")
    return 1 if any(s.get("status") == "error" or s.get("issues") for s in symbol_results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
