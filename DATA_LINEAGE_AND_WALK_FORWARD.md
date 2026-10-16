# MarketSage point-in-time data foundation and source selection

Status: implementation steps 1–3 are in progress. The FRED/ALFRED adapter ingests historical macro vintages into the point-in-time store; the existing global-proxy price snapshot now appends daily adjusted-close records to SQLite, and `/sources` exposes a versioned candidate/approval registry. These are local research foundations, not a scheduled production collector or production database service.

## Objective

Every feature used by a decision must be reproducible using only information that was available at that decision timestamp. The store in `temporal_data.py` provides an append-only SQLite foundation:

- `observed_at`: when the market event/value applies.
- `published_at`: when the provider made the fact public; null only when the source does not expose it (such records must not be used for release-sensitive macro/event features).
- `retrieved_at`: when MarketSage first captured this version.
- `source_revision` and `payload_sha256`: provider revision identifier where available and a content fingerprint.
- Revisions are appended, never overwritten. An as-of query chooses the newest version that had been retrieved and published by the requested decision time.

The FRED/ALFRED adapter in `fred_adapter.py` is the first concrete adapter. It requests FRED observation vintages, records the observation date, source vintage date and retrieval time, and appends revisions. Because the API's vintage dates are day-level rather than exact intraday release timestamps, it conservatively marks the value available at 23:59:59 UTC on that date. This is intentionally cautious, but it is not a substitute for an exact publisher release timestamp. The adapter is not yet scheduled as a collector or connected to scoring. Other live adapters, source licensing review, raw payload retention, migration/backup and API integration remain separate gates.

## Initial source registry (candidate sources, not all approved for scoring)

| Domain | Primary candidate | Use | Must be verified before production |
|---|---|---|---|
| Global prices | Existing Yahoo Finance/yfinance adapter for research only; replace or supplement with a vendor/exchange feed whose terms permit this use | OHLCV and proxy assets | Coverage, corporate actions, timestamps, corrections, reliability and data-use rights |
| US macro | Federal Reserve Bank of St. Louis FRED API; use series observations plus vintage/realtime fields where available | Rates, yields, inflation and selected macro series | API key/limits, release calendar, vintage availability and series-specific release timing |
| US company filings | SEC EDGAR APIs | Fundamentals and filings with accession/document timestamps | Filing acceptance time, amendment links, request policy and point-in-time field mapping |
| Global news discovery | GDELT 2.1 as a broad discovery/index layer, not as the truth source | Candidate articles/events and discovery timestamps | Coverage by language, duplicates, article URL survival, corrections and terms |
| News/event confirmation | Original issuer/government/regulator releases and reputable publishers with licensed/archive access | Verified event facts and event time | Preserve original publication/update times; do not infer facts from headlines alone |
| Iranian equities and funds | TSETMC public market pages/endpoints are candidates; CODAL for issuer disclosures | Prices, fund quotes/NAV-related fields, filings | Stable access from target host, terms/permission, adjusted history, suspensions, units, symbol identity and historical completeness |
| Iran macro | Central Bank of Iran and Statistical Center of Iran publications, series and release documents | Official macro releases | Publication time, revision history, accessible machine-readable history and unit definitions |
| Iranian gold/coin and FX | No source approved yet; evaluate at least two independent providers and official reference publications where relevant | Separate local gold/coin and rate series | Free-market vs official rate distinction, source rights, timestamped history, Rial/Toman units, spread and corrections |
| Iranian crypto | Official exchange APIs for each selected exchange, evaluated separately | Exchange-specific OHLCV and order-book/liquidity data | Terms, uptime, market symbol, fees, quote currency, missing intervals and historical depth |
| Social sentiment | No source approved yet; use only a provider/source whose collection and retention terms permit it | Public-post signals, if legally and technically available | Access rights, bot/spam controls, Persian-language quality, deletions, sampling bias and historical replay |

Do not merge official and free-market FX, different Iranian exchanges, fund NAV and exchange price, or local and USD crypto series into one price series. Keep market, instrument, venue, quote currency and unit explicit.

## Point-in-time rules

1. Store raw response bytes or a durable raw-object reference plus SHA-256, source URL/ID, request time, response time, parser version and ingestion run ID.
2. Store source publication time separately from observation/effective time and ingestion time. A web crawl timestamp is not proof of original publication time.
3. Append corrections and provider revisions. Never rewrite prior versions; link a revision to the prior record when the provider exposes a revision identifier.
4. For a decision at time T, only expose records both captured by T and published by T. If publication time is unknown, quarantine the record from release-sensitive backtests.
5. Persist model version, feature version, training cutoff, universe membership, costs and source snapshot IDs with each prediction/backtest.
6. Missing, stale, inconsistent, unlicensed or unparseable data must fail closed: mark unavailable and do not fill with a fabricated value.

