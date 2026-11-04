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
        "equal_weight_buy_and_hold_net",
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


def test_cost_scenarios_keep_distinct_labels_when_configured_costs_are_zero():
    report = evaluate_monthly_strategies(
        make_prices(),
        BacktestConfig(
            top_n=2, momentum_months=3, volatility_months=6,
            transaction_cost_bps=0, slippage_bps=0,
        ),
        holdout_months=12,
        min_train_months=24,
        fold_months=6,
    )
    scenarios = {item["scenario"]: item for item in report["cost_sensitivity"]}
    assert {"zero_cost_reference", "configured_costs", "higher_cost_stress"} == set(scenarios)
    assert scenarios["configured_costs"]["transaction_cost_bps"] == 0
    assert scenarios["configured_costs"]["slippage_bps"] == 0
    assert scenarios["higher_cost_stress"]["strictly_higher_than_configured"] is True
    assert scenarios["higher_cost_stress"]["transaction_cost_bps"] > 0
    assert scenarios["higher_cost_stress"]["slippage_bps"] > 0



def test_evaluation_reports_empirical_tail_risk_and_portfolio_diagnostics():
    from research.backtest import run_monthly_momentum_backtest

    prices = make_prices(60)
    config = BacktestConfig(
        top_n=2, momentum_months=3, volatility_months=6,
        transaction_cost_bps=10, slippage_bps=25,
    )
    report = evaluate_monthly_strategies(
        prices, config, holdout_months=12, min_train_months=24, fold_months=6,
    )
    strategy = run_monthly_momentum_backtest(prices, config)
    returns = strategy["monthly"]["net_return"]
    metrics = report["full_period_metrics"]["momentum_strategy_net"]
    q05 = returns.quantile(0.05)
    tail = returns[returns <= q05]

    assert metrics["sortino"] is not None
    assert metrics["annualized_downside_deviation"] >= 0
    assert metrics["historical_var_95_monthly_return"] == pytest.approx(q05)
    assert metrics["historical_expected_shortfall_95_monthly_return"] == pytest.approx(tail.mean())
    assert metrics["historical_tail_observations"] == len(tail)

    diagnostics = report["momentum_strategy_portfolio_diagnostics"]
    assert diagnostics["rebalance_periods"] == len(returns)
    assert diagnostics["input_universe_asset_count"] == prices.shape[1]
    assert diagnostics["unique_selected_asset_count"] <= prices.shape[1]
    assert 0 <= diagnostics["average_monthly_l1_turnover"] <= 2
    assert diagnostics["sum_total_cost_fractions"] == pytest.approx(
        strategy["monthly"]["total_cost"].sum()
    )
    assert diagnostics["average_invested_exposure"] == 1.0
    assert diagnostics["average_cash_fraction"] == 0.0

    for fold in report["walkforward_folds"]:
        fold_diag = fold["momentum_strategy_portfolio_diagnostics"]
        assert fold_diag["rebalance_periods"] == fold["periods"]
        assert fold_diag["average_invested_exposure"] == 1.0


def test_sortino_is_undefined_when_there_is_no_downside():
    from research.evaluation import _metric_summary

    summary = _metric_summary(
        pd.Series([0.01, 0.02, 0.03, 0.04]),
        BacktestConfig(risk_free_rate_annual=0.0),
    )
    assert summary["sortino"] is None
    assert summary["historical_var_95_monthly_return"] is not None
    assert summary["historical_expected_shortfall_95_monthly_return"] is not None
