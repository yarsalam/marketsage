# Stage 4 — Research data collection (Yahoo sample)

**Status:** preparation only; no historical download or backtest has been run by this commit.
**Branch:** `feat/tindex-free-data-connector`
**Purpose:** create a reproducible *research-only* sample so the data audit and baseline tests can proceed. This does not accept Yahoo Finance as a production source.

## Why this sample is limited

The default symbols are `BTC-USD ETH-USD SOL-USD GLD SPY QQQ TLT UUP USO XLF XLE`. They mix crypto with US-listed funds/equities and do not represent Tehran stocks, Iranian gold funds, free FX or Iranian coin markets. Do not use results to rank Iranian assets or claim a six-month return forecast.

## Run locally

From the repository root:

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
.venv/bin/python scripts/download_research_prices_yahoo.py
```

The script writes per-symbol CSVs and a `manifest.json` under `~/.cache/marketsage/research/yahoo`, outside the Git checkout. It uses daily bars from 2015-01-01 through the latest completed UTC date (the end date is exclusive), requests corporate-action columns, and keeps `Close` and `Adj Close` separate. It never prints raw price values or provider exception messages. Existing requested files are not overwritten unless `--overwrite` is supplied.

Example for a smaller initial connectivity test:

```bash
.venv/bin/python scripts/download_research_prices_yahoo.py --tickers SPY BTC-USD
```

If the default output already exists, choose a fresh output directory:

```bash
.venv/bin/python scripts/download_research_prices_yahoo.py --output /tmp/marketsage-yahoo-check
```

## After download

1. Share only the console summary and symbol row/date ranges; do not upload licensed/raw market files unless you have confirmed permission.
2. Review manifest, schemas, missingness, duplicates, prices and adjusted-price semantics locally.
3. Record currency, source terms/permission, point-in-time availability, revisions and survivorship as pass/fail/unknown. Unknown is not a pass.
4. Fix the exact chronological splits and six-month forward-label design before inspecting comparative results.
5. Compare predeclared baselines and the monthly momentum baseline net of costs; record drawdown, volatility, turnover, costs, and limitations.
6. Preserve the holdout and publish a reproducible manifest with data hashes, code commit and configuration.

Do not commit downloaded CSVs or the local manifest to Git. Download success does not mean the data is approved, and Stage 2 source acceptance remains open.
