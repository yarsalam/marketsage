# MarketSage — data-source acceptance matrix

**Checkpoint date:** 2026-11-03  
**Release posture:** candidate/research-only. No source in this matrix is approved for production scoring.  
**Workflow:** implement → identify source/series contract → automated tests → bounded live evidence → history/units/reconciliation/rights review → private staging smoke → explicit review → merge.  
**VPN rule:** before any foreign live-source request, tell the project owner to enable VPN. Iran providers TSETMC/CODAL/Tindex use VPN off. Never mix them in one probe batch.

## Acceptance matrix

| Market/data family | Primary candidate(s) | Secondary/source caveat | Current evidence | Acceptance gate before scoring |
|---|---|---|---|---|
| Iranian listed equities/funds | TSETMC daily history and instrument search | CODAL supports filing/event discovery, not replacement market prices | TSETMC/CODAL bounded probes returned responses; adjusted-price candidate path exists for TSETMC | Complete instrument master and identity; raw vs provider-adjusted OHLC; corporate-action dates; suspended/delisted symbols; missing-session coverage; independent reconciliation and collection rights |
| Gold/coins | Tindex enabled precious-metal indicators; Nerkhsanj archive candidate | StreamData is vendor-supplied, not free; TGJU automated collection is not approved | Owner-run Nerkhsanj capture (2026-10-22) parsed 28 keys / 91,245 rows; 2026-10-23 audit flagged scale/gap anomalies, so no series is accepted. Tindex unit/account reconciliation remains open. | Keep 18K gram gold, 24K, melted gold and each coin separate; verify key identity, unit, currency, quote convention, timestamps, history overlap, corrections, independent reference and rights; quarantine AYAR anomaly pending vendor/source evidence. |
| Free-market USD | Tindex current-rate/indicator candidates; Nerkhsanj archive candidate | World Bank is macro only, not a daily FX source; TGJU remains candidate-only | Nerkhsanj owner-run archive capture parsed candidate rows, but provider key does not prove free-market USD or unit. Tindex snapshot exists; units remain unconfirmed. | Verify free-vs-official market definition, currency pair and quote direction, Rial/Toman convention, timestamp/observation semantics, corrections, gaps, independent overlapping-date reconciliation and rights. |
| Crypto spot | Venue-specific public exchange APIs; Binance Spot is one candidate only | Yahoo Finance is a proxy; seller BTCUSDT is not a free source and rights remain unverified | Owner-reported Iran-network attempts returned HTTP 451 for BTCUSDT/ETHUSDT/SOLUSDT; a separate earlier foreign probe reported access but only 18 rows across eight series, not a multi-year audit. | Do not bypass the HTTP 451 route. Any alternative must have its own terms/access review. Freeze venue/pair/quote currency; audit full candle history, partial candles, gaps, fees/slippage and rights. Never call BTCUSDT a universal USD price. |
| Fixed income / bonds | No accepted series yet; TSETMC listed instruments/funds are only candidates | Fund price, NAV, coupon/yield, and yield-to-maturity are different measures | Provider and history contract not selected | Choose exact instrument type and yield convention, maturity/duration, coupon/cashflow and publication date; validate historical availability. Until then return unavailable/not-rankable |
| Iran inflation/macro | Central Bank of Iran and Statistical Center of Iran portals; World Bank annual indicator as a broad candidate | World Bank annual observation year is not exact publication time and can be revised | World Bank produced 26 annual Iran CPI observations, 2000–2025; no daily feed implied | Preserve annual frequency; capture release/vintage dates where available, series definitions/units and revisions; reconcile official domestic series; never manufacture daily dates |
| CODAL corporate disclosures/events | CODAL search adapter | Original filing and corrected/amended filing must be connected | Search adapter and bounded response exist; publication timestamp was not confirmed in prior report | Store original publication, first-seen/retrieval and amendment times separately; build a normalized event schema; verify corrections and point-in-time replay against source documents |
| News / geopolitical events | GDELT DOC as discovery only; original publisher for verification | Prior GDELT request returned HTTP 429; index time is not publication time | Adapter and keyword baseline exist; no recent GDELT probe in the latest batch | Check coverage by Persian/English and country/topic, canonical deduplication, original-source/time verification, rights, labelled-event recall and no look-ahead |
| Sentiment / social signals | No provider selected | Public posts are not automatically collectible, retainable or trainable | Lexicon baseline is a prototype only, not a validated ML model; no social signal connected to ranking | Confirm collection/retention/deletion rights; create time-stamped Persian/English labelled dataset; record annotator agreement; report held-out class-wise precision/recall/F1 and drift; abstain when uncertain |

