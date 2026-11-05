#!/usr/bin/env python3
"""Run a reproducible, research-only Stage 4 comparison from a monthly price CSV."""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np

import pandas as pd

# Allow direct execution as `python scripts/run_stage4_evaluation.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.backtest import BacktestConfig
from research.evaluation import evaluate_monthly_strategies
from research.provenance import capture_git_provenance, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="monthly_prices.csv")
    parser.add_argument("--output", required=True, help="output JSON report path (outside the repository)")
    parser.add_argument("--manifest-output", help="optional sidecar manifest path; defaults to OUTPUT.manifest.json")
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
    manifest_output = (
        Path(args.manifest_output).expanduser().resolve()
        if args.manifest_output else Path(str(output) + ".manifest.json")
    )
    repository_root = Path(__file__).resolve().parents[3]
    if output == repository_root or repository_root in output.parents:
        parser.error("write the report outside the repository so the captured code revision stays reproducible")
    if manifest_output == repository_root or repository_root in manifest_output.parents:
        parser.error("write the run manifest outside the repository")
    if output == source or manifest_output in {source, output}:
        parser.error("input, report and manifest paths must be three distinct files")
    if not source.is_file():
        parser.error(f"input CSV does not exist: {source}")
    try:
        git_metadata = capture_git_provenance(repository_root)
    except RuntimeError as exc:
        parser.error(str(exc))
    run_started_at = datetime.now(timezone.utc).isoformat()
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
    report["run_metadata"] = {
        **git_metadata,
        "started_at_utc": run_started_at,
        "python_version": platform.python_version(),
        "pandas_version": pd.__version__,
        "numpy_version": np.__version__,
        "randomness": "deterministic_no_rng",
        "source_manifest_sha256": None,
        "source_manifest_status": "not_supplied",
        "availability_timestamp_status": "not_verified_by_evaluation_runner",
    }
    report["code_note"] = (
        "The exact code commit and worktree state are recorded in run_metadata. "
        "No source manifest was supplied; this does not establish source provenance, "
        "publication timing, rights or point-in-time validity."
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    report_sha256 = sha256_file(output)
    manifest = {
        "schema_version": 1,
        "report_sha256": report_sha256,
        "report_bytes": output.stat().st_size,
        "input_sha256": report["dataset"]["sha256"],
        "code_commit": git_metadata["code_commit"],
        "git_worktree_clean": git_metadata["git_worktree_clean"],
        "git_status_sha256": git_metadata["git_status_sha256"],
        "git_status_entry_count": git_metadata["git_status_entry_count"],
        "strategy_config": report["strategy_config"],
        "evaluation_design": report["evaluation_design"],
        "randomness": "deterministic_no_rng",
        "source_manifest_sha256": None,
        "source_manifest_status": "not_supplied",
        "created_at_utc": run_started_at,
    }
    manifest_output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    manifest_sha256 = sha256_file(manifest_output)
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
        "code_commit": git_metadata["code_commit"],
        "git_worktree_clean": git_metadata["git_worktree_clean"],
        "report_sha256": report_sha256,
        "manifest": str(manifest_output),
        "manifest_sha256": manifest_sha256,
        "output": str(output),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
