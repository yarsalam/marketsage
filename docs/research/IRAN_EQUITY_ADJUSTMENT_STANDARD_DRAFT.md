# Iranian Equity Corporate-Action and Price-Adjustment Research Standard

**Status:** Draft v0.1 — working protocol, not an approved adjustment algorithm  
**Draft date:** 2026-11-13  
**Pilot instruments:** فولاد, وغدیر, پارسیان  
**Purpose:** reproducible, evidence-backed historical price-basis and total-return series  
**Release boundary:** research only. This document does not approve scoring, ranking, probability calibration, backtesting, production use, broker access or trading.

---

## 1. Purpose and decision boundary

This standard converts the three-symbol pilot into a repeatable process. It is intended to prevent every new symbol from requiring a fresh, unstructured source hunt. Proven source routes, document patterns, event relationships and tests should be reused; event-specific economic terms and effective dates must still be verified for each issuer action.

Separate six tasks:

1. discover candidate corporate actions;
2. verify issuer terms from original evidence;
3. establish the market-effective date and chronology;
4. reconstruct theoretical price-basis effects;
5. reconcile with TSETMC provider records and independent chart data;
6. accept only bounded historical intervals whose evidence is sufficient.

A parsed provider row, price discontinuity, nearby date, third-party adjusted series or successful HTTP response is not sufficient by itself.

## 2. Core principles

1. **Immutable raw data.** Never overwrite raw daily prices, provider payloads, original notices, source responses or hashes with adjusted values.
2. **No price-gap inference.** A price gap creates a candidate for investigation, not a corporate-action classification.
3. **No proximity-only joins.** A ±3-day or ±7-day search may generate candidate links, but cannot establish event identity, causality, deduplication or correction.
4. **Share-count change is not funding evidence.** Old/new shares alone cannot distinguish bonus shares from cash/receivables rights issues or mixed increases.
5. **Separate source factors from reconstructed factors.** Keep provider tuples and independent economic calculations in different fields. Never average conflicts.
6. **Preserve every date separately.** Publication, meeting/decision, eligibility/record date, ex-date, first affected trading session, rights period, subscription/allocation, registration, provider event date and local retrieval time are distinct.
7. **Unknown remains unknown.** Record conflicts and quarantine affected ranges; do not silently repair them.
8. **Price adjustment is not total return.** Maintain separate output definitions and explicit cash-distribution treatment.
9. **Partial acceptance is allowed.** A verified interval may be exposed while unresolved ranges remain unavailable for adjusted-price-dependent analysis.
10. **No investment-use gate changes.** This is a research and data-quality standard only.

## 3. Event universe

First-pass discovery must cover, at minimum:

| Event family | Required terms |
|---|---|
| Cash dividend or cash distribution | Approved amount per share, eligibility/record date, ex-date or first affected session, payment conditions |
| Bonus increase from retained earnings | Old/new capital and shares, approved percentage, effective date |
| Increase from reserves | Amount, shares, old/new capital, effective date |
| Rights issue from cash/receivables | Cash/receivables amount, nominal/subscription price, entitlement ratio, deadline, unused-rights treatment, allocation and registration sequence |
| Mixed-source increase | Each funding component, amount/share count and chronology |
| Split / reverse split / denomination change | Exact conversion ratio and effective session |
| Merger, demerger, share exchange or security conversion | Consideration, exchange ratio, fractional-share/cash treatment, effective date |
| In-kind distribution or spin-off | Distributed asset/security, distribution ratio, valuation basis, effective date |
| Other issuer action | Full economic terms and effect on per-share entitlement or price basis |

An announcement is not automatically an adjustment event. Assess its economic effect on the share and on the specific output series.

## 4. Source catalogue and authority

