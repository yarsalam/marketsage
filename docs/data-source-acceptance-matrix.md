# MarketSage — data-source acceptance matrix

**Checkpoint date:** 2026-10-20  
**Release posture:** candidate/research-only. No source in this matrix is approved for production scoring.  
**Workflow:** implement → identify source/series contract → automated tests → bounded live evidence → history/units/reconciliation/rights review → private staging smoke → explicit review → merge.  
**VPN rule:** before any foreign live-source request, tell the project owner to enable VPN. Iran providers TSETMC/CODAL/Tindex use VPN off. Never mix them in one probe batch.

## Acceptance matrix

| Market/data family | Primary candidate(s) | Secondary/source caveat | Current evidence | Acceptance gate before scoring |
|---|---|---|---|---|
| Iranian listed equities/funds | TSETMC daily history and instrument search | CODAL supports filing/event discovery, not replacement market prices | TSETMC/CODAL bounded probes returned responses; adjusted-price candidate path exists for TSETMC | Complete instrument master and identity; raw vs provider-adjusted OHLC; corporate-action dates; suspended/delisted symbols; missing-session coverage; independent reconciliation and collection rights |
| Gold/coins | Tindex enabled precious-metal indicators; Nerkhsanj archive is a publisher-announced candidate | StreamData is vendor-supplied, not free; TGJU automated collection is not approved | Tindex unit/account reconciliation remains open; Nerkhsanj has not been live-probed and claims archive history since 2010 | Keep 18K gram gold, 24K, melted gold and each coin as separate series; confirm unit, currency, quote convention, timestamps, history overlap and rights; quarantine the AYAR violation pending vendor/source evidence |
| Free-market USD | Tindex current-rate/indicator candidates; Nerkhsanj archive candidate may supply local free-market FX history | World Bank is macro only, not a daily FX source; TGJU remains candidate-only | Prior Tindex current snapshot was received; Nerkhsanj has not been live-probed | Explicit free/official market definition; Rial/Toman/Toman conventions; timestamp and history semantics; independent overlapping-date reconciliation; rights and missingness |
| Crypto spot | Binance public Spot klines (venue/pair-specific) | Yahoo Finance is a global research proxy; seller BTCUSDT is not a free source and rights remain unverified | Binance probe failed at HTTPStatusError; root cause is not established | With VPN on, diagnose once via a bounded probe; freeze pair/venue/quote currency; audit complete candle window, partial candles, duplicates/gaps, fees/slippage, and terms. Never call BTCUSDT a universal USD price |
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

## Tindex contract correction and Nerkhsanj candidate (2026-10-20)

- Current [Tindex developer docs](https://tindex.app/en/developers/) state the Free tier quota is 1 request/minute and 100 successful requests/day, with one active token per account. This supersedes the stale 3/minute and 300/day settings from earlier onboarding notes. The guarded local client now enforces a process-wide rolling minute and in-memory daily success budget, but it cannot see other hosts/processes sharing that account. Do not run concurrent jobs.
- Current public docs define currency-rate values as Toman per quoted unit and say Markets & Indicators values are Toman since 2026-07-20. Keep the normalized unit unconfirmed until a fresh account payload is compared with an independent lawful reference. The Tindex candles/history endpoint is capped at about 100 days, insufficient alone for the six-month horizon.
- Nerkhsanj was added as a discovery candidate based on publisher announcements: `https://nerkh.jahankhahan.shop/data/rates.json` is said to contain daily history since 2010 for selected Iranian FX/gold/coin series. No live access, schema, data lineage, license, attribution, coverage or accuracy has been verified. Before the first live request, explicitly remind the owner to turn VPN ON; one bounded archive request only, never per-record `/calc` polling. Source remains unapproved.
- Latest Tindex quota code/runner changes must pass CI on the exact PR heads before live tests or staging.

## Next execution order

1. Check PR #6 and PR #13 separately; never merge their different base branches together implicitly.
2. Run the exact latest CI-green commit in private staging after proxy/authentication and rollback gates are met.
3. For data: complete TSETMC adjustment sample, then foreign-source Binance diagnosis with VPN on; preserve sanitized evidence only.
4. Select and formalize fixed-income and social/news-labelled benchmark sources only after deciding the required data contract and use rights.
5. Review each evidence pack before making a narrowly scoped source-registry approval change. Do not enable global ranking as a side-effect.
