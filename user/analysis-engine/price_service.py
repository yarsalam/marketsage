# analysis-engine/price_service.py
from fastapi import FastAPI, Query
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="MarketSage Decision Engine")

TICKERS = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials', 'XLE': 'Energy'
}

def get_prices():
    data = yf.download(list(TICKERS.keys()), start='2015-01-01',
                       end=datetime.today().strftime('%Y-%m-%d'),
                       auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data = data['Close'].copy()
    return data.ffill().bfill()

def calculate_scores(prices, returns, lookback=4):
    p = prices.iloc[-lookback:]
    r = returns.iloc[-lookback:]
    momentum = p.iloc[-1] / p.iloc[0] - 1
    sharpe = r.mean() / (r.std().replace(0, np.nan) + 1e-10)
    inv_vol = 1 / (r.std().replace(0, np.nan) + 1e-10)
    def minmax(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-10)
    return minmax(momentum)*0.4 + minmax(sharpe)*0.3 + minmax(inv_vol)*0.3

@app.get("/decision")
def get_decision(horizon: str = Query("1M", description="1W, 1M, 3M, 6M"), capital: float = 500_000_000):
    prices = get_prices()
    if horizon == "1W":
        prices = prices.resample('W-FRI').last().ffill()
    elif horizon == "3M":
        prices = prices.resample('QE').last().ffill()
    elif horizon == "6M":
        prices = prices.resample('2QE').last().ffill()

    mp = prices.resample('ME').last().ffill()
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp, mr = mp.loc[idx], mr.loc[idx]

    scores = calculate_scores(mp, mr, lookback=4)
    top5 = scores.nlargest(5)
    vols = mr[top5.index].std()
    max_vol = 0.15
    valid_assets = [a for a in top5.index if vols[a] < max_vol] or top5.index.tolist()
    weights = {asset: 1/len(valid_assets) for asset in valid_assets}

    port_ret = mr[valid_assets].mean(axis=1).iloc[-12:]
    sharpe = port_ret.mean() / (port_ret.std() + 1e-10) * np.sqrt(12)
    confidence = min(95, max(50, int((sharpe / 1.5) * 100)))

    return {
        "horizon": horizon,
        "allocation": [{"asset": TICKERS[a], "weight": round(w, 3)} for a, w in weights.items()],
        "capital_allocated": {TICKERS[a]: int(capital * w) for a, w in weights.items()},
        "confidence": confidence
    }

@app.get("/scores")
def get_scores():
    prices = get_prices()
    mp = prices.resample('ME').last().ffill()
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp, mr = mp.loc[idx], mr.loc[idx]
    scores = calculate_scores(mp, mr, lookback=4)
    return {"scores": {TICKERS[k]: round(v, 3) for k, v in scores.items()}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)