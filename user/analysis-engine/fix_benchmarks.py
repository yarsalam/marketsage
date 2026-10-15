import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

tickers = {
    'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
    'GLD': 'Gold ETF', 'SPY': 'S&P500 ETF', 'QQQ': 'Nasdaq ETF',
    'TLT': 'US Long Bonds', 'UUP': 'Dollar Bullish',
    'USO': 'Oil ETF', 'XLF': 'Financials', 'XLE': 'Energy'
}

prices = yf.download(list(tickers.keys()), start='2015-01-01',
                    end=datetime.today().strftime('%Y-%m-%d'),
                    auto_adjust=True, progress=False)
if isinstance(prices.columns, pd.MultiIndex):
    prices = prices['Close'].copy()
prices = prices.ffill().bfill()

def compute_metrics(series):
    rets = series.pct_change().dropna()
    total_ret = (series.iloc[-1]/1e9 - 1) * 100
    ann_factor = 52 if 'W' in str(series.index.freq) else 12
    ann_ret = rets.mean() * ann_factor
    ann_vol = rets.std() * np.sqrt(ann_factor)
    sharpe = ann_ret / (ann_vol + 1e-10)
    maxdd = ((series - series.cummax())/series.cummax()).min() * 100
    return total_ret, sharpe, maxdd

def benchmark_eq(prices, freq='W'):
    rule = 'W-FRI' if freq=='W' else 'ME'
    mp = prices.resample(rule).last().ffill()
    mr = mp.pct_change().dropna()
    capital = 1_000_000_000
    history = [capital]
    dates = [mr.index[0]]
    for t in mr.index:
        capital *= (1 + mr.loc[t].mean())
        history.append(capital)
        dates.append(t)
    return compute_metrics(pd.Series(history, index=dates))

def benchmark_6040(prices, freq='W'):
    rule = 'W-FRI' if freq=='W' else 'ME'
    mp = prices.resample(rule).last().ffill()
    mr = mp[['SPY','TLT']].pct_change().dropna()
    port_ret = 0.6*mr['SPY'] + 0.4*mr['TLT']
    capital = 1_000_000_000
    history = [capital]
    dates = [port_ret.index[0]]
    for t in port_ret.index:
        capital *= (1 + port_ret.loc[t])
        history.append(capital)
        dates.append(t)
    return compute_metrics(pd.Series(history, index=dates))

print("📊 Benchmarks:")
for freq in ['W', 'M']:
    ret, sharpe, mdd = benchmark_eq(prices, freq)
    print(f"Equal Weight ({freq}): Return={ret:.0f}% Sharpe={sharpe:.2f} MaxDD={mdd:.1f}%")
    ret, sharpe, mdd = benchmark_6040(prices, freq)
    print(f"60/40 ({freq}): Return={ret:.0f}% Sharpe={sharpe:.2f} MaxDD={mdd:.1f}%")
