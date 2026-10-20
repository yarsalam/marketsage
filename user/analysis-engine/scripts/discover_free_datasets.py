#!/usr/bin/env python3
"""Inventory free-access candidates and run bounded, sanitized source probes.

This script never changes source approval, saves provider raw payloads, prints
quotes, or puts credentials in a report. Live probes are small and opt-in by
source; the default probes only four public-access candidates.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = Path(__file__).resolve().parents[3]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from binance_public_provider import BinancePublicClient, BinancePublicError
from codal_provider import CodalClient
from fred_alfred_provider import FredAlfredClient, FredProviderError
from gdelt_news_provider import GdeltDocClient, GdeltError
from tindex_normalizer import normalize_indicator_candles
from tindex_provider import TindexClient, TindexError
from tsetmc_provider import TsetmcClient
from world_bank_provider import WorldBankClient, WorldBankError

DEFAULT_SOURCES = (
    "iran.tsetmc",
    "iran.codal",
    "global.world_bank_indicators",
    "global.binance_spot_public",
)
SUPPORTED_SOURCES = (
    *DEFAULT_SOURCES,
    "iran.tindex.public_api",
    "iran.tindex.candles",
    "us.fred.alfred",
    "global.gdelt_doc_api",
)


def _shape(value: Any) -> dict[str, Any]:
    """Describe response structure without copying prices, headlines or tokens."""
    if isinstance(value, Mapping):
        return {
            "type": "object",
            "keys": sorted(str(key) for key in value.keys())[:80],
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        item_shape = _shape(value[0]) if value else None
        return {"type": "array", "length": len(value), "first_item_shape": item_shape}
    return {"type": type(value).__name__}


def _find_lists(value: Any) -> list[list[dict[str, Any]]]:
    found: list[list[dict[str, Any]]] = []
    if isinstance(value, list):
        rows = [item for item in value if isinstance(item, dict)]
        if rows or not value:
            found.append(rows)
        for item in value:
            found.extend(_find_lists(item))
    elif isinstance(value, dict):
        for item in value.values():
            found.extend(_find_lists(item))
    return found


def _summarize_search(payload: Any, query: str) -> dict[str, Any]:
    """Return search result shape and exact-match count without raw records."""
    records = max(_find_lists(payload), key=len, default=[])
    normalized_query = str(query).replace("\u064a", "\u06cc").replace("\u0643", "\u06a9").strip()
    alias_fields = ("lVal18AFC", "lVal30", "instrumentName", "name", "symbol", "ticker")
    matches = []
    for row in records:
        aliases = [
            str(row.get(field, "")).replace("\u064a", "\u06cc").replace("\u0643", "\u06a9").strip()
            for field in alias_fields if row.get(field) not in (None, "")
        ]
        if normalized_query in aliases:
            matches.append(row)
    codes = [
        row.get("insCode") or row.get("instrumentCode") or row.get("instrument_code")
        for row in matches
    ]
    has_code = sum(1 for code in codes if code is not None and str(code).isdigit())
    public_matches = []
    for row in matches[:10]:
        code = row.get("insCode") or row.get("instrumentCode") or row.get("instrument_code")
        public_matches.append({
            "instrument_id": str(code) if code is not None and str(code).isdigit() else None,
            "provider_ticker": row.get("lVal30") or row.get("symbol") or row.get("ticker"),
            "provider_name": row.get("lVal18AFC") or row.get("instrumentName") or row.get("name"),
        })
    return {
        "response_shape": _shape(payload),
        "candidate_record_count": len(records),
        "exact_name_match_count": len(matches),
        "exact_matches_with_numeric_instrument_id": has_code,
        "exact_match_identity_samples": public_matches,
        "raw_payload_saved": False,
    }


def _write_csv(path: Path, records: list[dict[str, Any]]) -> int:
    if not records:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in records for key in row.keys()))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({
                key: (str(value) if value is not None else "")
                for key, value in row.items()
            })
    return len(records)


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")[:100] or "candidate"


def _run_one(
    source_id: str,
    *,
    export_dir: Path | None,
    tsetmc_queries: list[str],
    tindex_slugs: list[str],
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    record: dict[str, Any] = {
        "source_id": source_id,
        "started_at_utc": started,
        "status": "probe_failed",
        "eligible_for_scoring": False,
        "raw_payload_saved": False,
    }
    try:
        if source_id == "iran.tsetmc":
            queries = tsetmc_queries or ["فولاد"]
            outcomes = []
            with TsetmcClient(timeout=15.0) as client:
                for query in queries:
                    payload = client.search_instruments(query)
                    outcomes.append({"query": query, **_summarize_search(payload, query)})
            record.update(status="reachable_response_received", query_count=len(queries), queries=outcomes)
        elif source_id == "iran.codal":
            with CodalClient(timeout=15.0) as client:
                payload = client.search_disclosures(page=1, page_size=3)
            record.update(status="reachable_response_received", response_shape=_shape(payload))
            lists = _find_lists(payload)
            record["candidate_record_count"] = max((len(rows) for rows in lists), default=0)
        elif source_id == "global.world_bank_indicators":
            with WorldBankClient(timeout=12.0) as client:
                rows = client.indicator(
                    "IRN", "FP.CPI.TOTL.ZG", start_year=2000, end_year=2025, per_page=100
                )
            available = [row for row in rows if row["value"] is not None]
            record.update(
                status="reachable_schema_validated_candidate",
                indicator_id="FP.CPI.TOTL.ZG",
                row_count=len(rows),
                non_null_values=len(available),
                first_observation_year=min((row["observation_year"] for row in rows), default=None),
                last_observation_year=max((row["observation_year"] for row in rows), default=None),
                publication_timestamps_known=False,
            )
            if export_dir is not None:
                target = export_dir / "world_bank_IRN_FP.CPI.TOTL.ZG_candidate.csv"
                record["candidate_export_rows"] = _write_csv(target, rows)
                record["candidate_export_path"] = str(target)
        elif source_id == "global.binance_spot_public":
            with BinancePublicClient(timeout=10.0) as client:
                rows = client.klines("BTCUSDT", interval="1d", limit=5)
            dates = [row["observation_time_utc"] for row in rows]
            record.update(
                status="reachable_schema_validated_candidate",
                instrument_key="BTCUSDT",
                interval="1d",
                row_count=len(rows),
                first_observation_time_utc=min(dates, default=None),
                last_observation_time_utc=max(dates, default=None),
                quote_asset_inferred=False,
            )
            if export_dir is not None:
                target = export_dir / "binance_BTCUSDT_1d_candidate.csv"
                record["candidate_export_rows"] = _write_csv(target, rows)
                record["candidate_export_path"] = str(target)
        elif source_id == "iran.tindex.public_api":
            with TindexClient(timeout=15.0) as client:
                payload = client.currency_rates()
            record.update(
                status="reachable_response_received",
                response_shape=_shape(payload),
                note="Snapshot only; not historical data or source approval.",
            )
            if isinstance(payload, dict) and payload.get("success") is True:
                data = payload.get("data")
                record["record_count"] = len(data) if isinstance(data, list) else None
        elif source_id == "iran.tindex.candles":
            slugs = tindex_slugs or ["GOLD-18K", "USD-EXCHANGE-RATE", "btc"]
            if len(slugs) > 3:
                raise ValueError("at most three Tindex slugs can be queried in a single run")
            results = []
            # Reuse a single client so the local three-requests/minute limiter is effective.
            with TindexClient(timeout=15.0) as client:
                for slug in slugs:
                    item: dict[str, Any] = {
                        "requested_slug": slug,
                        "status": "probe_failed",
                        "eligible_for_scoring": False,
                    }
                    try:
                        payload = client.indicator_candles(slug, range="3m", interval="daily")
                        rows = normalize_indicator_candles(payload)
                        item.update(
                            status="reachable_schema_validated_candidate",
                            row_count=len(rows),
                            first_observation_date=min((row["observation_date"] for row in rows), default=None),
                            last_observation_date=max((row["observation_date"] for row in rows), default=None),
                            unit_reported=next((row.get("unit") for row in rows if row.get("unit")), None),
                        )
                        if export_dir is not None and rows:
                            target = export_dir / f"tindex_{_safe_filename(slug)}_daily_candidate.csv"
                            item["candidate_export_rows"] = _write_csv(target, rows)
                            item["candidate_export_path"] = str(target)
                    except Exception as exc:
                        item.update(status="probe_failed", error_type=type(exc).__name__, error_detail_redacted=True)
                    results.append(item)
            record.update(
                status="reachable_response_received" if any(
                    result["status"] == "reachable_schema_validated_candidate" for result in results
                ) else "probe_failed",
                requests_attempted=len(slugs),
                results=results,
                note="Tindex quota is shared account-wide; no more than three requests were made.",
            )
        elif source_id == "us.fred.alfred":
            with FredAlfredClient(timeout=15.0) as client:
                rows = client.observations("FEDFUNDS", limit=3)
            record.update(
                status="reachable_response_received",
                response_shape=_shape(rows),
                record_count=len(rows) if isinstance(rows, list) else None,
                note="FRED observation period/vintage metadata is not exact intraday release time.",
            )
            if export_dir is not None and isinstance(rows, list):
                target = export_dir / "fred_FEDFUNDS_candidate.csv"
                record["candidate_export_rows"] = _write_csv(target, rows)
                record["candidate_export_path"] = str(target)
        elif source_id == "global.gdelt_doc_api":
            with GdeltDocClient(timeout=15.0) as client:
                payload = client.search_articles("Iran", max_records=3)
            record.update(
                status="reachable_response_received",
                response_shape=_shape(payload),
                note="Explicit probe only. GDELT may return HTTP 429; do not retry rapidly.",
            )
        else:
            raise ValueError("unknown source ID")
    except Exception as exc:
        # Never copy arbitrary exception text; it can include URLs or credentials.
        record.update(status="probe_failed", error_type=type(exc).__name__, error_detail_redacted=True)
        if source_id == "global.gdelt_doc_api" and isinstance(exc, GdeltError):
            record["safe_error_detail"] = str(exc)
            record["error_detail_redacted"] = False
        if source_id == "us.fred.alfred" and isinstance(exc, FredProviderError):
            record["safe_error_detail"] = str(exc)
            record["error_detail_redacted"] = False
        if source_id == "global.binance_spot_public" and isinstance(exc, BinancePublicError):
            record["safe_error_detail"] = str(exc)
            record["error_detail_redacted"] = False
        if source_id == "global.world_bank_indicators" and isinstance(exc, WorldBankError):
            record["safe_error_detail"] = str(exc)
            record["error_detail_redacted"] = False
        if source_id.startswith("iran.tindex") and isinstance(exc, TindexError):
            record["safe_error_detail"] = str(exc)
            record["error_detail_redacted"] = False
    record["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    return record


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("inventory", "probe"), default="inventory")
    parser.add_argument("--source", action="append", choices=SUPPORTED_SOURCES,
                        help="Select sources for mode=probe; repeat to batch several sources.")
    parser.add_argument("--output", help="Optional JSON report path. Parent directory is created.")
    parser.add_argument("--export-dir", help="Optional local directory for candidate CSV exports.")
    parser.add_argument("--tsetmc-query", action="append",
                        help="Exact TSETMC instrument-name search query; may be repeated, maximum 20.")
    parser.add_argument("--tindex-slug", action="append",
                        help="Tindex candle slug; at most three per run.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    catalog_path = REPO_DIR / "docs" / "free_dataset_source_catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"status": "catalog_error", "production_approved": False}, indent=2))
        return 2

    if args.tsetmc_query and len(args.tsetmc_query) > 20:
        print(json.dumps({"error": "at most 20 TSETMC search queries per run"}, indent=2))
        return 2
    if args.tindex_slug and len(args.tindex_slug) > 3:
        print(json.dumps({"error": "at most three Tindex slugs per run"}, indent=2))
        return 2

    if args.mode == "inventory":
        report = {
            "report_version": "1.0.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "inventory_only_no_network_requests",
            "catalog_version": catalog.get("catalog_version"),
            "free_access_is_not_reuse_license": True,
            "production_approved": False,
            "sources": catalog.get("sources", []),
        }
    else:
        selected = list(dict.fromkeys(args.source or DEFAULT_SOURCES))
        if not args.source:
            if os.getenv("TINDEX_API_BASE_URL", "").strip() and os.getenv("TINDEX_API_TOKEN", "").strip():
                selected.append("iran.tindex.candles")
            if os.getenv("FRED_API_KEY", "").strip():
                selected.append("us.fred.alfred")
        if "iran.tindex.public_api" in selected and "iran.tindex.candles" in selected:
            print(json.dumps({
                "error": "Do not combine Tindex currency-rates and candle probes in one run; the free-tier account quota is shared.",
                "hint": "Run one Tindex probe pack at a time. Candle mode makes at most three requests.",
                "production_approved": False,
            }, ensure_ascii=False, indent=2))
            return 2
        results = []
        export_dir = Path(args.export_dir).expanduser() if args.export_dir else None
        if export_dir is not None:
            export_dir.mkdir(parents=True, exist_ok=True)
        for source_id in selected:
            if source_id.startswith("iran.tindex") and not (
                os.getenv("TINDEX_API_BASE_URL", "").strip()
                and os.getenv("TINDEX_API_TOKEN", "").strip()
            ):
                results.append({
                    "source_id": source_id,
                    "status": "skipped_missing_credentials",
                    "required_environment_names": ["TINDEX_API_BASE_URL", "TINDEX_API_TOKEN"],
                    "eligible_for_scoring": False,
                })
                continue
            if source_id == "us.fred.alfred" and not os.getenv("FRED_API_KEY", "").strip():
                results.append({
                    "source_id": source_id,
                    "status": "skipped_missing_credentials",
                    "required_environment_names": ["FRED_API_KEY"],
                    "eligible_for_scoring": False,
                })
                continue
            results.append(_run_one(
                source_id,
                export_dir=export_dir,
                tsetmc_queries=args.tsetmc_query or [],
                tindex_slugs=args.tindex_slug or [],
            ))
        report = {
            "report_version": "1.0.0",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "mode": "bounded_live_probe",
            "selected_sources": selected,
            "source_results": results,
            "summary": {
                "probe_count": sum(1 for item in results if item.get("status") != "skipped_missing_credentials"),
                "reachable_count": sum(1 for item in results if item.get("status") in {
                    "reachable_response_received", "reachable_schema_validated_candidate"
                }),
                "failed_count": sum(1 for item in results if item.get("status") == "probe_failed"),
                "production_approved": False,
                "candidate_csv_exports_are_local_only": True,
            },
            "notes": [
                "Probe success is not history completeness, licensing approval or predictive evidence.",
                "No raw price rows, article text, or credentials are included in the JSON report.",
                "Tindex limits are shared by the account; its candle probe makes at most three requests.",
                "GDELT is excluded from defaults because a prior request returned HTTP 429; select it explicitly.",
            ],
        }

    rendered = json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n"
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if args.mode == "probe" and report["summary"]["failed_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