| Source | Role | Limits / checks |
|---|---|---|
| TSETMC GetPriceAdjustList | Discover and preserve provider price-adjustment tuples, dates and reference prices | Does not establish issuer event type, funding source, rights terms or economic correctness |
| TSETMC GetInstrumentShareChange | Discover old/new share counts and provider dates | Does not establish bonus vs cash-funded vs mixed issue |
| TSETMC daily history | Raw market prices, previous-close fields, trades, volume/value, no-trade observations | Verify identity, field semantics, scale, Rial/Toman convention and stale-price behavior |
| TSETMC instrument/status/security-master records | Identity, InsCode continuity, listing/status and suspension/reopening context | Test historical coverage and status-code meanings |
| TSE Client adjustInfo and related outputs | Independent provider/library event diagnostics | Diagnostic reference only, not issuer legal/economic authority |
| CODAL original notices and attachments | AGM/EGM terms, approved DPS, capital sources, rights and registration sequence | Preserve TracingNo, original files, publication/update metadata and amendment links |
| Original issuer/company notices and official publications | Recover or supplement historical issuer notices | Preserve original identity and wording; distinguish original from re-publication |
| Official Gazette/company-registration notices | Legal registration and corporate status | Registration date is not automatically market-effective date |
| Newspaper/press advertisements | Discover original meeting invitations, rights deadlines, subscription calls and legal announcements | Original notice from issuer/statutory authority may be primary for the fact it announces; commentary/republication is secondary and should be traced to original |
| Independent adjusted chart/history | External price-history comparison | First establish its adjustment policy, cash-dividend treatment, scale, rounding, anchor and field definitions |
| Third-party extractors/public code | Discover endpoint behavior, schemas, edge cases and test ideas | Not economic truth, completeness, or proof of MarketSage data rights |

Keep source provenance and legal/data-rights review separate from economic validation. A source can be useful for research while remaining unapproved for redistribution or production.

## 5. Standard investigation sequence

### 5.1 Freeze and identify inputs

For every instrument/run, record symbol, company, market/board, canonical identifier(s), InsCode, retrieval time, source route, query parameters, response status, raw response hash, encoding, coverage range, row count, duplicates, gaps and known truncation. Preserve each snapshot as a new version; never replace the earlier raw artifact.

### 5.2 Discover candidate events

Extract and preserve all rows from:

- GetPriceAdjustList;
- GetInstrumentShareChange;
- TSE Client adjustment/event responses;
- daily raw prices, including pClosing, pDrCotVal, priceYesterday, trade count and volume;
- instrument status and market calendar sources where available.

Build a candidate queue using exact identifiers, source payload, dates and value similarities. Calendar-neighborhood matching can suggest links only.

### 5.3 Search original issuer evidence

For each candidate:

1. Search CODAL by symbol, issuer name, Jalali date range, filing category and title.
2. Open and preserve each original notice and relevant attachment; capture TracingNo, letter code, issuer/symbol, title, filing date, update/correction date and hashes.
3. Follow the document chain: invitation → AGM/EGM decisions → regulatory authorization where relevant → rights/exercise notice → subscription/allocation notice → registration notice.
4. Search original issuer publications, official publications and newspaper advertisements for the same issuer and time range, especially where CODAL is unavailable or incomplete.
5. Use news, aggregators and third-party databases as locators or labelled corroboration; do not silently promote them to primary evidence.
6. Search amendments/corrections and implementation notices; decide whether a later notice amends, supersedes, supplements or republishes an earlier one.

Failure of one search route triggers a documented fallback search for that event; it is not evidence that no event occurred.

### 5.4 Build event chronology

Preserve separately:

- announcement publication date/time;
- meeting/decision date;
- eligibility/record date;
- ex-date, if stated;
- first affected trading session, established from market facts;
- rights start/deadline and subscription/allocation dates;
- capital registration date;
- provider event date (for example dEven);
- local retrieval timestamp and source publication/update metadata.

Do not infer ex-date from AGM date, registration date, provider date or nearby price gap without evidence.

### 5.5 Classify event identity and relationships

Every candidate receives one relation status:

- SAME_EVENT;
- COMPONENT_OF;
- AMENDS;
- SUPERSEDES;
- REVERSES_OR_WITHDRAWS;
- ROUND_TRIP_OR_TEMPORARY;
- INDEPENDENT_EVENT;
- UNRELATED;
- UNRESOLVED.

