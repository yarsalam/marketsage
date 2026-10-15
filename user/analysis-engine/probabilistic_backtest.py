import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Universe (حذف نمادهای مشکل‌دار)
# ============================================================
tickers = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials'
    # XLE حذف شد چون yfinance دیگر پشتیبانی نمی‌کند
}

# ============================================================
# ۱. داده‌های قیمت و Macro (با تاب‌آوری)
# ============================================================
def get_data():
    prices = yf.download(list(tickers.keys()), start='2015-01-01',
                         end=datetime.today().strftime('%Y-%m-%d'),
                         auto_adjust=True, progress=False)
    if isinstance(prices.columns, pd.MultiIndex):
        prices = prices['Close'].copy()
    prices = prices.ffill().bfill()
    # حذف ستون‌های کاملاً خالی
    prices = prices.dropna(axis=1, how='all')
    # به‌روزرسانی tickers بر اساس داده واقعی
    valid_tickers = {k: v for k, v in tickers.items() if k in prices.columns}
    
    macro = yf.download(['^VIX', '^TNX', 'DX-Y.NYB'], start='2015-01-01',
                        end=datetime.today().strftime('%Y-%m-%d'), progress=False)
    if isinstance(macro.columns, pd.MultiIndex):
        macro = macro['Close'].copy()
    macro.columns = ['VIX', 'US10Y', 'DXY']
    macro = macro.ffill().bfill()
    
    return prices, macro, valid_tickers

prices, macro, TICKERS = get_data()
print(f"✅ دارایی‌های معتبر: {list(TICKERS.values())}")

# ============================================================
# ۲. تابع ساخت ویژگی‌های غنی
# ============================================================
def create_features(prices, macro, lookback=4):
    mp = prices.resample('ME').last()
    mm = macro.resample('ME').last()
    mr = mp.pct_change().dropna()
    
    mom1 = mp.pct_change(1)
    mom3 = mp.pct_change(3)
    mom6 = mp.pct_change(6)
    vol1 = mr.rolling(1).std()
    vol3 = mr.rolling(3).std()
    
    vix = mm['VIX']
    dxy = mm['DXY']
    us10y = mm['US10Y']
    oil_trend = mp['USO'].pct_change(3) if 'USO' in mp.columns else pd.Series(0, index=mp.index)
    gold_trend = mp['GLD'].pct_change(3) if 'GLD' in mp.columns else pd.Series(0, index=mp.index)
    
    features = pd.DataFrame(index=mp.index)
    for asset in mp.columns:
        features[f'{asset}_mom1'] = mom1[asset]
        features[f'{asset}_mom3'] = mom3[asset]
        features[f'{asset}_mom6'] = mom6[asset]
        features[f'{asset}_vol1'] = vol1[asset]
        features[f'{asset}_vol3'] = vol3[asset]
    
    features['VIX'] = vix
    features['DXY'] = dxy
    features['US10Y'] = us10y
    features['oil_trend'] = oil_trend
    features['gold_trend'] = gold_trend
    
    target = (mr.shift(-1).sub(mr.shift(-1).mean(axis=1), axis=0) > 0).astype(int)
    return features.dropna(), target.dropna(), mp, mr

