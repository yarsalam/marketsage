import numpy as np
import pandas as pd
import pytest
from research.backtest import BacktestConfig, run_monthly_momentum_backtest, validate_monthly_prices

def make_prices(n=48):
    dates = pd.date_range("2018-01-31", periods=n, freq="ME")
    t = np.arange(n, dtype=float)
    return pd.DataFrame({"steady": 100 * 1.004**t, "growth": 100 * 1.012**t,
                         "volatile": 100 * 1.006**t * (1 + .03*np.sin(t))}, index=dates)

def test_rejects_missing_prices():
    p = make_prices(); p.iloc[10, 0] = np.nan
    with pytest.raises(ValueError, match="missing or non-finite"): validate_monthly_prices(p)

def test_rejects_duplicate_dates():
    p = make_prices(); p.index = list(p.index[:-1]) + [p.index[-2]]
    with pytest.raises(ValueError, match="duplicate"): validate_monthly_prices(p)

def test_turnover_costs_are_nonnegative_and_net_not_above_gross():
    r = run_monthly_momentum_backtest(make_prices(), BacktestConfig(top_n=2, momentum_months=3, volatility_months=6))
    m = r["monthly"]
    assert r["periods"] == len(m)
    assert (m["turnover"] >= 0).all() and (m["transaction_cost"] >= 0).all()
    assert (m["net_return"] <= m["gross_return"] + 1e-12).all()
    assert m["turnover"].iloc[0] == pytest.approx(1.0)

def test_higher_cost_does_not_improve_total_return():
    p = make_prices()
    free = run_monthly_momentum_backtest(p, BacktestConfig(top_n=2, momentum_months=3, volatility_months=6, transaction_cost_bps=0))
    costly = run_monthly_momentum_backtest(p, BacktestConfig(top_n=2, momentum_months=3, volatility_months=6, transaction_cost_bps=25))
    assert costly["metrics"]["total_return"] <= free["metrics"]["total_return"] + 1e-12

def test_future_perturbation_does_not_change_earlier_results():
    p = make_prices(); cfg = BacktestConfig(top_n=2, momentum_months=3, volatility_months=6)
    base = run_monthly_momentum_backtest(p, cfg)["monthly"]
    p.iloc[-1, :] *= 1.5
    changed = run_monthly_momentum_backtest(p, cfg)["monthly"]
    pd.testing.assert_series_equal(base["net_return"].iloc[:-1], changed["net_return"].iloc[:-1])
    pd.testing.assert_series_equal(base["selected_assets"].iloc[:-1], changed["selected_assets"].iloc[:-1])

def test_insufficient_history_fails():
    with pytest.raises(ValueError, match="need more than"):
        run_monthly_momentum_backtest(make_prices(7), BacktestConfig(volatility_months=6))

def test_return_metrics_are_defined_for_benchmarks():
    from research.backtest import summarize_returns
    metrics = summarize_returns(pd.Series([.01, -.02, .03, .01, -.01]), 12)
    assert metrics["total_return"] is not None
    assert metrics["max_drawdown"] <= 0
