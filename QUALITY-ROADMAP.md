# MarketSage Iran Equity Adjustment — Quality Roadmap

**Updated:** 2026-11-26  
**Scope:** فولاد، وغدیر، پارسیان as the three-symbol diagnostic pilot; later expansion to the full eligible TSETMC instrument universe.  
**Status:** research and engineering roadmap only. No adjusted series or investment output is approved for production by this document.

> This is a compact working checklist, not a new governance framework. A box is checked only when there is an inspectable artifact, reproducible test, or reviewed evidence supporting it. “CLI works”, “the run completed”, and “matches one provider output” are not, by themselves, acceptance.

## 1. Objective

Repair and generalize the existing MarketSage acquisition, event-reconciliation and adjustment engines rather than replace them prematurely.

The target system must:

1. reuse existing work and preserve the historical evidence already acquired for the three pilot symbols;
2. separate common rules from instrument-specific identity, history, event terms and source coverage;
3. accept new observations and detect additions, corrections, removals, identity changes and source-schema changes;
4. reconstruct only events whose terms, chronology and economic relationships are sufficiently evidenced;
5. detect unknown or contradictory cases and quarantine the affected instrument/range instead of guessing;
6. produce reproducible, versioned raw, price-basis-adjusted and total-return datasets with full provenance;
7. expand automation by adding reviewed event handlers and regression cases, without silently changing old results.

The goal is not one static formula that predicts every issuer action. The goal is a stable shared framework with versioned data contracts, event-family handlers, instrument-specific metadata, explicit review gates and a controlled exception path.

## 2. System boundaries — do not conflate these responsibilities

| Layer | Responsibility | Must not do |
|---|---|---|
| Instrument/Security Master | Canonical symbol, primary InsCode, related identifiers, market/listing lifecycle and effective dates | Treat names or related IDs as proof of identity |
| TSETMC acquisition and adapter | Preserve daily history, A0/A1 charts, PA, SC, instrument/status observations and response metadata | Infer issuer event terms or silently repair observations |
| CODAL acquisition and document adapter | Discover and preserve original letters, attachments, amendments and document chains | Treat a search result or title as a verified corporate action |
| Market-data QA and revision detection | Validate schema, dates, values, duplicates, gaps, no-trade states, revisions and source identity | Convert a market-state change into an adjustment factor |
| Event discovery and reconciliation | Link provider observations to issuer documents, distinguish same event/components/amendments/reversals and establish effective chronology | Join events solely by nearby dates or similar ratios |
| Canonical corporate-action ledger | Store verified event terms, dates, components, evidence, relationships and review state | Promote unknown/provisional facts automatically |
| Adjustment calculation | Apply the correct, versioned method to eligible event components | Download data, infer event terms or mix PA and SC indiscriminately |
| V6 discovery/review | Detect candidates and maintain append-only human decisions/manual-event records | Claim to be the final OHLCV adjustment engine |
| Orchestrator | Coordinate runs, hashes, stage state, retry/resume, dependency invalidation and publication | Reimplement any collector, reconciler or adjustment formula |

The repository currently contains several distinct things that have sometimes been called “engines”: main-branch candidate TSETMC/CODAL adapters, local acquisition scripts, the V6 discovery/review package, multiple historical adjustment-engine versions, and a separate offline TSETMC acceptance pipeline. Their names are not proof that they have the same inputs, formulas or outputs. The next audit must map each exact implementation and output to its code version.

## 3. Non-negotiable data and calculation principles

### 3.1 Identity and instrument lifecycle

- InsCode is a string/integer identifier, never a JavaScript floating-point number.
- A symbol name, ticker, ISIN, folder name or related InsCode is not sufficient to establish identity.
- Maintain a canonical primary identity plus dated, evidence-backed identity/alias relationships. Do not silently merge predecessor/successor instruments.
- An identity conflict blocks calculation for the affected instrument/range; it must not be fixed by substituting a convenient ID.

### 3.2 Immutable source history and revisions

- Raw provider responses, CODAL originals, attachments and earlier snapshots are immutable.
- Every acquisition records source/endpoint, exact instrument identifier, parameters, retrieval time, response status, byte/decoded hashes, schema/version and coverage.
- New data is not necessarily an appended row: an old date or filing can be corrected, removed, replaced or reclassified.
- Compare source snapshots semantically as well as by file hash. Record added, modified and removed records with the original and new snapshot references.
- A correction to a historical event invalidates the dependent adjustment interval and may require rebuilding all earlier prices affected by the backward factor chain.
- Never overwrite the last accepted output. Build a new isolated version, validate it, and only then mark it current.

### 3.3 Keep dates distinct

Preserve, separately, publication/update date, meeting date, issuer decision date, eligibility/record date, ex-date if stated, first affected trading session, rights period dates, subscription/allocation date, legal registration date, provider dEven, exchange session date and local retrieval timestamp. These dates are not interchangeable.

### 3.4 Keep event families and price bases separate

- Keep raw prices, provider PA tuples, provider SC rows, issuer terms and reconstructed factors in separate fields/ledgers.
- A PA tuple is a provider observation, not proof of the issuer event or its economic terms.
- Old/new share counts alone do not distinguish free capital, cash/receivables rights, mixed increases, reversals or temporary share-count round trips.
- Do not infer “free capital increase” merely because an SC row has no same-date PA row.
- Do not combine, multiply, suppress or deduplicate PA/SC rows solely by a ±N-day window. Date proximity is a candidate-search aid only.
- Apply a price effect once per verified economic component. SC may affect share-count/volume normalization; a price effect from a capital event requires its own evidenced economic terms and chronology.
- Cash dividend, capital increase, rights subscription, split/reverse split, merger/conversion and in-kind distribution require event-family-specific treatment. Mixed and sequential components must remain distinguishable.
- Price-basis adjustment and total return are different output products. Total return requires verified distributions, entitlement, payment/reinvestment policy and dates; it must not be inferred from PA alone.
- A missing trade, stale pClosing, suspension, reopening, price limit, holiday or ordinary market return is a market/data-state fact, not automatically a corporate-action factor.

### 3.5 Unknown and exceptional cases

Use explicit states such as DISCOVERED, DOCUMENT_SEARCHED, TERMS_VERIFIED, EFFECTIVE_DATE_VERIFIED, RELATIONSHIP_VERIFIED, FACTOR_RECONSTRUCTED, MARKET_RECONCILED, CONFLICT, UNKNOWN, REJECTED and QUARANTINED.

