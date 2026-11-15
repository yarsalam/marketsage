# MarketSage — Research, Instrument-Universe and Corporate-Action Operating Standard

**Status:** Research operating standard v1.0 — binding workflow proposal for this research branch  
**Scope:** Iranian listed securities first; separate, evidence-gated expansion to gold, FX, fixed income, commodities, global proxies and crypto  
**Research horizon:** The product's strategic decision horizon remains approximately six months. Shorter horizons are separate use cases and require their own validation.  
**Safety:** Research-only. This document does not approve investment recommendations, ranking, calibrated probabilities, backtesting for capital allocation, production deployment, broker connectivity or trading.

## 1. Decision: use an established research method, not an improvised adjustment recipe

There is an established, reproducible pattern used by institutional and academic financial databases:

1. Maintain a permanent security master and identifier history.
2. Preserve unadjusted observations and every source response.
3. Maintain a dated corporate-action/distribution ledger with event terms and effective dates.
4. Build adjusted price and return series from event-level factors, using a declared anchor date and method version.
5. Keep price-basis adjustment separate from total-return calculation.
6. Validate with independent observations and explicit missing-data rules.
7. Accept only intervals whose event history and calculations are complete; quarantine the rest.

CRSP's current data-description guide documents this pattern: raw/unadjusted data are preserved; adjusted data are derived using a chosen base date and cumulative factors; events are applied on the ex-distribution date; price/dividend and share/volume adjustments are distinct; and unknown corporate-action gaps can make affected adjusted observations missing. See the CRSP calculations guide, Chapter 3: https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-data-descriptions-guide-crspaccess/ .

**Important local adaptation:** CRSP is a methodological reference, not the legal or economic authority for Tehran-listed securities. Iranian event terms, price-reference rules, venue-specific calendars, halt/reopening procedures and effective sessions must be established from the applicable Iranian exchange/regulatory rules and the issuer's original documents. Never transplant a foreign exchange formula or assume a vendor's adjustment convention is the Iranian market rule.

## 2. Non-negotiable invariants

- Raw market observations, source payloads, original issuer notices, attachments and hashes are immutable.
- A price gap, provider adjustment tuple, nearby date or a third-party adjusted series creates a lead; it does not prove an event or its terms.
- Calendar proximity (for example ±3 or ±7 days) may generate a candidate review queue only. It must not be an identity join, event deduplication rule, causality rule or correction rule.
- Every identity mapping, event classification, formula, input, factor, effective session and output must be traceable to evidence and a versioned method.
- Unknown, conflicting, revised or incomplete evidence remains unknown/quarantined. Do not impute a factor to make a chart look continuous.
- A suspension, market closure, war, political shock, price limit, no-trade day or reopening gap is not itself a corporate-action price adjustment. Record the market state and its information separately; never fabricate prices for closed sessions.
- Company fundamentals, FX, inflation, rates, sanctions, war, production, contracts and news may explain real price movement or inform later research features; they do not mechanically create a historical price-adjustment factor by themselves.
- A symbol is not a security identity. Ticker, issuer, instrument, ISIN, exchange InsCode, related/legacy IDs and validity dates are separate fields.
- A successful parser, HTTP request, CI run, chart match or single source does not approve an investment data series.

## 3. Instrument universe: count first, classify second, research in controlled batches

### 3.1 What is currently known — and what is not

The current repository work must not confuse pilot coverage with market-wide coverage:

- The transferred evidence bundle contains three Iranian pilot instruments: وغدیر, فولاد and پارسیان, each with its own exact primary TSETMC InsCode and raw snapshot set.
- The separate canonical-registry work in Draft PR #73 describes eleven global research proxies; these are not Iranian-listed instruments and are not evidence of Iranian tradability.
- Draft PR #73 represents the Iranian equity, Iranian gold/coin, FX, fixed-income/fund and domestic-crypto universes as empty/quarantined pending source and identity evidence.
- An older local audit reported 2,493 instrument-universe rows. That is a historical inventory count, not yet a verified count of unique, active, ordinary Iranian shares as of a declared date. It may contain different security classes, inactive items or repeated identifiers.
- **Therefore the current authoritative count of the full Iranian listed-symbol universe is NOT YET ESTABLISHED.** Do not publish a guessed number or treat the three pilots as the complete universe.

