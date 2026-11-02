#!/usr/bin/env python3
"""Audit seller-provided StreamData CSV exports without guessing units or timezone.

This tool intentionally does not include or copy vendor data into the repository.
It creates normalized candidate CSVs and a JSON quality report in a local output
directory. Candidate outputs are not eligible for production scoring.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SOURCE_ID = "vendor.streamdata_export"
DEFAULT_FILES = {
    "gold_fund_ayar": "Ayar_Gold_Fund_1D_StreamData.csv",
    "bitcoin_btcusdt": "BTCUSDT_1D_StreamData.csv",
    "gold_18k": "Gold18_1D_StreamData.csv",
    "free_usd": "US_Dollar_1D_StreamData.csv",
}
REQUIRED_COLUMNS = (
    "<DTYYYYMMDD>", "<TIME>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"
)
CANONICAL_COLUMNS = (
    "source_id", "instrument_key", "source_file", "source_file_sha256",
    "source_row_number", "observation_date", "source_date_raw", "source_time_raw",
    "source_time_semantics", "open_raw", "high_raw", "low_raw", "close_raw",
    "volume_raw", "source_price_unit", "source_currency", "adjustment_status",
    "ohlc_consistency_ok", "eligible_for_scoring",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_date(value: Any) -> date | None:
    raw = str(value or "").strip()
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError:
        return None


def parse_time(value: Any) -> time | None:
    raw = str(value or "").strip()
    if len(raw) != 6 or not raw.isdigit():
        return None
    try:
        return datetime.strptime(raw, "%H%M%S").time()
    except ValueError:
        return None


def parse_decimal(value: Any) -> Decimal | None:
    raw = str(value or "").strip().replace(",", "")
    if not raw:
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    return number


def _number_text(value: Decimal | None) -> str:
    return "" if value is None else format(value, "f")


def audit_file(
    path: Path,
    *,
    instrument_key: str,
    large_return_threshold: float,
    output_dir: Path,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "instrument_key": instrument_key,
        "file": path.name,
        "exists": path.is_file(),
        "source_id": SOURCE_ID,
        "source_price_unit": None,
        "source_currency": None,
        "timezone": None,
        "adjustment_status": "unknown_unverified",
        "eligible_for_scoring": False,
    }
    if not path.is_file():
        item.update({"status": "missing_file", "error": "required_file_not_found"})
        return item

    file_hash = sha256_file(path)
    item["sha256"] = file_hash
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            source_rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        item.update({
            "status": "read_error",
            "error_type": type(exc).__name__,
            "eligible_for_scoring": False,
        })
        return item

    item["columns"] = headers
    item["missing_required_columns"] = [c for c in REQUIRED_COLUMNS if c not in headers]
    if item["missing_required_columns"]:
        item.update({"status": "schema_mismatch", "row_count": len(source_rows)})
        return item

    row_details: list[dict[str, Any]] = []
    canonical_rows: list[dict[str, Any]] = []
    empty_rows = invalid_dates = invalid_times = 0
    invalid_price_rows = invalid_volume_rows = ohlc_anomalies = 0
    nonpositive_price_rows = 0
    date_counts: Counter[date] = Counter()
    times: Counter[str] = Counter()
    source_order_dates: list[date] = []

    for row_number, row in enumerate(source_rows, start=2):
        if not any(str(v or "").strip() for v in row.values()):
            empty_rows += 1
            continue

        date_raw = str(row.get("<DTYYYYMMDD>") or "").strip()
        time_raw = str(row.get("<TIME>") or "").strip()
        parsed_day = parse_date(date_raw)
        parsed_clock = parse_time(time_raw)
        if parsed_day is None:
            invalid_dates += 1
        else:
            date_counts[parsed_day] += 1
            source_order_dates.append(parsed_day)
        if parsed_clock is None:
            invalid_times += 1
        if time_raw:
            times[time_raw] += 1

        numeric = {
            name: parse_decimal(row.get(f"<{name.upper()}>"))
            for name in ("open", "high", "low", "close", "vol")
        }
        prices = [numeric[k] for k in ("open", "high", "low", "close")]
        valid_prices = all(v is not None and v > 0 for v in prices)
        if not valid_prices:
            invalid_price_rows += 1
        if any(v is not None and v <= 0 for v in prices):
            nonpositive_price_rows += 1
        volume = numeric["vol"]
        valid_volume = volume is not None and volume >= 0
        if not valid_volume:
            invalid_volume_rows += 1

        ohlc_ok: bool | None = None
        if valid_prices:
            open_, high, low, close = prices
            ohlc_ok = high >= max(open_, low, close) and low <= min(open_, high, close)
            if not ohlc_ok:
                ohlc_anomalies += 1

        record = {
            "source_id": SOURCE_ID,
            "instrument_key": instrument_key,
            "source_file": path.name,
            "source_file_sha256": file_hash,
            "source_row_number": row_number,
            "observation_date": parsed_day.isoformat() if parsed_day else "",
            "source_date_raw": date_raw,
            "source_time_raw": time_raw,
            "source_time_semantics": "unknown_clock_and_timezone",
            "open_raw": _number_text(numeric["open"]),
            "high_raw": _number_text(numeric["high"]),
            "low_raw": _number_text(numeric["low"]),
            "close_raw": _number_text(numeric["close"]),
            "volume_raw": _number_text(volume),
            "source_price_unit": "",
            "source_currency": "",
            "adjustment_status": "unknown_unverified",
            "ohlc_consistency_ok": "" if ohlc_ok is None else str(ohlc_ok).lower(),
            "eligible_for_scoring": "false",
        }
        canonical_rows.append(record)
        row_details.append({
            "date": parsed_day,
            "close": numeric["close"],
            "prices_valid": valid_prices,
            "volume_valid": valid_volume,
            "ohlc_ok": ohlc_ok,
            "row_number": row_number,
            "date_raw": date_raw,
            "time_raw": time_raw,
        })

    duplicate_dates = sum(count - 1 for count in date_counts.values() if count > 1)
    out_of_order_pairs = sum(
        source_order_dates[index] < source_order_dates[index - 1]
        for index in range(1, len(source_order_dates))
    )
    unique_days = sorted(date_counts)
    first_day = unique_days[0] if unique_days else None
    last_day = unique_days[-1] if unique_days else None
    calendar_days_missing = (
        (last_day - first_day).days + 1 - len(unique_days)
        if first_day and last_day else None
    )
    gaps = []
    for previous, current in zip(unique_days, unique_days[1:]):
        distance = (current - previous).days
        if distance > 4:
            gaps.append({
                "previous_date": previous.isoformat(),
                "next_date": current.isoformat(),
                "calendar_days_between": distance,
            })

    # Return diagnostics are calculated chronologically only when each close is
    # valid and a date is unique. They do not classify jumps as errors because
    # corporate actions and source semantics are not yet independently reconciled.
    by_day: dict[date, Decimal] = {}
    for detail in row_details:
        if detail["date"] is not None and detail["prices_valid"] and detail["close"] is not None:
            if date_counts[detail["date"]] == 1:
                by_day[detail["date"]] = detail["close"]
    close_returns: list[tuple[float, str]] = []
    ordered_return_days = sorted(by_day)
    for previous, current in zip(ordered_return_days, ordered_return_days[1:]):
        previous_close = by_day[previous]
        current_close = by_day[current]
        if previous_close > 0:
            value = float(current_close / previous_close - Decimal(1))
            if math.isfinite(value):
                close_returns.append((value, current.isoformat()))
    return_values = [r for r, _ in close_returns]
    large_returns = [
        {"date": d, "return_fraction": r}
        for r, d in close_returns if abs(r) >= large_return_threshold
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / f"{instrument_key}.candidate.csv"
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(canonical_rows)

    item.update({
        "status": "audited_candidate",
        "row_count": len(source_rows),
        "empty_rows": empty_rows,
        "invalid_or_missing_date_rows": invalid_dates,
        "invalid_or_missing_time_rows": invalid_times,
        "distinct_source_time_values": dict(sorted(times.items())),
        "date_range": {
            "first": first_day.isoformat() if first_day else None,
            "last": last_day.isoformat() if last_day else None,
        },
        "duplicate_date_rows": duplicate_dates,
        "out_of_order_adjacent_pairs": out_of_order_pairs,
        "calendar_days_not_present_in_export": calendar_days_missing,
        "calendar_gaps_over_4_days": gaps,
        "rows_with_missing_or_non_numeric_or_nonpositive_ohlc": invalid_price_rows,
        "rows_with_nonpositive_ohlc_values": nonpositive_price_rows,
        "rows_with_invalid_volume": invalid_volume_rows,
        "ohlc_consistency_anomaly_rows": ohlc_anomalies,
        "ohlc_anomaly_sample": [
            {
                "date": d["date"].isoformat() if d["date"] else None,
                "source_row_number": d["row_number"],
                "source_time_raw": d["time_raw"],
            }
            for d in row_details if d["ohlc_ok"] is False
        ][:25],
        "close_return_count": len(close_returns),
        "close_return_min": min(return_values) if return_values else None,
        "close_return_median": statistics.median(return_values) if return_values else None,
        "close_return_max": max(return_values) if return_values else None,
        "large_return_threshold_fraction": large_return_threshold,
        "large_return_count": len(large_returns),
        "large_return_sample": large_returns[:25],
        "canonical_candidate_csv": str(output_csv),
        "time_interpretation": "not_inferred",
        "unit_or_currency_inference": "none",
        "adjustment_policy": "unknown; raw export values preserved",
        "eligible_for_scoring": False,
    })
    return item


def audit_exports(
    data_dir: Path,
    output_dir: Path,
    *,
    large_return_threshold: float = 0.10,
) -> dict[str, Any]:
    if not math.isfinite(large_return_threshold) or not 0 < large_return_threshold <= 5:
        raise ValueError("large_return_threshold must be in (0, 5]")
    files = {
        "gold_fund_ayar": data_dir / DEFAULT_FILES["gold_fund_ayar"],
        "bitcoin_btcusdt": data_dir / DEFAULT_FILES["bitcoin_btcusdt"],
        "gold_18k": data_dir / DEFAULT_FILES["gold_18k"],
        "free_usd": data_dir / DEFAULT_FILES["free_usd"],
    }
    assets = {
        key: audit_file(
            path, instrument_key=key,
            large_return_threshold=large_return_threshold,
            output_dir=output_dir,
        )
        for key, path in files.items()
    }
    report = {
        "report_version": "1.0",
        "source_id": SOURCE_ID,
        "scope": "local seller-provided CSV structure, OHLC consistency and return diagnostics",
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "input_directory": str(data_dir),
        "output_directory": str(output_dir),
        "source_rights_status": "seller supplied; contract, collection scope and redistribution rights not reviewed",
        "source_identity_status": "provider identity and instrument metadata require written confirmation",
        "policy": {
            "vendor_files_committed_to_repository": False,
            "raw_values_preserved": True,
            "unit_and_currency_inferred": False,
            "timezone_inferred": False,
            "price_adjustment_inferred": False,
            "missing_dates_filled": False,
            "eligible_for_production_scoring": False,
        },
        "assets": assets,
        "next_acceptance_gates": [
            "Confirm seller/provider identity, data delivery scope, redistribution and derived-data rights.",
            "Confirm each instrument's exchange/venue, ticker identity, currency, quote/base convention and price unit.",
            "Confirm source timezone, meaning of <TIME>, daily candle boundary and whether prices are raw or adjusted.",
            "Reconcile each series against a permitted independent reference; review every OHLC anomaly.",
            "Explain missing sessions, date gaps, corrections and export update/version policy.",
            "Only then map approved series into research inputs; production scoring remains blocked.",
        ],
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default=str(Path.home() / "Downloads" / "Telegram Desktop" / "4_Symbols_Data_StreamData"),
    )
    parser.add_argument("--out-dir", default="/tmp/marketsage-vendor-streamdata")
    parser.add_argument("--large-return-threshold", type=float, default=0.10)
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir).expanduser()
    output_dir = Path(args.out_dir).expanduser()
    try:
        report = audit_exports(
            data_dir, output_dir,
            large_return_threshold=args.large_return_threshold,
        )
        report_path = output_dir / "streamdata_validation_report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({
            "status": "audit_failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "eligible_for_production_scoring": False,
        }, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nREPORT_SAVED: {report_path}")
    return 0 if all(item.get("status") == "audited_candidate" for item in report["assets"].values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
