# MarketSage — Ten-Tab Product and API Build Roadmap

**Status:** Product design proposal aligned with the research operating standard.  
**Current investment state:** Research-only; all predictive/allocation outputs remain disabled by default.  
**Purpose:** Complete the user experience without presenting mock values or unvalidated analytics as real investment evidence.

## 1. Assessment of the supplied finance-app prototype

The pasted files are useful as a UI sketch but are not ready to power real investment decisions.

### Analysis-engine defects in the supplied price_service.py

| Code behavior | Why it is invalid/risky | Required correction |
|---|---|---|
| yfinance download with auto_adjust=True without per-field basis metadata | Provider-adjusted close semantics are implicit; corporate-action treatment cannot be independently audited | Use an instrument registry and store provider basis, raw/reference fields where available, retrieval time and hashes |
| ffill() and bfill() | Forward fill can disguise stale/no-trade observations; backward fill imports future prices into earlier dates | Never fill the canonical price history. Keep missing values and trading-state reasons explicit |
| lookback=4 on monthly price levels | Four prices provide only three monthly returns, far too few for stable Sharpe/volatility estimates | Declare sample sufficiency, calculate on a defined return frequency and require adequate observations |
| horizon resampling followed by another monthly resampling | The 1W/1M/3M/6M parameter does not create a forecast for that horizon | Define the prediction target and rebalance/holding period explicitly; separate horizons end-to-end |
| Top-five min-max score of momentum, Sharpe and inverse volatility | Relative min-max score depends on the current candidate set, is scale-sensitive, and does not establish expected return or risk-adjusted superiority | First report raw metrics and uncertainty; only add a predeclared, validated factor model later |
| max_vol=0.15 without a defined annual/monthly unit | The threshold is uninterpretable and potentially far too loose/tight | Store frequency, annualization, currency, risk-free benchmark and estimation window |
| confidence = Sharpe / 1.5 * 100 | A transformed Sharpe ratio is not calibrated probability or forecast confidence | Return null/not-calibrated until a probability model is evaluated with proper scoring and calibration |
| Equal weights among selected assets | Ignores covariance, liquidity, fees, capacity, trading access and investor constraints | Keep portfolio construction disabled; later use explicit constraints and net-of-cost optimization |
| No historical universe, delistings or point-in-time features | Allows survivorship and look-ahead bias | Time-valid security master, as-of universe membership, publication/vintage timestamps and delisting handling |
| No fees, taxes, spread, queues, price limits or suspensions | Backtest fills may not be executable in Iranian markets | Venue-aware execution simulator before any investment-facing backtest |

### UI components in the supplied prototype that must not appear as live data

- InvestmentDecision.tsx: mock rankings, example allocations and a fallback portfolio.
- PricePrediction.tsx: fixed prices, fixed 95% interval and fixed confidence.
- RiskAnalysis.tsx: hard-coded VaR, drawdown, Sharpe, beta and scenario probabilities.
- FearGreedIndex.tsx and SentimentAnalysis.tsx: static emotion scores and provider counts.
- EconomicCalendar.tsx: hard-coded event times and event names.
- MarketStories.tsx / WhyToday.tsx: illustrative narratives and synthetic chart points, not live market evidence.
- TopOpportunities.tsx: fabricated risk/return numbers and synthetic sparklines.
- AIChatbot.tsx: hard-coded facts/metrics that can be mistaken for current model outputs.
- The sample DecisionController and frontend fetches use hard-coded localhost URLs. Production code must go through the authenticated same-origin NestJS gateway, with strict DTO validation, bounded query inputs and timeouts.

**Decision:** do not copy this sketch over the current MarketSage repository. The repository's separate Draft work already contains a more mature canonical instrument registry, source/quality coverage, temporal price-basis audit and default-closed research output gate (PRs #73, #77 and #81). Review/integrate those existing branches in dependency order rather than creating a second architecture.

## 2. Dashboard contracts and release stages

