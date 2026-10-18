#!/usr/bin/env python3
"""Prepare Yahoo daily research CSVs as a conservative monthly price panel.

This is research-only tooling. It does not approve the source or enable ranking.
Crypto uses Close; non-crypto instruments use Adj Close when available, to
better represent adjusted total-return history. Missing observations are never
forward-filled. The output panel retains only months with an observed monthly
price for every requested instrument and reports any excluded months.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

DEFAULT_TICKERS = (
    "BTC-USD", "ETH-USD", "SOL-USD", "GLD", "SPY", "QQQ",
    "TLT", "UUP", "USO", "XLF", "XLE",
)


def _filename(symbol: str) -> str:
    return f"{symbol.replace('/', '_')}.csv"


def load_monthly_series(csv_path: Path, symbol: str) -> tuple[pd.Series, dict]:
    """Load one daily CSV, validate it, and select the last observed price per month."""
    try:
        frame = pd.read_csv(csv_path)
    except Exception as exc:
        raise ValueError(f"{symbol}: cannot read CSV ({type(exc).__name__})") from exc
    if frame.empty:
        raise ValueError(f"{symbol}: CSV is empty")
    date_col = next(
        (col for col in frame.columns if str(col).lower() in {"date", "datetime", "timestamp"}),
        None,
    )
    if date_col is None:
        raise ValueError(f"{symbol}: missing Date/Datetime/Timestamp column")

    dates = pd.to_datetime(frame[date_col], errors="coerce", utc=True)
    if dates.isna().any():
        raise ValueError(f"{symbol}: invalid date values")
    if dates.duplicated().any():
        raise ValueError(f"{symbol}: duplicate timestamps")
    if not dates.is_monotonic_increasing:
        raise ValueError(f"{symbol}: dates must be sorted oldest to newest")

    is_crypto = symbol.upper().endswith("-USD")
    preferred = "Close" if is_crypto else "Adj Close"
    if preferred not in frame.columns:
        # Do not silently replace an adjusted series with unadjusted close.
        raise ValueError(f"{symbol}: required price column {preferred!r} is missing")
    prices = pd.to_numeric(frame[preferred], errors="coerce")
    values = prices.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"{symbol}: {preferred} contains missing/non-finite values")
    if (values <= 0).any():
        raise ValueError(f"{symbol}: {preferred} contains non-positive values")

    daily = pd.Series(values, index=pd.DatetimeIndex(dates), name=symbol).sort_index()
    # Resample observed data only. No forward fill and no synthetic zero returns.
    monthly = daily.resample("ME").last().dropna()
    if monthly.empty:
        raise ValueError(f"{symbol}: no monthly observations after resampling")
    meta = {
        "symbol": symbol,
        "file": csv_path.name,
        "price_column": preferred,
        "asset_type_assumption": "crypto" if is_crypto else "non_crypto_adjusted_price",
        "daily_rows": int(len(daily)),
        "monthly_observations": int(len(monthly)),
        "first_month": monthly.index.min().date().isoformat(),
        "last_month": monthly.index.max().date().isoformat(),
        "missing_months_inside_observed_range": int(
            len(pd.date_range(monthly.index.min(), monthly.index.max(), freq="ME").difference(monthly.index))
        ),
    }
    return monthly, meta


def prepare_monthly_panel(
    input_dir: Path, symbols: Iterable[str] = DEFAULT_TICKERS
) -> tuple[pd.DataFrame, dict]:
    symbols = list(dict.fromkeys(s.strip().upper() for s in symbols if s.strip()))
    if not symbols:
        raise ValueError("at least one symbol is required")

    series_list = []
    per_symbol = []
    for symbol in symbols:
        path = input_dir / _filename(symbol)
        if not path.is_file():
            raise ValueError(f"{symbol}: expected file not found: {path}")
        series, meta = load_monthly_series(path, symbol)
        series_list.append(series)
        per_symbol.append(meta)

    # Inner alignment intentionally excludes months lacking a real observation
    # for any selected instrument; it does not carry prices forward.
    all_months = pd.concat(series_list, axis=1, join="outer").sort_index()
    common = all_months.dropna(axis=0, how="any")
    if common.empty:
        raise ValueError("no common months with observed prices across all requested symbols")

    report = {
        "schema_version": 1,
        "purpose": "research_only_unapproved",
        "input_dir": str(input_dir.resolve()),
        "alignment_policy": "calendar_month_end_last_observed_price; inner intersection; no forward fill",
        "price_policy": "Close for symbols ending -USD; Adj Close required for all other symbols",
        "symbols": per_symbol,
        "requested_symbols": symbols,
        "monthly_rows_before_alignment": int(len(all_months)),
        "monthly_rows_after_alignment": int(len(common)),
        "months_excluded_for_missing_asset_observations": int(len(all_months) - len(common)),
        "common_start_month": common.index.min().date().isoformat(),
        "common_end_month": common.index.max().date().isoformat(),
        "ranking_approved": False,
        "limitations": [
            "Yahoo Finance data remain unapproved for production or investment ranking.",
            "Non-crypto Adj Close selection is a research convention and requires instrument-specific review.",
            "Calendar-month last-observed prices are not guaranteed executable month-end prices.",
            "This sample is not representative of Iranian markets.",
            "No currency, licensing, point-in-time revision, delisting, or survivorship validation is performed.",
        ],
    }
    return common, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory containing downloaded symbol CSVs")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory, preferably outside the repository")
    parser.add_argument("--tickers", nargs="+", default=list(DEFAULT_TICKERS), help="Symbols to include")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing output files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.output_dir.expanduser().resolve()
    panel_path = out_dir / "monthly_prices.csv"
    report_path = out_dir / "monthly_preparation_report.json"
    if not args.overwrite and (panel_path.exists() or report_path.exists()):
        print("ERROR: output files already exist; choose another directory or pass --overwrite", file=sys.stderr)
        return 2
    try:
        panel, report = prepare_monthly_panel(args.input_dir.expanduser().resolve(), args.tickers)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    panel.index.name = "Date"
    panel.to_csv(panel_path, index=True, float_format="%.12g")
    report["output_file"] = panel_path.name
    report["report_file"] = report_path.name
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Symbols prepared: {len(report['symbols'])}")
    print(f"Monthly rows: {report['monthly_rows_after_alignment']}")
    print(f"Common range: {report['common_start_month']}..{report['common_end_month']}")
    print(f"Months excluded during alignment: {report['months_excluded_for_missing_asset_observations']}")
    for item in report["symbols"]:
        print(f"- {item['symbol']}: column={item['price_column']}; monthly_rows={item['monthly_observations']}; missing_months={item['missing_months_inside_observed_range']}")
    print(f"Panel: {panel_path}")
    print(f"Report: {report_path}")
    print("Approval remains unknown/fail-closed; no investment ranking is enabled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
