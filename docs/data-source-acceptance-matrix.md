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
| 1 — Iran price-history path | TSETMC equities/funds | Best current engineering path for an Iran-market sample because the offline integrated acceptance pipeline is implemented. **Not accepted**: the owner's 1,220-instrument local corpus has not been run through it in this environment; rights, raw/adjusted semantics and independent event reconciliation remain open. | Run the offline pipeline only after the trusted local Runner gate; review instrument identity, event families, missing sessions, price semantics, and lawful independent references. |
| 2 — Low-frequency macro context | World Bank Indicators | Candidate for annual macro context only; not a daily market-price substitute. Observation year is not release/availability time and revisions may create look-ahead. | Capture series definition, unit, release/vintage availability and revisions; preserve annual frequency and align only after a point-in-time rule is documented. |
| 3 — Issuer events | CODAL | Discovery adapter exists, but retrieval time cannot stand in for publication time and original/corrected filings are not yet linked. | Reconcile original, amendment and publication timestamps against source documents; establish historical replay and use terms. |
| 4 — Local multi-asset archive | Nerkhsanj | **Research-excluded pending remediation.** The owner-reported audit flagged 182 adjacent moves >=20% (48 >=100%), concentrated in IQD, silver and Tether; IQD has a 373-day maximum gap and silver/Tether/Bitcoin have gaps up to 84 days. No raw files were re-audited here. | Resolve exact key identity, scale/unit, upstream lineage, attribution and commercial/model-use rights; compare overlapping dates against a lawful independent source. Keep IQD/silver/Tether out of features and Bitcoin as a coverage warning meanwhile. |
| 5 — Current Iran indicators | Tindex | Account-scoped candidate only. The documented latest-100-day candle history is shorter than the six-month horizon; 1 request/minute and 100 successful requests/day are shared account limits. | Do not use as a standalone six-month price history. Reconcile one authorized account payload per selected series to an independent reference, and document rights and actual account-level access. |
| 6 — Global proxy histories | Yahoo Finance | Existing captures may support exploratory plumbing only; unofficial access/terms, adjustments, survivorship and point-in-time availability are unresolved. US ETFs are not a representative Iran universe. | Reuse existing captures; do not redownload without a changed acceptance question. Verify symbol mapping, adjustments, terms and historical availability before any performance claim. |
| 7 — Venue-specific crypto | Binance Spot | Iran-network HTTP 451 is a blocked route. Do not bypass it or repeat the same blocked request. A separate small foreign sample is not multi-year coverage evidence. | Keep blocked for this environment; any future alternative requires its own lawful access, venue/pair identity, history, fees and rights review. |
| 8 — News discovery | GDELT DOC | Adapter is research-only; prior HTTP 429 remains in cooldown. First-seen/index time is not publisher publication time. | No repeat probe until a materially changed acceptance question and deliberate request budget; verify original publisher/time and a labelled Persian/English event set. |
| 9 — Macro vintages | FRED/ALFRED | Adapter exists but key/access was unavailable in the prior environment. Observation/vintage dates are not exact intraday release times. | Keep unprobed until secure key/network access is available; document series-specific release calendars and vintage semantics. |
| 10 — Vendor and unverified local feeds | StreamData, TGJU, Iran official macro portals, fixed income and social signals | No accepted series. StreamData is vendor-supplied rather than free; TGJU automated rights are unapproved; official macro machine-readable coverage and fixed-income contract are not established; no social provider/labelled benchmark exists. | Resolve contracts/rights, exact series definition, units, timestamps, history and independent reconciliation before implementation or collection. |

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
