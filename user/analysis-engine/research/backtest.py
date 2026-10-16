"""Leakage-aware monthly momentum research baseline."""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd

@dataclass(frozen=True)
class BacktestConfig:
    top_n: int = 3
    momentum_months: int = 3
    volatility_months: int = 12
    transaction_cost_bps: float = 10.0
    annualization_periods: int = 12
    def validate(self):
        if self.top_n < 1 or self.momentum_months < 1 or self.volatility_months < 2:
            raise ValueError("top_n and lookbacks must be positive; volatility lookback >= 2")
        if not 0 <= self.transaction_cost_bps <= 1000:
            raise ValueError("transaction_cost_bps must be between 0 and 1000")

def validate_monthly_prices(prices: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        raise ValueError("prices must be a non-empty DataFrame")
    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError("prices index must be a DatetimeIndex")
    if prices.index.has_duplicates:
        raise ValueError("prices index must not contain duplicate dates")
    if not prices.index.is_monotonic_increasing:
        raise ValueError("prices must be sorted oldest to newest")
    if prices.columns.has_duplicates or prices.shape[1] < 1:
        raise ValueError("asset columns must be unique and non-empty")
    out = prices.apply(pd.to_numeric, errors="coerce").astype(float)
    values = out.to_numpy()
    if not np.isfinite(values).all():
        raise ValueError("prices must not contain missing or non-finite values; align data explicitly")
    if (values <= 0).any():
        raise ValueError("prices must be strictly positive")
    return out

def summarize_returns(r: pd.Series, periods: int = 12) -> dict:
    r = r.dropna().astype(float)
    if r.empty:
        return {"total_return": None, "cagr": None, "annualized_volatility": None, "sharpe": None, "max_drawdown": None}
    equity = (1 + r).cumprod()
    vol = float(r.std(ddof=1) * math.sqrt(periods)) if len(r) > 1 else None
    years = len(r) / periods
    return {
        "total_return": float(equity.iloc[-1] - 1),
        "cagr": float(equity.iloc[-1] ** (1 / years) - 1) if equity.iloc[-1] > 0 else None,
        "annualized_volatility": vol,
        "sharpe": float(r.mean() * periods / vol) if vol and vol > 0 else None,
        "max_drawdown": float((equity / equity.cummax() - 1).min()),
    }

def run_monthly_momentum_backtest(monthly_prices: pd.DataFrame, config: BacktestConfig | None = None) -> dict:
    """Long-only top momentum with drift-aware turnover and rebalance costs.

    Signal uses data through the prior month-end. Target weights are formed at
    that close, turnover is measured against prior holdings after their weights
    have drifted with the just-completed month, and the next month's return is
    then applied. Costs are deducted from capital before that next-period return.
    """
    cfg = config or BacktestConfig()
    cfg.validate()
    prices = validate_monthly_prices(monthly_prices)
    warmup = max(cfg.momentum_months, cfg.volatility_months) + 1
    if len(prices) <= warmup:
        raise ValueError(f"need more than {warmup} monthly observations")
    asset_returns = prices.pct_change(fill_method=None)
    previous_target = pd.Series(0.0, index=prices.columns)
    rows = []
    for i in range(warmup, len(prices)):
        past_prices, past_returns = prices.iloc[:i], asset_returns.iloc[:i]
        momentum = past_prices.iloc[-1] / past_prices.iloc[-cfg.momentum_months - 1] - 1
        vol = past_returns.iloc[-cfg.volatility_months:].std(ddof=1)
        valid = momentum.notna() & np.isfinite(momentum) & vol.notna() & np.isfinite(vol)
        scores = (momentum[valid] / (1 + vol[valid])).sort_values(ascending=False)
        selected = scores.head(cfg.top_n).index
        if len(selected) == 0:
            raise ValueError(f"no eligible assets at {prices.index[i - 1].date()}")
        target = pd.Series(0.0, index=prices.columns)
        target.loc[selected] = 1 / len(selected)

        if previous_target.sum() == 0:
            pretrade = previous_target
        else:
            drift_returns = asset_returns.iloc[i - 1]
            if drift_returns.loc[previous_target > 0].isna().any():
                raise ValueError(f"missing held-asset return at {prices.index[i - 1].date()}")
            pretrade = previous_target * (1 + drift_returns.fillna(0))
            total = float(pretrade.sum())
            if not np.isfinite(total) or total <= 0:
                raise ValueError("invalid pre-trade portfolio value")
            pretrade = pretrade / total

        turnover = float((target - pretrade).abs().sum())
        cost = turnover * cfg.transaction_cost_bps / 10000
        next_returns = asset_returns.iloc[i]
        if next_returns.loc[selected].isna().any():
            raise ValueError(f"missing next-period return for selected assets at {prices.index[i].date()}")
        gross = float((target.loc[selected] * next_returns.loc[selected]).sum())
        net = float((1 - cost) * (1 + gross) - 1)
        rows.append({"date": prices.index[i], "gross_return": gross, "turnover": turnover,
                     "transaction_cost": cost, "net_return": net,
                     "selected_assets": ",".join(map(str, selected))})
        previous_target = target
    result = pd.DataFrame(rows).set_index("date")
    result["equity"] = (1 + result["net_return"]).cumprod()
    result["drawdown"] = result["equity"] / result["equity"].cummax() - 1
    metrics = summarize_returns(result["net_return"], cfg.annualization_periods)
    metrics["average_monthly_turnover"] = float(result["turnover"].mean())
    metrics["sum_of_period_cost_fractions"] = float(result["transaction_cost"].sum())
    return {"config": {"top_n": cfg.top_n, "momentum_months": cfg.momentum_months,
                       "volatility_months": cfg.volatility_months,
                       "transaction_cost_bps": cfg.transaction_cost_bps,
                       "annualization_periods": cfg.annualization_periods},
            "metrics": metrics, "periods": len(result),
            "start": result.index.min().date().isoformat(),
            "end": result.index.max().date().isoformat(), "monthly": result}