- Unknown event type, unknown schema, unexpected units, invalid identity, unresolved event relation or conflicting sources must fail closed.
- Quarantine should be as narrow as evidence permits: instrument × event × affected historical interval, not automatically the whole market.
- Preserve the last verified series while the new candidate is blocked.
- No silent fallback from missing adjusted data to raw data, no forward-fill, no price-gap inference and no silent deletion of duplicates.

### 3.6 Reproducibility

Each output version must identify:
- exact code commit and dirty/clean state;
- engine/adapter and rule versions;
- Python/runtime and dependency versions;
- exact configuration and symbol identity;
- all input artifact paths/IDs, byte hashes and semantic fingerprints;
- event/ledger/decision version and reviewer references;
- output hashes, QA results, quarantined ranges and limitations.

The same code, configuration and identical inputs must reproduce the same calculation values. Timestamps and run IDs may differ, but they must not alter the mathematical result. Every factor must be traceable to source values, units, formula, direction, event IDs and dates.

## 4. Variables to inventory before generalization

| Variable family | Common contract fields | Instrument-/event-specific facts to preserve |
|---|---|---|
| Identity | primary ID, ticker/name, ISIN, market, instrument type | InsCode lifecycle, predecessor/successor IDs, name/market changes |
| Daily market state | dEven/session date, OHLC, last, previous close, volume, value, trade count | suspension/no-trade/reopening history, price limits, listing start/end, stale fields |
| TSETMC events | source route, raw tuple, provider date, exact ID, payload hash | PA/SC count, repeated/reciprocal/temporary rows, event-specific field semantics |
| CODAL documents | TracingNo, issuer, symbol, letter type, publication/update time, original file hash | issuer wording, amendment chain, component amounts, rights terms and chronology |
| Corporate-action economics | event family, component, old/new shares/capital, units, dates | DPS, retained earnings/reserves/cash/receivables, nominal/subscription price, rights treatment, exchange ratio |
| Data quality | schema version, row counts, duplicates, gaps, missing/invalid values, hashes | source coverage and reliability by instrument and period |
| Adjustment policy | output series type, formula version, factor direction, anchor and rounding | event-specific calculation inputs, linked events, unresolved assumptions and tolerance |

A field is “common” only if its meaning and units are stable across instruments and time. A similar column name is not enough. Each normalized field needs a source mapping, semantic definition, unit, null/zero meaning, date semantics, identity rule and validation test.

## 5. Three-symbol diagnostic baseline already present in repository evidence

The following are historical diagnostics from the offline run 20261112T194429Z, not a fresh acquisition or an acceptance decision. The audit states network_access=false, all_source_inputs_unchanged=true, and both its event-coverage and factor-diagnostic self-tests passed.

| Symbol | Primary InsCode | Candidate daily rows | TSETMC A1 chart rows | PA rows | SC rows |
|---|---:|---:|---:|---:|---:|
| فولاد | 46348559193224090 | 4,680 | 4,266 | 23 | 12 |
| وغدیر | 26014913469567886 | 5,688 | 5,383 | 25 | 7 |
| پارسیان | 9481703061634967 | 3,866 | 3,539 | 18 | 9 |

On common dates in that capture, the raw candidate fields matched the TSETMC a=0 chart exactly for each compared OHLC/last/volume field. This validates that particular raw mapping and common-date comparison; it does not validate event completeness or adjusted prices. The candidate histories had respectively 414, 305 and 327 dates not present in the corresponding chart capture, which still needs explicit calendar/coverage explanation.

The event-feed comparison used a ±7-calendar-day window only as a diagnostic candidate matcher. It is not a legal event join or a deduplication rule:

| Symbol | TSE Client event rows | PA matches within ±7d | Same-date PA matches | SC matches within ±7d | Same-date SC matches |
|---|---:|---:|---:|---:|---:|
| فولاد | 31 | 23/23 | 7 | 12/12 | 0 |
| وغدیر | 15 | 13/25 | 6 | 3/7 | 0 |
| پارسیان | 18 | 12/18 | 5 | 7/9 | 0 |

This immediately shows that one global “same date” join does not work, while a proximity join is not safe enough to become the event identity rule. Each match still needs exact identity, event relationship, date chronology and economic evidence.

A separate 2026-11-12 factor-shape diagnostic against the TSETMC a=1 chart reported:
- فولاد: current candidate variant median error 80.48%, p95 91.02%; an exact-date PA/SC suppression experiment reduced this to median 0.41%, p95 7.34%.
- وغدیر: current candidate variant median 6.61%, p95 30.99%.
- پارسیان: current candidate variant median 2.40%, p95 4.81%.

These numbers are diagnostic only. A different 2026-11-18/19 validation record compares another adjustment output with TSE Client 2.27.6 F7 and reports different errors (فولاد median 0.17%, p95 2.23%; پارسیان 2.40%, 4.80%; وغدیر 6.60%, 63.65%). These are not interchangeable benchmarks: the reference fields, calculation versions, snapshots, anchors and adjustment semantics must first be reconciled. Do not declare the engine correct or incorrect from a single metric without reproducing the exact inputs and method.

### Known symbol-specific diagnostic clues

- **فولاد:** strong PA-to-TSE-Client candidate coverage, but PA and SC dEven dates often differ by one or more sessions. A historical acceptance record marked B3 as passed against TSE Client F7, yet retained a high-priority CODAL funding-source blocker and a total-return blocker. Some prior logic treated SC-only events as free increases; that assumption must be independently verified for each event.
- **وغدیر:** the 1390/2011 case is a mixed event, not a simple bonus issue. Existing evidence records DPS of 500 Rial and an increase from 6.075bn to 12bn shares, funded by retained earnings, reserves and cash/receivables components; rights-use, public-subscription and registration dates continue later. The provider feed contains multiple 2011 tuples including a reciprocal/display-like tuple that must not all be multiplied. A 2024 SC-only increase (72bn to 216bn) was previously missed and later surfaced in V2 work; it must be linked to its CODAL evidence before being treated as a verified price event. A 2010-04-21 candidate remains quarantined in the existing report.
- **پارسیان:** the exact primary InsCode is 9481703061634967. An earlier apparent mismatch was attributed to JavaScript Number precision loss; all 18 PA and 9 SC raw rows were later checked against the exact decimal token. Keep IDs as strings/BigInt. CODAL re-verification and several PA/SC-to-TSE-Client links remain unresolved.

The three-symbol evidence demonstrates a mixture of shared structures and issuer-specific event economics. It does not yet prove that any current engine version accepts the full three-symbol history.

## 6. Existing implementation and GitHub reuse audit

Do not merge whole historical branches just because a PR was marked merged into its own feature base.