| Tab | Primary question | Initial read-only contract | Later analytical contract | Release condition |
|---|---|---|---|---|
| prediction | What range of outcomes is plausible over a stated horizon? | Current series, data-as-of, benchmark and historical context | Forecast distribution/quantiles, calibration, scenario drivers and error history | Point-in-time features, enough data, walk-forward and holdout pass |
| risk | How can the asset/portfolio lose value and become untradeable? | Historical volatility, drawdown, gaps, liquidity and known event risks | VaR/Expected Shortfall, stress tests and portfolio risk decomposition | Correct basis, costs, tail and execution assumptions |
| strategy | What predeclared rules can be studied? | Strategy specification, assumptions and run status | Paper backtest and cost-aware walk-forward comparisons | No leakage, reproducible runs, multiple-testing controls |
| anomaly | What looks unusual in the data or market state? | Gap/stale/volume/price/state flags with evidence | Statistical anomaly models and calibrated alert precision | Precision/false-positive analysis; never claim manipulation based only on anomaly score |
| sentiment | What tone and disagreement appear in available text? | Source coverage, language, duplicates, publisher time and classification evaluation | Financial-Persian sentiment distributions and uncertainty | Representative labelled set, publication-time replay and drift tests |
| news | What happened, to whom, and when was it known? | Source-linked event timeline, issuer/instrument links and corrections | Event-study evidence and conditional impact estimates | Exact event time, source chain, confounders and reproducible event study |
| technical | What does the observed price/volume history show? | RSI/MACD/Bollinger/returns with explicit basis and missingness | Conditional historical statistics by regime | Data-quality and point-in-time series accepted |
| patterns | Which chart structures may be present? | Candidate shape and detection rule | Historical frequency, false-positive rate and post-detection distribution | Out-of-sample precision; no deterministic target-price promise |
| ranking | Which instruments pass transparent research filters? | Universe filters, source completeness and factor exposures | Validated cross-sectional model with uncertainty and sector controls | Full point-in-time universe and multiple-testing correction |
| opportunities | Which markets can be compared on a common basis? | Comparable units, currency, venue access, source status, fees and liquidity | Scenario/return-risk comparison and constraints | Comparable assets, common horizon, actual costs and validated forecast/risk inputs |

The Market Coverage/source page and Corporate Action Evidence page are **foundational workspace pages**, not substitutes for these ten tabs. They should be reachable globally and provide the source-of-truth drill-down behind each analytical result.

## 3. Recommended API topology

**Public-facing boundary:** Next.js → authenticated NestJS gateway → internal Python/FastAPI analytics. The browser must not call localhost:8000, direct provider endpoints or internal service hosts.

### Core evidence APIs (build/complete first)

- GET /api/markets/instruments — canonical instrument registry and time-valid aliases.
- GET /api/markets/universes — canonical counts by as-of date, asset family, venue, sector and status.
- GET /api/markets/sources — source identity, permissions, freshness, timestamps, coverage and approval state.
- GET /api/markets/data-quality — gaps, duplicates, stale/no-trade, units, basis and quarantine reasons.
- GET /api/markets/instruments/:id/series?basis=raw|reference|price_adjusted|total_return — one explicit series basis only.
- GET /api/markets/instruments/:id/events — event chronology and event-to-source links.
- GET /api/markets/events/:eventId — terms, relationship graph, evidence, formulas, factor status and reviewer decisions.
- GET /api/markets/instruments/:id/adjustment-status — accepted date intervals and quarantined intervals.

### Analytical APIs (separate feature gates)

- GET /api/research/indicators
- GET /api/research/anomalies
- GET /api/research/news
- GET /api/research/sentiment
- GET /api/research/risk
- GET /api/research/forecasts
- GET /api/research/strategies
- GET /api/research/rankings
- GET /api/research/opportunities
- GET /api/research/backtests

Every response should include:
as_of, published_at if known, retrieved_at, source_ids, canonical_instrument_id, price_basis, currency, unit, method_version, coverage_status, quality_status, research_gate and warnings.

For forecasts additionally include horizon, target definition, model version, training window, evaluation window, quantile/distribution definition, calibration status and benchmark. Do not overload a field called confidence with a Sharpe transformation.

For events additionally include source-document IDs, exact event dates, relationship state, formula ID, factor direction, factor inputs and acceptance decision.