## Global official-source candidates screened — 2026-11-03

A documentation-only screen added five candidates to the catalog/registry. No API endpoint was contacted, no adapter was enabled, and all entries remain excluded from scoring. See [the full source-contract screen](global-source-candidate-screen-2026-11.md).

| Candidate | Intended role | Verified documentation facts | Unresolved acceptance gates |
|---|---|---|---|
| ECB Data Portal SDMX | Daily reference FX, euro-area yields and macro | Public SDMX REST; daily reference exchange rates documented since 1999; `updatedAfter` and `includeHistory` support update/history retrieval. ESCB public statistics are reusable with attribution and without modification; third-party data are excluded without permission. | Exact series key, currency direction, reference-vs-executable quote, release/availability time, revision replay and third-party rights. |
| US Treasury XML | USD par yields, bills and real yields | Daily par yields from 1990; bills from 2002; real-yield series from 2003; default 300 rows and zero-based pagination. | Maturity/curve definitions, units, publication/availability timestamp, revisions/schema changes and reuse terms. Rates are not bond prices or total-return series. |
| EIA API v2 | Oil, petroleum inventories, natural gas and electricity context | Free API; key registration required; bulk downloads do not require a key; API supports series/date/frequency/facet selection. EIA government information is generally public domain with acknowledgment, subject to API terms and third-party material exceptions. | Secure key, API terms, exact series/geography/frequency/unit, release calendar, revisions, source attribution and separation of energy statistics from tradable market prices. |
| SEC EDGAR | US issuer filings, fundamentals and events | Public submissions/XBRL APIs require no API key; indexes extend to 1994Q3; 10 requests/second/user Fair Access and descriptive User-Agent required. Acceptance and public availability are distinct; post-acceptance corrections can alter indexes. | CIK/form identity, acceptance-vs-availability mapping, amendments/corrections, XBRL contexts/units/periods, reuse terms and point-in-time replay. Not a price feed. |
| IMF SDMX 2.1/3.0 | International macro and external-sector context | IMF documents SDMX 2.1/3.0 APIs; its Swagger explorer requires a beta portal account. | Actual endpoint authentication/quota, exact dataflow/history, release/vintage semantics, country/units and reuse rights. |

**Execution order:** start with one ECB reference-FX or yield series; then one Treasury curve; then one EIA energy series; then one SEC CIK/form history; leave IMF until its API access contract is clarified. Before each foreign live request, remind the owner to turn VPN ON. Do not batch these candidates or add them to the default probe runner.

## What is already tested vs what is not

### TSETMC adjusted history

The current candidate implementation joins raw TSETMC daily history to the provider's legacy `a=1` adjusted chart. It does not calculate adjustment factors itself. Raw values are retained, missing adjusted dates stay null, and all rows remain quarantined/not-scoreable. The legacy chart's positional schema is empirically mapped, not an official stable contract.

On the PR #13 discovery branch, the adjustment/history regression suite currently spans **32 collected test cases across three files**:
- `tests/test_tsetmc_adapter.py`: parser, invalid rows, adjusted field mapping, no raw-price fallback, point-in-time quarantine, and atomic ingestion failure.
- `tests/test_tsetmc_adjusted_dataset.py`: source identity, date coverage, raw-vs-adjusted separation, missing-date behavior and malformed adjusted prices.
- `tests/test_tsetmc_adjustment_validation.py`: raw chart shape preservation and extraction of the expected provider wrapper.

