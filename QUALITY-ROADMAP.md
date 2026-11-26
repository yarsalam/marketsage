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
