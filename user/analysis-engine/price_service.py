"""Research-only MarketSage API using global proxies, not Iran-market feeds."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf
from research.backtest import BacktestConfig, run_monthly_momentum_backtest, summarize_returns
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("marketsage.analysis")
app = FastAPI(title="MarketSage Analysis API", version="0.3.0")

TICKERS = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
    "GLD": "Gold ETF (US proxy)", "SPY": "S&P 500 ETF (US proxy)",
    "QQQ": "Nasdaq ETF (US proxy)", "TLT": "US Treasury ETF (US proxy)",
    "UUP": "US Dollar ETF (US proxy)", "USO": "Oil ETF (US proxy)",
    "XLF": "US Financials ETF", "XLE": "US Energy ETF",
}
CACHE_TTL = max(60, int(os.getenv("PRICE_CACHE_TTL_SECONDS", "900")))
DATA_SNAPSHOT_DIR = Path(os.getenv("DATA_SNAPSHOT_DIR", "/data/snapshots"))
_cache_lock = threading.Lock()
_cache_frame: pd.DataFrame | None = None
_cache_time = 0.0
_cache_metadata: dict = {"loaded": False, "stale": False}


class AllocationItem(BaseModel):
    asset: str
    ticker: str
    weight: float = Field(ge=0, le=1)
    capital_allocated: float = Field(ge=0)


class DecisionResponse(BaseModel):
    horizon: str
    market_scope: str
    source: str
    data_as_of: str
    generated_at: str
    allocation: list[AllocationItem]
    capital: float
    confidence: None = None
    confidence_status: str = "not_calibrated"
    risk_level: str
    annualized_volatility: float | None
    total_assets_analyzed: int
    warnings: list[str]


def _extract_close(data: pd.DataFrame) -> pd.DataFrame:
    """Extract adjusted close values without guessing or filling missing observations."""
    if data is None or data.empty:
        raise RuntimeError("Market-data provider returned no prices")
    if isinstance(data.columns, pd.MultiIndex):
        close_level = next(
            (level for level in range(data.columns.nlevels)
             if "Close" in data.columns.get_level_values(level)),
            None,
        )
        if close_level is None:
            raise RuntimeError("Price response has no Close field")
        prices = data.xs("Close", axis=1, level=close_level, drop_level=True).copy()
        if isinstance(prices.columns, pd.MultiIndex):
            raise RuntimeError("Unexpected multi-level ticker columns in price response")
    elif len(TICKERS) == 1 and "Close" in data.columns:
        prices = data[["Close"]].rename(columns={"Close": next(iter(TICKERS))})
    else:
        raise RuntimeError("Unexpected price response format; expected ticker/Close columns")

    prices = prices.sort_index()
    prices.index = pd.to_datetime(prices.index, utc=True).tz_convert(None)
    if prices.index.has_duplicates:
        raise RuntimeError("Market-data provider returned duplicate observations")
    prices = prices.loc[:, ~prices.columns.duplicated()]
    # Keep the complete expected universe. Missing observations remain missing and
    # make the affected asset ineligible; never forward-fill provider gaps.
    prices = prices.reindex(columns=list(TICKERS))
    prices = prices.apply(pd.to_numeric, errors="coerce").astype(float)
    prices = prices.replace([np.inf, -np.inf], np.nan)
    prices = prices.mask(prices <= 0)
    if len(prices.dropna(how="all")) < 260:
        raise RuntimeError("Not enough usable price history")
    if prices.dropna(how="all").empty:
        raise RuntimeError("No usable prices after data-quality checks")
    return prices


def write_daily_snapshot(prices: pd.DataFrame, retrieved_at: datetime,
                         directory: Path | None = None) -> dict:
    """Persist the first successful provider snapshot per UTC day, atomically."""
    target = directory or DATA_SNAPSHOT_DIR
    target.mkdir(parents=True, exist_ok=True)
    day = retrieved_at.astimezone(timezone.utc).date().isoformat()
    csv_path = target / f"prices-{day}.csv"
    meta_path = target / f"prices-{day}.json"
    if csv_path.exists() and meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    csv_bytes = prices.to_csv(index_label="date", date_format="%Y-%m-%dT%H:%M:%S").encode("utf-8")
    metadata = {
        "source": "Yahoo Finance via yfinance",
        "retrieved_at": retrieved_at.astimezone(timezone.utc).isoformat(),
        "data_as_of": pd.Timestamp(prices.dropna(how="all").index.max()).isoformat(),
        "symbols": list(prices.columns),
        "rows": int(len(prices)),
        "sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "adjustment_policy": "yfinance auto_adjust=True; Close field",
        "snapshot_policy": "first successful fetch per UTC date; immutable once written",
    }
    csv_tmp, meta_tmp = csv_path.with_suffix(".csv.tmp"), meta_path.with_suffix(".json.tmp")
    csv_tmp.write_bytes(csv_bytes)
    meta_tmp.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    os.replace(csv_tmp, csv_path)
    os.replace(meta_tmp, meta_path)
    return metadata


def download_prices() -> pd.DataFrame:
    end = (pd.Timestamp.now(tz="UTC").normalize().tz_localize(None) + pd.Timedelta(days=1))
    data = yf.download(
        list(TICKERS), start="2015-01-01", end=end.strftime("%Y-%m-%d"),
        auto_adjust=True, progress=False, threads=False, group_by="column",
    )
    return _extract_close(data)


def get_prices() -> pd.DataFrame:
    global _cache_frame, _cache_time, _cache_metadata
    with _cache_lock:
        if _cache_frame is not None and time.monotonic() - _cache_time < CACHE_TTL:
            return _cache_frame.copy()
    try:
        frame = download_prices()
    except Exception as exc:
        logger.exception("Market data refresh failed")
        with _cache_lock:
            if _cache_frame is not None and not _cache_frame.empty:
                _cache_metadata = {**_cache_metadata, "stale": True, "last_refresh_error": type(exc).__name__}
                logger.warning("Returning stale cached prices after refresh failure")
                return _cache_frame.copy()
        raise HTTPException(status_code=503, detail="Market data unavailable; no decision generated.") from exc

    retrieved_at = datetime.now(timezone.utc)
    snapshot = None
    try:
        snapshot = write_daily_snapshot(frame, retrieved_at)
    except OSError:
        logger.exception("Unable to persist daily market-data snapshot")
    with _cache_lock:
        _cache_frame, _cache_time = frame, time.monotonic()
        _cache_metadata = {
            "loaded": True, "stale": False, "source": "Yahoo Finance via yfinance",
            "retrieved_at": retrieved_at.isoformat(),
            "data_as_of": pd.Timestamp(frame.dropna(how="all").index.max()).date().isoformat(),
            "row_count": int(len(frame)),
            "available_symbols": [symbol for symbol in frame if frame[symbol].notna().any()],
            "snapshot_sha256": snapshot.get("sha256") if snapshot else None,
            "snapshot_policy": "first successful fetch per UTC date",
        }
    return frame.copy()


def completed_monthly_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Return completed months, rejecting stale month-end observations without filling."""
    monthly = prices.resample("ME").last()
    if monthly.empty:
        return monthly
    for column in prices.columns:
        valid = prices[column].dropna()
        observed_by_month = pd.Series(
            valid.index, index=valid.index.to_period("M")
        ).groupby(level=0).last()
        max_age_days = 3 if column.endswith("-USD") else 7
        for month_end in monthly.index:
            observed_at = observed_by_month.get(month_end.to_period("M"))
            if observed_at is None or pd.isna(observed_at):
                monthly.loc[month_end, column] = np.nan
            elif (month_end - observed_at).days > max_age_days:
                monthly.loc[month_end, column] = np.nan
    current_month = pd.Timestamp.now(tz="UTC").tz_localize(None).to_period("M")
    return monthly.loc[monthly.index.to_period("M") < current_month]