# ============================================================
# ۳. تابع Backtest با مدل احتمالاتی (XGBoost)
# ============================================================
def run_probabilistic_backtest(prices, macro, top_n=5, tc=0.005, lookback=4, freq='M'):
    if freq == 'W':
        rule = 'W-FRI'
        ann = 52
    else:
        rule = 'ME'
        ann = 12
        
    mp = prices.resample(rule).last().ffill()
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp, mr = mp.loc[idx], mr.loc[idx]

    feat, tgt, _, _ = create_features(prices, macro, lookback)
    common_idx = feat.index.intersection(mp.index)
    feat = feat.loc[common_idx]
    tgt = tgt.loc[common_idx]
    mp = mp.loc[common_idx]
    mr = mr.loc[common_idx]

    min_start = max(lookback, 12)
    if len(mp) <= min_start:
        return None
        
    capital = 1_000_000_000
    history = [capital]
    dates = [mp.index[min_start]]

    for t in range(min_start, len(mp)-1):
        train_X = feat.iloc[:t]
        train_y = tgt.iloc[:t]
        if train_X.shape[0] < 20 or train_y.nunique().get(0, 0) < 2:
            continue
            
        model = XGBClassifier(max_depth=3, n_estimators=100, random_state=0, verbosity=0)
        model.fit(train_X, train_y.values.ravel())
        
        X_current = feat.iloc[t:t+1]
        probs = model.predict_proba(X_current)[:, 1]
        prob_series = pd.Series(probs, index=mp.columns)
        top_assets = prob_series.nlargest(top_n).index.tolist()
        
        port_ret = mr.iloc[t+1][top_assets].mean() - tc
        capital *= (1 + port_ret)
        history.append(capital)
        dates.append(mp.index[t+1])

    if len(history) == 1:
        return None
        
    hist = pd.Series(history, index=dates)
    rets = hist.pct_change().dropna()
    total_ret = (hist.iloc[-1]/1e9 - 1) * 100
    cagr = (hist.iloc[-1]/1e9)**(1/(len(hist)/ann)) - 1
    ann_ret = rets.mean() * ann
    ann_vol = rets.std() * np.sqrt(ann)
    sharpe = ann_ret / (ann_vol + 1e-10)
    max_dd = ((hist - hist.cummax()) / hist.cummax()).min() * 100
    win_rate = (rets > 0).mean() * 100

    return {
        'Return%': total_ret,
        'CAGR%': cagr*100,
        'Sharpe': sharpe,
        'MaxDD%': max_dd,
        'WinRate%': win_rate,
        'Volatility%': ann_vol*100
    }

# ============================================================
# ۴. اجرای ماتریس مقایسه
# ============================================================
print("🧪 Probability Engine Backtest (XGBoost) — مقایسه با Momentum Baseline\n")

results_prob = []
for top_n in [1, 3, 5]:
    for freq in ['M']:
        for tc in [0.001, 0.003, 0.005, 0.01]:
            for lookback in [4, 8, 12, 26, 52]:
                res = run_probabilistic_backtest(prices, macro, top_n=top_n, tc=tc,
                                                 lookback=lookback, freq=freq)
                if res:
                    res.update({'TopN': top_n, 'Freq': freq, 'TC%': tc*100, 'Lookback': lookback})
                    results_prob.append(res)

df_prob = pd.DataFrame(results_prob)

print("\n📊 نتایج Probability Engine (Top 10 بر اساس Sharpe):")
if not df_prob.empty:
    print(df_prob.sort_values('Sharpe', ascending=False).head(10)[
        ['TopN','Freq','TC%','Lookback','Return%','Sharpe','MaxDD%','WinRate%']
    ].to_string(index=False))

    print("\n🔍 مقایسه مستقیم با Momentum Baseline (Top5, Monthly, TC=0.5%):")
    print("Baseline Momentum: Return=2354% Sharpe=1.03")
    best_prob = df_prob[(df_prob['TopN']==5) & (df_prob['TC%']==0.5) & (df_prob['Lookback']==4)]
    if not best_prob.empty:
        print(f"Probability Engine: Return={best_prob['Return%'].values[0]:.0f}% Sharpe={best_prob['Sharpe'].values[0]:.2f}")
    else:
        print("⚠️ ترکیب مشابه در Probability Engine یافت نشد.")
else:
    print("❌ هیچ نتیجه معتبری برای Probability Engine تولید نشد. احتمالاً داده‌های macro ناقص هستند.")
    print("🔧 راه‌حل: اجرای دوباره با VPN یا بازبینی تاریخچه دانلودها.")
