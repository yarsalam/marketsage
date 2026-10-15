import pandas as pd
import numpy as np
from datetime import datetime
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# ۱. داده مصنوعی چندرژیمه (همانند قبل)
# ============================================================
np.random.seed(42)
dates = pd.date_range(start='2015-01-01', end=datetime.today().strftime('%Y-%m-%d'), freq='D')
n = len(dates)

assets = ['BTC', 'ETH', 'SOL', 'GLD', 'SPY', 'QQQ', 'TLT', 'UUP', 'USO', 'XLF']
trend_params = {'BTC':0.0006, 'ETH':0.0005, 'SOL':0.0008, 'GLD':0.0002,
                'SPY':0.00025, 'QQQ':0.00035, 'TLT':0.00005, 'UUP':0.0001,
                'USO':0.0003, 'XLF':0.0002}
vol_params = {'BTC':0.028, 'ETH':0.033, 'SOL':0.05, 'GLD':0.011,
              'SPY':0.014, 'QQQ':0.016, 'TLT':0.004, 'UUP':0.007,
              'USO':0.024, 'XLF':0.015}

regimes = ['bull', 'bear', 'sideways', 'volatile', 'crypto_boom'] * (n//5 + 1)
regimes = regimes[:n]

prices = pd.DataFrame(index=dates)
for asset in assets:
    trend = trend_params[asset]
    vol = vol_params[asset]
    mult = np.where(np.array(regimes)=='bear', -1.0,
             np.where(np.array(regimes)=='crypto_boom', 2.0 if asset in ['BTC','ETH','SOL'] else 1.0,
             np.where(np.array(regimes)=='volatile', 1.5, 1.0)))
    drift = trend * mult
    vol_adj = vol * np.where(np.array(regimes)=='volatile', 1.8, 1.0)
    prices[asset] = 100 * np.exp((drift + np.random.randn(n) * vol_adj).cumsum())

macro = pd.DataFrame(index=dates)
macro['VIX'] = np.where(np.array(regimes)=='volatile', 30 + np.random.rand(n)*10,
                 np.where(np.array(regimes)=='bear', 25 + np.random.rand(n)*5, 15 + np.random.rand(n)*5))
macro['US10Y'] = 2.5 + np.random.randn(n).cumsum() * 0.02
macro['DXY'] = 95 + np.where(np.array(regimes)=='bear', 5, 0) + np.random.randn(n).cumsum() * 0.3

print("✅ داده مصنوعی چندرژیمه ساخته شد.")

def to_monthly(df):
    return df.resample('ME').last().ffill()

# ============================================================
# ۲. Momentum Baseline (بدون تغییر)
# ============================================================
def momentum_backtest(prices, top_n=5, tc=0.005, lookback=4):
    mp = to_monthly(prices)
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp, mr = mp.loc[idx], mr.loc[idx]
    min_start = lookback + 6
    if len(mp) <= min_start:
        return 1_000_000_000
    capital = 1_000_000_000
    for t in range(min_start, len(mp)-1):
        p = mp.iloc[:t+1].iloc[-lookback:]
        r = mr.iloc[:t+1].iloc[-lookback:]
        mom = p.iloc[-1] / p.iloc[0] - 1
        sharpe = r.mean() / (r.std().replace(0, np.nan) + 1e-10)
        inv_vol = 1 / (r.std().replace(0, np.nan) + 1e-10)
        def minmax(s):
            return (s - s.min()) / (s.max() - s.min() + 1e-10)
        scores = minmax(mom)*0.4 + minmax(sharpe)*0.3 + minmax(inv_vol)*0.3
        top_assets = scores.nlargest(top_n).index.tolist()
        port_ret = mr.iloc[t+1][top_assets].mean() - tc
        capital *= (1 + port_ret)
    return capital

# ============================================================
# ۳. Probability Engine (رفع مشکل – یک مدل برای هر دارایی)
# ============================================================
def probability_backtest(prices, macro, top_n=5, tc=0.005, lookback=4):
    mp = to_monthly(prices)
    mr = mp.pct_change().dropna()
    mm = to_monthly(macro)
    idx = mp.index.intersection(mr.index).intersection(mm.index)
    mp, mr, mm = mp.loc[idx], mr.loc[idx], mm.loc[idx]

    # ساخت ویژگی‌های پایه
    feat_base = pd.DataFrame(index=mp.index)
    for asset in mp.columns:
        feat_base[f'{asset}_mom1'] = mp[asset].pct_change(1)
        feat_base[f'{asset}_mom3'] = mp[asset].pct_change(3)
        feat_base[f'{asset}_mom6'] = mp[asset].pct_change(6)
        feat_base[f'{asset}_vol3'] = mr[asset].rolling(3).std()
    feat_base['VIX'] = mm['VIX']
    feat_base['DXY'] = mm['DXY']
    feat_base['US10Y'] = mm['US10Y']

    # هدف: Outperform برای هر دارایی (بازده > میانگین)
    avg_ret = mr.mean(axis=1)
    target = (mr.sub(avg_ret, axis=0) > 0).astype(int)

    min_start = max(lookback, 12)
    if len(feat_base) <= min_start:
        return None

    # آموزش یک مدل برای هر دارایی
    models = {}
    for asset in mp.columns:
        X = feat_base.dropna()
        y = target[asset].loc[X.index]
        if y.nunique() < 2:
            continue
        model = XGBClassifier(max_depth=3, n_estimators=100, random_state=0, verbosity=0)
        model.fit(X, y)
        models[asset] = model

    capital = 1_000_000_000
    for t in range(min_start, len(feat_base)-1):
        X_curr = feat_base.iloc[t:t+1]
        probs = {}
        for asset, model in models.items():
            try:
                prob = model.predict_proba(X_curr)[0, 1]
            except:
                prob = 0.5
            probs[asset] = prob
        prob_series = pd.Series(probs)
        top_assets = prob_series.nlargest(top_n).index.tolist()
        port_ret = mr.iloc[t+1][top_assets].mean() - tc
        capital *= (1 + port_ret)
    return capital

# ============================================================
# ۴. اجرای مقایسه
# ============================================================
capital_mom = momentum_backtest(prices)
capital_prob = probability_backtest(prices, macro)

print("\n📊 نتایج مقایسه در محیط کنترل‌شده:")
print(f"Momentum Baseline: Return={((capital_mom/1e9)-1)*100:.0f}%")
if capital_prob:
    print(f"Probability Engine (per-asset XGBoost): Return={((capital_prob/1e9)-1)*100:.0f}%")
    if capital_prob > capital_mom:
        print("✅ Probability Engine برتری دارد!")
    else:
        print("❌ Probability Engine نتوانست برتری ایجاد کند.")
else:
    print("❌ Probability Engine خطا داد.")