def calculate_scores(monthly_prices: pd.DataFrame) -> pd.Series:
    if len(monthly_prices) < 13:
        raise HTTPException(status_code=503, detail="At least 13 completed monthly observations are required")
    # Require 13 contiguous monthly closes per asset for 12 complete returns.
    eligible = monthly_prices.iloc[-13:].notna().all(axis=0)
    clean = monthly_prices.loc[:, eligible]
    if clean.empty:
        raise HTTPException(status_code=503, detail="No assets have 13 complete recent monthly observations")
    returns = clean.pct_change(fill_method=None).iloc[-12:]
    momentum = clean.iloc[-1].div(clean.iloc[-4]).sub(1)
    volatility = returns.std(ddof=1)
    mean_return = returns.mean()
    # A zero-volatility series has undefined Sharpe; assign neutral 0 for ranking,
    # rather than dropping an otherwise complete asset or calling it risk-free.
    sharpe_like = mean_return.div(volatility.replace(0, np.nan)).fillna(0.0)

    def scale(values: pd.Series) -> pd.Series:
        values = values.replace([np.inf, -np.inf], np.nan)
        low, high = values.min(skipna=True), values.max(skipna=True)
        if pd.isna(low) or pd.isna(high) or np.isclose(low, high):
            return pd.Series(0.5, index=values.index, dtype=float)
        return (values - low) / (high - low)

    return (0.50 * scale(momentum) + 0.25 * scale(sharpe_like)
            + 0.25 * (1 - scale(volatility))).replace([np.inf, -np.inf], np.nan).dropna().sort_values(ascending=False)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "analysis-engine"}


