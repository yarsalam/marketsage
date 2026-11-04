"""Predeclared, chronological evaluation helpers for the Stage 4 baseline."""
from __future__ import annotations

from dataclasses import asdict, replace
import math

import pandas as pd

from research.backtest import (
    BacktestConfig,
    run_monthly_momentum_backtest,
    summarize_returns,
    validate_monthly_prices,
)


def _net_equal_weight_returns(prices: pd.DataFrame, dates: pd.DatetimeIndex, config: BacktestConfig) -> pd.Series:
    """All-asset equal-weight monthly-rebalanced comparator with the same cost knobs."""
    asset_returns = prices.pct_change(fill_method=None)
    target = pd.Series(1.0 / len(prices.columns), index=prices.columns)
    previous_target = pd.Series(0.0, index=prices.columns)
    values = []
    for j, date in enumerate(dates):
        if j == 0:
            pretrade = previous_target
        else:
            prior_date = dates[j - 1]
            drift = asset_returns.loc[prior_date]
            pretrade = previous_target * (1 + drift)
            total = float(pretrade.sum())
            if not math.isfinite(total) or total <= 0:
                raise ValueError("invalid equal-weight benchmark pre-trade portfolio value")
            pretrade = pretrade / total
        turnover = float((target - pretrade).abs().sum())
        cost = turnover * (config.transaction_cost_bps + config.slippage_bps) / 10000
        row_returns = asset_returns.loc[date]
        if row_returns.isna().any():
            raise ValueError(f"missing benchmark return at {date.date()}")
        gross = float((target * row_returns).sum())
        values.append((1 - cost) * (1 + gross) - 1)
        previous_target = target.copy()
    return pd.Series(values, index=dates, name="equal_weight_monthly_rebalanced")


def _net_equal_weight_buy_hold_returns(
    prices: pd.DataFrame, dates: pd.DatetimeIndex, config: BacktestConfig
) -> pd.Series:
    """Initial equal-weight allocation, then let holdings drift without rebalancing."""
    asset_returns = prices.pct_change(fill_method=None)
    weights = pd.Series(1.0 / len(prices.columns), index=prices.columns)
    initial_cost = (config.transaction_cost_bps + config.slippage_bps) / 10000
    values = []
    for j, date in enumerate(dates):
        if j > 0:
            prior_date = dates[j - 1]
            drift = asset_returns.loc[prior_date]
            weights = weights * (1 + drift)
            total = float(weights.sum())
            if not math.isfinite(total) or total <= 0:
                raise ValueError("invalid buy-and-hold benchmark portfolio value")
            weights = weights / total
        row_returns = asset_returns.loc[date]
        if row_returns.isna().any():
            raise ValueError(f"missing buy-and-hold benchmark return at {date.date()}")
        gross = float((weights * row_returns).sum())
        cost = initial_cost if j == 0 else 0.0
        values.append((1 - cost) * (1 + gross) - 1 if j == 0 else gross)
    return pd.Series(values, index=dates, name="equal_weight_buy_and_hold_net")


def _metric_summary(returns: pd.Series, config: BacktestConfig) -> dict:
    """Return conventional metrics plus explicitly defined downside/tail measures."""
    r = returns.dropna().astype(float)
    summary = summarize_returns(
        r, config.annualization_periods, config.risk_free_rate_annual
    )
    summary["periods"] = int(r.shape[0])
    summary["sortino"] = None
    summary["annualized_downside_deviation"] = None
    summary["historical_var_95_monthly_return"] = None
    summary["historical_expected_shortfall_95_monthly_return"] = None
    summary["historical_tail_observations"] = 0
    summary["tail_measure_method"] = "empirical monthly 5th-percentile return; small-sample unstable"
    if r.empty:
        return summary

    periodic_rf = (1 + config.risk_free_rate_annual) ** (1 / config.annualization_periods) - 1
    excess = r - periodic_rf
    downside = excess.clip(upper=0.0)
    downside_deviation = float(
        math.sqrt(float((downside ** 2).mean())) * math.sqrt(config.annualization_periods)
    )
    annualized_mean_excess = float(excess.mean() * config.annualization_periods)
    summary["annualized_downside_deviation"] = downside_deviation
    if downside_deviation > 0:
        summary["sortino"] = annualized_mean_excess / downside_deviation

    var_return = float(r.quantile(0.05))
    tail = r[r <= var_return]
    summary["historical_var_95_monthly_return"] = var_return
    summary["historical_expected_shortfall_95_monthly_return"] = float(tail.mean())
    summary["historical_tail_observations"] = int(tail.shape[0])
    return summary


