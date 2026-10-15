# Research data and backtest protocol

This directory contains an auditable baseline, not evidence of profitability or investment advice.

## Data contract

- Backtest input is a monthly adjusted-close panel with unique, increasing DatetimeIndex values.
- Values must be numeric, finite, strictly positive, and complete. The engine refuses to silently forward-fill or treat missing returns as zero.
- Record provider, retrieval timestamp, observation timestamp, adjustment policy, timezone/calendar, symbol mapping, and raw-data checksum for every research run. The current Yahoo Finance integration does not persist immutable raw snapshots, so provider revisions limit reproducibility.
- Current universe is US-listed ETF proxies and crypto symbols, not direct Tehran Stock Exchange, Iranian FX, Iranian gold/coin, or Iran macro/news feeds.
- Align different asset calendars to a documented monthly calendar; do not fill across unbounded gaps.

## Backtest conventions

`backtest.py` is a monthly, long-only, equal-weight top-momentum baseline. Signals use only observations through the prior month-end; holdings earn the following month's return. Turnover is the sum of absolute weight changes; cost = turnover × bps / 10,000. Initial entry is charged from cash (zero weights). Metrics include gross/net returns, total return, CAGR, annualized volatility, Sharpe-like ratio, max drawdown, turnover, and estimated costs.

Not modeled: taxes, borrow, market impact, liquidity, FX conversion, survivorship, delistings, execution, or cash yield. Costs are sensitivity parameters, not calibrated estimates. Parameter tuning requires an untouched final test period and walk-forward/out-of-sample reporting.

## Run locally

From `user/analysis-engine`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Tests cover missing/duplicate data rejection, transaction-cost accounting, insufficient history, and a future-data perturbation check.

## Sources

- yfinance project and caveats: https://github.com/ranaroussi/yfinance
- pandas time-series: https://pandas.pydata.org/docs/user_guide/timeseries.html
- pandas returns: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html
- pandas resampling: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- pytest: https://docs.pytest.org/en/stable/
- Docker Compose production guidance: https://docs.docker.com/compose/how-tos/production/