@app.get("/ready")
def ready() -> dict:
    return {"status": "ready", "service": "analysis-engine"}


@app.get("/markets")
def markets() -> dict:
    return {
        "market_scope": "global_proxy",
        "source": "Yahoo Finance via yfinance",
        "assets": [{"ticker": t, "name": n} for t, n in TICKERS.items()],
        "limitations": ["No direct Tehran Stock Exchange, Iranian gold/coin, or Iranian FX feed is configured."],
    }


@app.get("/data-status")
def data_status() -> dict:
    with _cache_lock:
        return dict(_cache_metadata)


@app.get("/decision", response_model=DecisionResponse)
def get_decision(
    horizon: Literal["1W", "1M", "3M", "6M"] = Query("1M"),
    capital: float = Query(500_000_000, ge=0, le=1e15),
    top_n: int = Query(5, ge=1, le=10),
) -> DecisionResponse:
    prices = get_prices()
    monthly = completed_monthly_prices(prices)
    scores = calculate_scores(monthly)
    selected = scores.head(min(top_n, len(scores))).index.tolist()
    if not selected:
        raise HTTPException(status_code=503, detail="No assets have sufficient valid history")
    returns = monthly[selected].pct_change(fill_method=None).iloc[-12:]
    portfolio_returns = returns.mean(axis=1, skipna=False).dropna()
    vol = float(portfolio_returns.std(ddof=1) * np.sqrt(12)) if len(portfolio_returns) > 1 else float("nan")
    annualized_vol = vol if np.isfinite(vol) else None
    weight = 1 / len(selected)
    allocations = [
        AllocationItem(asset=TICKERS.get(t, t), ticker=t, weight=weight,
                       capital_allocated=round(capital * weight, 2))
        for t in selected
    ]
    risk = ("unknown" if annualized_vol is None else
            "lower_observed_volatility" if annualized_vol < .10 else
            "moderate_observed_volatility" if annualized_vol < .20 else
            "higher_observed_volatility")
    with _cache_lock:
        metadata = dict(_cache_metadata)
    warnings = [
        "Research ranking only; it is not a validated return forecast or personalized financial advice.",
        "Confidence is unavailable until probabilities are calibrated out-of-sample.",
        "The current universe uses global proxies and crypto, not direct Iranian market instruments.",
        "Equal weights do not guarantee minimum risk; fees, slippage, taxes, liquidity and FX conversion are not modeled.",
        "The horizon is recorded for the client; ranking still uses trailing monthly observations and is not horizon-specific.",
    ]
    if metadata.get("stale"):
        warnings.append("WARNING: provider refresh failed; cached data may be stale.")
    return DecisionResponse(
        horizon=horizon, market_scope="global_proxy", source="Yahoo Finance via yfinance",
        data_as_of=pd.Timestamp(prices.dropna(how="all").index.max()).date().isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(), allocation=allocations,
        capital=capital, confidence=None, confidence_status="not_calibrated", risk_level=risk,
        annualized_volatility=round(annualized_vol, 6) if annualized_vol is not None else None,
        total_assets_analyzed=len(scores), warnings=warnings,
    )