def _portfolio_diagnostics(monthly: pd.DataFrame, input_asset_count: int) -> dict:
    """Summarize realized portfolio mechanics; cost sums are not compounded P&L drag."""
    if monthly.empty:
        return {
            "rebalance_periods": 0,
            "average_monthly_l1_turnover": None,
            "total_l1_turnover": 0.0,
            "sum_transaction_cost_fractions": 0.0,
            "sum_slippage_cost_fractions": 0.0,
            "sum_total_cost_fractions": 0.0,
            "average_monthly_selected_asset_count": None,
            "unique_selected_asset_count": 0,
            "input_universe_asset_count": int(input_asset_count),
            "unique_selected_asset_coverage_fraction": None,
            "average_invested_exposure": None,
            "average_cash_fraction": None,
            "selected_asset_frequency": {},
        }

    frequencies: dict[str, int] = {}
    selected_counts = []
    for value in monthly["selected_assets"].astype(str):
        selected = [item for item in value.split(",") if item]
        selected_counts.append(len(selected))
        for symbol in selected:
            frequencies[symbol] = frequencies.get(symbol, 0) + 1

    unique_selected = len(frequencies)
    return {
        "rebalance_periods": int(len(monthly)),
        "average_monthly_l1_turnover": float(monthly["turnover"].mean()),
        "total_l1_turnover": float(monthly["turnover"].sum()),
        "max_monthly_l1_turnover": float(monthly["turnover"].max()),
        "sum_transaction_cost_fractions": float(monthly["transaction_cost"].sum()),
        "sum_slippage_cost_fractions": float(monthly["slippage_cost"].sum()),
        "sum_total_cost_fractions": float(monthly["total_cost"].sum()),
        "average_monthly_selected_asset_count": float(sum(selected_counts) / len(selected_counts)),
        "unique_selected_asset_count": int(unique_selected),
        "input_universe_asset_count": int(input_asset_count),
        "unique_selected_asset_coverage_fraction": (
            float(unique_selected / input_asset_count) if input_asset_count else None
        ),
        "average_invested_exposure": 1.0,
        "average_cash_fraction": 0.0,
        "selected_asset_frequency": dict(sorted(frequencies.items())),
        "turnover_convention": "L1 gross traded weight (buys plus sells)",
        "cost_sum_note": "Sum of per-period cost fractions; not compounded portfolio return drag.",
        "exposure_note": "The current long-only strategy is fully invested each rebalance; no cash sleeve is modeled.",
    }


