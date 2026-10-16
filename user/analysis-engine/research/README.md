# Research data and backtest protocol

This directory contains an auditable baseline, not evidence of profitability or investment advice.

## Data contract

- Backtest input is a monthly adjusted-close panel with unique, increasing dates and strictly positive finite prices. Missing values are rejected; never forward-fill missing observations for backtesting.
- The live feed preserves the expected symbol universe and keeps missing observations missing. An asset is eligible for live scoring only when its latest 13 completed monthly closes are all present.
- Live ranking uses completed calendar months only, avoiding a partial current month being compared with complete historical monthly returns.
- The first successful price snapshot per UTC day is stored as CSV in the persistent `market_data` volume. A JSON manifest records source, retrieval time, latest observation, symbols, row count, adjustment policy and SHA-256. This improves reproducibility but does not certify provider accuracy or licensing.
- Current universe is global-market proxies and crypto, not direct Tehran Stock Exchange, Iranian FX, Iranian gold/coin, or Iran macro/news feeds.

## Backtest conventions

`backtest.py` is a monthly, long-only, equal-weight top-momentum baseline. Signals use observations through the prior month-end. Previous holdings are marked to market and their weights drift before turnover is measured against the new target. Costs are `turnover × bps / 10,000`, deducted from capital before applying the following month's return. Initial entry is charged from cash.

The `/backtest` API uses the longest common complete monthly window available among eligible assets and requires at least 36 monthly observations. It separates the final chronological 30% of that window as a holdout period and reports holdout metrics separately from full-history descriptive metrics. Strategy parameters are fixed and no hyperparameter search is run. This is a useful first holdout check, not a guarantee of independence if developers have already repeatedly inspected these same dates. It compares against monthly-rebalanced equal weight, SPY buy-and-hold when available, and monthly-rebalanced 60/40 SPY/GLD when both assets are available. Benchmark returns currently exclude transaction costs. The API exposes only the latest 36 monthly rows while calculating metrics over the full window.

Metrics include gross/net returns, total return, CAGR, annualized volatility, Sharpe-like ratio without a risk-free rate, maximum drawdown, historical monthly 95% VaR, beta versus SPY when available, turnover and estimated costs. Cost assumptions are sensitivity parameters, not calibrated broker fees. Taxes, market impact, liquidity, FX conversion, survivorship/delistings and execution are not modeled. Parameter tuning requires an untouched final test period and walk-forward/out-of-sample reporting.

## Run locally

```bash
cd user/analysis-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## Sources

- yfinance project and caveats: https://github.com/ranaroussi/yfinance
- pandas time-series: https://pandas.pydata.org/docs/user_guide/timeseries.html
- pandas returns: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html
- pandas resampling: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- pytest: https://docs.pytest.org/en/stable/
- Docker Compose production guidance: https://docs.docker.com/compose/how-tos/production/
