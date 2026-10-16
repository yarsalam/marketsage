# MarketSage strategy implementation audit

Audit date: 2026-10-16  
Scope: repository code on `deploy/production-readiness` plus the separate draft PRs for Iranian data contracts and admin-workspace CI. This is a code-scope audit, not a live-server or investment-performance certification.

## Executive conclusion

MarketSage currently implements a **limited global-proxy price/momentum research prototype**, with a leakage-aware historical research baseline and an API/UI path for displaying data-backed momentum and backtest results. It does **not** yet implement the original integrated market-intelligence strategy in which price, macro releases, political events, news and sentiment jointly influence calibrated probabilities and portfolio decisions.

A UI component, label, mock card or candidate provider URL is not evidence that a data source is ingested or that its values affect scoring.

## Feature-by-feature status

| Intended capability | Current evidence | Status |
| --- | --- | --- |
| Global markets | Small fixed universe of global-market proxies/ETFs and crypto; price history uses Yahoo Finance/yfinance | Partial prototype; not comprehensive global coverage |
| Iranian equities | Separate draft PR adds a provider catalog and fail-closed contract; TSETMC URLs are only candidates | Not live; scoring disabled |
| Iranian gold/coins | No provider selected or validated | Not implemented |
| Iranian free-market FX | No provider selected; official/free-market series not integrated | Not implemented |
| Iranian local-exchange crypto | No provider selected; no validated FX conversion/fees integration | Not implemented |
| Price/momentum ranking | Python API computes momentum scores from available monthly price history | Implemented as a research baseline |
| Macro inputs | VIX, DXY and US 10-year yield appear in experimental ML scripts; no publication-time-aware macro pipeline in the production API | Research-only / incomplete |
| Regime detection | Active Research UI explicitly reports unavailable; no validated walk-forward regime classifier in production scoring | Not implemented in production |
| News ingestion | Active News tab reports no configured auditable news collector; no verified news pipeline | Not implemented |
| Political/geopolitical/social events | No timestamped event store, event taxonomy, source validation or event-to-asset scoring path | Not implemented |
| Sentiment analysis | No production sentiment model/pipeline connected to scoring. Older UI components contain hard-coded example values and must not be treated as live analysis | Not implemented in production |
| Probability engine | Earlier Logistic Regression/XGBoost experiments were not leakage-safe/production-validated; confidence is intentionally unavailable in the current API/UI | Experimental only; not approved for decisions |
| Portfolio allocation | Current API returns research allocation based on the limited scoring path; it is not a risk-optimized multi-market portfolio | Partial prototype |
| Risk analysis | Risk/backtest views consume research API output; no evidence of fully integrated macro/event stress testing or validated tail-risk controls | Partial research tooling |
| Backtesting | Research baseline includes chronological holdout and benchmark comparisons; results remain sensitive to provider data, universe, costs and assumptions | Useful baseline; not proof of future outperformance |
| AI analyst | Active UI reports unavailable until connected to real, citable market evidence | Not implemented |
| Persistent market data | First-seen daily snapshots/manifests exist in the user-stack design; they are not certified exchange records and need operational retention/backup verification | Partial |
| Admin service | Admin UI source is tracked and now included in CI; NestJS admin API is a starter controller/module and not deployed in production Compose | Not production-ready |

## Alignment with the original strategy

The original strategy was to combine price action, macroeconomics, politics/geopolitics, news, sentiment, regime detection, calibrated probability estimates, portfolio construction, risk controls and walk-forward backtesting.

The current code follows that strategy in **direction and some engineering safeguards**, but not yet in end-to-end capability:

- **Aligned:** separate Python analysis and NestJS API layers; current scoring output is sourced from the analysis service; unavailable/uncalibrated capabilities are increasingly shown as unavailable instead of inventing a confidence score; backtesting has a chronological holdout baseline; Iran data is being added behind strict quality gates.
- **Partially aligned:** global asset comparison, momentum scoring, risk/backtest views, and limited macro features in research experiments.
- **Not yet aligned in implementation:** news/politics/sentiment do not feed the decision engine; macro data does not have release-time vintages; there is no validated production regime engine or calibrated probability model; Iranian markets do not yet have live verified feeds; there is no proven multi-market portfolio optimizer with real trading constraints.
- **Must remain blocked:** public claims of calibrated success probability, minimum risk, verified alpha or integrated geopolitical intelligence.

A numeric “percent complete” would be misleading because a screen can exist without its underlying pipeline. The defensible summary is: **the price/momentum research baseline exists; the integrated intelligence strategy is still largely an architecture goal.**

## Required acceptance gates before enabling a feature

1. Name the provider and confirm terms/permission, uptime, geographic access and rate limits.
2. Save source payload fixtures with source timestamp, retrieval timestamp, symbol/asset identity, units and provenance.
3. Test missing, duplicate, stale, corrected and out-of-order observations; never silently fill gaps.
4. For macro data, preserve the original release timestamp and vintage/revision history.
5. For news/events, deduplicate syndicated stories, retain original publication time, identify affected assets and distinguish confirmed reports from unverified claims.
6. For sentiment, validate on a manually reviewed sample and test language/domain drift; sentiment is a feature, not a trade signal by itself.
7. Test each new data family incrementally against the same walk-forward baseline. Report net returns after realistic turnover-based costs, drawdown, tail risk, calibration and stability by regime.
8. Enable scoring only if the new feature improves out-of-sample results robustly; otherwise retain it as contextual information or leave it disabled.
9. Keep all unvalidated screens visibly marked unavailable; remove or relabel any hard-coded legacy demo values before they are routed into the active app.
10. Complete admin authentication, authorization, audit logs, persistence and API contract tests before exposing any admin endpoint.

## Deployment scope

The current `docker-compose.production.yml` deploys the user research stack only. A successful build or CI run does not establish source licensing, production data access, secure admin operations, DNS/TLS correctness or successful deployment on the target server. Those must be verified independently before launch.
