from fastapi import FastAPI, Query
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="MarketSage Decision Engine")

# ============================================================
# Universe (همان ۱۱ دارایی مقاوم)
# ============================================================
TICKERS = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials', 'XLE': 'Energy'
}

# ============================================================
# Scoring Engine (همان نسخه برنده: Monthly, Lookback=4, TC=0.5%)
# ============================================================
def calculate_scores(prices: pd.DataFrame, returns: pd.DataFrame, lookback=4):
    p = prices.iloc[-lookback:]
    r = returns.iloc[-lookback:]
    momentum = p.iloc[-1] / p.iloc[0] - 1
    sharpe = r.mean() / (r.std().replace(0, np.nan) + 1e-10)
    inv_vol = 1 / (r.std().replace(0, np.nan) + 1e-10)
    def minmax(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-10)
    return minmax(momentum)*0.4 + minmax(sharpe)*0.3 + minmax(inv_vol)*0.3

def get_top_assets(prices: pd.DataFrame, top_n=5):
    monthly_prices = prices.resample('ME').last().ffill()
    monthly_returns = monthly_prices.pct_change().dropna()
    common_idx = monthly_prices.index.intersection(monthly_returns.index)
    monthly_prices = monthly_prices.loc[common_idx]
    monthly_returns = monthly_returns.loc[common_idx]

    if len(monthly_prices) < 5:
        return None

    scores = calculate_scores(monthly_prices, monthly_returns, lookback=4)
    top_assets = scores.nlargest(top_n).index.tolist()
    return top_assets

# ============================================================
# Allocation ساده (Equal Weight با فیلتر نوسان بالا)
# ============================================================
def allocate_capital(prices: pd.DataFrame, top_assets: list, max_vol=0.15):
    monthly_prices = prices.resample('ME').last().ffill()
    monthly_returns = monthly_prices.pct_change().dropna()
    volatilities = monthly_returns[top_assets].std()

    # فیلتر دارایی‌های بسیار پرنوسان (مثلاً > 15% ماهانه)
    valid_assets = [a for a in top_assets if volatilities[a] < max_vol]
    if not valid_assets:
        valid_assets = top_assets  # در صورت نبود گزینه، همه را نگه دار

    weight = 1.0 / len(valid_assets)
    allocation = {ticker: weight for ticker in valid_assets}
    return allocation

# ============================================================
# Confidence Score (بر اساس Sharpe تاریخی استراتژی)
# ============================================================
def calculate_confidence(prices: pd.DataFrame, top_assets: list):
    # محاسبه شارپ ۱۲ ماه اخیر پرتفوی پیشنهادی
    monthly_prices = prices.resample('ME').last().ffill()
    monthly_returns = monthly_prices.pct_change().dropna()[-12:]
    if monthly_returns.empty:
        return 60
    port_ret = monthly_returns[top_assets].mean(axis=1)
    sharpe = port_ret.mean() / (port_ret.std() + 1e-10) * np.sqrt(12)
    confidence = min(95, max(50, int((sharpe / 1.5) * 100)))
    return confidence

# ============================================================
# مدل‌های خروجی
# ============================================================
class AllocationItem(BaseModel):
    asset: str
    weight: float

class DecisionResponse(BaseModel):
    horizon: str
    risk_level: str
    portfolio: list[AllocationItem]
    confidence: int

# ============================================================
# API Endpoint
# ============================================================
@app.get("/decision", response_model=DecisionResponse)
def get_decision(horizon: str = Query("1M", description="افق سرمایه‌گذاری: 1W, 1M, 3M, 6M")):
    # دانلود داده‌ها (در نسخه نهایی از دیتابیس داخلی خوانده شود)
    data = yf.download(list(TICKERS.keys()), start='2015-01-01',
                       end=datetime.today().strftime('%Y-%m-%d'),
                       auto_adjust=True, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        prices = data['Close'].copy()
    else:
        prices = data.copy()
    prices = prices.ffill().bfill()

    # انتخاب افق (تغییر فرکانس بر اساس horizon)
    if horizon == "1W":
        prices = prices.resample('W-FRI').last().ffill()
    elif horizon == "1M":
        prices = prices.resample('ME').last().ffill()
    elif horizon == "3M":
        prices = prices.resample('QE').last().ffill()
    elif horizon == "6M":
        prices = prices.resample('2QE').last().ffill()

    top_assets = get_top_assets(prices, top_n=5)
    if not top_assets:
        # Fallback: دارایی‌های امن
        top_assets = ['GLD', 'TLT', 'SPY', 'UUP']

    allocation = allocate_capital(prices, top_assets)
    confidence = calculate_confidence(prices, top_assets)

    # تعیین سطح ریسک بر اساس نوسان پرتفوی
    monthly_returns = prices.resample('ME').last().pct_change().dropna()
    port_vol = monthly_returns[list(allocation.keys())].mean(axis=1).std() * np.sqrt(12)
    if port_vol < 0.10:
        risk = "Low"
    elif port_vol < 0.20:
        risk = "Medium"
    else:
        risk = "High"

    portfolio = [AllocationItem(asset=TICKERS.get(k, k), weight=round(w, 3)) for k, w in allocation.items()]
    return DecisionResponse(
        horizon=horizon,
        risk_level=risk,
        portfolio=portfolio,
        confidence=confidence
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)