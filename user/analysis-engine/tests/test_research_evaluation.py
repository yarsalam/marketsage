import numpy as np
import pandas as pd
import pytest

from research.backtest import BacktestConfig
from research.evaluation import evaluate_monthly_strategies


def make_prices(n=60):
    dates = pd.date_range("2020-01-31", periods=n, freq="ME")
    t = np.arange(n, dtype=float)
    return pd.DataFrame({
        "steady": 100 * 1.004**t,
        "growth": 100 * 1.012**t,
        "volatile": 100 * 1.006**t * (1 + .03 * np.sin(t)),
        "cyclical": 100 * (1.003**t) * (1 + .08 * np.sin(t / 3)),
    }, index=dates)


def test_evaluation_reports_full_holdout_and_pre_holdout_folds():
    report = evaluate_monthly_strategies(
        make_prices(),
        BacktestConfig(top_n=2, momentum_months=3, volatility_months=6),
        holdout_months=12,
        min_train_months=24,
        fold_months=6,
    )
    assert report["purpose"] == "exploratory_research_only"
    assert report["ranking_approved"] is False
    assert report["evaluation_design"]["holdout_used_for_tuning"] is False
    assert report["evaluation_design"]["walkforward_folds_end_before_final_holdout"] is True
    assert report["evaluation_design"]["holdout_start"] == "2024-01-31"
    assert report["evaluation_design"]["holdout_end"] == "2024-12-31"
    assert report["locked_holdout_metrics"]["momentum_strategy_net"]["periods"] == 12
    assert len(report["walkforward_folds"]) == 4
    assert all(fold["end"] < report["evaluation_design"]["holdout_start"] for fold in report["walkforward_folds"])
    assert set(report["full_period_metrics"]) == {
        "momentum_strategy_net",
        "equal_weight_monthly_rebalanced_net",
        "cash_zero_return",
    }


def test_evaluation_rejects_too_short_history():
    with pytest.raises(ValueError, match="insufficient observations"):
        evaluate_monthly_strategies(
            make_prices(30),
            BacktestConfig(top_n=2, momentum_months=3, volatility_months=6),
            holdout_months=12,
            min_train_months=24,
        )


def test_six_month_label_inventory_is_not_claimed_as_prediction():
    report = evaluate_monthly_strategies(
        make_prices(),
        BacktestConfig(top_n=2, momentum_months=3, volatility_months=6),
        holdout_months=12,
        min_train_months=24,
    )
    labels = report["six_month_forward_label_inventory"]
    assert len(labels) == 4
    assert all(row["label_horizon_months"] == 6 for row in labels)
    assert all(row["purpose"] == "label_inventory_only_not_predictive_evaluation" for row in labels)
    assert all(row["available_forward_6m_labels"] == 54 for row in labels)

def test_cost_sensitivity_is_predeclared_and_higher_costs_do_not_improve_return():
    report = evaluate_monthly_strategies(
        make_prices(),
        BacktestConfig(
            top_n=2, momentum_months=3, volatility_months=6,
            transaction_cost_bps=10, slippage_bps=0,
        ),
        holdout_months=12,
        min_train_months=24,
        fold_months=6,
    )
    scenarios = {item["scenario"]: item for item in report["cost_sensitivity"]}
    assert {"zero_cost_reference", "configured_costs", "higher_cost_stress"} <= set(scenarios)
    assert scenarios["higher_cost_stress"]["full_period_metrics"]["total_return"] <= (
        scenarios["configured_costs"]["full_period_metrics"]["total_return"] + 1e-12
    )
    assert scenarios["higher_cost_stress"]["period_cost_fractions"]["total"] >= (
        scenarios["configured_costs"]["period_cost_fractions"]["total"]
    )