### 3.2 Required universe snapshot

Create a versioned universe snapshot from a complete, permissioned source, with:
- source, retrieval timestamp, snapshot hash and as-of date;
- unique canonical instrument count, unique issuer count and provider-record count, reported separately;
- active, suspended, inactive, delisted and unknown status counts;
- market/venue, board, instrument/security type, currency and price unit;
- TSETMC group/industry code and name, plus the classification-system version;
- stable canonical ID, provider IDs, ISIN when present, ticker/name history, valid-from and valid-to dates;
- parent issuer / related instrument links (for example rights symbols), without merging distinct securities;
- first/last observation, trading calendar, data coverage and source-permission status.

Count **canonical instruments**, not ticker strings. Report active and historical/delisted instruments separately. Rights symbols, ETFs, bonds, futures, options, certificates and ordinary shares must not be collapsed into one stock count. Keep the mapping from security to issuer and industry time-aware.

### 3.3 Universe taxonomy

Build separate universe families, then sub-classify each by market/venue and industry:

| Universe family | Required subgroups / separation rules |
|---|---|
| Iranian listed equities | Exchange vs. OTC market; market/board; TSETMC industry/group; ordinary shares vs. preferred or other share classes; active vs. suspended vs. delisted |
| Rights and other equity entitlements | Rights instruments kept as separate instruments, linked to the parent share and the relevant corporate action |
| Listed funds / ETFs | Equity, fixed-income, gold/commodity, mixed and other funds; exchange price kept separate from NAV/estimated NAV |
| Gold and coins | Physical gold purity/weight, each coin denomination/type, certificates and gold funds; never mix gram, mithqal, coin or fund-unit prices |
| FX | Official, exchange, NIMA/SANA and free-market rates as distinct series; explicit base/quote direction, unit, source and observation time |
| Fixed income | Bond/sukuk/fund; clean vs. dirty price, coupon/accrual, maturity, yield convention and cash-flow schedule |
| Commodities and energy | Iran commodity exchange instruments/contracts vs. physical benchmarks vs. global futures; contract month, delivery terms and roll methodology |
| Derivatives | Options, futures and structured instruments kept separate from the underlying; expiry, multiplier, settlement and contract specification |
| Global benchmarks / proxies | Global index, ETF and commodity/FX/rates proxies kept separate from locally tradable instruments |
| Crypto | Spot, margin and perpetual/futures separated by venue and pair; quote asset, contract and custody/venue risk explicit |
| Non-listed real assets (later scope) | Real estate, vehicles and other appraised/quoted markets kept outside exchange-security universes and labelled with their own valuation/observation model |

### 3.4 Industry classification

For Iranian equities, classify by the exchange's issuer/instrument group metadata, preserve the raw code and description, and version the taxonomy. Do not infer industry from the ticker or company name. Where the issuer has multiple lines of business, keep the official sector code and optionally add a separately labelled analyst classification. Industry history is time-dependent; do not retroactively assign today's sector to all historical dates without evidence.

## 4. Scientific event-discovery and adjustment workflow

### Stage 0 — Freeze inputs and identify the security

For every instrument and ingestion run, record:
- canonical instrument ID, issuer ID, market/venue, provider IDs, ISIN and ticker/name history;
- source endpoint, parameters, retrieval time, response status, raw bytes, encoding and SHA-256;
- date range, record count, duplicates, gaps, schema/parser version and source permission;
- price basis, currency, price unit, volume unit and trading calendar.

Resolve identity continuity before matching events. Do not treat insCode2/3/4 as aliases unless their historical continuity is demonstrated by source records, ISIN/issuer evidence and date-valid security-master history.

### Stage 1 — Search for existing adjusted histories and documented methodologies

For every symbol:
1. Search official exchange/TSETMC adjusted series and any other legally usable vendor, broker, charting platform, research package or public implementation.
2. Record the exact series, provider, observation dates, retrieval time, methodology disclosure, adjustment basis, anchor date, rounding, cash-dividend treatment, volume treatment and rights/spin-off handling.
3. Compare the provider's series with raw source observations and issuer documents on event-by-event samples.
4. Use an external adjusted history as a **reconciliation/reference candidate**, not an unquestioned replacement. Adopt it as an output source only when identity, methodology, coverage, rights to use/redistribute, historical revisions and local-market event treatment are understood.
5. If its basis is undocumented or mismatched, retain it as a labelled comparison only.

