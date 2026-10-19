#!/usr/bin/env python3
"""One-request-at-a-time, research-only live smoke for an Iranian TSETMC instrument.

This deliberately does not scrape TGJU, collect news, or enable MarketSage scoring.
It records response shape, selected instrument identity, date range, row count and
a small sample so a human can review source semantics before broader collection.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests

BASE = "https://cdn.tsetmc.com/api"
USER_AGENT = "MarketSage-research-smoke/0.1 (+read-only; bounded request)"
TIMEOUT = 20


def normalized(value: Any) -> str:
    return str(value or "").replace("\u064a", "\u06cc").replace("\u0643", "\u06a9").strip()


def first_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, list) and (not value or isinstance(value[0], dict)):
                return [x for x in value if isinstance(x, dict)]
    return []


def find_field(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if row.get(name) not in (None, ""):
            return row[name]
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="فولاد", help="Exact Iranian instrument name to look up (default: فولاد)")
    parser.add_argument("--out-dir", default="artifacts/iran-free-data-smoke")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "source_id": "iran.tsetmc",
        "purpose": "bounded live source smoke; not production approval",
        "symbol_query": args.symbol,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "eligible_for_scoring": False,
        "requests_attempted": 0,
        "checks": {},
        "limitations": [
            "One instrument only; not a market-wide coverage assessment.",
            "Price units, adjustment methodology, corporate actions, volume semantics and legal collection rights remain unverified.",
            "Retrieval time is not asserted to be the original observation/publication time.",
        ],
    }
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    try:
        # One bounded search request.
        report["requests_attempted"] += 1
        search_url = f"{BASE}/Instrument/GetInstrumentSearch/{quote(args.symbol, safe='')}"
        response = session.get(search_url, timeout=TIMEOUT)
        report["checks"]["search_http_status"] = response.status_code
        response.raise_for_status()
        search_payload = response.json()
        candidates = first_list(search_payload)
        report["checks"]["search_payload_type"] = type(search_payload).__name__
        report["checks"]["search_candidate_count"] = len(candidates)

        query = normalized(args.symbol)
        # Prefer an exact normalized display-name match; never silently choose candidate #1.
        exact = []
        for item in candidates:
            display = find_field(item, ("lVal18AFC", "lVal30", "instrumentName", "name", "symbol"))
            if normalized(display) == query:
                exact.append(item)
        if not exact:
            report["status"] = "blocked_no_exact_instrument_match"
            report["checks"]["candidate_name_samples"] = [
                find_field(x, ("lVal18AFC", "lVal30", "instrumentName", "name", "symbol"))
                for x in candidates[:10]
            ]
            raise RuntimeError("Search response did not contain an exact instrument-name match; refusing to select an arbitrary result.")

        selected = exact[0]
        instrument_code = find_field(selected, ("insCode", "instrumentCode", "instrument_code"))
        if not instrument_code:
            report["status"] = "blocked_missing_instrument_code"
            report["checks"]["selected_record_keys"] = sorted(selected.keys())
            raise RuntimeError("Exact match found but instrument code field was not recognized.")

        report["instrument"] = {
            "requested_name": args.symbol,
            "matched_name": find_field(selected, ("lVal18AFC", "lVal30", "instrumentName", "name", "symbol")),
            "instrument_code": str(instrument_code),
            "record_keys": sorted(selected.keys()),
        }

        # Keep the request count bounded: exactly one daily-history request after search.
        time.sleep(1.0)
        report["requests_attempted"] += 1
        history_url = f"{BASE}/ClosingPrice/GetClosingPriceDailyList/{quote(str(instrument_code), safe='')}/0"
        history_response = session.get(history_url, timeout=TIMEOUT)
        report["checks"]["history_http_status"] = history_response.status_code
        history_response.raise_for_status()
        history_payload = history_response.json()
        rows = first_list(history_payload)
        report["checks"]["history_payload_type"] = type(history_payload).__name__
        report["checks"]["history_row_count"] = len(rows)
        report["checks"]["history_payload_top_level_keys"] = sorted(history_payload.keys()) if isinstance(history_payload, dict) else None

        if not rows:
            report["status"] = "reachable_but_no_history_rows"
            raise RuntimeError("History endpoint returned no recognizable row list.")

        frame = pd.DataFrame(rows)
        frame.to_csv(out_dir / "tsetmc_daily_history.csv", index=False)
        date_col = next((c for c in ("dEven", "date", "tradeDate") if c in frame.columns), None)
        close_col = next((c for c in ("pClosing", "close", "closingPrice") if c in frame.columns), None)
        last_col = next((c for c in ("pDrCotVal", "last", "lastPrice") if c in frame.columns), None)
        volume_col = next((c for c in ("qTotTran5J", "volume", "totalVolume") if c in frame.columns), None)
        dates = []
        if date_col:
            raw_dates = frame[date_col].dropna().astype(str)
            parsed = pd.to_datetime(raw_dates, format="%Y%m%d", errors="coerce")
            dates = [x.strftime("%Y-%m-%d") for x in parsed.dropna()]
        report["checks"].update({
            "history_columns": list(frame.columns),
            "recognized_date_column": date_col,
            "recognized_closing_price_column": close_col,
            "recognized_last_price_column": last_col,
            "recognized_volume_column": volume_col,
            "date_parseable_row_count": len(dates),
            "first_date_seen": min(dates) if dates else None,
            "last_date_seen": max(dates) if dates else None,
            "sample_rows": frame.head(3).where(pd.notna(frame.head(3)), None).to_dict(orient="records"),
        })
        report["status"] = "reachable_data_received"
        report["interpretation"] = (
            "Transport and basic schema were observed. This is not proof of complete/adjusted history, "
            "valid units, collection rights, or suitability for backtesting."
        )
    except Exception as exc:
        report.setdefault("status", "probe_failed")
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)[:500]
    finally:
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        (out_dir / "tsetmc_smoke_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    return 0 if report.get("status") == "reachable_data_received" else 1


if __name__ == "__main__":
    raise SystemExit(main())
