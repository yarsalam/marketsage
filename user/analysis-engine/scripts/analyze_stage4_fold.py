#!/usr/bin/env python3
"""Attribute a suspicious Stage 4 fold to monthly holdings and asset returns.

This is a diagnostic only: it does not tune parameters, approve sources, or enable ranking.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.backtest import BacktestConfig, run_monthly_momentum_backtest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analyze_fold(
    prices: pd.DataFrame,
    start_date: str,
    end_date: str,
    config: BacktestConfig | None = None,
    outlier_return_threshold: float = 1.0,
) -> dict:
    if not np.isfinite(outlier_return_threshold) or outlier_return_threshold <= 0:
        raise ValueError("outlier_return_threshold must be finite and greater than zero")
    prices = prices.copy()
    prices.index = pd.DatetimeIndex(prices.index)
    # Compare timestamps in one consistent convention. Normalize both the
    # input index and requested dates to UTC-naive to support UTC CSVs and
    # local/naive monthly fixtures without tz-awareness comparison errors.
    if prices.index.tz is not None:
        prices.index = prices.index.tz_convert("UTC").tz_localize(None)
    prices = prices.sort_index()
    cfg = config or BacktestConfig()
    result = run_monthly_momentum_backtest(prices, cfg)
    start, end = pd.Timestamp(start_date), pd.Timestamp(end_date)
    if start.tzinfo is not None:
        start = start.tz_convert("UTC").tz_localize(None)
    if end.tzinfo is not None:
        end = end.tz_convert("UTC").tz_localize(None)
    if start > end:
        raise ValueError("start_date must be on or before end_date")
    monthly = result["monthly"].loc[(result["monthly"].index >= start) & (result["monthly"].index <= end)]
    if monthly.empty:
        raise ValueError("requested fold has no backtest return rows")
    asset_returns = prices.pct_change(fill_method=None)
    rows = []
    contribution_totals: dict[str, float] = {}
    outliers = []
    for date, row in monthly.iterrows():
        selected = [item for item in str(row["selected_assets"]).split(",") if item]
        if not selected:
            raise ValueError(f"no selected assets recorded for {date.date()}")
        returns = asset_returns.loc[date, selected]
        if returns.isna().any() or not np.isfinite(returns.to_numpy(dtype=float)).all():
            raise ValueError(f"missing/non-finite selected-asset return at {date.date()}")
        contributions = {symbol: float(returns[symbol]) / len(selected) for symbol in selected}
        for symbol, value in contributions.items():
            contribution_totals[symbol] = contribution_totals.get(symbol, 0.0) + value
        asset_return_map = {symbol: float(returns[symbol]) for symbol in selected}
        for symbol, value in asset_return_map.items():
            if abs(value) >= outlier_return_threshold:
                outliers.append({
                    "date": date.date().isoformat(),
                    "symbol": symbol,
                    "monthly_return": value,
                    "threshold": outlier_return_threshold,
                })
        rows.append({
            "date": date.date().isoformat(),
            "selected_assets": selected,
            "asset_monthly_returns": asset_return_map,
            "equal_weight_gross_contributions": contributions,
            "gross_return": float(row["gross_return"]),
            "net_return": float(row["net_return"]),
            "turnover_l1": float(row["turnover"]),
            "transaction_cost_fraction": float(row["transaction_cost"]),
            "slippage_cost_fraction": float(row["slippage_cost"]),
            "total_cost_fraction": float(row["total_cost"]),
            "equity_within_fold": None,
            "drawdown_within_fold": None,
        })
    equity = (1 + monthly["net_return"]).cumprod()
    drawdown = equity / equity.cummax() - 1
    for i, row in enumerate(rows):
        row["equity_within_fold"] = float(equity.iloc[i])
        row["drawdown_within_fold"] = float(drawdown.iloc[i])
    return {
        "purpose": "exploratory_fold_attribution_only",
        "ranking_approved": False,
        "source_scoring_approved": False,
        "requested_start": start.date().isoformat(),
        "requested_end": end.date().isoformat(),
        "actual_start": monthly.index.min().date().isoformat(),
        "actual_end": monthly.index.max().date().isoformat(),
        "periods": int(len(monthly)),
        "fold_total_net_return": float((1 + monthly["net_return"]).prod() - 1),
        "fold_max_drawdown": float(drawdown.min()),
        "largest_monthly_gross_return": float(monthly["gross_return"].max()),
        "largest_monthly_net_return": float(monthly["net_return"].max()),
        "outlier_return_threshold": outlier_return_threshold,
        "selected_asset_return_outliers": outliers,
        "asset_sum_of_periodic_gross_contributions": dict(sorted(
            contribution_totals.items(), key=lambda item: abs(item[1]), reverse=True
        )),
        "contribution_note": (
            "Per-period equal-weight gross contributions sum to the strategy gross return for each row. "
            "The cross-period sum is additive diagnostic attribution, not compounded portfolio P&L attribution."
        ),
        "config": result["config"],
        "monthly": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="same monthly_prices.csv used by Stage 4")
    parser.add_argument("--output", required=True, help="output JSON path")
    parser.add_argument("--start-date", default="2023-10-31")
    parser.add_argument("--end-date", default="2024-03-31")
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--momentum-months", type=int, default=3)
    parser.add_argument("--volatility-months", type=int, default=12)
    parser.add_argument("--transaction-cost-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=25.0)
    parser.add_argument("--outlier-return-threshold", type=float, default=1.0,
                        help="flag selected-asset monthly returns whose absolute value meets this fraction; default 1.0 = 100%%")
    args = parser.parse_args()
    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        parser.error(f"input CSV does not exist: {source}")
    prices = pd.read_csv(source, index_col=0, parse_dates=True)
    config = BacktestConfig(
        top_n=args.top_n,
        momentum_months=args.momentum_months,
        volatility_months=args.volatility_months,
        transaction_cost_bps=args.transaction_cost_bps,
        slippage_bps=args.slippage_bps,
    )
    report = analyze_fold(prices, args.start_date, args.end_date, config, args.outlier_return_threshold)
    report["dataset"] = {
        "path": str(source),
        "sha256": sha256_file(source),
        "bytes": source.stat().st_size,
        "format": "CSV",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed_exploratory_fold_attribution",
        "purpose": report["purpose"],
        "ranking_approved": False,
        "dataset_sha256": report["dataset"]["sha256"],
        "actual_start": report["actual_start"],
        "actual_end": report["actual_end"],
        "periods": report["periods"],
        "fold_total_net_return": report["fold_total_net_return"],
        "fold_max_drawdown": report["fold_max_drawdown"],
        "selected_asset_return_outliers": len(report["selected_asset_return_outliers"]),
        "output": str(output),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