def evaluate_monthly_strategies(
    monthly_prices: pd.DataFrame,
    config: BacktestConfig | None = None,
    *,
    holdout_months: int = 12,
    min_train_months: int = 24,
    fold_months: int = 6,
) -> dict:
    """Compare fixed strategy with cash/equal-weight baselines and chronological folds.

    The final holdout is reported separately and must not be used to tune settings.
    Walk-forward folds end before that holdout. Parameters remain fixed throughout;
    this is not model training or proof of future predictive performance.
    """
    cfg = config or BacktestConfig()
    cfg.validate()
    prices = validate_monthly_prices(monthly_prices)
    if holdout_months < 1 or fold_months < 1 or min_train_months < 1:
        raise ValueError("holdout_months, fold_months, and min_train_months must be positive")
    if len(prices) <= min_train_months + holdout_months:
        raise ValueError("insufficient observations for minimum training history and holdout")

    strategy = run_monthly_momentum_backtest(prices, cfg)
    strategy_returns = strategy["monthly"]["net_return"]
    result_dates = pd.DatetimeIndex(strategy_returns.index)
    equal_weight = _net_equal_weight_returns(prices, result_dates, cfg)
    buy_hold = _net_equal_weight_buy_hold_returns(prices, result_dates, cfg)
    cash = pd.Series(0.0, index=result_dates, name="cash_zero_return")

    returns_by_name = {
        "momentum_strategy_net": strategy_returns,
        "equal_weight_monthly_rebalanced_net": equal_weight,
        "equal_weight_buy_and_hold_net": buy_hold,
        "cash_zero_return": cash,
    }
    holdout_start = result_dates[-holdout_months]
    holdout_dates = result_dates[result_dates >= holdout_start]
    development_dates = result_dates[result_dates < holdout_start]
    first_walkforward_date = prices.index[min_train_months]
    walkforward_dates = development_dates[development_dates >= first_walkforward_date]

    folds = []
    for start in range(0, len(walkforward_dates), fold_months):
        dates = walkforward_dates[start:start + fold_months]
        if len(dates) == 0:
            continue
        fold = {
            "fold": len(folds) + 1,
            "start": dates[0].date().isoformat(),
            "end": dates[-1].date().isoformat(),
            "periods": len(dates),
            "metrics": {},
        }
        for name, series in returns_by_name.items():
            fold["metrics"][name] = _metric_summary(series.loc[dates], cfg)
        fold["momentum_strategy_portfolio_diagnostics"] = _portfolio_diagnostics(
            strategy["monthly"].loc[dates], prices.shape[1]
        )
        folds.append(fold)

    full_metrics = {name: _metric_summary(series, cfg) for name, series in returns_by_name.items()}
    holdout_metrics = {
        name: _metric_summary(series.loc[holdout_dates], cfg)
        for name, series in returns_by_name.items()
    }
    # Predeclared cost stress cases; do not select a case after inspecting the holdout.
    stress_transaction_bps = min(max(cfg.transaction_cost_bps + 15.0, 25.0), 1000.0)
    stress_slippage_bps = min(max(cfg.slippage_bps + 25.0, 50.0), 1000.0)
    scenarios = [
        ("zero_cost_reference", 0.0, 0.0),
        ("configured_costs", cfg.transaction_cost_bps, cfg.slippage_bps),
        ("higher_cost_stress", stress_transaction_bps, stress_slippage_bps),
    ]
    cost_sensitivity = []
    for label, transaction_bps, slippage_bps in scenarios:
        scenario_cfg = replace(
            cfg,
            transaction_cost_bps=float(transaction_bps),
            slippage_bps=float(slippage_bps),
        )
        scenario_result = run_monthly_momentum_backtest(prices, scenario_cfg)
        scenario_returns = scenario_result["monthly"]["net_return"]
        cost_sensitivity.append({
            "scenario": label,
            "transaction_cost_bps": float(transaction_bps),
            "slippage_bps": float(slippage_bps),
            "strictly_higher_than_configured": (
                float(transaction_bps) > cfg.transaction_cost_bps
                or float(slippage_bps) > cfg.slippage_bps
            ),
            "stress_cap_reached": (
                label == "higher_cost_stress"
                and float(transaction_bps) == cfg.transaction_cost_bps
                and float(slippage_bps) == cfg.slippage_bps
            ),
            "full_period_metrics": _metric_summary(scenario_returns, scenario_cfg),
            "locked_holdout_metrics": _metric_summary(
                scenario_returns.loc[holdout_dates], scenario_cfg
            ),
            "period_cost_fractions": {
                "transaction": float(scenario_result["monthly"]["transaction_cost"].sum()),
                "slippage": float(scenario_result["monthly"]["slippage_cost"].sum()),
                "total": float(scenario_result["monthly"]["total_cost"].sum()),
            },
        })

    label_rows = []
    six_month = prices.shift(-6).div(prices).sub(1)
    for symbol in prices.columns:
        valid = six_month[symbol].dropna()
        label_rows.append({
            "symbol": str(symbol),
            "available_forward_6m_labels": int(len(valid)),
            "first_label_start": prices.index[0].date().isoformat() if len(valid) else None,
            "last_label_start": valid.index[-1].date().isoformat() if len(valid) else None,
            "label_horizon_months": 6,
            "purpose": "label_inventory_only_not_predictive_evaluation",
        })

    return {
        "purpose": "exploratory_research_only",
        "ranking_approved": False,
        "source_scoring_approved": False,
        "data_rows": int(len(prices)),
        "asset_count": int(prices.shape[1]),
        "assets": [str(c) for c in prices.columns],
        "data_start": prices.index.min().date().isoformat(),
        "data_end": prices.index.max().date().isoformat(),
        "strategy_config": asdict(cfg),
        "evaluation_design": {
            "monthly_rebalance": True,
            "final_holdout_months": holdout_months,
            "holdout_start": holdout_dates[0].date().isoformat(),
            "holdout_end": holdout_dates[-1].date().isoformat(),
            "holdout_used_for_tuning": False,
            "minimum_prior_observations_before_walkforward": min_train_months,
            "walkforward_fold_months": fold_months,
            "walkforward_folds_end_before_final_holdout": True,
            "walkforward_parameters_fixed": True,
            "risk_free_rate_annual_for_sharpe": cfg.risk_free_rate_annual,
            "cost_convention": "cost fractions charged on sum of absolute target-minus-pretrade weights (L1 gross traded weight: buys plus sells), including initial allocation",
            "benchmark_definitions": {
                "cash_zero_return": "simplified zero-return reference; not a real cash yield",
                "equal_weight_monthly_rebalanced_net": "equal weights across all input assets each month, same transaction-cost and slippage assumptions",
                "equal_weight_buy_and_hold_net": "initial equal-weight allocation across all input assets, then weights drift without rebalancing; initial costs only",
            },
        },
        "full_period_metrics": full_metrics,
        "locked_holdout_metrics": holdout_metrics,
        "momentum_strategy_portfolio_diagnostics": _portfolio_diagnostics(
            strategy["monthly"], prices.shape[1]
        ),
        "locked_holdout_momentum_strategy_portfolio_diagnostics": _portfolio_diagnostics(
            strategy["monthly"].loc[holdout_dates], prices.shape[1]
        ),
        "walkforward_folds": folds,
        "cost_sensitivity": cost_sensitivity,
        "six_month_forward_label_inventory": label_rows,
        "limitations": [
            "Fixed-parameter historical simulation; no trained predictive model or calibrated probability.",
            "Monthly-rebalanced portfolio performance is not the same experiment as predicting six-month forward returns.",
            "Equal-weight and zero-return cash are simple references, not necessarily investable benchmarks.",
            "No accepted source licensing, point-in-time revision, survivorship, or executable-price validation is implied.",
            "Current mixed US-listed funds/equities and crypto universe is not representative of Iranian assets.",
            "Slippage is an assumption; actual spread, fees, liquidity and execution are not established by this report.",
            "A locked historical holdout is not evidence of future returns and must not be used for parameter selection.",
        ],
    }
