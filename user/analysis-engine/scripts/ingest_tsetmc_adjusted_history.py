#!/usr/bin/env python3
"""Explicit opt-in CLI to store TSETMC adjusted prices as quarantined candidates."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from temporal_data import PointInTimeStore
from tsetmc_adapter import TSETMCDataError, ingest_adjusted_history


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instrument-code", required=True, help="Numeric TSETMC insCode")
    parser.add_argument(
        "--store-path",
        default=os.getenv("TEMPORAL_STORE_PATH", "/tmp/marketsage-temporal.sqlite3"),
        help="SQLite point-in-time store path; defaults to TEMPORAL_STORE_PATH or /tmp/marketsage-temporal.sqlite3",
    )
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args(argv)

    try:
        store = PointInTimeStore(args.store_path)
        result = ingest_adjusted_history(
            store,
            args.instrument_code,
            timeout=args.timeout,
        )
    except (OSError, ValueError, TSETMCDataError) as exc:
        print(json.dumps({
            "status": "adjusted_ingestion_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "eligible_for_production_scoring": False,
        }, ensure_ascii=False, indent=2))
        return 2

    result["store_path"] = args.store_path
    result["status"] = "candidate_ingested"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
