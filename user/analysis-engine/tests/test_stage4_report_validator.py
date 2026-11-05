import hashlib
import json

from scripts.validate_stage4_report import validate_manifest, validate_report


def valid_report():
    return {
        "purpose": "exploratory_research_only",
        "ranking_approved": False,
        "source_scoring_approved": False,
        "data_rows": 78,
        "asset_count": 11,
        "dataset": {"sha256": "a" * 64},
        "run_metadata": {
            "code_commit": "c" * 40,
            "git_worktree_clean": True,
            "git_status_sha256": "b" * 64,
            "git_status_entry_count": 0,
            "randomness": "deterministic_no_rng",
        },
        "strategy_config": {"top_n": 3, "transaction_cost_bps": 10},
        "evaluation_design": {
            "holdout_used_for_tuning": False,
            "walkforward_folds_end_before_final_holdout": True,
            "holdout_start": "2025-10-31",
        },
        "locked_holdout_metrics": {
            "momentum_strategy_net": {"periods": 12},
            "equal_weight_monthly_rebalanced_net": {"periods": 12},
            "equal_weight_buy_and_hold_net": {"periods": 12},
            "cash_zero_return": {"periods": 12},
        },
        "walkforward_folds": [
            {"fold": 1, "start": "2023-01-31", "end": "2023-06-30"},
            {"fold": 2, "start": "2023-07-31", "end": "2023-12-31"},
        ],
        "cost_sensitivity": [
            {"scenario": "zero_cost_reference"},
            {"scenario": "configured_costs"},
            {"scenario": "higher_cost_stress"},
        ],
    }


def test_valid_report_passes_fail_closed_invariants():
    assert validate_report(valid_report()) == []


def test_validator_rejects_ranking_enabled_or_holdout_tuning():
    report = valid_report()
    report["ranking_approved"] = True
    report["evaluation_design"]["holdout_used_for_tuning"] = True
    errors = validate_report(report)
    assert any("ranking_approved must be false" in error for error in errors)
    assert any("holdout_used_for_tuning must be false" in error for error in errors)


def test_validator_rejects_fold_overlapping_holdout_and_missing_baseline():
    report = valid_report()
    report["walkforward_folds"][1]["end"] = "2025-10-31"
    del report["locked_holdout_metrics"]["equal_weight_buy_and_hold_net"]
    errors = validate_report(report)
    assert any("overlaps the final holdout" in error for error in errors)
    assert any("equal_weight_buy_and_hold_net" in error for error in errors)


def test_validator_rejects_invalid_hash_and_missing_cost_stress():
    report = valid_report()
    report["dataset"]["sha256"] = "not-a-hash"
    report["cost_sensitivity"] = [{"scenario": "configured_costs"}]
    errors = validate_report(report)
    assert any("SHA-256" in error for error in errors)
    assert any("higher_cost_stress" in error for error in errors)


def test_validator_rejects_missing_or_dirty_code_provenance():
    report = valid_report()
    del report["run_metadata"]
    assert any("run_metadata is missing" in error for error in validate_report(report))

    report = valid_report()
    report["run_metadata"]["git_worktree_clean"] = False
    report["run_metadata"]["git_status_entry_count"] = 2
    errors = validate_report(report)
    assert any("git_worktree_clean must be true" in error for error in errors)
    assert any("git_status_entry_count must be zero" in error for error in errors)


def test_manifest_binds_report_input_code_and_configuration(tmp_path):
    report = valid_report()
    report_path = tmp_path / "stage4-report.json"
    report_path.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
    report_bytes = report_path.read_bytes()
    manifest = {
        "schema_version": 1,
        "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "report_bytes": len(report_bytes),
        "input_sha256": report["dataset"]["sha256"],
        "code_commit": report["run_metadata"]["code_commit"],
        "git_worktree_clean": True,
        "git_status_sha256": report["run_metadata"]["git_status_sha256"],
        "strategy_config": report["strategy_config"],
        "evaluation_design": report["evaluation_design"],
        "source_manifest_status": "not_supplied",
    }
    assert validate_manifest(report, manifest, report_path) == []

    manifest["report_sha256"] = "0" * 64
    manifest["input_sha256"] = "f" * 64
    errors = validate_manifest(report, manifest, report_path)
    assert any("report_sha256" in error for error in errors)
    assert any("input_sha256" in error for error in errors)
