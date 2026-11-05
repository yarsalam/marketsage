#!/usr/bin/env python3
"""Validate structural and fail-closed invariants in a Stage 4 report and sidecar manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.provenance import sha256_file


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

    run_metadata = report.get("run_metadata")
    if not isinstance(run_metadata, dict):
        errors.append("run_metadata is missing; exact code/environment provenance is required")
    else:
        if not re.fullmatch(r"[0-9a-f]{40}", str(run_metadata.get("code_commit", ""))):
            errors.append("run_metadata.code_commit must be a full lowercase Git commit SHA")
        if run_metadata.get("git_worktree_clean") is not True:
            errors.append("run_metadata.git_worktree_clean must be true for reproducible evaluation")
        if not re.fullmatch(r"[0-9a-f]{64}", str(run_metadata.get("git_status_sha256", ""))):
            errors.append("run_metadata.git_status_sha256 must be a 64-character lowercase SHA-256 digest")
        if type(run_metadata.get("git_status_entry_count")) is not int or run_metadata.get("git_status_entry_count") != 0:
            errors.append("run_metadata.git_status_entry_count must be integer zero")
        if run_metadata.get("git_worktree_clean") is True and run_metadata.get("git_status_sha256") != hashlib.sha256(b"").hexdigest():
            errors.append("a clean worktree must have the SHA-256 digest of an empty Git status")
        if run_metadata.get("randomness") != "deterministic_no_rng":
            errors.append("run_metadata.randomness must state deterministic_no_rng")
        if run_metadata.get("source_manifest_status") != "not_supplied":
            errors.append("run_metadata.source_manifest_status must disclose that no source manifest was supplied")
        if run_metadata.get("availability_timestamp_status") != "not_verified_by_evaluation_runner":
            errors.append("run_metadata must disclose that source availability timestamps are not verified")
        for field in ("started_at_utc", "python_version", "pandas_version", "numpy_version"):
            if not isinstance(run_metadata.get(field), str) or not run_metadata[field]:
                errors.append(f"run_metadata.{field} must be a non-empty string")

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


def validate_manifest(report: dict, manifest: dict, report_path: Path) -> list[str]:
    """Verify the sidecar binds the report, input dataset, code and configuration."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["run manifest must be a JSON object"]
    if manifest.get("schema_version") != 1:
        errors.append("manifest.schema_version must be 1")
    try:
        actual_report_sha = sha256_file(report_path)
        actual_report_bytes = report_path.stat().st_size
    except OSError as exc:
        return [f"cannot hash report artifact: {exc}"]
    if manifest.get("report_sha256") != actual_report_sha:
        errors.append("manifest.report_sha256 does not match the report artifact")
    if manifest.get("report_bytes") != actual_report_bytes:
        errors.append("manifest.report_bytes does not match the report artifact")
    dataset = report.get("dataset") if isinstance(report, dict) else None
    run_metadata = report.get("run_metadata") if isinstance(report, dict) else None
    if not isinstance(dataset, dict) or manifest.get("input_sha256") != dataset.get("sha256"):
        errors.append("manifest.input_sha256 does not match report.dataset.sha256")
    if not isinstance(run_metadata, dict):
        errors.append("report.run_metadata is required to validate the manifest")
    else:
        if manifest.get("code_commit") != run_metadata.get("code_commit"):
            errors.append("manifest.code_commit does not match report.run_metadata.code_commit")
        if manifest.get("git_worktree_clean") is not True or run_metadata.get("git_worktree_clean") is not True:
            errors.append("manifest and report must both record a clean Git worktree")
        if manifest.get("git_status_sha256") != run_metadata.get("git_status_sha256"):
            errors.append("manifest.git_status_sha256 does not match report.run_metadata")
        if manifest.get("git_status_entry_count") != run_metadata.get("git_status_entry_count"):
            errors.append("manifest.git_status_entry_count does not match report.run_metadata")
        if manifest.get("randomness") != run_metadata.get("randomness"):
            errors.append("manifest.randomness does not match report.run_metadata")
        if manifest.get("source_manifest_status") != run_metadata.get("source_manifest_status"):
            errors.append("manifest.source_manifest_status does not match report.run_metadata")
    if manifest.get("strategy_config") != report.get("strategy_config"):
        errors.append("manifest.strategy_config does not match the report")
    if manifest.get("evaluation_design") != report.get("evaluation_design"):
        errors.append("manifest.evaluation_design does not match the report")
    if manifest.get("source_manifest_status") != "not_supplied":
        errors.append("manifest.source_manifest_status must disclose that no source manifest was supplied")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Path to run_stage4_evaluation.py JSON output")
    parser.add_argument("--manifest", help="sidecar manifest path; defaults to REPORT.manifest.json")
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

    manifest_path = (
        Path(args.manifest).expanduser().resolve()
        if args.manifest else Path(str(path) + ".manifest.json")
    )
    errors = validate_report(report)
    if not manifest_path.is_file():
        errors.append(f"run manifest does not exist: {manifest_path}")
        manifest_sha256 = None
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read run manifest JSON: {exc}")
            manifest_sha256 = None
        else:
            errors.extend(validate_manifest(report, manifest, path))
            manifest_sha256 = sha256_file(manifest_path)

    result = {
        "status": "failed" if errors else "passed",
        "purpose": report.get("purpose"),
        "ranking_approved": report.get("ranking_approved"),
        "source_scoring_approved": report.get("source_scoring_approved"),
        "dataset_sha256": report.get("dataset", {}).get("sha256") if isinstance(report.get("dataset"), dict) else None,
        "code_commit": report.get("run_metadata", {}).get("code_commit") if isinstance(report.get("run_metadata"), dict) else None,
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_sha256,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