## 4. Python service boundaries

Use domain modules rather than one large price_service.py:

- universe/: canonical registry, symbol lifecycle, industry/venue taxonomy.
- ingestion/: provider adapters, immutable snapshot capture, source permissions and response hashing.
- market_state/: sessions, halts, closures, stale/no-trade and reopening.
- corporate_actions/: event ledger, document linking, economic terms, calculation rules, factor graph.
- series/: raw/reference/price-adjusted/total-return construction, each basis explicit.
- quality/: coverage, missingness, duplicate and reconciliation checks.
- features/: indicators and point-in-time fundamentals/macro/news features.
- models/: forecast/risk/anomaly models with model cards and feature lineage.
- validation/: walk-forward, purging/embargo, cost model, holdout and multiple-testing reports.
- api/: FastAPI routers and Pydantic schemas; no hidden calculations inside route handlers.

Python owns calculation reproducibility. NestJS owns authentication/authorization, rate limiting, audit logging, request validation and the stable product API. Admin sees source/event/research gate state and can review evidence; admin does not override failed scientific gates silently.

## 5. Model strategy: what is more efficient than starting with LSTM/VAR/GA?

### Six-month strategic horizon

Start with transparent baselines and interpretable factors:
- medium-term trend/momentum at several non-overlapping lookbacks;
- volatility, drawdown, liquidity and turnover;
- valuation/fundamental revisions and earnings quality only when point-in-time CODAL data is complete;
- industry and market-regime context;
- FX, commodity, rates and macro variables only with correct publication vintages;
- news/event information only when source and publication/update time are replayable.

Then compare regularized linear models, tree-based methods and regime-aware models against simple baselines. Neural networks (LSTM/Transformer) are candidates only after enough clean, point-in-time, cross-sectional and temporal data exist. Genetic optimization is not an initial priority because large parameter searches raise multiple-testing/overfit risk.

### Short horizons (intraday to seven days)

These need a different data and execution standard: intraday timestamp precision, order-book/trade data if available, auction/price-limit/queue state, market microstructure, fees and fill simulation. Daily EOD data alone cannot credibly support next-day execution claims.

### Probability and confidence

A forecast should be a distribution or set of quantiles, not just a point. Calibration is checked on untouched out-of-sample data. Until then, use not_calibrated / unavailable, not a coloured 0–100 gauge.

## 6. Monetizable product value without false promises

The defensible differentiator is not “AI says buy this”. It is an evidence-rich research workspace:
- every claim links to its original document and market observation;
- users can see what changed, when it became known, and which parts remain uncertain;
- raw/reference/adjusted/total-return bases cannot be confused;
- event explanations expose formulas and source citations;
- source coverage, data quality and model-validation status are visible;
- later, research subscriptions can offer custom watchlists, alerts, sector/event reports, portfolio risk diagnostics and reproducible scenario studies.

Do not market the app as guaranteeing investment success. It cannot make a user successful merely because it has AI or backtests. The product must earn trust by showing uncertainty, limitations, failure cases and provenance.

## 7. Build sequence

1. Stabilize and review existing Draft PR #73 (instrument identity, source coverage and temporal price basis).
2. Review Draft PR #77 (default-closed analytical outputs) and PR #81 integration; do not deploy or merge without the existing explicit release gates.
3. Integrate the three-symbol imported evidence bundle from PR #82 and run real data validation, not just structural CI.
4. Build the complete as-of instrument universe snapshot; establish canonical counts and classifications.
5. Expand event discovery and primary-source evidence to the entire accepted universe in bounded batches.
6. Create price-basis and total-return outputs for independently accepted intervals.
7. Complete user-facing evidence/quality/event pages, then descriptive indicators and anomaly diagnostics.
8. Add fundamental/news/macro context with point-in-time provenance.
9. Validate risk analytics and forecast research on walk-forward/holdout.
10. Only after separate approvals enable strategy, ranking, opportunity comparison or investment-facing recommendations.

**Rule:** a tab may exist visually before its model is validated, but it must show an honest disabled/research-only state rather than invented values.