| Existing work | Verified repository status | Disposition |
|---|---|---|
| Main-branch tsetmc_adapter.py, codal_adapter.py, source_registry.py, source_acceptance.py | Present on main; candidate/quarantined ingestion and source gate, not the local full acquisition + adjustment chain | Reuse as the source-normalization/temporal boundary where appropriate; do not mistake them for the complete collectors |
| PR #10 — TSETMC adjusted-history validation | Merged into feature/iran-live-data-dashboard, not directly into main; that branch is 238 commits ahead and 14 behind main in comparison | Salvage selected adapter/tests only after exact contract review; no whole-branch merge |
| PR #14 — offline integrated TSETMC acceptance pipeline | Merged into feat/tindex-free-data-connector, not directly into main; that branch is 415 commits ahead and 14 behind main in comparison. Its documented analysis suite reported 277 tests passed | Reuse as a pre-adjustment data-quality/evidence gate if the exact code/tests are still valid; it does not calculate/approve corporate-action factors and was not run against the owner's full 1,220-instrument corpus |
| PR #82 — event investigation notebook and adjustment standard | Closed unmerged; 116 commits and 454 changed files in its final branch | Preserve as research source; selectively reuse methodology and issuer-specific evidence, not the entire branch |
| PR #83 — governance cleanup | Merged to main; removed bulky governance documents | Keep this roadmap intentionally lightweight; do not recreate multiple overlapping governance systems |
| PR #86 — cleaned evidence plus daily orchestrator | Open Draft, 11 commits, 253 changed files; current branch was ahead of main by 11 and behind by 0 when compared | Keep Draft/unmerged while the existing local acquisition and adjustment implementations are inventoried and connected. Its reconcile.argv and adjustment.argv are deliberately empty; it is not an end-to-end engine |

Historical PR/branch “merged” status is not proof that a feature is present on main. Use commit-level selective porting after base comparison. Do not force-push, delete recovery branches, merge these PRs, or overwrite local work as part of this roadmap.

## 7. Phased execution checklist and gates

Status key: [x] verified for the stated limited scope; [~] partial/diagnostic; [ ] not yet demonstrated.

### Gate 0 — Scope and safety baseline

- [x] Use فولاد،وغدیر،پارسیان as the initial diagnostic cohort.
- [x] Reuse existing source captures and prior work; do not restart acquisition without a demonstrated gap.
- [x] Keep raw artifacts, documents and prior outputs immutable.
- [x] Keep adjustment research-only; no scoring/backtest/production activation.
- [~] One lightweight roadmap is created; exact implementation inventory and per-engine ownership are still pending.

### Gate 1 — Exact code and artifact inventory (next)

- [ ] Inventory all local engine versions, package roots, scripts, CLIs, tests and output formats (including V2/V4/V5/V6 and any legacy builder).
- [ ] Map each historical output/manifest to its exact producing code commit, version, configuration and input hashes.
- [ ] Compare local working-tree files, main, PR #86, PR #82 and the old PR #10/#14 feature branches without wholesale merging.
- [ ] Build a per-symbol input manifest for raw TSETMC, CODAL originals/attachments, provider events, identity, status/calendar data, ledgers and historical outputs.
- [ ] Explain every missing file, mismatched identity, stale snapshot, duplicate, gap and conflicting capture.

**Gate 1 exit:** no implementation is selected as canonical until its exact code, inputs, outputs and tests are traceable.

### Gate 2 — Variable and contract matrix

- [ ] Freeze the common instrument, daily-observation, source-document, provider-event, canonical-event and adjustment-output schemas.
- [ ] Document field semantics, unit, null/zero meaning, calendar/timezone, date and identity meanings.
- [ ] Separate generic fields/rules from symbol-specific identity history, source coverage, event terms and unresolved relations.
- [ ] Define event relationship states: same event, component of, amends, supersedes, reverses/withdraws, temporary/round-trip, independent, unrelated or unresolved.
- [ ] Define separate raw, price-basis-adjusted and total-return output contracts.
- [ ] Define data-revision invalidation: which changed inputs require a local interval rebuild and when a full-history replay is mandatory.

**Gate 2 exit:** all three symbols can be represented by the same schemas without discarding their specific facts.

### Gate 3 — Diagnose the existing engines on identical frozen inputs

- [ ] Run each extant engine version offline against the same three-symbol snapshot manifests.
- [ ] Compare event detection, event linking, factor selection, factor direction, date convention, output rows and quarantine decisions.
- [ ] Reproduce TSE Client F7 and TSETMC A1 comparisons separately, with exact version/input/anchor/field semantics.
- [ ] Explain the 2011 Vaghdir mixed event and reciprocal tuples; the 2024 SC-only increase; all unresolved 2010/2012/2013 Vaghdir candidates; and outstanding Foolad/Parsian events.
- [ ] Explain why each engine passes/fails per symbol and per affected date interval. Do not accept only symbol-level averages.
- [ ] Identify duplicated, contradictory or unsafe rules (including any SC-only-to-free-capital assumption, same-day suppression, date-neighborhood joins and stale daily-file selection).

**Gate 3 exit:** a root-cause matrix names the exact file/function/rule, the affected symbols/events, the evidence and the required correction. “Engine does not work for Vaghdir” is not a sufficient diagnosis.

### Gate 4 — Generalize only proven rules

- [ ] Refactor shared ingestion/normalization/identity contracts without changing source economics.
- [ ] Implement event-family calculation handlers only where issuer terms and date semantics are established.
- [ ] Keep PA provider observations, SC share-count observations, issuer terms and reconstructed factors separate.
- [ ] Support mixed/sequential components without applying a price effect twice.
- [ ] Make new event types/data schemas become explicit unsupported/quarantined cases until a reviewed handler and tests are added.
- [ ] Preserve symbol-specific overrides only when backed by evidence and versioned configuration; never fork a new engine per symbol by default.

**Gate 4 exit:** the same engine code handles all three symbols; only verified metadata, evidence and event inputs differ.

### Gate 5 — Revisions, unknowns and reproducibility

- [ ] Test added, modified and removed daily records and historical CODAL amendments.
- [ ] Test ID changes, source schema changes, duplicate/reciprocal PA, temporary SC round trips, no-trade/stale records and halts/reopenings.
- [ ] Test unknown event types and conflicting documents fail closed and produce an actionable exception queue.
- [ ] Test failed/resumed/retried runs cannot overwrite prior successful source or adjustment outputs.
- [ ] Verify identical frozen inputs/config/code reproduce identical calculation values and matching semantic output hashes.
- [ ] Verify corrected historical events invalidate every dependent earlier row, not only the latest session.

