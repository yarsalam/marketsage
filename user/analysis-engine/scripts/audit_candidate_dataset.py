#!/usr/bin/env python3
"""Metadata-only CSV quality audit for candidate price or annual macro datasets.

Supports StreamData-style headers (<DTYYYYMMDD>, <OPEN>, ...) and annual
observation_year/value files. It never repairs data or prints raw numeric values.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

DATE_ALIASES = (
    "dtyyyymmdd", "date", "trading_date", "tradingdate", "observation_date",
    "observationdate", "observation_year", "observationyear", "year",
    "annual_year", "period", "day", "datetime", "timestamp",
)
YEAR_ALIASES = {"observation_year", "observationyear", "year", "annual_year"}
OPEN_ALIASES = ("open", "o", "openprice", "pricefirst", "open_raw")
HIGH_ALIASES = ("high", "h", "highprice", "pricemax", "high_raw")
LOW_ALIASES = ("low", "l", "lowprice", "pricemin", "low_raw")
CLOSE_ALIASES = (
    "close", "c", "closingprice", "pclosing", "close_raw",
    "adjusted_close", "adj_close", "last",
)
VALUE_ALIASES = ("value", "observation_value", "indicator_value", "rate", "raw_rate")
VOLUME_ALIASES = ("vol", "volume", "qtottran5j", "base_volume", "quote_volume")


def normalize_header(value: str) -> str:
    value = value.strip().strip("<>").strip().lower()
    return re.sub(r"[\s-]+", "_", value)


def _column(fieldnames: list[str], aliases: tuple[str, ...]) -> str | None:
    reverse = {normalize_header(name): name for name in fieldnames}
    for alias in aliases:
        if alias in reverse:
            return reverse[alias]
    return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or re.fullmatch(r"\d{4}", text):
        return None
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _parse_number(value: Any) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        number = float(str(value).strip().replace(",", ""))
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return number


def audit_file(path: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "path": str(path.expanduser().resolve()),
        "sha256": None,
        "status": "audit_failed",
        "production_approved": False,
        "raw_values_emitted": False,
    }
    try:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        report["sha256"] = digest.hexdigest()

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            date_col = _column(fieldnames, DATE_ALIASES)
            open_col = _column(fieldnames, OPEN_ALIASES)
            high_col = _column(fieldnames, HIGH_ALIASES)
            low_col = _column(fieldnames, LOW_ALIASES)
            close_col = _column(fieldnames, CLOSE_ALIASES)
            value_col = _column(fieldnames, VALUE_ALIASES)
            volume_col = _column(fieldnames, VOLUME_ALIASES)
            row_count = 0
            invalid_date_count = 0
            missing_date_count = 0
            duplicate_date_count = 0
            order_inversion_count = 0
            missing_numeric = Counter()
            nonnumeric_numeric = Counter()
            ohlc_violation_count = 0
            dates: list[date] = []
            years: list[int] = []
            seen_periods: set[str] = set()
            previous_order: int | None = None
            numeric_cols = {
                "open": open_col, "high": high_col, "low": low_col,
                "close": close_col, "value": value_col, "volume": volume_col,
            }

            for row in reader:
                row_count += 1
                raw_period = str(row.get(date_col, "") or "").strip() if date_col else ""
                parsed_day: date | None = None
                year_only: int | None = None
                if not date_col or not raw_period:
                    missing_date_count += 1
                elif normalize_header(date_col) in YEAR_ALIASES and re.fullmatch(r"\d{4}", raw_period):
                    candidate_year = int(raw_period)
                    if not 1 <= candidate_year <= 2200:
                        invalid_date_count += 1
                    else:
                        year_only = candidate_year
                else:
                    parsed_day = _parse_date(raw_period)
                    if parsed_day is None:
                        invalid_date_count += 1

                period_key: str | None = None
                order_value: int | None = None
                if year_only is not None:
                    years.append(year_only)
                    period_key = f"year:{year_only:04d}"
                    order_value = year_only * 372
                elif parsed_day is not None:
                    dates.append(parsed_day)
                    period_key = f"date:{parsed_day.isoformat()}"
                    order_value = parsed_day.year * 372 + parsed_day.month * 31 + parsed_day.day

                if period_key is not None and order_value is not None:
                    if period_key in seen_periods:
                        duplicate_date_count += 1
                    seen_periods.add(period_key)
                    if previous_order is not None and order_value < previous_order:
                        order_inversion_count += 1
                    previous_order = order_value

                nums: dict[str, float | None] = {}
                for label, column in numeric_cols.items():
                    if column is None:
                        continue
                    raw = row.get(column)
                    if raw is None or not str(raw).strip():
                        missing_numeric[label] += 1
                        nums[label] = None
                    else:
                        number = _parse_number(raw)
                        if number is None:
                            nonnumeric_numeric[label] += 1
                        nums[label] = number

                if all(numeric_cols[key] is not None for key in ("open", "high", "low", "close")):
                    values = [nums.get(key) for key in ("open", "high", "low", "close")]
                    if all(value is not None and value > 0 for value in values):
                        opening, high, low, close = values
                        if low > high or high < max(opening, close) or low > min(opening, close):
                            ohlc_violation_count += 1

        columns = {
            "date_or_period": date_col, "open": open_col, "high": high_col,
            "low": low_col, "close": close_col, "value": value_col, "volume": volume_col,
        }
        critical_missing_columns = []
        if date_col is None:
            critical_missing_columns.append("date_or_period")
        if close_col is None and value_col is None:
            critical_missing_columns.append("close_or_value")
        report.update({
            "status": "schema_incomplete" if critical_missing_columns else "audited_candidate",
            "row_count": row_count,
            "columns_detected": columns,
            "source_columns": fieldnames,
            "missing_critical_columns": critical_missing_columns,
            "date_precision": "year" if years and not dates else "date" if dates and not years else (
                "mixed" if dates and years else None
            ),
            "valid_observation_period_count": len(dates) + len(years),
            "invalid_date_count": invalid_date_count,
            "missing_date_count": missing_date_count,
            "duplicate_date_count": duplicate_date_count,
            "source_order_inversion_count": order_inversion_count,
            "first_date": min(dates).isoformat() if dates else None,
            "last_date": max(dates).isoformat() if dates else None,
            "first_observation_year": min(years) if years else None,
            "last_observation_year": max(years) if years else None,
            "missing_numeric_counts": dict(missing_numeric),
            "nonnumeric_numeric_counts": dict(nonnumeric_numeric),
            "ohlc_violation_count": (
                ohlc_violation_count
                if all(numeric_cols[k] for k in ("open", "high", "low", "close"))
                else None
            ),
            "issues_detected": bool(
                critical_missing_columns or invalid_date_count or missing_date_count
                or duplicate_date_count or order_inversion_count
                or any(missing_numeric.values()) or any(nonnumeric_numeric.values())
                or ohlc_violation_count
            ),
        })
        return report
    except (OSError, UnicodeError, csv.Error) as exc:
        report["error_type"] = type(exc).__name__
        report["error_detail_redacted"] = True
        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_files", nargs="+", help="CSV files to audit; source files are not modified")
    parser.add_argument("--out-report", required=True, help="Path for metadata-only JSON report")
    args = parser.parse_args(argv)
    reports = [audit_file(Path(name).expanduser()) for name in args.csv_files]
    summary = {
        "report_version": "1.1.0",
        "purpose": "candidate CSV data-quality audit, not source approval",
        "production_approved": False,
        "raw_values_emitted": False,
        "file_count": len(reports),
        "audited_count": sum(1 for item in reports if item["status"] in {"audited_candidate", "schema_incomplete"}),
        "failed_count": sum(1 for item in reports if item["status"] == "audit_failed"),
        "files": reports,
    }
    rendered = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    report_path = Path(args.out_report).expanduser()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if summary["failed_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
