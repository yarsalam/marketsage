"""Research-only MarketSage API using global-market proxies, not Iran-market feeds."""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timezone
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("marketsage.analysis")
app = FastAPI(title="MarketSage Analysis API", version="0.2.0")

TICKERS = {
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "SOL-USD": "Solana",
    "GLD": "Gold ETF (US proxy)", "SPY": "S&P 500 ETF (US proxy)",
    "QQQ": "Nasdaq ETF (US proxy)", "TLT": "US Treasury ETF (US proxy)",
    "UUP": "US Dollar ETF (US proxy)", "USO": "Oil ETF (US proxy)",
    "XLF": "US Financials ETF", "XLE": "US Energy ETF",
}
CACHE_TTL = max(60, int(os.getenv("PRICE_CACHE_TTL_SECONDS", "900")))
_cache_lock = threading.Lock()
_cache_frame: pd.DataFrame | None = None
_cache_time = 0.0


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


def download_prices() -> pd.DataFrame:
    end = (pd.Timestamp.now(tz="UTC").normalize().tz_localize(None) + pd.Timedelta(days=1))
    data = yf.download(
        list(TICKERS), start="2015-01-01", end=end.strftime("%Y-%m-%d"),
        auto_adjust=True, progress=False, threads=False, group_by="column",
    )
    if data is None or data.empty:
        raise RuntimeError("Market-data provider returned no prices")
    if isinstance(data.columns, pd.MultiIndex):
        if "Close" not in data.columns.get_level_values(0):
            raise RuntimeError("Price response has no Close field")
        prices = data["Close"].copy()
    elif "Close" in data.columns:
        prices = data[["Close"]].rename(columns={"Close": next(iter(TICKERS))})
    else:
        prices = data.copy()
    prices = prices.sort_index().loc[:, ~prices.columns.duplicated()]
    prices = prices.replace([np.inf, -np.inf], np.nan).ffill().dropna(axis=1, how="all")
    prices = prices.dropna(how="all")
    if prices.empty or len(prices) < 260:
        raise RuntimeError("Not enough usable price history")
    return prices


def get_prices() -> pd.DataFrame:
    global _cache_frame, _cache_time
    with _cache_lock:
        if _cache_frame is not None and time.monotonic() - _cache_time < CACHE_TTL:
            return _cache_frame.copy()
    try:
        frame = download_prices()
    except Exception as exc:
        logger.exception("Market data refresh failed")
        with _cache_lock:
            if _cache_frame is not None and not _cache_frame.empty:
                logger.warning("Returning stale cached prices")
                return _cache_frame.copy()
        raise HTTPException(status_code=503, detail="Market data unavailable; no decision generated.") from exc
    with _cache_lock:
        _cache_frame, _cache_time = frame, time.monotonic()
    return frame.copy()


def calculate_scores(monthly_prices: pd.DataFrame) -> pd.Series:
    if len(monthly_prices) < 7:
        raise HTTPException(status_code=503, detail="Insufficient monthly history")
    returns = monthly_prices.pct_change(fill_method=None)
    momentum = monthly_prices.iloc[-1].div(monthly_prices.iloc[-4]).sub(1)
    trailing = returns.iloc[-12:]
    volatility = trailing.std().replace(0, np.nan)
    sharpe_like = trailing.mean().div(volatility)

    def scale(values: pd.Series) -> pd.Series:
        values = values.replace([np.inf, -np.inf], np.nan)
        low, high = values.min(skipna=True), values.max(skipna=True)
        if pd.isna(low) or pd.isna(high) or np.isclose(low, high):
            return pd.Series(0.5, index=values.index, dtype=float)
        return (values - low) / (high - low)

    return (
        0.50 * scale(momentum) + 0.25 * scale(sharpe_like)
        + 0.25 * (1 - scale(volatility))
    ).replace([np.inf, -np.inf], np.nan).dropna().sort_values(ascending=False)


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


@app.get("/decision", response_model=DecisionResponse)
def get_decision(
    horizon: Literal["1W", "1M", "3M", "6M"] = Query("1M"),
    capital: float = Query(500_000_000, ge=0, le=1e15),
    top_n: int = Query(5, ge=1, le=10),
) -> DecisionResponse:
    prices = get_prices()
    monthly = prices.resample("ME").last().ffill().dropna(axis=1, how="all")
    scores = calculate_scores(monthly)
    selected = scores.head(min(top_n, len(scores))).index.tolist()
    if not selected:
        raise HTTPException(status_code=503, detail="No assets have sufficient valid history")
    returns = monthly[selected].pct_change(fill_method=None).dropna(how="all").tail(12)
    vol = float(returns.mean(axis=1).std(ddof=1) * np.sqrt(12)) if len(returns) > 1 else float("nan")
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
    return DecisionResponse(
        horizon=horizon, market_scope="global_proxy",
        source="Yahoo Finance via yfinance",
        data_as_of=pd.Timestamp(prices.index.max()).date().isoformat(),
        generated_at=datetime.now(timezone.utc).isoformat(),
        allocation=allocations, capital=capital, confidence=None,
        confidence_status="not_calibrated", risk_level=risk,
        annualized_volatility=round(annualized_vol, 6) if annualized_vol is not None else None,
        total_assets_analyzed=len(scores),
        warnings=[
            "Research ranking only; it is not a validated return forecast or personalized financial advice.",
            "Confidence is unavailable until probabilities are calibrated out-of-sample.",
            "The current universe uses global proxies and crypto, not direct Iranian market instruments.",
            "Equal weights do not guarantee minimum risk; fees, slippage, taxes, liquidity and FX conversion are not modeled.",
            "The horizon is recorded for the client; ranking still uses trailing monthly observations and is not horizon-specific.",
        ],
    )


@app.get("/scores")
def get_scores() -> dict:
    prices = get_prices()
    scores = calculate_scores(prices.resample("ME").last().ffill())
    return {
        "data_as_of": pd.Timestamp(prices.index.max()).date().isoformat(),
        "scores": {TICKERS.get(t, t): round(float(v), 4) for t, v in scores.items()},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