**Gate 5 exit:** every output can be reproduced and explained; unknowns remain visible and do not contaminate verified ranges.

### Gate 6 — Test efficiency and three-symbol acceptance

- [ ] Replay the full available history for all three symbols offline; use event-complete regression cases, property/invariant tests, pairwise combination coverage and targeted high-risk combinations.
- [ ] Validate every known event row and its relationships; test all unresolved candidates as negative/quarantine cases.
- [ ] Set tolerances by event family, price tick/scale, source rounding and reference semantics—not one arbitrary global percentage.
- [ ] Require separate checks for raw-history integrity, event completeness, event-term correctness, effective dates, factor arithmetic, official/provider chart comparison and volume treatment.
- [ ] Publish per-symbol and per-interval acceptance reports with explicit exclusions and remaining unknowns.
- [ ] Do not mark a symbol complete while any unresolved event can change its accepted historical interval.

**Gate 6 exit:** فولاد، وغدیر and پارسیان all pass the same acceptance protocol, or their rejected/quarantined intervals and blockers are precisely documented.

### Gate 7 — Controlled expansion to all eligible symbols

- [ ] Build the as-of instrument universe and historical security master; do not assume the three pilots represent all instrument types.
- [ ] Run broad read-only discovery and data-quality screening first.
- [ ] Group symbols by actual data/event characteristics and failure modes; sample representative and worst-case members.
- [ ] Expand by cohorts only after cohort-specific pass criteria; retain a per-symbol exception queue.
- [ ] Measure automated coverage, human-review rate, unresolved/unknown rate, revision frequency, runtime and false-accept rate.
- [ ] Add a reviewed rule/test when a new pattern is understood; preserve the old behavior and regression fixtures.

**Gate 7 exit:** automatic coverage grows from evidence and regression tests, not from loosening checks or assuming every symbol resembles فولاد.

## 8. Immediate next work order

1. Complete Gate 1: inventory every local adjustment implementation/version and all three symbols' current artifacts. Do not write another adapter yet.
2. Build the engine × symbol × output comparison matrix from the existing artifacts.
3. Use the exact Vaghdir 2011 mixed action, Vaghdir 2024 SC-only candidate, and the largest unresolved PA/SC mismatches in Parsian/Foolad as high-value diagnostic cases.
4. Select one canonical implementation only after Gate 3 root causes are evidenced.
5. Fix the existing engines incrementally, then rerun the frozen three-symbol replay before any full-universe rollout.

**Current release boundary:** no daily scheduler activation, no automatic ledger approval, no production scoring/backtest, no adjustment-series promotion and no wholesale PR merge until the relevant gate has passed.


## 9. Operating correction — event-centred reconciliation is the primary workflow

This section clarifies and takes precedence over any interpretation of the earlier diagnostic tables as a proposal to compare raw price differences first.

**TSETMC observations must not be interpreted in isolation.** The normal workflow is to acquire TSETMC and CODAL evidence for the same instrument/history window, establish issuer events and market operating states, then interpret the TSETMC observations in that documented context. Repeated manual inspection of unexplained price gaps is not the operating model.

### 9.1 Parallel acquisition, joined interpretation

Acquisition may run in parallel because the sources are independent:

1. **TSETMC capture:** immutable daily observations, raw/adjusted chart captures where available, PA and SC feeds, instrument identity/security master and instrument/trading status observations.
2. **CODAL capture:** issuer disclosures across the full available history, original letters and attachments, publication/update metadata, linked notices, amendments, corrections, withdrawals and registration/subscription documents.
3. **Market-calendar/status capture:** official exchange sessions, holidays, closures, suspensions, reopening and no-trade context from the appropriate market sources.

The outputs are not interpreted independently. They are joined using canonical instrument identity, document/event relationships and verified chronology. A missing CODAL filing is not proof that no event occurred; a TSETMC PA/SC row is not proof of issuer terms.

### 9.2 Build the event timeline before factor calculation

For each instrument, produce a dated timeline containing:
- original CODAL document and amendment chain;
- issuer decision and all economic components;
- record/eligibility date and ex-date where established;
- rights, subscription, allocation and registration stages where applicable;
- first affected exchange session, established using market-session and instrument-status evidence;
- TSETMC PA/SC raw observations associated with the candidate event, without silently merging them;
- pre-event and post-event traded observations, no-trade/stale observations, suspension and reopening context;
- evidence references, source hashes, unresolved claims and confidence/review state.

CODAL establishes issuer decisions and economic terms. It does not, by itself, establish whether the exchange was closed, whether the symbol was suspended, or which session was the first affected trading session. Those require market-calendar/status evidence.

### 9.3 Classify the cause before explaining a price change

Every relevant interval or apparent discontinuity should be classified into one or more evidence-backed categories:

| Cause category | Main evidence | Treatment |
|---|---|---|
| Exchange holiday / non-session | Exchange calendar | No price factor; no synthetic observation |
| Instrument suspension / reopening | Official instrument-status and market observations | Preserve state and first real traded session; no automatic corporate-action factor |
| No trade / stale close | Trade count, last traded price, previous close and daily fields | Do not treat stale pClosing as an executed price |
| Cash dividend / distribution | CODAL AGM decision and distribution terms | Apply only the verified price-basis or total-return policy |
| Capital increase | CODAL decision, funding components, rights and registration chain | Calculate each verified economic component; do not assume all share-count growth is free |
| Rights / subscription / allocation | CODAL notices and related security/market evidence | Track rights lifecycle separately; apply only a verified economic method |
| Split / reverse split / conversion / merger / spin-off | Original legal/issuer documents and market implementation evidence | Use a dedicated event-family handler |
| Ordinary market repricing | Traded market observations without an evidenced corporate/operational event | Retain as market return; do not adjust |
| Provider correction / backfill / schema change | Versioned TSETMC snapshots and semantic diff | Revalidate source observations and invalidate dependent outputs as necessary |
| Unknown / conflicting cause | Missing or contradictory evidence | Quarantine the affected interval and open a targeted exception |

A daily gap is a symptom to classify, not a cause. A price discontinuity alone must never create an event or factor.

### 9.4 Reconcile TSETMC only after the event is understood

For every verified or candidate event, compare:
- CODAL economic terms and each funding component;
- the event's chronology and first affected trading session;
- TSETMC PA raw tuples, including reciprocal, repeated, correction-like or display-like records;
- TSETMC SC old/new share counts and any temporary/round-trip behavior;
- pre/post market observations, traded close versus stale close, previous close, trade count and volume;
- independent chart/provider output, after its adjustment definition, field mapping, units, rounding and anchor are established.