### Stage 2 — Acquire raw market and instrument-state data

Collect, version and preserve daily observations including the actual fields available from the source (for example closing/last price, previous reference price, high/low, volume, value, number of trades, shares outstanding and status). Do not infer field semantics from a field name. Check unit (Rial/Toman), scaling, stale-price conventions, auction data and source revisions.

Maintain the market calendar and a separate state timeline:
- exchange session, holiday and exceptional closure;
- suspension/halt, reason, start, resume and reopening auction;
- no-trade/stale observation, zero volume, price limit/queue and cancelled/unapproved trades;
- IPO/listing, relisting, delisting, symbol/name/ID change, venue migration.

Never fill a closure with a synthetic daily close. Forward fill can convert stale/no-trade prices into false observations; backward fill can leak a future price into the past. Missing observations remain missing unless an explicit, documented data transformation is appropriate for a particular feature.

### Stage 3 — Discover events from all relevant source families

Search the complete history, not only the event types that are easiest to retrieve:

**Corporate-action candidates**
- cash dividend/distribution, special dividend, return of capital;
- bonus/stock dividend from retained earnings or reserves;
- cash/receivables rights issue, subscription rights, unused-right sales and final allocation;
- mixed-source capital increase, split/reverse split, denomination change;
- spin-off, demerger, merger, share exchange, conversion, in-kind distribution and other entitlement-changing action;
- capital decrease/write-off where applicable.

**Market-state and identity events (record, but do not mechanically price-adjust)**
- halt, suspension, reopening, auction, trading restrictions, price limits/queues;
- holidays, exchange-wide closure, exceptional closures and disrupted sessions;
- no-trade/stale prices, IPO, delisting, ticker/ISIN/InsCode change and venue migration.

**Fundamental, macro and external context (explanatory features, not mechanical adjustment)**
- financial statements, EPS, revenue, margins, production, capacity, contracts and management changes;
- FX regimes/rates, inflation, policy rates, fiscal/energy rules, input/output commodity prices and trade restrictions;
- sanctions, war, geopolitical incidents, cyber incidents, natural disasters, regulatory decisions and broad market shocks;
- news and public statements with original publication time, updates/corrections and affected entities.

**Source routes**
- TSETMC/TSE market and corporate-action records;
- original CODAL notices, amendments and attachments;
- original issuer disclosures and official publications;
- official gazette/company-registration and statutory/newspaper notices where relevant;
- exchange/regulator notices and market calendars;
- independent adjusted charts, vendors, libraries and public code as labelled comparators/discovery leads.

A secondary article may help locate a document; it does not supersede the original issuer resolution for approved event terms. CODAL category labels alone are not enough: inspect issuer identity, the complete letter, attachments, corrections and chain of implementation.

### Stage 4 — Build one event, many evidence records

The event ledger is the canonical record; documents and provider rows are evidence records attached to it. One economic event may have many documents and provider observations. Deduplicate by stable event identity and document relationships, not by dropping repeated rows.

Keep these dates distinct:
- source publication timestamp;
- issuer decision/meeting date;
- record/eligibility date;
- ex-date or entitlement date;
- first affected trading session established from exchange calendar and market facts;
- rights subscription, deadline, allocation and registration dates;
- provider event date;
- local retrieval/capture time;
- amendment/correction publication time.

Required event fields include:
- event_id, issuer_id, affected instrument_id(s), event family/subtype;
- source_document_id(s), TracingNo/letter serial, original URL, attachment hashes;
- original and corrected terms, units, source authority and evidence status;
- each distinct date above, including uncertainty intervals where a date is unknown;
- event relationship: independent, component-of, same-event duplicate, amended, superseded, cancelled, reversed, linked or unresolved;
- provider event tuples and third-party comparisons stored separately from issuer terms;
- analyst decision, reviewer, method version and rationale.

Never join or deduplicate events solely because their dates are close.

### Stage 5 — Reconstruct event economics before choosing a formula

For every event determine:
1. what the holder owned immediately before the event;
2. what the holder is legally entitled to receive or pay;
3. shares old/new and each funding source;
4. subscription price, cash distribution, tax/withholding if relevant, rights conversion/expiry/unused-right treatment, fractional treatment and any other consideration;
5. the applicable exchange/venue rule and its effective date;
6. the correct ex-date/first affected market session;
7. whether this is a price-basis event, a total-return cash flow, a market-state event or only explanatory information.

