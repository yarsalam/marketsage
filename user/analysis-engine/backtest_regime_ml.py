import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# ۱. Universe
# ============================================================
tickers = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials', 'XLE': 'Energy'
}

# ============================================================
# ۲. دریافت داده
# ============================================================
def get_data():
    print("📥 دانلود داده‌ها...")
    d = yf.download(list(tickers.keys()), start='2015-01-01',
                    end=datetime.today().strftime('%Y-%m-%d'),
                    auto_adjust=True, progress=False)
    if isinstance(d.columns, pd.MultiIndex):
        prices = d['Close'].copy()
    else:
        prices = d.copy()
    prices = prices.drop(columns=[c for c in prices.columns if 'Volume' in str(c)], errors='ignore')
    prices = prices.ffill().bfill()
    return prices

prices = get_data()

# ============================================================
# ۳. تابع Scoring ساده (بدون تغییر)
# ============================================================
def calculate_scores(prices, returns, lookback=12):
    p = prices.iloc[-lookback:]
    r = returns.iloc[-lookback:]
    momentum = p.iloc[-1] / p.iloc[0] - 1
    mean_ret = r.mean()
    std_ret = r.std().replace(0, np.nan)
    sharpe = mean_ret / (std_ret + 1e-10)
    inv_vol = 1 / (std_ret + 1e-10)
    def minmax(s):
        return (s - s.min()) / (s.max() - s.min() + 1e-10)
    return minmax(momentum)*0.4 + minmax(sharpe)*0.3 + minmax(inv_vol)*0.3

# ============================================================
# ۴. تابع Backtest چندمنظوره
# ============================================================
def run_backtest(prices, rebalance='W', top_n=3, lookback=12, tc=0.001):
    # تبدیل به فرکانس مورد نظر
    if rebalance == 'W':
        freq = 'W-FRI'
        ann_factor = 52
    else:
        freq = 'ME'
        ann_factor = 12

    mp = prices.resample(freq).last().ffill()
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp = mp.loc[idx]
    mr = mr.loc[idx]

    min_start = max(6, lookback)  # حداقل داده اولیه
    if len(mp) <= min_start:
        return None

    capital = 1_000_000_000
    history = [capital]
    dates = [mp.index[min_start]]

    for i in range(min_start, len(mp)-1):
        prices_sofar = mp.iloc[:i+1]
        rets_sofar = mr.iloc[:i+1]
        scores = calculate_scores(prices_sofar, rets_sofar, lookback)
        top_assets = scores.nlargest(min(top_n, len(scores))).index.tolist()

        port_ret = mr.iloc[i+1][top_assets].mean() - tc
        capital *= (1 + port_ret)
        history.append(capital)
        dates.append(mp.index[i+1])

    hist = pd.Series(history, index=dates)
    rets = hist.pct_change().dropna()
    total_ret = (hist.iloc[-1]/1e9 - 1) * 100
    cagr = (hist.iloc[-1]/1e9)**(1/(len(hist)/ann_factor)) - 1
    ann_ret = rets.mean() * ann_factor
    ann_vol = rets.std() * np.sqrt(ann_factor)
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
# ۵. Benchmarks
# ============================================================
def benchmark_equal_weight(prices, rebalance='W'):
    freq = 'W-FRI' if rebalance == 'W' else 'ME'
    mp = prices.resample(freq).last().ffill()
    mr = mp.pct_change().dropna()
    idx = mp.index.intersection(mr.index)
    mp = mp.loc[idx]
    mr = mr.loc[idx]

    # Equal Weight daily rebalance simulated monthly/weekly
    port_ret = mr.mean(axis=1)  # ساده‌ترین حالت
    capital = 1_000_000_000
    hist = [capital]
    for r in port_ret:
        capital *= (1 + r)
        hist.append(capital)
    hist = pd.Series(hist, index=mp.index)
    rets = hist.pct_change().dropna()
    ann_factor = 52 if rebalance == 'W' else 12
    sharpe = (rets.mean() * ann_factor) / (rets.std() * np.sqrt(ann_factor) + 1e-10)
    return {
        'Return%': (hist.iloc[-1]/1e9-1)*100,
        'Sharpe': sharpe,
        'MaxDD%': ((hist - hist.cummax())/hist.cummax()).min()*100
    }

def benchmark_6040(prices, rebalance='W'):
    freq = 'W-FRI' if rebalance == 'W' else 'ME'
    mp = prices.resample(freq).last().ffill()
    port_ret = mp[['SPY','TLT']].pct_change().dropna().apply(lambda x: 0.6*x['SPY'] + 0.4*x['TLT'], axis=1)
    capital = 1_000_000_000
    hist = [capital]
    for r in port_ret:
        capital *= (1 + r)
        hist.append(capital)
    hist = pd.Series(hist, index=port_ret.index)
    rets = hist.pct_change().dropna()
    ann_factor = 52 if rebalance == 'W' else 12
    sharpe = (rets.mean() * ann_factor) / (rets.std() * np.sqrt(ann_factor) + 1e-10)
    return {
        'Return%': (hist.iloc[-1]/1e9-1)*100,
        'Sharpe': sharpe,
        'MaxDD%': ((hist - hist.cummax())/hist.cummax()).min()*100
    }

# ============================================================
# ۶. اجرای ماتریس تست
# ============================================================
print("\n🧪 Robustness Test Matrix (2015-2026)\n")
results = []

for top_n in [1, 3, 5]:
    for freq in ['W', 'M']:
        for tc in [0.001, 0.003, 0.005, 0.01]:
            for lookback in [4, 8, 12, 26, 52]:
                res = run_backtest(prices, rebalance=freq, top_n=top_n, lookback=lookback, tc=tc)
                if res:
                    res['TopN'] = top_n
                    res['Freq'] = 'Weekly' if freq == 'W' else 'Monthly'
                    res['TC%'] = tc*100
                    res['Lookback'] = lookback
                    results.append(res)

df = pd.DataFrame(results)

# نمایش بهترین‌ها بر اساس Sharpe
print("🏆 Top 10 by Sharpe (All Combinations):")
print(df.sort_values('Sharpe', ascending=False).head(10)[['TopN','Freq','TC%','Lookback','Return%','Sharpe','MaxDD%','WinRate%']].to_string(index=False))

# نمایش بهترین‌ها با کارمزد 0.5%
print("\n💪 Best with TC=0.5% (Realistic):")
df_tc = df[df['TC%'] == 0.5].sort_values('Sharpe', ascending=False)
print(df_tc.head(5)[['TopN','Freq','Lookback','Return%','Sharpe','MaxDD%','WinRate%']].to_string(index=False))

# Benchmarks
print("\n📊 Benchmarks:")
for freq in ['W', 'M']:
    ew = benchmark_equal_weight(prices, freq)
    b6040 = benchmark_6040(prices, freq)
    print(f"Equal Weight ({'W' if freq=='W' else 'M'}): Return={ew['Return%']:.0f}% Sharpe={ew['Sharpe']:.2f} MaxDD={ew['MaxDD%']:.1f}%")
    print(f"60/40 ({'W' if freq=='W' else 'M'}): Return={b6040['Return%']:.0f}% Sharpe={b6040['Sharpe']:.2f} MaxDD={b6040['MaxDD%']:.1f}%")