A reciprocal factor pair is not proof of a reversal. A round-trip share-count record is not proof of a corporate action. Require source chronology, instrument identity and supporting market/issuer evidence.

### 5.6 Establish economics before selecting a formula

For cash distributions, establish approved per-share amount, eligibility, ex-date and relevant payment conditions.

For capital increases, establish old/new capital and shares, nominal value, each funding component, cash/receivables amount, subscription price, entitlement ratio and rights implementation/registration sequence.

For mixed events, calculate each component from its own terms and establish whether components are simultaneous or sequential. A headline percentage or old/new share ratio alone is insufficient.

Only then calculate a candidate theoretical factor. The formula and factor direction must be recorded with inputs, units, rounding and event assumptions.

### 5.7 Reconcile with TSETMC market records

- Compare price-adjust and share-change feeds as separate datasets.
- Verify the meaning and direction of each provider field before interpreting a ratio.
- Compare theoretical reference prices with provider references and the first actual trading session.
- Distinguish traded close from stale/no-trade pClosing and pDrCotVal/last traded price.
- Inspect previous-close, no-trade sessions, halt/resume state, price limits and session calendar.
- Report rounding in absolute price ticks and relative percentage.
- Do not treat ordinary market return between sessions as an adjustment factor.

### 5.8 Compare independent adjusted history

Before comparison, determine whether the chart is price-return or total-return adjusted; whether cash dividends/rights are included; its unit/scale; price field; rounding/anchor policy; and whether revisions/backfills occur. Compare the same instrument, session and price field. Report absolute tick error and relative error. Whole-unit rounded low-price observations may not distinguish two close factors.

## 6. Output-series definitions

Do not expose one ambiguous field called adjusted_price without specifying its economics.

Maintain at least:

1. **Raw market series:** source prices exactly as received, with provenance and field semantics.
2. **Corporate-action price-basis adjusted series:** an explicit policy for price-basis-changing events; cash-dividend treatment must be stated.
3. **Total-return series:** separate methodology including cash and other shareholder distributions.
4. **Rights/security lifecycle data:** rights instruments and conversions remain distinct securities/events until an explicit economic method is verified.

A price series adjusted for capital changes is not automatically a total-return series. Identify the independent chart's policy empirically before treating it as a target.

## 7. Standard ledgers

### 7.1 Corporate-action ledger

One row per issuer event or component. Minimum fields:

event_id, symbol, company_name, ins_code, event_family, event_subtype, component_id, announcement_date, meeting_date, decision_date, record_date, ex_date, first_affected_session, rights_start_date, rights_deadline, subscription_date, allocation_date, registration_date, provider_date, old_capital, new_capital, old_shares, new_shares, nominal_value, retained_earnings_amount, reserves_amount, cash_amount, receivables_amount, subscription_price, DPS, event_relation_status, related_event_ids, event_terms_status, effective_date_status, source_document_ids, source_payload_ids, evidence_status, notes.

### 7.2 Evidence ledger

One row per claim. Minimum fields:

evidence_id, event_id, claim, source_owner, source_type, URL/path, TracingNo/publication_id, original_title, publication_date, update_date, original_file_or_response_hash, local_archive_path, authority_level (PRIMARY / OFFICIAL_MARKET / SECONDARY_LOCATOR / COMMUNITY_REFERENCE), exact_extracted_value_or_text, page/section/field, supports_or_contradicts_or_context_only, review_status, unresolved_question.

### 7.3 Provider-factor ledger

Keep the raw tuple unmodified and the interpretation separate. Include source route, raw payload id/hash, provider date, instrument identifier, original fields/values, diagnostic ratio formula/direction, independent theoretical factor and inputs, units/rounding, event link and justification, candidate/accepted/rejected/conflict status.

### 7.4 Acceptance manifest

For every symbol and bounded range, record output type, covered start/end, excluded/quarantined intervals, event/document coverage, unresolved-event counts, accepted event/factor IDs, code/version, input hashes, chart comparison and tolerances, limitations, rights and point-in-time metadata status, acceptance state and reviewer/date.

## 8. Evidence and acceptance states

### Event states

