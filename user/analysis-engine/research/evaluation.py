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
    summary = summarize_returns(
        returns, config.annualization_periods, config.risk_free_rate_annual
    )
    summary["periods"] = int(returns.dropna().shape[0])
    return summary


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
        folds.append(fold)

    full_metrics = {name: _metric_summary(series, cfg) for name, series in returns_by_name.items()}
    holdout_metrics = {
        name: _metric_summary(series.loc[holdout_dates], cfg)
        for name, series in returns_by_name.items()
    }
    # Predeclared cost stress cases; do not select a case after inspecting the holdout.
    scenarios = [
        ("zero_cost_reference", 0.0, 0.0),
        ("configured_costs", cfg.transaction_cost_bps, cfg.slippage_bps),
        (
            "higher_cost_stress",
            max(cfg.transaction_cost_bps, 25.0),
            max(cfg.slippage_bps, 50.0),
        ),
    ]
    cost_sensitivity = []
    seen_scenarios = set()
    for label, transaction_bps, slippage_bps in scenarios:
        key = (float(transaction_bps), float(slippage_bps))
        if key in seen_scenarios:
            continue
        seen_scenarios.add(key)
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