Formulas are event-specific. Theoretical price is a reconciliation check, not a substitute for the original terms or actual opening auction. For orientation only, simplified cases may have forms such as:

- pure cash distribution: theoretical ex-price may be based on pre-event reference price less the approved per-share distribution, subject to the applicable venue rule and distribution definition;
- pure bonus issue: theoretical price relates old shares and new shares, with no new cash injected;
- cash/receivables rights issue: theoretical price must include the subscription amount and new shares, with the rights entitlement treated consistently;
- mixed issue: reconstruct each funding component and sequence separately.

These simplified identities are **not blanket approval formulas** for every Iranian event. The exact applicable Iranian regulation, event terms, taxes, rights path, market procedure and dates must be pinned before calculation. Do not infer that all share-count increases are bonus issues. A market reopening price may differ from theoretical reference because new information, auction demand/supply, price limits or trading conditions affect the actual price.

### Stage 6 — Maintain separate output series

Every instrument must expose distinct, explicitly labelled bases:

1. **Raw observed series:** original source values at the time, no rewriting.
2. **Exchange/provider reference series:** source-reported reference/adjusted fields, if present, preserved with provider semantics and raw payload.
3. **Corporate-action price-basis series:** price transformed by accepted event factors for the defined purpose and methodology version.
4. **Total-return series:** compounds price change plus cash/in-kind distributions under a declared reinvestment/entitlement convention.
5. **Trading-state series:** halt/closure/no-trade/auction/stale/limit states alongside prices, not silently baked into a smooth chart.

Do not call a series simply “adjusted close” without disclosing whether it is split-adjusted, price-basis adjusted, dividend-adjusted or total return. CRSP's return methodology treats distribution cash flows in the holding-period return; its adjusted-price and volume rules are separately documented. MarketSage should do the same separation and declare its own Iran-specific convention.

Each accepted factor record must contain:
- factor_id, event_id, instrument_id, factor type and direction convention;
- formula/method version, input values, units, source evidence references;
- pre-event basis/reference price, theoretical price, provider factor and independent factor in separate columns;
- effective date/session, anchor date, cumulative factor and price fields affected;
- precision/rounding rule, computation code hash and test result;
- approval status, reviewer and unresolved assumptions.

### Stage 7 — Apply and validate

Apply factors in deterministic event/date order to a new derived series. Never overwrite raw values. Validate:
- exact instrument identity and date alignment;
- factor direction and anchor-date normalization;
- independent recomputation from original event terms;
- price/volume/share transformations under the declared convention;
- duplicate, overlapping, simultaneous, corrected and reversed events;
- trading calendar, closure, halt, stale and no-trade treatment;
- numerical precision, rounding and reproducibility;
- event-by-event comparison against official chart/provider history and any licensed independent series;
- unexplained discontinuities and missing event windows.

A price-chart match is supporting evidence, not proof of correct economic terms. A mismatch may be due to a wrong event, wrong date, wrong field, stale/no-trade record, rounding, provider policy, or an actual change in market value; investigate instead of forcing the series to match.

### Stage 8 — Accept intervals, not entire symbols by default

A security may have:
- raw data accepted for a range;
- event display accepted with unresolved terms;
- corporate-action price-basis series accepted for a later interval;
- total-return series accepted only for a narrower interval;
- older unresolved intervals quarantined.

To expose an adjusted interval, require complete material event coverage from that interval to its anchor, confirmed instrument continuity, source-linked terms, correct effective sessions, reproducible calculations, and independent validation. An unresolved event affecting an earlier period blocks all derived values that depend on it, but need not block later unaffected intervals.

## 5. Source hierarchy and confidence policy

Source authority is claim-specific:

1. applicable law/regulation and official exchange rules for venue mechanics;
2. original issuer resolutions, official CODAL notices and their original attachments for economic terms;
3. official exchange/security-master/trading records for instrument identity, actual sessions and observed market facts;
4. original legal/company-registration and statutory notices for registration/legal implementation;
5. independent data vendors and chart histories for reconciliation, once methodology and rights are understood;
6. media, blog posts, public code and third-party aggregators as discovery leads or labelled secondary corroboration.