The reconciliation asks whether the observed market/provider behavior is compatible with the documented event and its timing. It does not decide the issuer event type from a matching ratio. Date proximity is permitted to generate candidate links but cannot prove identity, causality, deduplication or correction.

### 9.5 Separate event discovery from unexplained residual detection

The primary pass is document/event-led across the full available history. A secondary residual pass finds:
- provider PA/SC records not explained by a known issuer event;
- CODAL events with no corresponding provider/market observation;
- market discontinuities not explained by a corporate event or market state;
- contradictory event chronology or economic terms;
- corrected/removed historical source records.

These become specific exception tasks with symbol, date range, event/document IDs, source snapshots, exact discrepancy and required evidence. Do not repeatedly compare arbitrary rows by hand when the same question can be expressed as a reusable event rule or test.

### 9.6 Event-centred calculation and invalidation

The adjustment engine consumes a reviewed event ledger and market-session mapping, not an unstructured list of price jumps. Each calculation step references:
- a canonical event/component ID;
- accepted source-document and source-payload hashes;
- verified economic inputs and units;
- event-family handler and formula version;
- first affected session and factor application convention;
- PA/SC records used as reconciliation evidence, not automatically as economic inputs;
- resulting factor, direction, scope and QA outcome.

When a CODAL amendment, corrected decision, changed market-effective session, TSETMC historical revision or identity change arrives, the dependency graph identifies every event and historical row affected. The system creates a new output version; it never overwrites the earlier raw capture or accepted result.

### 9.7 Practical three-symbol workflow

For فولاد، وغدیر، پارسیان, the next research runs should therefore proceed in this order:

1. inventory the already acquired CODAL documents and event ledgers for all three symbols; identify missing history and amendments before launching new downloads;
2. connect each documented issuer event to its dates, components and market-session implementation;
3. add the applicable TSETMC PA/SC and daily records to that event timeline;
4. identify which engine version currently handles that event and exactly what it calculated;
5. replay the existing engine on the same frozen inputs and compare the result with the event-specific expected economics;
6. record the root cause for each failure and add a regression case before modifying shared code.

Do not begin by downloading the same TSETMC data again or hand-reviewing every price gap. Reacquire only when a specific source-coverage or revision gap has been demonstrated.

**Gate consequence:** Gate 3 cannot pass merely because an engine reproduces a chart or matches provider ratios. It must demonstrate event-led classification, CODAL/market chronology, correct event-specific economics, safe handling of unknowns, and reproducible output for all three symbols.


## 10. Event-first tri-symbol investigation — initial evidence inventory (2026-11-26)

This section records the first inspection pass only; it is **not** the completed reconciliation.

### 10.1 CODAL-first status from currently imported evidence

- **Foolad:** current event ledger has 23 TSETMC price-adjust records and 12 SC/share-change records, but its rows are all labeled PROVISIONAL/existence-only and are not yet joined to a complete issuer-document timeline. The imported shared CODAL metadata index spans only 1388/01/01–1405/08/21 and is not evidence of full history; the user's estimate of >98% local Foolad evidence coverage remains a user-reported local-store estimate until a local manifest/coverage calculation is inspected. Older years—especially 1387—must be audited against the local evidence store and external archive/press, not presumed absent.
- **Vaghdir:** 25 PA + 7 SC rows. One event (2011) already has CODAL tracing 38805/59965 plus dividend tracing 38448, but is still provisional: capital source/terms need component-level reading, and the four PA rows require reconstruction as two economically distinct factors and two reciprocal/display records, not blindly multiplied. 2010-04-21 PA factor 0.8881 remains BLOCKED/NO_SOURCE. 2024-08-03 share change 72B→216B is a known CODAL registration lead, but original chain and financing/terms must be verified before the engine treats it as free.
- **Parsian:** 18 PA + 9 SC rows. The exact primary InsCode identity is verified for all captured feeds, but the imported event ledger remains TSETMC-only provisional. CODAL event coverage and original documents are not yet demonstrated by the imported files.

### 10.2 Immediate evidence priorities

1. Build an event-coverage matrix by symbol: every PA/SC row with source values, event date, identity, candidate relation, exact CODAL tracing(s), original/attachment/amendment state, effective/first-trading-session evidence, terms, confidence and disposition.
2. Inspect local owner-side CODAL inventory and manifests first, because the PR import may be incomplete and cannot establish what is locally held. Do not re-download already captured originals.
3. For gaps, targeted deep-search archive sources: issuer and exchange notices, official newspapers/announcements, reputable contemporary market publications, and accessible original scanned ads. Record source URL, publication date, archive/page, exact quoted facts, hash if locally saved, source rank and conflicts. Search is event-specific, not a blanket web scrape.
4. Reconcile the 3 market histories with official session/state evidence after the event timeline exists. The long-gap review already has unresolved cases: Vaghdir 173d and 121d gaps, Parsian largest 10d, and Foolad 43d in 1387. Foolad's gap has secondary reports suggesting suspension and reopening around 23 Shahrivar–5 Aban 1387, but one report conflicts with the observed 23 Shahrivar trade; primary exchange state evidence is still required. This is a market-state gap, not automatically a corporate action.
5. Only after the event ledger is reconciled, run engines V2/V6 and prior versions on the same frozen inputs; explain failures by shared-contract versus symbol-specific fields and event-family support. No engine result is accepted merely because it matches provider/chart output.

### 10.3 Cross-symbol differences already visible (hypotheses to verify)

- **Foolad:** PA feed coverage is complete against TSE Client's captured diagnostic rows (23/23 candidate matches), but SC feed and chronology are not same-date; dates shift by 1–3 sessions in several matches. The 1387 history/status gap and local CODAL evidence coverage need priority.
- **Vaghdir:** mixed 2011 dividend + capital action creates multiple PA records and reciprocal/display rows; the 2024 +200% SC-only event is a potential handler blind spot; one 2010 PA row remains source-blocked. PA matching to TSE Client is only 13/25 in the diagnostic.
- **Parsian:** primary InsCode was initially mishandled by JavaScript Number precision, now corrected to exact string/BigInt. PA/SC matching is partial (12/18 and 7/9) in the ±7-day diagnostic; this may reflect event-feed semantics/coverage rather than missing actions and must be investigated row-by-row.

### 10.4 Engine architecture direction (not implemented/approved yet)

