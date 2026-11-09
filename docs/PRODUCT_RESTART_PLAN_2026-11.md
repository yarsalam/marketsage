# MarketSage — Product restart and delivery plan

**Decision date:** 2026-11-08  
**Product owner:** Repository owner  
**Execution posture:** Internal research and decision-support system; research-only

## Product objective

MarketSage is an internal investment-decision system for the owner's own capital. Its core decision horizon is approximately six months. It compares opportunities across Iranian and global asset classes using information that was available at the decision time. It should explain potential return/loss scenarios, conditions that support or invalidate them, liquidity and risk constraints, macroeconomic context, corporate actions, news and geopolitical/social events, and opportunity cost versus cash and lower-risk alternatives.

Iranian and global assets are distinct investable universes. A common evidence, temporal and scenario architecture may relate them, but raw price series, venues, symbols, currency/quote units, fees, corporate actions and tradability remain explicit and separate.

A forecast is never a promise. A provider response, UI card, parser success, model output or green CI run is not proof of source accuracy or investment merit.

## Active product increment — Phase 1: evidence-first market coverage

Issue: [#72](https://github.com/yarsalam/marketsage/issues/72)  
Branch: `research/market-coverage-workspace-2026-11`

Expose the source registry, runtime data-quality report and Iranian provider-readiness catalog already present in the Python analysis service through the NestJS API and a Persian RTL Next.js page.

The first page is intended to answer:
- Which market and asset families are represented in the registry?
- Which providers are selected, merely candidates, connected to research, or not scheduled?
- What data has actually been captured in the temporal store?
- What are the observed and retrieved timestamps, freshness status and known limitations?
- What source-specific legal, identity, unit, historical, revision and timestamp checks remain?
- Why is a source blocked from production scoring?

No synthetic prices, inferred connectivity, guessed permissions, fabricated coverage or unverified source approval may be displayed.

## Active product increment — Phase 2: canonical instrument and market-universe registry

Issue: [#75](https://github.com/yarsalam/marketsage/issues/75)  
Implementation is currently grouped with the Market Coverage product branch so the API and evidence UI can be reviewed together.

The first registry contains only the eleven symbols already present in the global research prototype. Each has a provider-neutral canonical ID separate from its Yahoo symbol, explicit USD quote convention and price basis, and a research-proxy role. Venue and tradability remain unassessed. Every instrument is blocked from production scoring.

Iranian equities, gold/coins, FX, fixed income/funds and local crypto remain empty and quarantined. No placeholder securities or invented identities are inserted. The read-only analysis API exposes /instruments; NestJS forwards it as /api/markets/instruments, and the Persian Market Coverage page displays the catalog and quarantined universes. The data-quality response resolves observed series to canonical instrument IDs when a source-symbol mapping exists.

Freshness evaluation is now policy-specific: only explicitly registered global crypto and ETF proxies use the 3-day and 7-day observed-age thresholds. Other sources (including macro series) remain unknown unless a source-specific calendar/policy is defined.

New snapshot writes now follow the canonical registry: crypto series use `provider_close` with USD per token; ETF series use `adjusted_close` with USD per share. The payload records the canonical ID, basis and adjustment policy. Existing temporal rows are deliberately not rewritten; a read-only audit must precede any possible migration.

This registry is metadata only: it does not collect prices, change provider eligibility or alter any research calculation.

## Product architecture and staged roadmap

### A. Product truth and data observability
1. Market coverage, source readiness and data-quality UX.
2. Instrument/universe registry with explicit market, venue, asset family, symbol history, currency, quote convention and units.
3. Per-source provenance and audit view: request/retrieval time, publisher publication time, observation/effective time, revisions, parser/version and content digest.
4. User-visible quarantine reasons for missing, stale, malformed, identity-conflicted, unlicensed or timestamp-unknown records.
5. Separate captured-as-of replay from publisher-source-vintage replay.

### B. Permissioned data foundations
1. Preserve global-proxy Yahoo data as research-only until terms, history, adjustments, corporate actions and independent reconciliation are accepted.
2. Stabilize FRED/ALFRED vintages and verify each series' release calendar, revisions and publication-time semantics before use.
3. Keep TSETMC/CODAL candidate adapters quarantined until usage rights, identity, units, adjusted-price/corporate-action behavior, historical depth and actual-host access are proven.
4. Select and independently reconcile at least two providers for Iranian gold/coins and FX; keep official and free-market FX distinct, and maintain Rial/Toman unit metadata.
5. Evaluate fixed-income/fund price, NAV and yield sources separately.
6. Evaluate local and global crypto venues separately, including pairs, quote currency, fees, liquidity, missing intervals and access terms.
7. Add news, issuer and geopolitical event sources only with original-source verification, publication/update timestamps, corrections and deduplication. Discovery indexes are not truth sources.
8. Add social sentiment only after collection/retention rights, sampling bias, Persian-language quality, bot/spam controls and deletion handling are validated.

### C. Research validity before any decision output
1. Freeze a representative and survivorship-aware universe for each market.
2. Rebuild the six-month price/momentum baseline using corrected point-in-time and total-return data.
3. Attribute the previously reported extreme Stage 4 fold using the exact original input hash; do not substitute reconstructed data.
4. Keep the final holdout unopened for parameter selection.
5. Add time-aware macro, event, news and sentiment features only as controlled ablations against the same baseline.
6. Use chronological walk-forward splits; fit scaling, feature selection, thresholds, models and calibration only on prior data.
7. Report net results after realistic fees, slippage, taxes, FX conversion and liquidity assumptions, as applicable; also report drawdown, tail loss, turnover, uncertainty, coverage/abstention and fold stability.
8. Probability estimates remain unavailable until calibrated out-of-sample and independently reviewed.
9. Risk-aware allocation remains a research experiment until portfolio constraints, liquidity and downside behavior are demonstrated.

## Global release controls

- Every source has an explicit approval state. Unknown is not pass.
- All data records retain market, venue, instrument identity, currency, units, observation time, publisher publication time (nullable only when unknown), retrieval time, revision and provenance.
- Candidate/unregistered sources remain blocked from scoring.
- A successful parser or data download does not approve a source.
- Backtests remain research artifacts, not evidence of future performance.
- UI labels must describe what the underlying service actually implements; unavailable capabilities stay visibly unavailable.
- No production recommendations, auto-investment, broker connection, trading or real-money allocation are authorized by this plan.
- Any change to product objective, investment horizon/universe principles, fundamental modeling approach or material capital risk requires explicit owner approval.

## Infrastructure track — independent, not a product blocker

Infrastructure acceptance is optional and must not gate product delivery. No new Runner registration/dispatch is used for ordinary work. Owner-reported host-level Rootless Docker checks passed for UID 110, rootless mode, seccomp and no default bridge, with the system Docker kept separate. The latest recorded local dataset-acceptance dispatch [#42482678959](https://github.com/yarsalam/marketsage/actions/runs/42482678959) succeeded once on 2026-11-08; this is a single manual run, not proof of Runner availability or a 24/7 service. Infrastructure PRs #71 and #74 remain Draft and parked. Live independent-backend failover and a full 24-hour observation window are not evidenced. Product work does not depend on them.

This evidence discrepancy must be corrected by subsequent runs and records, but it does not prevent safe, independently scoped product development. No infrastructure acceptance claim is changed by starting this roadmap.

## Current implementation facts as of 2026-11-09

- Python analysis service exposes `/sources`, `/data-quality`, and `/iran-market/providers`.
- The source registry lists ten sources; none is production-approved. One source (Yahoo Finance via yfinance) is currently wired into the research baseline.
- FRED/ALFRED adapter exists but is not scheduled or connected to scoring.
- TSETMC and CODAL are candidate-only; Iranian gold/FX providers are not selected.
- Existing decision/momentum output is a small global-proxy/crypto historical research baseline; it is not an Iran-market decision engine and its nominal horizon parameter does not make the model horizon-specific.
- News/politics/sentiment and calibrated probabilities are not implemented as production decision inputs.
- The Market Coverage UI surfaces these facts, the canonical instrument catalog and series-to-instrument mappings without changing source approvals or investment calculation gates.
- Legacy temporal rows whose stored price basis differs from the canonical registry are explicitly counted and flagged in the API/UI; no automatic historical rewrite is performed.
- Future snapshot writes validate symbols before any file write and store crypto close versus ETF adjusted-close semantics with explicit units and adjustment policy.
- Production-images CI runs the analysis image and probes `/health`, `/sources`, `/data-quality`, `/iran-market/providers` and `/instruments`.
- A read-only local SQLite audit CLI is included at `user/analysis-engine/audit_temporal_price_basis.py`. It prints only aggregate counts, opens with SQLite read-only mode, and never changes the temporal database. Usage when a local-only audit is needed: `python3 user/analysis-engine/audit_temporal_price_basis.py --db <path-to-temporal.sqlite3>`. It is tested against synthetic DBs in GitHub-hosted CI; no owner DB was accessed.
- Exact final PR #73 head `87d0eab55422f5a58d48a4c0b8faa0dc9aad10fd` passed push run #42620847077 and pull_request run #42620857089; all jobs succeeded. CI built all production images, started the real analysis container and validated five read-only endpoints on GitHub-hosted runners.

## Owner priority update — 2026-11-09

The owner directed that all product work continue without waiting for the self-hosted Runner. Standard development, tests, builds and runtime smoke use GitHub-hosted Actions. A local command is reserved only for a task that demonstrably needs a local-only dataset or host; the independent backlog continues meanwhile. No current Runner-online status has been verified, so no claim of current availability/offline state or host cleanup is made. The last known local dataset acceptance #42482678959 succeeded once on 2026-11-08; it is not 24/7 evidence.

Research-output safety is separately tracked in Draft PR [#77](https://github.com/yarsalam/marketsage/pull/77): decision, scores, portfolio allocation and backtest outputs are disabled by default at the UI and NestJS API until evidence gates and explicit owner approval. Its exact head passed run #42618957174. Neither PR #73 nor #77 has been merged or deployed.