DISCOVERED → DOCUMENT_SEARCHED → TERMS_VERIFIED → EFFECTIVE_DATE_VERIFIED → RELATIONSHIP_VERIFIED → FACTOR_RECONSTRUCTED → MARKET_RECONCILED.

Alternative terminal/exception states: CONFLICT, UNKNOWN, REJECTED. Do not collapse source completeness and arithmetic fit into one score.

### Interval and symbol states

- RAW_READY: raw history validated for the bounded range.
- EVENT_LEDGER_PARTIAL: discovery exists but event coverage/terms remain incomplete.
- EVENT_LEDGER_READY: known candidates are classified and unknowns explicitly listed.
- INTERVAL_ADJUSTMENT_VERIFIED: every factor affecting this interval is verified and reproducible.
- PARTIAL_SERIES_ACCEPTED: bounded intervals accepted; excluded intervals explicit.
- SYMBOL_SERIES_ACCEPTED: full declared history meets event, calculation, reconciliation and rights requirements.
- NOT_ACCEPTED: the stated output cannot safely be supplied.

A symbol can enter a read-only raw-data/event panel at RAW_READY or EVENT_LEDGER_PARTIAL. Do not expose a quarantined adjusted interval as verified. Partial intervals must display coverage boundaries and exclusions.

## 9. Triage: broad first pass, deep research only for exceptions

Run the standardized first pass for each symbol:

1. reuse or retrieve immutable instrument identity, raw prices and provider event snapshots;
2. enumerate all price-adjust and share-change rows;
3. search issuer notices and original official advertisements across the full history range;
4. link original evidence and date chronology to candidates;
5. reconstruct only events with verified terms;
6. run market, field-semantics and independent-chart checks;
7. generate a date-bounded exception queue.

Deep research is limited to missing primary notices, conflicting/unknown effective dates, unmatched provider/issuer events, possible corrections/reversals/duplicates/round trips, cash/mixed issues with missing terms, material theoretical/provider/chart disagreement, and unexplained raw gaps or scale discontinuities.

An unresolved event may affect all earlier prices through a backward factor chain. Propagate the affected range; do not assume only the event day is uncertain.

## 10. Vaghdir 2011 mixed-event case study

This is a case study, not an approved general algorithm.

### 10.1 Issuer evidence already collected

- CODAL 38803 (AGM decisions): Vaghdir's AGM for fiscal year ended 1389/09/30 was held 1390/01/29 and approved a cash dividend of **500 Rial per share**.
- CODAL 38805 (EGM decisions): on 1390/01/29 capital increased from 6,075,000 million Rial to 12,000,000 million Rial. Sources: retained earnings 1,410,000 million Rial; reserves 2,721,000 million Rial; claims/cash contribution 1,794,000 million Rial; share premium zero.
- Old/new shares: 6.075bn / 12bn = **0.50625**. TSETMC share-change dated 2011-04-23 carries exactly 6.075bn old and 12bn new shares.
- CODAL 46666 extends the rights-use period from 1390/04/13 through 1390/05/11.
- CODAL 59965 records 1,770,016,021 rights shares used by existing holders and 23,983,979 shares offered for public subscription; total 1,794,000,000. Subscription window: 1390/09/27–1390/10/26.
- CODAL 61220 says registration occurred on 1390/10/12. This is later than the April 2011 provider rows; do not conflate the market-effective date, rights period, subscription period and legal registration date.

### 10.2 Provider and daily-market observations

From the preserved local snapshots shown in the owner's terminal output:

- GetInstrumentShareChange, 2011-04-23: old 6,075,000,000; new 12,000,000,000.
- GetPriceAdjustList, 2011-04-23: pClosing 3,820; pClosingNotAdjusted 7,252.
- GetPriceAdjustList, 2011-04-26: (7,252; 3,820), (3,567; 6,752), (6,752; 7,252), in the order (pClosing; pClosingNotAdjusted).
- Daily raw history: 2011-04-16 pClosing 7,252 with 1,338 trades; 2011-04-23 pClosing 3,820 with zero trades; 2011-04-24 and 25 were no-trade observations at 3,820; 2011-04-26 pClosing 3,569, priceYesterday 3,820 and 1,131 trades.
- Decoded independent chart: 2011-04-16 close 60; 2011-04-26 close 56; 2011-04-27 close 54; 2011-04-30 close 53. The local chart file is semicolon-separated records with comma-separated fields, not a conventional one-header CSV.