Prefer a pipeline with explicit contracts and handlers:
- **Source Snapshot/Identity** → **CODAL Document Graph** (originals, amendments, attachments, withdrawal/correction chains) → **Canonical Event Components** (economic subcomponents, exact units, dates, provenance, confidence) → **Market Session/Instrument State Reconciliation** → **Independent Factor Calculation** → **Series Builder (price-basis and total-return separated)** → **QA/Validation/Quarantine** → **Versioned Publication**.
- Shared core owns stable contracts, identity precision, immutable snapshots, chronology graph, factor chain, invalidation/reproducibility and validation. Handlers own event-family logic (cash dividend; free/retained-earnings/reserve increase; cash/receivables rights; mixed increases; split/reverse; merger/demerger/conversion; spin-off/in-kind; rights lifecycle). Instrument adapters supply exact ID lifecycle, source coverage, calendar/status quirks and mappings.
- Unknown handler, ambiguous document relation, unresolved units or conflicting chronology must emit a review case and quarantine only the affected event/interval. New symbol support is earned through replayable fixtures and regression tests, not a symbol-name special case.

### 10.5 Status

- [x] Read the current PR-imported ledgers and shared event-coverage / market-gap audit artifacts.
- [x] Confirm current event feeds are still provisional and that no pilot symbol has final acceptance.
- [ ] Inspect full owner-side CODAL inventory and coverage manifest (not visible from GitHub-only context).
- [ ] Complete row-by-row PA/SC ↔ CODAL/other-source ↔ market-session reconciliation for all three symbols.
- [ ] Targeted deep-search and archive retrieval for each genuinely unsupported event, beginning with Foolad 1387 and Vaghdir 2010 / mixed 2011 / 2024.
- [ ] Run comparative same-input engine replay and identify general vs symbol-specific failure causes.
- [ ] Implement minimal reusable handler/contract corrections with tests; replay three symbols and quantify unresolved intervals.
- [ ] Expand to additional symbols only after pilot regression gates pass.


### 10.6 Targeted external search — Foolad 1387 (lead, not economic-event proof)
A first web search found contemporary 1387 press coverage about Foolad market suspension/price volatility, and BourseEye's 1387 price history confirms non-zero trade records around the long gap. The current search results do **not** yet identify a specific 1387 corporate-action notice or prove the user's remembered newspaper event. The 1387 lead is therefore split into two separate queues: (a) market-state chronology for the Sep–Oct 2008 gap, and (b) a corporate-action/issuer-notice search over the whole 1387 year. Do not treat the suspension story as the missing corporate action. Search archive candidates by year, company name, meeting, dividend, capital increase, rights, registration, and Gazette/company registry; then cross-check the user's local evidence store before acquiring anything.


### 10.7 Owner-side directory evidence and revised CODAL-first priority (2026-11-26)

The owner has now shown the actual local directory listing under `~/projects/marketsage/data/market-research/iran-equities/adjustment-evidence/`:

- **Foolad:** `event-ledger.csv`, `identity.json`, `source-register.csv`, `raw/`, `runs/`, `derived/`, `validation/`, scripts, and local `engine-v2` through `engine-v6` directories are present. No top-level `codal/` directory appeared in the shown listing. This is not proof that CODAL evidence is absent: it may be stored in `runs/`, `raw/`, shared evidence roots or another local archive. The owner reports that more than 98% of Foolad evidence is already available locally; treat this as a high-priority owner-reported coverage estimate to validate against actual manifests and file contents, not as an independently measured percentage.
- **Vaghdir:** `event-ledger.csv`, `identity.json`, `source-register.csv`, `raw/`, `derived/`, `diagnostics/`, `validation/`, scripts and a dedicated `codal/` directory are present. The imported branch visibly contains original CODAL PDFs 38803, 38805 and 40620 plus dated CODAL acquisition subdirectories. Inspect all originals, attachments, amendments and manifests before deciding whether any 2011/2024 chain is complete.
- **Parsian:** `event-ledger.csv`, `identity.json`, `source-register.csv`, `raw/`, `derived/` and `validation/` are present. No top-level `codal/` directory appeared in the shown listing; inspect nested/local/shared stores and manifests before concluding CODAL coverage is missing.

The owner reports a practical Foolad finding: more than 90% of the observed adjustment gaps can be explained by CODAL capital-increase notices and the preceding/following issuer-document chain (including extraordinary-meeting decisions). This is a strong operational hypothesis that changes search priority, but it is not yet a measured cross-symbol statistic. The first pass must therefore prioritize capital-increase lifecycles and their linked documents rather than generic news searches:

1. proposal/explanatory report and audit opinion;
2. board recommendation and statutory/audit reports where available;
3. extraordinary general meeting decision/approval;
4. regulatory permission/registration notices where applicable;
5. subscription-rights notice and subscription window;
6. extension, correction and unused-rights notices;
7. result/allocation notices;
8. final legal registration of the capital increase.

Treat these as linked stages/components of one canonical capital-action case, not as eight independent price adjustments. Preserve each document and date, distinguish proposed/approved/implemented amounts, identify each funding source (retained earnings, reserves, cash, receivables, mixed), and establish the first affected trading session independently. Search newspapers, official gazettes/company-registration records and other archives only for stages or terms not evidenced by CODAL or for historical periods where CODAL coverage is incomplete (including the known Foolad 1387 lead).

**Immediate local inventory request:** produce a read-only listing of every CODAL-related manifest, TracingNo, original HTML/PDF/attachment, and source hash across the three symbol folders plus the known shared/local CODAL roots. Do not download again until this inventory identifies a specific missing document or revision. Compare the local file inventory with `source-register.csv`, `event-ledger.csv`, `import_manifest.json` and SHA256 manifests; a directory name or search-result count alone is not a coverage proof.

This owner-side directory listing is a first-hand snapshot of top-level folders only. It does not expose nested contents or the wider `~/marketsage-data` archive and must not be misrepresented as a complete CODAL inventory.


### 10.8 Vaghdir capital-action reconciliation — uploaded CODAL registration bundle plus existing TSETMC snapshots (2026-11-26)

**Scope clarification:** the owner-uploaded `va-ghadir.zip` contains issuer/CODAL capital-increase notices and supporting registry/Gazette documents, not TSETMC payloads. TSETMC PA/SC and daily observations below are read from the already-imported immutable project snapshots. Do not claim the ZIP itself contains market data.

#### A. Seven capital increases: all seven SC rows linked to an issuer-document chain

The uploaded `وغدیر.txt` and attached CODAL PDFs/registry records show the following capital lifecycles. Amount columns below are million Rials; share counts are billions of shares. The first date is the TSETMC SC `dEven`, not necessarily the first executable market session.

