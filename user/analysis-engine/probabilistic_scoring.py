# probabilistic_scoring.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import json
import warnings
warnings.filterwarnings('ignore')

TICKERS = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials', 'XLE': 'Energy'
}

# ۱. دانلود قیمت‌ها و شاخص‌های Macro
print("📥 دریافت داده‌ها...")
prices = yf.download(list(TICKERS.keys()), start='2015-01-01',
                     end=datetime.today().strftime('%Y-%m-%d'),
                     auto_adjust=True, progress=False)
if isinstance(prices.columns, pd.MultiIndex):
    prices = prices['Close'].copy()
prices = prices.ffill().bfill()

# شاخص‌های Macro
macro_data = yf.download(['^VIX', '^TNX', 'DX-Y.NYB'], start='2015-01-01',
                         end=datetime.today().strftime('%Y-%m-%d'),
                         progress=False)
if isinstance(macro_data.columns, pd.MultiIndex):
    macro_data = macro_data['Close'].copy()
macro_data.columns = ['VIX', 'US10Y', 'DXY']
macro_data = macro_data.ffill().bfill()

# ۲. ساخت دیتاست آموزشی (هدف: بازده ماه بعد > میانگین)
def create_dataset(prices, macro, lookback=4):
    monthly_prices = prices.resample('ME').last()
    monthly_returns = monthly_prices.pct_change().dropna()
    monthly_macro = macro.resample('ME').last()
    
    X, y = [], []
    dates = []
    for t in range(lookback + 1, len(monthly_returns)):
        # ویژگی‌های Momentum
        window_prices = monthly_prices.iloc[t-lookback:t+1]
        momentum = window_prices.iloc[-1] / window_prices.iloc[0] - 1  # سری برای هر دارایی
        
        # ویژگی‌های Macro
        macro_t = monthly_macro.iloc[t-1]  # ماه قبل
        vix = macro_t['VIX']
        dxy = macro_t['DXY']
        us10y = macro_t['US10Y']
        
        # برچسب: آیا بازده این ماه از میانگین همه دارایی‌ها بیشتر بوده؟
        returns_t = monthly_returns.iloc[t]
        avg_return = returns_t.mean()
        label = (returns_t > avg_return).astype(int)  # 1 اگر بهتر از میانگین
        
        # ذخیره برای هر دارایی
        for asset in monthly_prices.columns:
            features = [momentum[asset], vix, dxy, us10y,
                        monthly_returns[asset].rolling(3).std().iloc[t-1]]  # نوسان ۳ ماهه
            X.append(features)
            y.append(label[asset])
            dates.append(monthly_returns.index[t])
    
    return np.array(X), np.array(y), dates

X, y, _ = create_dataset(prices, macro_data)
print(f"✅ دیتاست ساخته شد: {X.shape[0]} نمونه")

# ۳. آموزش مدل Logistic Regression برای پیش‌بینی احتمال
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = LogisticRegression()
model.fit(X_scaled, y)

# ۴. تولید خروجی برای امروز (پیش‌بینی احتمالات)
today = datetime.today()
current_prices = prices.resample('ME').last().iloc[-4:]  # ۴ ماه اخیر
momentum = current_prices.iloc[-1] / current_prices.iloc[0] - 1
current_macro = macro_data.resample('ME').last().iloc[-1]
current_vol = prices.pct_change().resample('ME').std().iloc[-1]  # نوسان ماهانه

probs = {}
for asset in prices.columns:
    features = np.array([[momentum[asset], current_macro['VIX'], current_macro['DXY'],
                          current_macro['US10Y'], current_vol[asset]]])
    features_scaled = scaler.transform(features)
    prob = model.predict_proba(features_scaled)[0, 1]  # احتمال کلاس ۱ (Outperform)
    probs[asset] = round(float(prob), 4)

# ۵. Allocation: Risk Parity ساده بر اساس احتمالات
# هرچه احتمال بالاتر، وزن بیشتر؛ اما با نوسان معکوس تعدیل می‌شود
vols = current_vol.copy()
weights = {asset: probs[asset] / (vols[asset] + 1e-10) for asset in probs}
total = sum(weights.values())
weights = {k: v/total for k, v in weights.items()}

# انتخاب ۵ دارایی با بیشترین وزن نهایی
top5 = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:5]
allocation = {TICKERS.get(asset, asset): round(weight, 3) for asset, weight in top5}
confidence = max(probs.values()) * 100  # بالاترین احتمال به عنوان اطمینان

result = {
    "horizon": "1M",
    "probabilities": {TICKERS.get(k, k): p for k, p in probs.items()},
    "allocation": allocation,
    "confidence": round(confidence)
}

print(json.dumps(result, indent=2, ensure_ascii=False))