The 23-Apr 3,820 is a no-trade/stale pClosing observation, not an executed close. The 26-Apr 3,569 is a traded close. Do not treat these as interchangeable.

### 10.3 Arithmetic reconstruction

Using billions of shares and nominal subscription value 1,000 Rial:

(7,252 × 6.075 + 1,000 × 1.794) / 12 = **3,820.825**.

This is within one Rial of the 3,820 provider reference.

After subtracting the approved 500-Rial dividend:

(6,752 × 6.075 + 1,000 × 1.794) / 12 = **3,567.7**.

This is within one Rial of the 3,567 provider reference and two Rial of the 3,569 first traded close.

This is strong numerical evidence that provider tuples are compatible with the mixed increase and cash distribution. It does not yet establish provider tuple ordering semantics or the reason for the reciprocal 3,820/7,252 tuple.

### 10.4 Independent chart comparison and current limit

- Implied chart factor at 2011-04-16: 60 / 7,252 = 0.00827358.
- Implied chart factor at 2011-04-26: 56 / 3,569 = 0.01569067.
- Pre/post implied-factor ratio: approximately 0.527293.

This is close to single capital-factor candidates 0.526751 and 0.528288 (about 0.103% and 0.188% differences), and materially different from combined product 0.491864. Because chart closes are rounded to whole units and several tuples occur in the same interval, this does not prove whether the chart includes or excludes cash dividends. It motivates single-factor tests using independent events.

The supplied candidate adjusted series had about 15.3% normalized price error against the chart at 2011-04-26; it is not accepted.

### 10.5 Event classifications at draft time

| Candidate | Current state | Remaining issue |
|---|---|---|
| 2011-04-23 share change 6.075bn → 12bn | TERMS_VERIFIED; effective/implementation chronology still under review | EGM shares match; rights/subscription/registration sequence continues later in 1390 |
| 2011-04-23 7,252 → 3,820 | FACTOR_RECONSTRUCTED candidate | Matches theoretical mixed increase before DPS; no-trade observation |
| 2011-04-26 7,252 → 6,752 | FACTOR_RECONSTRUCTED candidate | Exact 500-Rial difference agrees with AGM DPS; provider semantics still need verification |
| 2011-04-26 6,752 → 3,567 | FACTOR_RECONSTRUCTED candidate | Matches mixed-increase arithmetic after DPS |
| 2011-04-26 3,820 → 7,252 | UNRESOLVED | Reciprocal tuple; no direct evidence yet that it is a correction, reversal or superseding record |

Do not promote these candidates to accepted factors until event chronology, provider semantics and chart policy are reconciled.

## 11. Vaghdir independent-event pilot queue

These are candidate examples, not proven standalone actions.

### 11.1 Capital-increase candidates

| Gregorian provider date | Jalali date on secondary history page | Share-change feed | Price-adjust feed | Purpose | Current state |
|---|---|---|---|---|---|
| 2012-12-08 | 1391/09/18 | 12bn → 16bn; ratio 0.75 | Ratio approximately 0.749902 | Test 33.33% share-count increase | Primary CODAL resolution, funding source and effective-session chain still required |
| 2013-04-09 | 1392/01/20 | 16bn → 18bn; ratio 0.8888889 | Ratio approximately 0.888807 | Test 12.5% share-count increase | Primary CODAL resolution, funding source and effective-session chain still required |

BourseEye lists the share-count changes and price-adjust observations, but does not identify the economic cause of each price adjustment. Use it only as a locator/cross-check, not as primary proof.

### 11.2 Cash-distribution candidates