| TSETMC SC date (Jalali) | Shares old → new (bn) | CODAL decision / implementation | Funding mix (million Rials) | Legal registration |
|---|---:|---|---:|---|
| 1390/02/03 | 6.075 → 12 | EGM 1390/01/29 | claims/cash 1,794,000; retained earnings 1,410,000; reserve 2,721,000 | 1390/10/12; tracing 61220 |
| 1391/09/18 | 12 → 16 | EGM 1391/09/14 | retained earnings 4,000,000 | 1391/10/17; tracing 100404 |
| 1392/01/20 | 16 → 18 | Board 1392/01/08 under delegation granted by EGM 1391/09/14 | retained earnings 2,000,000 | 1392/03/11; tracing 118368 |
| 1393/07/22 | 18 → 36 | EGM 1393/07/19 | claims/cash 11,340,000; reserve 6,660,000 | 1393/12/06; tracing 200959 |
| 1394/08/12 | 36 → 46.08 | EGM 1394/08/07 | claims/cash 10,080,000 | 1394/12/03; tracing 249128 |
| 1395/09/03 | 46.08 → 72 | EGM 1395/08/24 | claims/cash 8,750,000; reserve 17,170,000 | 1395/12/14; tracing 334274 |
| 1403/05/13 | 72 → 216 | Regulator permission 1403/03/26; EGM 1403/05/03 | retained earnings 83,324,420; reserve 60,675,580; no cash/receivables component shown | 1403/06/11; tracing 1242530 → correction 1242885 → latest 1242963 |

All seven TSETMC share-change rows map to these seven capital transitions. This is event existence/terms reconciliation; the table does not by itself approve all first affected sessions or adjusted output.

The 1391/09/14 EGM is a parent authorization with two tranches: 4,000,000 retained earnings executed under the EGM and a further 2,000,000 retained-earnings tranche delegated to the Board, later implemented by the 1392/01/08 Board decision. Model this as one authorization/case with two implementation tranches, not as two unrelated issuers' events.

The 1403 registration record has three CODAL tracing numbers, but the uploaded source index identifies the later numbers as corrections/updates, not three capital increases. The latest 1242963 follows 1242885, which corrects 1242530 after publication of the official Gazette notice. Preserve the amendment chain and select the latest accepted version without double-counting the capital increase.

The uploaded ZIP also contains a text file whose filename suggests Vaghdir registration details but whose contents clearly identify ** فولاد مبارکه (فولاد)** and list its capital registration notices. It is misfiled/mislabeled in the Vaghdir bundle; preserve it as a future Foolad source and do not attach those notices to Vaghdir.

#### B. Independent arithmetic checks against PA observations

Use issuer capital terms, not a K inferred from the provider tuple. For a simple par-value increase, the diagnostic theoretical post price is:

`P_{post} = (P_{pre} \times S_{old} + 1000 \times S_{paid,new}) / S_{new}`

where `S_paid,new` is the new share count paid at 1,000 Rial nominal value. Retained-earnings/reserve shares add zero cash in this price-only equation. This formula is a documented-event diagnostic for the simple capital cases below; it is not a universal corporate-action handler.

| Case | TSETMC PA input | CODAL-term theoretical post | TSETMC PA post | Difference |
|---|---:|---:|---:|---:|
| 1390 capital before DPS | 7,252 | 3,820.825 | 3,820 | -0.825 Rial |
| 1391 fully from retained earnings | 5,106 | 3,829.500 | 3,829 | -0.500 Rial |
| 1392 fully from retained earnings | 4,065 | 3,613.333 | 3,613 | -0.333 Rial |
| 1393 mixed: 11.34T claims/cash + 6.66T reserve | 6,530 | 3,580.000 | 3,580 | 0 |
| 1394 fully paid claims/cash | 2,362 | 2,064.063 | 2,064 | -0.063 Rial |
| 1395 mixed: 8.75T claims/cash + 17.17T reserve | 1,862 | 1,313.208 | 1,313 | -0.208 Rial |

The 1393 official registry scan included in the upload independently records the 18T→36T increase and a Bank Saderat certificate for the 11,340,000 million Rial paid component (certificate no. 72/4339/362 dated 1393/11/29). This agrees with the CODAL split; it is not an unresolved mismatch.

For 1390, CODAL's cash/claims component of 1.794T Rial implies 1.794bn newly paid shares at par. Based on `P_pre=7252`, `S_old=6.075bn`, `S_new=12bn`, the issuer-terms calculation is 3820.825, versus provider PA 3820. After the separate 500-Rial DPS component, the capital calculation is (6752×6.075+1794×1000)/12 = 3567.700; the first daily TSETMC traded close in the available history is 3569 on 2011-04-26 (difference 1.3 Rial). This is near the issuer-term calculation, not an exact equality.

**Correction to the older Vaghdir 2011 audit interpretation:** its `K=301.113924` was inferred from the TSETMC PA tuple and then inserted back into a reconstruction of the same tuple. That is a provider-implied parameter, not an independent CODAL validation of K. The issuer-terms calculation above replaces the circular claim of exact factor proof. Retain the small difference and any unit/rounding/tick convention as a documented residual.

#### C. Vaghdir 2011 is a mixed event; PA observations are not four independent price factors

The issuer evidence includes:
- EGM/capital case 6.075bn → 12bn, with 1.794T claims/cash, 1.410T retained earnings, and 2.721T reserve;
- cash dividend DPS = 500 Rial (CODAL evidence in the existing Vaghdir source pack; verify the original meeting TracingNo linkage where source indexes contain both 38803 and 38448);
- TSETMC provider PA observations: 2011-04-23 7252→3820; on 2011-04-26, 7252→6752, 6752→3567, and 3820→7252 (reciprocal/display-like record).

The 2011-04-26 ledger line previously labelled `dividend` with factor about 0.4919 is semantically composite: it reflects the DPS and capital components, not a dividend-only factor. The reciprocal 3820→7252 is not another event factor. The 2011-04-23 PA observation and the 2011-04-26 tuples must be represented as provider observations related to one mixed economic case, with explicit component/reciprocal relationships. Do not multiply every tuple and double-apply the capital effect.

The daily CSV contains no 2011-04-23 trade row; 2011-04-26 is the first observed traded row, with final price 3569, previous price 3820, volume 11,274,132 and 1,131 trades. Preserve this market chronology separately from the issuer decision and PA dates.

#### D. 1403 is the high-value SC-only and market-state test

