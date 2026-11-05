#!/usr/bin/env python3
"""Opt-in fetch and local export for a single Tindex indicator candle series.

Requires TINDEX_API_BASE_URL and TINDEX_API_TOKEN in the caller's environment.
This script never writes the token or provider payload into the console report. It
stores raw/normalized candidates in the configured SQLite store and optionally
exports the successful stored candles to a local CSV.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from iran_live_data import get_candidate_indicator_candles, refresh_tindex_indicator_candles


EXPORT_COLUMNS = (
    "source_id", "instrument_key", "observation_date",
    "open_raw", "high_raw", "low_raw", "close_raw",
    "unit", "partial", "retrieved_at",
    "observation_precision", "source_publication_time",
    "eligible_for_scoring",
)


def export_candidate_csv(slug: str, output: Path) -> int:
    result = get_candidate_indicator_candles(slug)
    if result["status"] != "candidate_history_available":
        raise RuntimeError("No successful history snapshot is available to export")
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = result["candles"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "source_id": result["source_id"],
                "instrument_key": result["instrument_key"],
                "observation_date": row["observation_date"],
                "open_raw": row["open_raw"],
                "high_raw": row["high_raw"],
                "low_raw": row["low_raw"],
                "close_raw": row["close_raw"],
                "unit": row["unit"],
                "partial": str(row["partial"]).lower(),
                "retrieved_at": row["retrieved_at"],
                "observation_precision": row["observation_precision"],
                "source_publication_time": "",
                "eligible_for_scoring": "false",
            })
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True, help="Tindex slug from boards/categories, e.g. GOLD-18K, USD-EXCHANGE-RATE, btc")
    parser.add_argument("--range", dest="requested_range", choices=("1m", "3m"), default="3m")
    parser.add_argument("--interval", choices=("daily", "weekly"), default="daily")
    parser.add_argument("--out-csv", help="Optional local path for exporting the latest successful candidate candles")
    args = parser.parse_args(argv)

    if not os.getenv("TINDEX_API_BASE_URL", "").strip() or not os.getenv("TINDEX_API_TOKEN", "").strip():
        print(json.dumps({
            "status": "not_configured",
            "required_environment": ["TINDEX_API_BASE_URL", "TINDEX_API_TOKEN"],
            "token_was_logged": False,
            "eligible_for_scoring": False,
        }, ensure_ascii=False, indent=2))
        return 2

    try:
        result = refresh_tindex_indicator_candles(
            args.slug,
            requested_range=args.requested_range,
            interval=args.interval,
        )
        result["database_path"] = os.getenv("IRAN_DATA_DB_PATH", "/data/iran-market.sqlite3")
        if args.out_csv:
            csv_path = Path(args.out_csv).expanduser()
            result["exported_rows"] = export_candidate_csv(args.slug, csv_path)
            result["exported_csv"] = str(csv_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        # Keep endpoint body, token and request headers out of CLI output.
        print(json.dumps({
            "status": "candidate_ingestion_failed",
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
            "token_was_logged": False,
            "eligible_for_scoring": False,
        }, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