@app.get("/backtest")
def get_backtest(
    top_n: int = Query(3, ge=1, le=10),
    transaction_cost_bps: float = Query(10.0, ge=0, le=1000),
) -> dict:
    prices = get_prices()
    monthly = completed_monthly_prices(prices)
    present = [column for column in monthly if monthly[column].notna().any()]
    if not present:
        raise HTTPException(status_code=503, detail="No monthly market prices are available")
    first_dates = [monthly[column].first_valid_index() for column in present]
    common_start = max(date for date in first_dates if date is not None)
    common = monthly.loc[monthly.index >= common_start, present]
    complete = [column for column in common if common[column].notna().all()]
    common = common[complete]
    if len(common) < 36 or common.shape[1] < 2:
        raise HTTPException(status_code=503, detail="At least 36 complete common monthly observations and two assets are required")
    config = BacktestConfig(
        top_n=min(top_n, common.shape[1]),
        momentum_months=3,
        volatility_months=12,
        transaction_cost_bps=transaction_cost_bps,
    )
    try:
        result = run_monthly_momentum_backtest(common, config)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=f"Backtest data-quality gate failed: {exc}") from exc

    strategy_returns = result["monthly"]["net_return"]
    asset_returns = common.pct_change(fill_method=None).loc[strategy_returns.index]
    benchmark_returns = {"equal_weight_monthly_rebalanced": asset_returns.mean(axis=1)}
    if "SPY" in asset_returns:
        benchmark_returns["SPY_buy_and_hold"] = asset_returns["SPY"]
    if "SPY" in asset_returns and "GLD" in asset_returns:
        benchmark_returns["60_40_SPY_GLD_monthly_rebalanced"] = (
            0.6 * asset_returns["SPY"] + 0.4 * asset_returns["GLD"]
        )
    benchmarks = {
        name: summarize_returns(returns, 12)
        for name, returns in benchmark_returns.items()
    }
    metrics = dict(result["metrics"])
    metrics["historical_var_95_monthly"] = float(max(0.0, -strategy_returns.quantile(0.05)))
    if "SPY" in asset_returns:
        benchmark = asset_returns["SPY"]
        variance = float(benchmark.var(ddof=1))
        metrics["beta_vs_spy"] = (
            float(strategy_returns.cov(benchmark) / variance)
            if variance > 0 else None
        )
    else:
        metrics["beta_vs_spy"] = None

    # Chronological untouched holdout: the strategy has fixed parameters and no
    # parameter search. All signals remain strictly trailing, including during
    # the holdout, but the displayed holdout metrics are separated from full history.
    split_index = max(1, int(len(common) * 0.70))
    holdout_start = common.index[split_index]
    holdout_returns = strategy_returns.loc[strategy_returns.index >= holdout_start]
    if len(holdout_returns) < 12:
        raise HTTPException(status_code=503, detail="Not enough out-of-sample monthly returns after chronological split")
    holdout_benchmarks = {
        name: summarize_returns(returns.loc[returns.index >= holdout_start], 12)
        for name, returns in benchmark_returns.items()
    }
    holdout_metrics = summarize_returns(holdout_returns, 12)
    holdout_metrics["historical_var_95_monthly"] = float(max(0.0, -holdout_returns.quantile(0.05)))
    if "SPY" in asset_returns:
        holdout_spy = asset_returns.loc[holdout_returns.index, "SPY"]
        variance = float(holdout_spy.var(ddof=1))
        holdout_metrics["beta_vs_spy"] = (
            float(holdout_returns.cov(holdout_spy) / variance) if variance > 0 else None
        )
    else:
        holdout_metrics["beta_vs_spy"] = None
    holdout = {
        "method": "chronological 70/30 split; fixed strategy parameters; no hyperparameter search",
        "start": holdout_returns.index.min().date().isoformat(),
        "end": holdout_returns.index.max().date().isoformat(),
        "periods": len(holdout_returns),
        "metrics": holdout_metrics,
        "benchmarks": holdout_benchmarks,
    }
    recent = result["monthly"].tail(36)
    monthly_rows = []
    for date, row in recent.iterrows():
        item = {
            "date": date.date().isoformat(),
            "gross_return": float(row["gross_return"]),
            "net_return": float(row["net_return"]),
            "equity": float(row["equity"]),
            "drawdown": float(row["drawdown"]),
            "turnover": float(row["turnover"]),
            "transaction_cost": float(row["transaction_cost"]),
            "selected_assets": row["selected_assets"],
        }
        for name, returns in benchmark_returns.items():
            item[name + "_return"] = float(returns.loc[date])
        monthly_rows.append(item)
    with _cache_lock:
        metadata = dict(_cache_metadata)
    return {
        "market_scope": "global_proxy",
        "source": "Yahoo Finance via yfinance",
        "data_as_of": metadata.get("data_as_of"),
        "start": result["start"],
        "end": result["end"],
        "periods": result["periods"],
        "config": result["config"],
        "metrics": metrics,
        "benchmarks": benchmarks,
        "holdout": holdout,
        "monthly": monthly_rows,
        "confidence_status": "not_calibrated",
        "warnings": [
            "Research-only historical simulation; not a forecast or personalized advice.",
            "Assets are restricted to those with complete monthly observations over the common test window.",
            "Equal-weight and 60/40 benchmarks are monthly rebalanced and exclude transaction costs; SPY buy-and-hold is not rebalanced.",
            "Transaction costs are sensitivity assumptions, not calibrated broker fees or market impact.",
            "Taxes, liquidity, slippage, FX conversion, survivorship/delistings, and execution are not modeled.",
            "No parameter tuning or untouched holdout test has been performed.",
        ] + (["Provider refresh failed; cached prices may be stale."] if metadata.get("stale") else []),
    }


@app.get("/scores")
def get_scores() -> dict:
    prices = get_prices()
    scores = calculate_scores(completed_monthly_prices(prices))
    with _cache_lock:
        metadata = dict(_cache_metadata)
    return {
        "market_scope": "global_proxy", "source": "Yahoo Finance via yfinance",
        "signal_as_of": pd.Timestamp(completed_monthly_prices(prices).index.max()).date().isoformat(),
        "provider_data_as_of": metadata.get("data_as_of"),
        "scores": {TICKERS.get(t, t): round(float(v), 4) for t, v in scores.items()},
        "stale": bool(metadata.get("stale")),
        "confidence_status": "not_calibrated",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
