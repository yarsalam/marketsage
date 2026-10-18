#!/usr/bin/env python3
"""Run a reproducible, research-only Stage 4 comparison from a monthly price CSV."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from research.backtest import BacktestConfig
from research.evaluation import evaluate_monthly_strategies


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="monthly_prices.csv")
    parser.add_argument("--output", required=True, help="output JSON report path")
    parser.add_argument("--holdout-months", type=int, default=12)
    parser.add_argument("--min-train-months", type=int, default=24)
    parser.add_argument("--fold-months", type=int, default=6)
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument("--momentum-months", type=int, default=3)
    parser.add_argument("--volatility-months", type=int, default=12)
    parser.add_argument("--transaction-cost-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=25.0)
    parser.add_argument("--risk-free-rate-annual", type=float, default=0.0)
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    if not source.is_file():
        parser.error(f"input CSV does not exist: {source}")
    prices = pd.read_csv(source, index_col=0, parse_dates=True)
    prices.index = pd.DatetimeIndex(prices.index)
    config = BacktestConfig(
        top_n=args.top_n,
        momentum_months=args.momentum_months,
        volatility_months=args.volatility_months,
        transaction_cost_bps=args.transaction_cost_bps,
        slippage_bps=args.slippage_bps,
        risk_free_rate_annual=args.risk_free_rate_annual,
    )
    report = evaluate_monthly_strategies(
        prices,
        config,
        holdout_months=args.holdout_months,
        min_train_months=args.min_train_months,
        fold_months=args.fold_months,
    )
    report["dataset"] = {
        "path": str(source),
        "sha256": sha256_file(source),
        "bytes": source.stat().st_size,
        "format": "CSV",
    }
    report["code_note"] = (
        "Record the exact git commit separately when running; this script does not infer "
        "or approve the source provenance or license."
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "completed_research_report",
        "purpose": report["purpose"],
        "ranking_approved": report["ranking_approved"],
        "input": str(source),
        "dataset_sha256": report["dataset"]["sha256"],
        "data_rows": report["data_rows"],
        "asset_count": report["asset_count"],
        "data_start": report["data_start"],
        "data_end": report["data_end"],
        "holdout_start": report["evaluation_design"]["holdout_start"],
        "holdout_end": report["evaluation_design"]["holdout_end"],
        "walkforward_folds": len(report["walkforward_folds"]),
        "output": str(output),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