These are automated fixture tests. They do not count as 32 independent live-data reconciliations.

A prior owner-reported live candidate build for **one instrument (فولاد)** contained 4,664 raw daily rows, 4,249 rows with adjusted close, and 415 rows with no matching adjusted chart row. This is one-instrument evidence only; it is not complete-universe acceptance. Keep the 415 unmatched dates null and never substitute raw prices.

### Minimum next live acceptance sample for adjustments

Do not rerun the same test arbitrarily many times. The required checks are different layers:

1. **Code regression:** the focused tests and full offline suite run on each candidate code commit; CI is the repeatable record. The latest PR #13 adjustment-test increment passed the full CI workflow.
2. **Live instrument sample:** keep فولاد as the existing baseline, then add at least two other verified instruments. Select them after inspecting the provider adjustment-event response so the sample covers at least two distinct corporate-action patterns; do not guess event dates or instrument IDs.
3. **Event-window reconciliation:** for each selected instrument, inspect pre/post-event raw history, adjustment-event records, the unadjusted chart, and adjusted chart. Check multiple sessions on each side, factor/ratio behavior, OHLC invariants, chart/raw coverage and unexpected gaps.
4. **Independent reference:** compare overlapping dates and corporate-action effects against a second legally usable source where possible. Comparing two endpoints from the same provider is an internal consistency check, not independent reconciliation.
5. **Universe expansion:** after the adapter passes the sample, run automated schema/coverage/OHLC/adjustment checks on every symbol admitted to the research universe. A three-symbol test validates the method, not the entire Iranian market.

For TSETMC live checks, **VPN must be OFF**. The script `scripts/validate_tsetmc_adjustments.py` writes raw comparison artifacts locally; keep its output out of Git and share only reviewed, sanitized summary metadata. For any foreign comparison provider, first explicitly remind the owner to turn VPN ON.

## Repeat policy for other data families

- Run deterministic parser/contract tests with fixtures on every relevant code change.
- Run bounded live probes only when needed to identify/diagnose a source or confirm that its contract has not drifted. A failed foreign probe must not be retried until VPN is enabled and the specific error class is understood.
- Run history/quality audits on each candidate series before inclusion, when provider schema changes, and when coverage/scale/anomaly monitoring flags drift. Do not issue repeated identical live requests merely to create a test count.
- Source approval is per source and use case; a valid adapter does not approve units, rights, history, point-in-time semantics or investment scoring.
- The staging prototype may use deterministic fixtures/research-only datasets while acceptance proceeds. Unaccepted markets must show explicit insufficient-data/not-rankable state. No source or model ranking is enabled by staging success.

## Tindex contract correction and Nerkhsanj evidence update (2026-11-02)