| Gregorian provider date | Jalali date on secondary history page | Price-adjust feed | Same-date share-change row in saved list | Purpose | Current state |
|---|---|---|---|---|---|
| 2012-02-20 | 1390/12/01 | Ratio approximately 0.890370 | None identified on same date | Candidate cash-distribution-only test | DPS and ex-date not yet verified |
| 2013-02-27 | 1391/12/09 | Ratio approximately 0.892311 | None identified on same date | Candidate cash-distribution-only test | DPS and ex-date not yet verified |

The 2013-02-27 / 1391/12/09 candidate has a useful secondary lead: a contemporary source reports Vaghdir's AGM for 1391/12/08 and a board proposal to distribute 400 Rial per share. This is not the final AGM decision. The secondary rounded price history displays approximately 464 to 414 Toman around the 1391/12/09 adjustment, a roughly 500-Rial difference; this discrepancy must be resolved from the original AGM resolution and exact provider reference prices. Prioritize this date for the first cash-distribution document search, but do not classify it as a confirmed dividend-only event yet.

Absence of a same-date share-change row does not prove a dividend or prove no related capital event nearby. Verify all original notices and neighboring provider rows before selecting the cleanest example.

### 11.3 Completion conditions for standalone tests

For each selected event:

1. obtain the original CODAL notice and attachments, or record the unsuccessful search and fallback route;
2. establish issuer decision, economic terms and exact first affected trading session;
3. search amendments, rights/subscription/registration records where applicable;
4. verify whether it is independent, mixed, duplicated, corrected or linked;
5. calculate a terms-based candidate factor only after the preceding steps;
6. compare provider references and same-session raw market data;
7. compare independent chart over a narrow pre/post interval and document its policy/rounding;
8. conclude per event: CONFIRMED_SINGLE_FACTOR, MIXED_OR_LINKED, CONFLICT or UNRESOLVED.

The objective is to determine what the independent chart actually reflects for capital increases versus cash distributions, not to force chart agreement.

## 12. Replication to فولاد and پارسیان

After the three Vaghdir examples are sufficiently resolved, freeze standard v1 and run the same first-pass extraction for فولاد and پارسیان. Reuse existing local files, hashes, event queues, adapters and reports; do not redownload or recount unchanged inputs merely to reproduce previous work.

For each symbol, inventory all provider event rows; search issuer notices and official advertisements for the full history; build chronology and ledgers; classify candidates; calculate only verified terms; run independent checks; and create a date-bounded exception queue.

Deep research is limited to missing, contradictory, linked, corrected or unreconciled intervals. Any unresolved factor affecting earlier history must quarantine the full dependent historical range.

## 13. Minimum panel-release policy

| Panel capability | Minimum gate |
|---|---|
| Read-only raw history | Valid identity, field/unit semantics, provenance, row/date/value integrity and no silent mutation |
| Corporate-action timeline | Source, original document, distinct dates, event classification and unresolved relationship state visible |
| Candidate adjusted series | Clearly marked research-only, event provenance visible, never represented as verified |
| Verified adjusted-price interval | Every affecting event terms-verified, effective-date-verified, reproducible and independently reconciled within documented tolerance |
| Total-return interval | Above plus verified cash/in-kind distributions and entitlement treatment |
| Full symbol series | Every event affecting declared range verified; no unresolved factor chain; rights and point-in-time limitations reviewed |

Do not reject the whole symbol solely because one bounded interval remains unresolved. Raw data and verified intervals can be released with explicit boundaries; calculations must not cross quarantined ranges.

## 14. Versioning plan

- Draft v0.1: current three-symbol workflow, Vaghdir 2011 case and independent-event test queue.
- Draft v0.2: incorporate original CODAL/official-publication evidence for selected standalone events and record contradictions.
- Standard v1.0: freeze only after the standalone tests are sufficiently supported and the first-pass procedure is checked against فولاد and پارسیان.
- Later changes require a versioned change note and regression review.

## 15. References and limitations

### Primary Vaghdir issuer records preserved locally

- CODAL 38803 — AGM decisions, fiscal year ended 1389/09/30.
- CODAL 38805 — EGM decisions, capital increase on 1390/01/29.
- CODAL 46666 — extension of rights-use period, 1390/04/13–1390/05/11.
- CODAL 59965 — public subscription notice, 1390/09/27–1390/10/26.
- CODAL 61220 — capital registration, 1390/10/12.

