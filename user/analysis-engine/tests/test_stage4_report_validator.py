from copy import deepcopy

from scripts.validate_stage4_report import validate_report


def valid_report():
    return {
        "purpose": "exploratory_research_only",
        "ranking_approved": False,
        "source_scoring_approved": False,
        "data_rows": 78,
        "asset_count": 11,
        "dataset": {"sha256": "a" * 64},
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
