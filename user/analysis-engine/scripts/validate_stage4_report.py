#!/usr/bin/env python3
"""Validate structural and fail-closed invariants in a Stage 4 evaluation report."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def validate_report(report: dict) -> list[str]:
    errors: list[str] = []
    if report.get("purpose") != "exploratory_research_only":
        errors.append("purpose must be exploratory_research_only")
    if report.get("ranking_approved") is not False:
        errors.append("ranking_approved must be false")
    if report.get("source_scoring_approved") is not False:
        errors.append("source_scoring_approved must be false")

    dataset = report.get("dataset")
    if not isinstance(dataset, dict):
        errors.append("dataset metadata is missing")
    elif not re.fullmatch(r"[0-9a-f]{64}", str(dataset.get("sha256", ""))):
        errors.append("dataset.sha256 must be a 64-character lowercase SHA-256 digest")

    try:
        rows = int(report["data_rows"])
        assets = int(report["asset_count"])
        if rows < 1 or assets < 1:
            errors.append("data_rows and asset_count must be positive")
    except (KeyError, TypeError, ValueError):
        errors.append("data_rows and asset_count must be positive integers")

    design = report.get("evaluation_design")
    if not isinstance(design, dict):
        errors.append("evaluation_design is missing")
        design = {}
    if design.get("holdout_used_for_tuning") is not False:
        errors.append("holdout_used_for_tuning must be false")
    if design.get("walkforward_folds_end_before_final_holdout") is not True:
        errors.append("walk-forward folds must end before the final holdout")

    metrics = report.get("locked_holdout_metrics")
    if not isinstance(metrics, dict) or not metrics:
        errors.append("locked_holdout_metrics is missing")
    else:
        expected = {
            "momentum_strategy_net",
            "equal_weight_monthly_rebalanced_net",
            "equal_weight_buy_and_hold_net",
            "cash_zero_return",
        }
        missing = expected.difference(metrics)
        if missing:
            errors.append("missing holdout baselines: " + ", ".join(sorted(missing)))
        for name, item in metrics.items():
            if not isinstance(item, dict):
                errors.append(f"holdout metric entry {name} must be an object")
                continue
            try:
                periods = int(item["periods"])
                if periods < 1:
                    errors.append(f"holdout metric {name} must have positive periods")
            except (KeyError, TypeError, ValueError):
                errors.append(f"holdout metric {name} has invalid periods")

    folds = report.get("walkforward_folds")
    if not isinstance(folds, list) or not folds:
        errors.append("walkforward_folds must be a non-empty list")
    else:
        holdout_start = str(design.get("holdout_start", ""))
        previous_end = ""
        for idx, fold in enumerate(folds, start=1):
            if not isinstance(fold, dict):
                errors.append(f"walk-forward fold {idx} must be an object")
                continue
            start, end = str(fold.get("start", "")), str(fold.get("end", ""))
            if not start or not end or start > end:
                errors.append(f"walk-forward fold {idx} has invalid date boundaries")
            if holdout_start and end >= holdout_start:
                errors.append(f"walk-forward fold {idx} overlaps the final holdout")
            if previous_end and start <= previous_end:
                errors.append(f"walk-forward fold {idx} overlaps or is out of order")
            previous_end = end

    scenarios = report.get("cost_sensitivity")
    required_scenarios = {"zero_cost_reference", "configured_costs", "higher_cost_stress"}
    if not isinstance(scenarios, list):
        errors.append("cost_sensitivity must be a list")
    else:
        labels = {str(item.get("scenario")) for item in scenarios if isinstance(item, dict)}
        missing = required_scenarios.difference(labels)
        if missing:
            errors.append("missing cost scenarios: " + ", ".join(sorted(missing)))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Path to run_stage4_evaluation.py JSON output")
    args = parser.parse_args()
    path = Path(args.report).expanduser().resolve()
    if not path.is_file():
        parser.error(f"report does not exist: {path}")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot read report JSON: {exc}")
    if not isinstance(report, dict):
        parser.error("report root must be a JSON object")

    errors = validate_report(report)
    result = {
        "status": "failed" if errors else "passed",
        "purpose": report.get("purpose"),
        "ranking_approved": report.get("ranking_approved"),
        "source_scoring_approved": report.get("source_scoring_approved"),
        "dataset_sha256": report.get("dataset", {}).get("sha256") if isinstance(report.get("dataset"), dict) else None,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