Do not produce one vague numeric confidence score from source counts. State evidence completeness, unresolved issues, source conflicts and the precise release decision. Keep claim-level provenance so one strong source cannot silently validate unrelated claims.

## 6. Scientific model validation for the six-month product

The data/evidence work above must precede investment-facing model outputs. Once the inputs pass:

- Define a prediction target, decision time, horizon, asset universe and tradability assumptions before fitting anything.
- Use point-in-time inputs: the data value, document or news must have been available to the decision-maker at the simulated decision time. Keep observation date separate from publication/revision/capture time. The FRED/ALFRED design illustrates why historical vintages matter: macro observations are revised, and the data known at a past date can differ from today's history (https://fred.stlouisfed.org/docs/api/fred/alfred.html).
- Keep a final chronological holdout untouched. Use expanding or rolling walk-forward evaluation; do not randomly shuffle time series. Where labels overlap in time, use purging and an embargo gap.
- Include inactive/delisted securities and point-in-time universe membership to avoid survivorship bias.
- Model executable constraints and costs: Iranian fees/taxes, spread, slippage, price limits, queues, no-trade days, suspension/reopening, settlement and liquidity/market impact.
- Record every model/feature/parameter trial. Apply multiple-testing/selection-bias controls; the Deflated Sharpe Ratio and Probability of Backtest Overfitting literature specifically warn that repeatedly trying variants inflates apparent performance (Bailey & López de Prado, 2014/2017: https://doi.org/10.21314/jcf.2016.322 ; https://doi.org/10.3905/jpm.2014.40.5.094). Harvey, Liu and Zhu show why conventional significance thresholds are inadequate after broad factor mining (https://doi.org/10.1093/rfs/hhv059).
- Compare against predeclared baselines: cash/benchmark, equal weight, simple momentum and interpretable statistical models. Report net performance, drawdown, turnover, tail loss, liquidity capacity, regime breakdown, uncertainty, and failure cases.
- Forecast distributions must be evaluated with proper scoring/calibration metrics and coverage tests. A Sharpe ratio rescaled to 0–100 is not a probability or confidence score.
- Prefer robust, interpretable baselines before LSTM/VAR/Genetic Algorithms. Add complex models only when they improve repeated out-of-sample results after costs and multiple-testing controls.

## 7. Product release gates and the ten dashboards

The app should deliver useful evidence before claiming predictive ability:

**Available early as read-only research surfaces**
- instrument/universe coverage and source status;
- raw price history with price basis, units, coverage, missingness and trading state;
- corporate-action/event timeline with source documents, event terms and unresolved questions;
- separate raw, reference, corporate-action price-basis and total-return views where each is available;
- data-quality/anomaly diagnostics and transparent explanations.

**Ten analytical dashboards — staged by evidence readiness**

| Dashboard | Correct first release | What must remain disabled until validated |
|---|---|---|
| Prediction | Historical context, baseline forecast research and uncertainty explanation | Daily/7-day/six-month point predictions or 95% intervals without proper OOS calibration |
| Risk | Historical volatility, drawdown, liquidity and scenario definitions | Uncalibrated loss probabilities or claims of maximum loss |
| Strategy lab | Reproducible hypothesis definitions and paper research | “Best entry/exit”, genetic optimization, live signals and deployment |
| Anomaly | Data-quality, trading-state and statistically unusual observation flags | Claims of manipulation, fraud or causal explanation from anomaly score alone |
| Sentiment | Source-linked news coverage, duplicate handling and transparent text classification evaluation | Fear/greed number used as a decision factor without representative validation |
| News/events | Event timeline, issuer/entity links, source time, corrections and affected-instrument hypotheses | Causal impact scores presented as facts without event-study evidence |
| Technical indicators | Descriptive RSI/MACD/Bollinger/returns with clear price basis | Automated buy/sell labels or “optimized” parameters without OOS tests |
| Chart patterns | Pattern candidates and historical conditional frequencies, with false-positive counts | Deterministic targets/returns from visual pattern names |
| Equity research screen | Transparent factor exposures, accounting/source completeness and filters | Opaque K-Score, cross-sectional ranks or selection recommendations |
| Cross-market opportunities | Comparable data coverage, units, costs, liquidity and market access | “Best/lowest-risk/highest-return” recommendation across incomparable assets |

**Priority order:** (1) instrument master + source coverage, (2) raw price/market-state quality, (3) event/CODAL evidence ledger, (4) independently validated price-basis and total-return series, (5) descriptive indicators and data anomalies, (6) news/fundamental context, (7) risk analytics, (8) forecast research, (9) strategy lab, (10) ranking/opportunity comparison. The order can be accelerated only by evidence, not by UI completeness.

## 8. API and data-contract architecture

Use one canonical instrument ID across Python and NestJS. Keep provider identifiers in source mappings. Every response should disclose as_of, published_at where known, retrieved_at, source IDs, method/version, price basis, units, coverage status, quality status and warnings.

Recommended resource contract (NestJS is the authenticated public API gateway; Python/FastAPI owns reproducible analytics):
- GET /api/v1/instruments and /instruments/{instrument_id} — identity, sector, market, listing status and identifier history.
- GET /api/v1/markets/universes — counts by as-of date, asset family, venue, sector and status; counts are canonical-instrument counts.
- GET /api/v1/sources and /api/v1/coverage — source role, rights, freshness, observed coverage and approval status.
- GET /api/v1/instruments/{instrument_id}/series?basis=raw|reference|price_adjusted|total_return — basis-explicit series only.
- GET /api/v1/instruments/{instrument_id}/events and /api/v1/events/{event_id} — event ledger, relationships and source evidence.
- GET /api/v1/instruments/{instrument_id}/quality — gaps, duplicates, stale/no-trade, identity and event coverage.
- GET /api/v1/research/indicators, /risk, /anomalies, /news, /sentiment — each with methods, sources and validation status.
- GET /api/v1/research/forecasts, /strategies, /rankings, /opportunities, /backtests — default-closed feature-gated resources. No capital amount or allocation endpoint is enabled by default.

Use typed request/response models, strict horizon and identifier validation, bounded date ranges, timeouts, pagination, stable error codes and source attribution. Do not make frontend code call localhost services directly. UI must not contain mock metrics that look live; demonstration data must be explicitly labelled demo.

## 9. Required repository layout

Keep all symbol-level evidence in its own folder. The current pilot layout is retained; do not move raw files to a shared bucket simply because a common event type exists.

    data/market-research/
      iran-equities/
        adjustment-evidence/
          _shared/
            archive/acceptance-review/
            official_chart_validation/
            adjustment_factor_diagnostics/
            three_symbol_audit_runs/
            tse_client_validation/
          vaghdir/
            identity.json
            raw/tsetmc/
            codal/
            other_sources/
            events/
            calculations/
            outputs/
            validation/
          foolad/...
          parsian/...
        universe/
          snapshots/<as_of_date>/
          sector-map/
      iran-gold/
      iran-fx/
      iran-fixed-income/
      iran-commodities/
      global-proxies/
      crypto/

Every copied source/derived artifact needs a manifest entry with original path, original filename, source, retrieval time, bytes, SHA-256, transformation, parser/method version and evidence status. Shared files remain in _shared; per-symbol extracts retain links to the original source row and hash.

## 10. Review checklist before leaving this workflow

- [ ] Full instrument universe snapshot retrieved from an approved source and canonical unique counts computed.
- [ ] Market families and sector/industry classifications populated without mixing instrument types.
- [ ] Each symbol has a canonical identity and time-valid identifier history.
- [ ] All source rights, units, time conventions and price bases are explicit.
- [ ] Raw price history and market-state timeline are preserved.
- [ ] Peer adjusted histories and their published methodologies have been screened and documented.
- [ ] Corporate-action discovery covers the full event universe and relevant CODAL/issuer/official document chain.
- [ ] Events are deduplicated by identity/relationship, not date proximity.
- [ ] Price-only, corporate-action price-basis and total-return series are kept separate.
- [ ] Easy, evidence-complete intervals are accepted independently; unresolved periods remain quarantined.
- [ ] Only then do validated intervals enter read-only frontend/backend/admin research surfaces.
- [ ] The final six-month decision outputs remain disabled until point-in-time, cost-aware, genuinely out-of-sample validation passes.

**Operating rule:** do not leave this chart to build a flashy model. Finish each gate with a reproducible artifact, mark what is known/unknown, then move to the next gate. The process is reusable across symbols; event economics remain issuer- and event-specific.
