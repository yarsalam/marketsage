#!/usr/bin/env python3
"""Targeted, read-only TSETMC price-adjustment reconciliation for one instrument.

Fetches the daily closing-price history, price-adjustment events, and the legacy
Financial.aspx chart with a=0/a=1. It does not alter production data or enable scoring.
The chart endpoint's positional columns are preserved as generic fields because
TSETMC does not publish a stable official schema for this legacy endpoint.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

API = "https://cdn.tsetmc.com/api"
CHART = "https://members.tsetmc.com/tsev2/chart/data/Financial.aspx"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36"
DEFAULT_ANOMALY_DATES = (
    "2020-11-08", "2013-06-15", "2014-06-29", "2014-02-12",
    "2014-06-30", "2012-06-23", "2011-01-26", "2022-12-03",
    "2020-05-26",
)


def norm(value: Any) -> str:
    return str(value or "").replace("\u064a", "\u06cc").replace("\u0643", "\u06a9").strip()


def extract_list(payload: Any, preferred_key: str) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        value = payload.get(preferred_key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


def parse_chart(text: str) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    for item in text.strip().split(";"):
        parts = [x.strip() for x in item.split(",")]
        if len(parts) >= 2 and len(parts[0]) == 8 and parts[0].isdigit():
            rows[parts[0]] = parts
    return rows


def request_json(session: requests.Session, url: str) -> Any:
    response = session.get(url, timeout=25)
    response.raise_for_status()
    return response.json()


def request_chart(session: requests.Session, instrument_code: str, adjusted: int) -> dict[str, list[str]]:
    response = session.get(
        CHART,
        params={"i": instrument_code, "t": "ph", "a": str(adjusted)},
        timeout=25,
    )
    response.raise_for_status()
    return parse_chart(response.text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="فولاد")
    parser.add_argument("--instrument-code", default="46348559193224090",
                        help="Known TSETMC insCode for فولاد; use only if symbol search is unavailable.")
    parser.add_argument("--out-dir", default="artifacts/tsetmc-adjustment-validation")
    parser.add_argument("--anomaly-dates", default=",".join(DEFAULT_ANOMALY_DATES),
                        help="Comma-separated Gregorian YYYY-MM-DD dates from the prior QC.")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    dates_of_interest = {d.replace("-", "") for d in args.anomaly_dates.split(",") if d.strip()}
    report: dict[str, Any] = {
        "source_id": "iran.tsetmc",
        "symbol_query": args.symbol,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "targeted adjustment reconciliation; research-only; no scoring approval",
        "eligible_for_scoring": False,
        "checks": {},
        "limitations": [
            "TSETMC endpoints are reverse-engineered/community-documented, not a stable official API contract.",
            "The legacy chart's positional fields are retained without asserting undocumented semantics.",
            "Adjustment-event records are evidence, not proof that the complete adjusted history is correct.",
            "Commercial/redistribution rights, units, suspension handling, and point-in-time availability remain separate gates.",
        ],
    }
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/json, text/plain, */*"})

    try:
        # Resolve identity, but do not silently replace the known code unless exact match agrees.
        search_url = f"{API}/Instrument/GetInstrumentSearch/{quote(args.symbol, safe='')}"
        search_payload = request_json(session, search_url)
        candidates = extract_list(search_payload, "instrumentSearch")
        query = norm(args.symbol)
        exact = [
            row for row in candidates
            if query in {norm(row.get("lVal18AFC")), norm(row.get("lVal30"))}
        ]
        if len(exact) != 1:
            report["checks"]["identity"] = {
                "status": "blocked_exact_match_not_unique",
                "candidate_count": len(exact),
                "candidate_samples": [
                    {"insCode": r.get("insCode"), "lVal18AFC": r.get("lVal18AFC"), "lVal30": r.get("lVal30")}
                    for r in candidates[:8]
                ],
            }
            raise RuntimeError("Could not resolve exactly one instrument by exact normalized name.")
        selected_code = str(exact[0].get("insCode") or "")
        if not selected_code:
            raise RuntimeError("Exact instrument match has no insCode.")
        if args.instrument_code and selected_code != str(args.instrument_code):
            report["checks"]["identity"] = {
                "status": "blocked_instrument_code_mismatch",
                "search_insCode": selected_code,
                "configured_insCode": str(args.instrument_code),
                "provider_name": exact[0].get("lVal30"),
            }
            raise RuntimeError("Exact-name result does not match the configured instrument code.")
        instrument_code = selected_code
        report["instrument"] = {
            "requested_name": args.symbol,
            "provider_ticker": exact[0].get("lVal18AFC"),
            "provider_full_name": exact[0].get("lVal30"),
            "insCode": instrument_code,
        }
        time.sleep(1.0)

        daily_payload = request_json(
            session, f"{API}/ClosingPrice/GetClosingPriceDailyList/{quote(instrument_code, safe='')}/0"
        )
        daily = extract_list(daily_payload, "closingPriceDaily")
        if not daily:
            raise RuntimeError("Daily history endpoint returned no recognizable rows.")
        daily_by_date = {
            str(row.get("dEven", "")).zfill(8): row
            for row in daily if str(row.get("dEven", "")).isdigit()
        }
        (out / "daily_history_raw.json").write_text(
            json.dumps(daily, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        time.sleep(1.0)

        adjustment_payload = request_json(
            session, f"{API}/ClosingPrice/GetPriceAdjustList/{quote(instrument_code, safe='')}"
        )
        adjustments = extract_list(adjustment_payload, "priceAdjust")
        (out / "price_adjustments_raw.json").write_text(
            json.dumps(adjustments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        time.sleep(1.0)

        chart_raw = request_chart(session, instrument_code, 0)
        time.sleep(1.0)
        chart_adjusted = request_chart(session, instrument_code, 1)
        (out / "chart_unadjusted_raw.json").write_text(
            json.dumps(chart_raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (out / "chart_adjusted_raw.json").write_text(
            json.dumps(chart_adjusted, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        common_chart_dates = sorted(set(chart_raw) & set(chart_adjusted))
        chart_differences = []
        for date in common_chart_dates:
            raw_fields, adj_fields = chart_raw[date], chart_adjusted[date]
            max_width = max(len(raw_fields), len(adj_fields))
            changed = [
                i for i in range(1, max_width)
                if (raw_fields[i] if i < len(raw_fields) else None)
                != (adj_fields[i] if i < len(adj_fields) else None)
            ]
            if changed:
                chart_differences.append({
                    "date": date,
                    "changed_field_indexes_zero_based": changed,
                    "unadjusted_fields": raw_fields,
                    "adjusted_fields": adj_fields,
                })

        adjustment_by_date: dict[str, list[dict[str, Any]]] = {}
        for event in adjustments:
            d = str(event.get("dEven", ""))
            if d.isdigit():
                adjustment_by_date.setdefault(d.zfill(8), []).append(event)

        comparison = []
        for date in sorted(dates_of_interest):
            comparison.append({
                "date": date,
                "daily_history_row": daily_by_date.get(date),
                "chart_unadjusted_fields": chart_raw.get(date),
                "chart_adjusted_fields": chart_adjusted.get(date),
                "adjustment_events_on_same_date": adjustment_by_date.get(date, []),
                "chart_raw_and_adjusted_differ": (
                    chart_raw.get(date) != chart_adjusted.get(date)
                    if date in chart_raw and date in chart_adjusted else None
                ),
            })
        with (out / "anomaly_date_comparison.json").open("w", encoding="utf-8") as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
            f.write("\n")

        # A compact event file for reviewing the source's exact schema and date coverage.
        with (out / "chart_adjustment_differences.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "date", "changed_field_indexes_zero_based", "unadjusted_fields", "adjusted_fields"
            ])
            writer.writeheader()
            for row in chart_differences:
                writer.writerow({
                    **row,
                    "changed_field_indexes_zero_based": json.dumps(row["changed_field_indexes_zero_based"]),
                    "unadjusted_fields": json.dumps(row["unadjusted_fields"]),
                    "adjusted_fields": json.dumps(row["adjusted_fields"]),
                })

        report["checks"] = {
            "identity": "exact_name_and_instrument_code_match",
            "daily_history_rows": len(daily),
            "daily_history_date_range": [
                min(daily_by_date) if daily_by_date else None,
                max(daily_by_date) if daily_by_date else None,
            ],
            "price_adjustment_event_count": len(adjustments),
            "price_adjustment_event_keys": sorted({k for row in adjustments for k in row}),
            "chart_unadjusted_rows": len(chart_raw),
            "chart_adjusted_rows": len(chart_adjusted),
            "chart_common_dates": len(common_chart_dates),
            "chart_dates_with_any_field_difference": len(chart_differences),
            "anomaly_dates_found_in_daily_history": [d for d in sorted(dates_of_interest) if d in daily_by_date],
            "anomaly_dates_found_in_both_chart_series": [
                d for d in sorted(dates_of_interest) if d in chart_raw and d in chart_adjusted
            ],
            "anomaly_dates_with_adjustment_event": [
                d for d in sorted(dates_of_interest) if d in adjustment_by_date
            ],
            "anomaly_comparison_file": "anomaly_date_comparison.json",
            "chart_differences_file": "chart_adjustment_differences.csv",
        }
        report["status"] = "evidence_collected_requires_human_reconciliation"
        report["decision"] = {
            "tsetmc_transport": "reachable for this run",
            "adjusted_history": "not approved until the output is inspected and reconciled",
            "scoring": "disabled",
        }
    except Exception as exc:
        report.setdefault("status", "validation_probe_failed")
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)[:500]
    finally:
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        (out / "tsetmc_adjustment_validation_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))

    return 0 if report.get("status") == "evidence_collected_requires_human_reconciliation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