Original PDFs/text extracts and TSETMC snapshots are in the owner's local audit run dated 2026-11-12. This draft records their reported contents; it does not claim the local files are committed to the repository.

### Secondary locator/cross-check only

- BourseEye, Vaghdir capital increases and price-adjust history: https://bourseeye.com/stocks/137/وغدیر-سرمایه‌گذاری-غدیر-هلدینگ/capital-increases (accessed 2026-11-13). It lists share changes on 1391/09/18 and 1392/01/20 and price-adjust observations including 1390/12/01 and 1391/12/09; the page explicitly does not identify whether each adjustment is caused by cash dividend or capital increase.
- Bourse Secret, week 3 of Azar 1391: https://secretgroup.blogfa.com/1391/09/3 (accessed 2026-11-13). It reports an EGM on 1391/09/14 approving a 33.3% increase from retained earnings and a further proposed increase. This is a search lead only; the original CODAL resolution remains required.

### Existing repository research carried forward

- docs/research/IRAN_EQUITY_EVENT_INVESTIGATION_NOTEBOOK.md — prior source/adapter audit, three-symbol inventory and public extractor comparison.
- Existing source acceptance and quarantine controls remain in force. This draft approves no source, event factor, adjusted series or investment use.

---

**Draft decision:** proceed with the two capital-increase samples and two cash-distribution candidates in §11. Do not close the Vaghdir method study until original issuer terms and first affected sessions are verified for at least one clean capital-increase-only event and one clean cash-distribution-only event.



## 16. CODAL search-pagination and issuer-identity correction

**Observed owner run:** 2026-11-13. Three requested date windows each returned exactly 20 records. The script included a `PageSize=100` query parameter, but the CODAL search endpoint uses a default 20-record page; `PageSize` is not the pagination control. Its loop stopped when the number of records was below 100, so it read only page 1 in each window. Therefore the 60 collected headers are not a complete search of those windows.

The initial parser also did not print or assert the issuer symbol/company identity for each result. Titles mentioning another investment company are not enough to conclude whether the filing is unrelated, but no TracingNo may be assigned to وغدیر until its response metadata confirms the symbol/company.

**Correction required before using this search result:**
1. Fetch each high-priority candidate directly by exact `TracingNo` and preserve the raw response.
2. Print and verify `TracingNo`, `Symbol`, issuer/company name, title, LetterCode, PublishDateTime, Url/LetterSerial and attachment metadata.
3. For symbol/date-window discovery, parse top-level `Total` and `Letters`; paginate using the endpoint's 20-record default and continue until all pages implied by `Total` have been retrieved (with a safe request cap and rate spacing).
4. Send `Accept: application/json` explicitly when parsing JSON; retain XML parsing only as an explicitly handled fallback.
5. Deduplicate by TracingNo only after preserving the individual query/page provenance; do not discard alternate snapshots or revisions.
6. Preserve every response hash and report pages requested, pages completed, Total, rows returned, symbol-matched rows and any errors.

**High-priority candidate TracingNos seen in the first-page-only run (issuer identity not yet verified):**

- Earlier window: 64699, 64727, 66202, 66259.
- Later window: 105144, 105243, 107226, 108468, 108280, 109609, 110016, 118368.

For the 2012-02-20 candidate, 66202 (AGM resolutions, published 1390/11/30) and 66259 (AGM decisions, published 1390/12/11) are useful exact-ID lookups. For the 2013-02-27 candidate, 107226 (AGM decision summary, published 1391/12/08) and 108468 (AGM decisions, published 1391/12/19) are useful exact-ID lookups. The 108280, 109609, 110016 and 118368 records may help establish a later capital-increase chronology around 1391/12–1392/03, but must first be identity-checked and then linked to the 2013-04-09 provider event by terms and chronology.

**Current status:** discovery leads only. No issuer assignment, event classification, DPS, capital terms or effective date is accepted from these headers until exact-ID retrieval and original-document inspection are complete.
