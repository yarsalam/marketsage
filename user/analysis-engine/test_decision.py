# test_decision.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

TICKERS = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials', 'XLE': 'Energy'
}

def calculate_scores(prices, returns, lookback=4):
    p = prices.iloc[-lookback:]
    r = returns.iloc[-lookback:]
    momentum = p.iloc[-1] / p.iloc[0] - 1
    sharpe = r.mean() / (r.std().replace(0, np.nan) + 1e-10)
    inv_vol = 1 / (r.std().replace(0, np.nan) + 1e-10)
    def minmax(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-10)
    return minmax(momentum)*0.4 + minmax(sharpe)*0.3 + minmax(inv_vol)*0.3

def get_top_assets(prices, top_n=5):
    mp = prices.resample('ME').last().ffill()
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp, mr = mp.loc[idx], mr.loc[idx]
    if len(mp) < 5:
        return None
    scores = calculate_scores(mp, mr, lookback=4)
    return scores.nlargest(top_n).index.tolist()

def allocate_capital(prices, top_assets, max_vol=0.15):
    mp = prices.resample('ME').last().ffill()
    mr = mp.pct_change().dropna()
    vols = mr[top_assets].std()
    valid = [a for a in top_assets if vols[a] < max_vol]
    if not valid:
        valid = top_assets
    weight = 1.0 / len(valid)
    return {a: weight for a in valid}

def calculate_confidence(prices, top_assets):
    mp = prices.resample('ME').last().ffill()
    mr = mp.pct_change().dropna()[-12:]
    if mr.empty:
        return 60
    port_ret = mr[top_assets].mean(axis=1)
    sharpe = port_ret.mean() / (port_ret.std() + 1e-10) * np.sqrt(12)
    return min(95, max(50, int((sharpe / 1.5) * 100)))

# دریافت داده
data = yf.download(list(TICKERS.keys()), start='2015-01-01',
                   end=datetime.today().strftime('%Y-%m-%d'),
                   auto_adjust=True, progress=False)
if isinstance(data.columns, pd.MultiIndex):
    prices = data['Close'].copy()
else:
    prices = data.copy()
prices = prices.ffill().bfill()

horizon = '1M'  # می‌توانید دستی تغییر دهید
if horizon == '1W':
    prices = prices.resample('W-FRI').last().ffill()
elif horizon == '3M':
    prices = prices.resample('QE').last().ffill()
elif horizon == '6M':
    prices = prices.resample('2QE').last().ffill()
# برای 1M از داده روزانه اصلی استفاده می‌کنیم که در get_top_assets مجدداً ماهانه می‌شود

top_assets = get_top_assets(prices, top_n=5)
if not top_assets:
    top_assets = ['GLD', 'TLT', 'SPY', 'UUP']

allocation = allocate_capital(prices, top_assets)
confidence = calculate_confidence(prices, top_assets)

# سطح ریسک
mp = prices.resample('ME').last().ffill()
mr = mp.pct_change().dropna()
port_vol = mr[list(allocation.keys())].mean(axis=1).std() * np.sqrt(12)
risk = "Low" if port_vol < 0.10 else "Medium" if port_vol < 0.20 else "High"

result = {
    "horizon": horizon,
    "risk_level": risk,
    "portfolio": [{"asset": TICKERS.get(k, k), "weight": round(w, 3)} for k, w in allocation.items()],
    "confidence": confidence
}

print(json.dumps(result, indent=2, ensure_ascii=False))