- Current [Tindex developer docs](https://tindex.app/en/developers/) state the Free tier quota is 1 request/minute and 100 successful requests/day, with one active token per account. This supersedes the stale 3/minute and 300/day settings from earlier onboarding notes. The guarded local client now enforces a process-wide rolling minute and in-memory daily success budget, but it cannot see other hosts/processes sharing that account. Do not run concurrent jobs.
- Current public docs define currency-rate values as Toman per quoted unit and say Markets & Indicators values are Toman since 2026-07-20. Keep the normalized unit unconfirmed until a fresh account payload is compared with an independent lawful reference. The Tindex candles/history endpoint is capped at about 100 days, insufficient alone for the six-month horizon.
- Nerkhsanj remains a discovery candidate, but the owner-run bounded archive request on 2026-10-22 did complete: 28 candidate keys and 91,245 pairs were parsed, followed by a local audit on 2026-10-23. The parser reported no invalid dates, non-positive values or duplicate-date conflicts; the audit flagged 182 adjacent changes >=20% and 48 >=100%, concentrated in IQD, silver and Tether. IQD also had a 373-day maximum gap; silver/Tether and Bitcoin had gaps up to 84 days. Keep IQD, silver and Tether excluded from features; retain Bitcoin as a coverage warning. These are owner-reported local summaries, not an independent re-audit. Raw response was not retained as a fixture. Source ownership/upstream lineage, attribution, commercial/model-use rights, key identity, price semantics, units, market convention, calendar, corrections, stale-value behavior and independent reconciliation remain unverified. Do not rescale, delete, forward-fill or poll `/calc` per record. See the owner-run sections in `free-dataset-discovery-and-acceptance.md` for sanitized counts and triage.
- The conservative Tindex quota implementation was merged into #6 and its post-merge CI passed. Any future live probe still requires VPN OFF, one request/minute, the shared 100-success/day budget, one slug per request and the remaining source-acceptance gates. No Tindex live request was made in this update.

## Candidate disposition and next evidence sequence — 2026-11-03

This is a decision-oriented triage of evidence already present in the repository and sanitized owner-reported summaries. No provider was probed in this update, no local raw file was accessed, and no source was approved.

| Priority | Candidate | Current disposition | Next evidence required |
|---|---|---|---|
| 1 — Iran price-history path | TSETMC equities/funds | Best current engineering path, but **not accepted**. A previously shared owner-run whole-corpus report records 1,220 raw archives, 1,220 normalized histories and 1,677,202 history rows; an earlier candidate build emitted 128 series / 167,912 feature rows / 151,784 forward-label rows, all fail-closed. That internal QA is not independent economic or rights validation. The PR #14 integrated runner has not been verified against the 1,220-instrument corpus. | Preserve prior hashes/reports; compare the exact PR #14 runner and discovery scope with the earlier 47-instrument/zero-feature diagnostic before one trusted local run. Then review identity, event families, missing sessions, price semantics, and lawful independent references. |
| 2 — Low-frequency macro context | World Bank Indicators | Candidate for annual macro context only; not a daily market-price substitute. Observation year is not release/availability time and revisions may create look-ahead. | Capture series definition, unit, release/vintage availability and revisions; preserve annual frequency and align only after a point-in-time rule is documented. |
| 3 — Issuer events | CODAL | Discovery adapter exists, but retrieval time cannot stand in for publication time and original/corrected filings are not yet linked. | Reconcile original, amendment and publication timestamps against source documents; establish historical replay and use terms. |
| 4 — Local multi-asset archive | Nerkhsanj | **Research-excluded pending remediation.** The owner-reported audit flagged 182 adjacent moves >=20% (48 >=100%), concentrated in IQD, silver and Tether; IQD has a 373-day maximum gap and silver/Tether/Bitcoin have gaps up to 84 days. No raw files were re-audited here. | Resolve exact key identity, scale/unit, upstream lineage, attribution and commercial/model-use rights; compare overlapping dates against a lawful independent source. Keep IQD/silver/Tether out of features and Bitcoin as a coverage warning meanwhile. |
| 5 — Current Iran indicators | Tindex | Account-scoped candidate only. Previously reviewed public docs describe a 1,644-active-instrument TSE screener, stock endpoints in Rial and other Markets & Indicators values in Toman since 2026-07-20; the documented history cap is 100 days, and account-specific endpoint access remains unverified. The 1/minute and 100-success/day limits are shared account-wide. | Do not bulk-crawl the screener or use the 100-day history as standalone six-month evidence. Keep stock and indicator unit families separate; reconcile one authorized payload per selected series to an independent reference and document rights/account scope. |
| 6 — Global proxy histories | Yahoo Finance | Existing captures may support exploratory plumbing only; unofficial access/terms, adjustments, survivorship and point-in-time availability are unresolved. US ETFs are not a representative Iran universe. | Reuse existing captures; do not redownload without a changed acceptance question. Verify symbol mapping, adjustments, terms and historical availability before any performance claim. |
| 7 — Venue-specific crypto | Binance Spot | Iran-network HTTP 451 is a blocked route. Do not bypass it or repeat the same blocked request. A separate small foreign sample is not multi-year coverage evidence. | Keep blocked for this environment; any future alternative requires its own lawful access, venue/pair identity, history, fees and rights review. |
| 8 — News discovery | GDELT DOC | Adapter is research-only; prior HTTP 429 remains in cooldown. First-seen/index time is not publisher publication time. | No repeat probe until a materially changed acceptance question and deliberate request budget; verify original publisher/time and a labelled Persian/English event set. |
| 9 — Macro vintages | FRED/ALFRED | Adapter exists but key/access was unavailable in the prior environment. Observation/vintage dates are not exact intraday release times. | Keep unprobed until secure key/network access is available; document series-specific release calendars and vintage semantics. |
| 10 — Vendor and unverified local feeds | StreamData, TGJU, Iran official macro portals, fixed income and social signals | No accepted series. StreamData is vendor-supplied rather than free; TGJU automated rights are unapproved; official macro machine-readable coverage and fixed-income contract are not established; no social provider/labelled benchmark exists. | Resolve contracts/rights, exact series definition, units, timestamps, history and independent reconciliation before implementation or collection. |

### Previously shared local TSETMC evidence — scope and interpretation

A sanitized owner-run report shared on 2026-10-23 records 1,220 raw archives, 1,220 normalized histories and 1,677,202 history rows. Its earlier whole-corpus candidate build reports 128 series, 167,912 research-feature rows and 151,784 forward-label rows. Every feature row was marked `research_only=1`, `adjusted_returns_allowed=0`, `scoring_allowed=0` and `backtest_approved=0`; every forward-label row was marked research-only and not scoring-eligible. The report metadata showed zero distinct dates for the forward-label artifact, so row count alone does not establish valid label chronology.

The same sanitized report lists 48,902 corporate-action rows and 48,059 date-gap rows in review queues. These are candidate rows extracted from earlier reports, not independently verified events or gaps. The report explicitly says internal QA passed but corporate-action economics/licensing, calendar explanations, return semantics and point-in-time tradability remain open.

A separate earlier diagnostic of a then-current `run_tsetmc_acceptance_pipeline.py` discovered 47 instruments, quarantined all 47 and emitted zero features/labels. Do not repeat that exact run blindly. Before executing the merged PR #14 runner, compare its exact commit, discovery rules, corpus root and manifest against that diagnostic and the 1,220-history inventory; use one trusted local run only after the Runner gate is satisfied.

### Current decision

- No candidate currently passes the complete source-acceptance gate for investment scoring.
- TSETMC is the first local technical acceptance workload, not an accepted investment dataset.
- World Bank and CODAL can only contribute low-frequency macro or event context after point-in-time semantics are resolved; neither replaces price history.
- Nerkhsanj IQD, silver and Tether remain excluded from feature generation; Bitcoin remains flagged for coverage.
- No source status, production-approval flag, ranking gate or scoring gate was changed.
- The next empirical blocker is not another provider probe: it is trusted access to the owner's local corpus, followed by review of the already-recorded extreme Stage 4 fold and a locked, permissioned evaluation.

## Next execution order

1. Keep the current integration branch at its verified head; PRs #7, #9, #13, #14, #16, #17 and #18 are already merged into #6. Do not merge #6 into `main` without explicit owner approval.
2. Do not repeat the parked GitHub-hosted TSETMC request (#8), the Binance HTTP 451 route, or GDELT's HTTP 429 request without a materially changed acceptance question and a permitted environment.
3. After the local Runner trust boundary is satisfied, run the integrated offline TSETMC pipeline on the owner's designated corpus and review quarantined instruments; do not access raw local data through an untrusted workflow.
4. Attribute the previously recorded extreme Stage 4 six-month fold using the same dataset hash and code/config provenance. Do not inspect or tune against the locked final holdout.
5. Resolve rights, exact series identity, units, timestamp/publication availability, historical continuity, corporate actions and lawful independent reconciliation in the priority order above.
6. Run a locked chronological evaluation only on permissioned, representative data; report net returns, costs/slippage, turnover, drawdown, baseline comparisons, currency assumptions and uncertainty.
7. Keep all source approval, ranking and scoring flags fail-closed until every relevant data and empirical gate is independently satisfied.