## Walk-forward value-add protocol

Freeze a time-ordered universe and use identical dates, instruments, execution assumptions and transaction costs for all comparisons. At each fold, fit scalers, feature selection, models and calibration only on the training window; choose thresholds only on training/validation data; score the next untouched window; then roll forward.

Required ablations:
- B0: price/momentum baseline.
- B1: B0 + macro values as actually known at each decision time.
- B2: B1 + verified news and political/geopolitical events.
- B3: B2 + sentiment features.
- B4: B3 + regime-conditioned probabilities, calibrated on prior data only.
- B5: B4 + risk-aware allocation and explicit exposure/turnover limits.

Report net returns, benchmark-relative returns, volatility, Sharpe/Sortino with caveats, max drawdown, turnover, fees/slippage, tail loss, calibration (Brier/log loss/reliability), coverage/abstention, and fold-by-fold uncertainty. Compare each Bk to B(k-1), not just to a single historical headline result. Use block/bootstrap uncertainty where appropriate and keep a final untouched holdout. A layer is retained only if its incremental benefit is stable across folds and markets after costs; otherwise it remains research-only.

## Release gates

- Provider permission, actual-host connectivity and documented schema.
- Versioned raw fixtures and parser/unit tests.
- Historical reconciliation and timestamp/revision audit.
- Data quality and freshness dashboards with explicit quarantine.
- Leakage tests, including future perturbation and revision-as-of tests.
- Walk-forward ablation report signed off before any live recommendation mode.
- Deployment only after persistent volume, backup/restore drill, monitoring, secrets, firewall and TLS checks.

## Current limitation

The yfinance snapshot path now appends captured price records to SQLite using the snapshot retrieval time and checksum. Yahoo does not provide a trustworthy original publication timestamp per historical row, so `published_at` remains null: the records support captured-as-of replay only, not a claim that the price was available at its market observation time. The `/sources` registry is versioned and records research wiring separately from production approval; all providers remain unapproved for production. The new `/data-quality` endpoint joins this registry to actual SQLite coverage by source and series, reporting record versions, distinct records, latest observed/retrieved timestamps and a basic freshness indicator for global proxy price series. A source with no records is reported as `no_data_captured`, not assumed unavailable; freshness does not certify publication-time correctness, licensing or data accuracy. Iranian providers remain disabled for scoring. Passing unit tests does not certify source quality or strategy performance.


## Version-one scope decision

The first research release covers **Iran and global markets as separate investable universes**, across equities, gold, FX, fixed income/bonds and crypto. A common data lineage and scenario layer can relate them, but raw series, venue, quote currency, instrument type, fees, and tradability must remain distinct.

### Universe A — Iran
- Equities and exchange-traded funds (equity, mixed, fixed-income, and gold funds).
- Gold/coin prices, with separate gram/coin definitions and units.
- Official and free-market FX as separate series.
- Local fixed-income/fund returns and available rate proxies.
- Crypto pairs on each selected Iranian exchange, separate from global USD pairs.

### Universe B — Global
- Equity indices and liquid market proxies/ETFs.
- Gold and oil benchmarks; distinguish futures, spot proxies, and ETF total-return behavior.
- Government-bond/rate series and yield curves.
- FX pairs and broad USD indicators.
- Crypto spot prices and liquidity from named venues or a clearly defined aggregate.

Do not imply every item is directly tradable for every user. The global universe can provide context for an Iran decision without being treated as an Iranian brokerage universe.

### Implementation order after this PR
1. Stabilize and test the temporal store plus the FRED/ALFRED vintage adapter.
2. ~~Add a versioned provider registry and data-quality status endpoint for every instrument family.~~ A versioned candidate/approval registry and `/sources` endpoint are now present; operational freshness/quality status remains pending.
3. ~~Connect the existing price collector to the temporal store and persist raw snapshot metadata, source and retrieval time.~~ Daily adjusted-close rows now append to SQLite with source ID, retrieval time, snapshot checksum and explicit adjustment/unit metadata. Durable raw provider response retention and production database migration remain pending.
4. Add one validated source adapter per family, beginning with the sources that have legal access, sufficient historical depth, and reliable timestamps.
5. Build a daily data-quality report and explicit quarantine behavior before a record can affect scoring.
6. Rebuild walk-forward baseline/ablation runs on the selected universes; do not enable model-driven live allocation before acceptance.