The 1403 capital increase is all from retained earnings and reserve, 72bn→216bn shares (a 200% increase); CODAL registration is 1403/06/11. TSETMC has SC at 1403/05/13 but **no matching PA row** in its 25-record PA list. The existing daily CSV's last pre-gap record is 2024-07-22 / 1403/05/01; the next row is 2024-09-09 / 1403/06/19 — a 49-calendar-day interval without a daily observation. It is therefore not yet proven whether this was a suspension, no-trade interval, symbol-specific technical halt or source coverage gap; official exchange/symbol-status records are required. The first observed post-gap trade at 7,150 versus 22,000 on 2024-07-22 is broadly consistent with a one-third price basis after a tripling of shares, but the price path across a 49-day absence cannot be used as proof of an adjustment factor.

This case demonstrates that an event engine cannot rely exclusively on PA rows. A CODAL-confirmed all-free increase plus SC can establish the economic share conversion; the first affected session still requires market-status evidence. An SC-only event must not be ignored simply because the PA endpoint has no row.

#### E. Dividend PA coverage: mixed evidence, not yet a complete CODAL dividend ledger

The existing PA feed contains 25 rows. Its pre/post price differences include 250 (2009), 310 (2010), 500 (2011), 510 (2012), 500 (2013), 630 (2014), 500 (2015), 400 (2016), 160 (2017), 190 (2018), 250 (2019), 800 (2021), 1,930 (2022), 2,350 (2023), 3,000 (2024), 1,170 (2025) and 1,500 (2026), plus capital/mixed/reciprocal tuples. These differences are provider observations, not accepted DPS values by themselves.

CODAL/issuer evidence currently identified:
- DPS 500 in 1390/2011 mixed case (existing CODAL PDF evidence; original TracingNo cross-reference still to reconcile because source packs mention 38803 and 38448).
- DPS 510 for the AGM of 1390/11/30 (CODAL TracingNo 66259), consistent with PA 2012-02-20 4652→4142.
- DPS 500 for the AGM of 1391/12/08 (CODAL TracingNo 108468), consistent with PA 2013-02-27 4643→4143.
- 1392/12/25 AGM (existing CODAL source TracingNo 155748) has an attachments page but the PDF attachment itself is not present in the staged source directory; it must be retrieved/inspected before calling the 2014 PA difference of 630 a verified DPS.
- Contemporary press archive records DPS 250 for Vaghdir in Farvardin 1388 (consistent with PA 2009-04-19); another contemporary archive quoting the CEO records DPS 310 in Ordibehesht 1389 (consistent with PA 2010-04-21). These are secondary contemporaneous sources, not substitutes for the original AGM/CODAL decision.
- DPS 400 for AGM 1394/12/25 and DPS 160 for AGM 1395/12/25 are supported by a dividend-information archive; classify as secondary evidence until primary AGM/CODAL minutes are found.
- Public CODAL aggregator records DPS 800 at AGM 1399/12/25, DPS 1,930 at AGM 1400/12/23, DPS 2,350 at AGM 1402/01/31, DPS 3,000 at AGM 1403/01/28, and DPS 1,170 at AGM 1403/12/08. The latter amounts and meeting dates align closely with PA observations, but originals and ex-date chronology should be captured.
- A third-party dividend schedule reports 490 Rial payout in 1399/02, while the annual meeting scheduled for 1398/12/26 was cancelled and the PA feed has no 2020 PA row. Treat this as an important missing-provider-observation/document-chain candidate, not an automatic missing factor.
- DPS/AGM evidence for the 2026 PA difference of 1,500 and several older amounts (630, 500, 190, 250, etc.) remains to be connected to original notices or reliable archived notices.

The independent BourseEye page reproduces the same seven share-count changes and the PA history, and explicitly warns that PA observations alone do not reveal whether the cause was a dividend or a capital increase. It is a cross-check/discovery aid, not the issuer source of truth.

#### F. Engine design/test implications

Vaghdir now supplies at least these reusable regression patterns:
1. Mixed capital + cash dividend, with repeated/reciprocal provider PA observations (1390).
2. One EGM authorization producing multiple retained-earnings tranches, one later implemented by Board (1391–1392).
3. Mixed claims/cash plus reserve, including one case with exact independent arithmetic and matching bank certificate (1393).
4. Fully paid claims/cash capital increase (1394).
5. Mixed paid + reserve capital increase (1395).
6. All-free retained-earnings/reserve tripling with SC but no PA row, coinciding with a long market-data gap and delayed first observed session (1403).
7. Duplicate/corrected/latest CODAL versions (1242530 → 1242885 → 1242963), which must remain one legal event with an amendment chain.

A shared engine should therefore keep distinct entities for issuer authorization, approved tranche/component, legal registration, market-effective/first-traded session, provider PA observation and provider SC observation. It needs a capital-increase handler parameterized by funding components (paid subscription at nominal, non-cash retained earnings/reserve, rights/receivables) and a separate dividend handler. The 1391 authorization/tranche structure requires event parent/child relations. The 1403 case proves price-effect candidate discovery cannot require PA. The Vaghdir local V2 implementation was previously inventoried as PA-driven for price factors and SC-only for volume normalization; that design would miss a CODAL-confirmed SC-only price event unless a dedicated reviewed handler/reconciliation path is added. This is an architectural finding; full V2/V3/V4/V5/V6 offline replay against one frozen source snapshot is still required before selecting or changing the canonical engine.

#### G. Remaining Vaghdir blockers (keep open)

- [ ] Reconcile the 2011 DPS source reference (38803 vs 38448) and document the exact component/PA relationship.
- [ ] Retrieve the missing PDF attachment for CODAL AGM TracingNo 155748 and verify the 630-Rial 1394-03-17 PA candidate.
- [ ] Reconstruct primary CODAL AGM/dividend chain for all unresolved PA-only candidates; do not equate PA difference with DPS.
- [ ] Resolve 2010-04-21 (2770→2460, 310 Rial) with the contemporary CEO quote plus primary AGM decision/market date; keep ledger status blocked until the source relationship is accepted.
- [ ] Obtain official symbol status/suspension/reopening evidence for 1403/05/02 through 1403/06/19; do not label the 49-day data gap as a suspension until verified.
- [ ] Inspect the exact original bank certificate pages for 1390 and 1393, preserving certificate amounts, issuer and relation to total subscription/claims.
- [ ] Rebuild one canonical Vaghdir event timeline with exact CODAL tracing numbers, document amendments, components, PA/SC IDs and market dates.
- [ ] Run all existing Vaghdir engine versions on the same frozen inputs and produce event-level before/after outputs; do not approve any output yet.

**Current Vaghdir result:** all seven capital/share-change events are documented and economically classifiable at component level to the extent above; dividend and effective-session history remains partially open. No Vaghdir adjusted series is accepted by this investigation.
