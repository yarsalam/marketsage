# Iranian Listed-Equity Event Investigation Notebook

**Notebook date:** 2026-11-12  
**Repository baseline:** main at 4c4b032196137af4658ea2c28e38a21605ee923b  
**Scope:** TSETMC-listed equities; pilot instruments: فولاد, وغدیر, پارسیان  
**Mode:** discovery and evidence reconciliation only  
**Release state:** research-only; no source/data acceptance, scoring, ranking, backtest approval, production use, broker access or trading

---

## 1. Purpose and stop boundary

This notebook is deliberately narrower than a general market-research plan. Its job is to determine **why a historical equity price series changes**, distinguish genuine corporate-action price-basis changes from ordinary market movements and missing trading sessions, and establish whether the event history is complete enough to calculate price-return and total-return series.

It does **not** attempt to explain every daily price move, predict prices, collect macro/news/sentiment feeds, or build a new market-data platform.

Do not:
- change or overwrite raw price histories;
- apply a factor because two dates are within a nearby calendar window;
- infer a corporate action from a price gap alone;
- treat a TSETMC/API adjustment factor as economically verified merely because it parses;
- use market holidays, suspensions, stale quotes or earnings announcements as mechanical adjustment factors;
- approve any candidate series for scoring or backtesting.

Unknown remains unknown. A conflict is recorded, not silently repaired.

## 2. Existing work audit — reuse, do not rebuild

### 2.1 Code and governance already present on main

| Existing asset | What it already does | What is still missing for this investigation |
|---|---|---|
| user/analysis-engine/tsetmc_adapter.py | Parses candidate TSETMC daily history, validates dates/values, preserves retrieval time and response hash; keeps source quarantined | No complete event/market-status history adapter; unit and publication semantics remain unverified |
| user/analysis-engine/codal_adapter.py | Parses CODAL search XML headers, validates TracingNo/title/symbol, preserves original date strings and response hash | Publication time is intentionally null; Jalali/time-zone semantics, amendments, event-specific details and historical completeness are not resolved |
| user/analysis-engine/source_registry.py | Registers iran.tsetmc and iran.codal as candidates; both are explicitly unapproved | Does not yet represent the newly announced official TSETMC REST service as a separately evidenced contract |
| user/analysis-engine/source_acceptance.py and SOURCE_ACCEPTANCE_EVIDENCE.md | Enforce evidence checklists and fail-closed acceptance | Cannot create rights, source-of-truth evidence, or human attestations |
| IRAN_SOURCE_ACCEPTANCE.md | Records candidate-only status and the CODAL timestamp/rights caveats | Must be extended only after the official REST contract is inspected |
| docs/research/TSETMC_INTEGRATED_RUN_2026-11-05.md | Records the 47-candidate offline acceptance result and blockers | It does not prove economic correctness of any adjustment factor |
| docs/research/TSETMC_REMEDIATION_PLAN_2026-11-05.md | Already covers identity, rights, units, event payloads, reconciliation, dates and point-in-time controls | The present notebook operationalizes the event-specific scope for the three-symbol pilot |

The repository also has staged validation workflows and tests for TSETMC, CODAL, temporal storage, source registry and source acceptance. They are not a substitute for the event research below.

### 2.2 Prior empirical work and results to carry forward

**Whole-corpus TSETMC acceptance, 2026-11-05:** 47 candidates discovered; 47 quarantined; 0 research-eligible; 0 feature rows; 0 forward-label rows. The dominant reasons were unverified rights, identity, price/volume units and semantics, corporate-action completeness/payload, independent reconciliation and history quality. Seven identity conflicts were reported separately from file-read errors in the later owner review. This is an evidence failure, not a runner failure.

**Prior offline review queues:** an earlier local review extracted 48,902 candidate corporate-action rows and 48,059 date-gap rows from existing reports. These are *review queues*, not verified events or proven explanations. Reuse and filter them; do not regenerate or recount the whole corpus as if they were new evidence.

**Three-symbol price/event work performed in November 2026 (owner terminal results):**

| Check | فولاد | وغدیر | پارسیان | Interpretation |
|---|---:|---:|---:|---|
| Daily history rows in candidate CSV | 4,680 | 5,688 | 3,866 | Existing local candidate snapshots |
| TSE Client adjustInfo events | 31 | 15 | 18 | Dividend / capital-increase event feed retrieved |
| TSE Client validGPLRatio | true | true | true | Library-specific eligibility flag only; not source acceptance |
| Raw-price chart comparison in the dedicated chart-validation run | 100% exact | 100% exact | 100% exact | For the common dates and fields in that run |
| GetPriceAdjustList matched to TSE Client events (candidate window ±7 calendar days) | 23/23 | 13/25 | 12/18 | Window used to propose matches only; not an event join or dedup rule |
| GetInstrumentShareChange matched to TSE Client events (same candidate window) | 12/12 | 3/7 | 7/9 | Same caveat |
| Official-chart adjusted comparison | Requires review | Requires review | Requires review | Do not accept from an aggregate match percentage |

**Transport / endpoint evidence actually observed on the owner's laptop:**
- cdn.tsetmc.com/api/Instrument/GetInstrumentSearch: HTTP 200.
- GetClosingPriceDailyList: HTTP 200 with JSON history.
- GetPriceAdjustList: HTTP 200.
- GetInstrumentShareChange: HTTP 200.
- Financial.aspx?a=0 and a=1 chart responses were obtained after adding response decompression.
- The legacy service.tsetmc.com/tsev2/data/TseClient2.aspx InstrumentAndShare request returned HTTP 200 through Python on both HTTP and HTTPS. A Node HTTP attempt timed out; after explicitly configuring the library to HTTPS, TSE Client 2.27.6 successfully returned adjustInfo for all three instruments.
- CODAL has a repository parser prototype and fixtures. The evidence reviewed here does **not** establish a successful, complete, live CODAL historical-event crawl or verified publication/update timestamps.
- The browser could not open https://api.tsetmc.com/docs/ directly. The documentation content was subsequently inspected through the public m-idasa/Documents mirror (latest commit 2025-09-28, authored with an @tsetmc.com address but unsigned). The owner's successful endpoint tests are still against the older CDN/legacy routes; no authenticated new-REST live request has been performed for these three symbols.

**Important diagnostic inconsistency to resolve:** the earlier dedicated raw-chart comparison reported 100% exact raw matches for all three instruments, but the subsequent event/precision audit printed large raw-source/chart differences for old وغدیر and پارسیان rows (for example, 2004-08 values for وغدیر and 2010-12 values for پارسیان). These reports may have compared different price fields, scales, snapshots or modes. Do not use the latter figures as proof of a historical scale break until the report lineage and column mapping are reconciled. Foulad's chart reports whole-unit values and 99.3% integer-rounded match in the precision audit; sub-unit decimal differences must be measured in price ticks, not only relative percent.

### 2.3 What is not already proven

- Complete official event coverage for any of the three instruments.
- The authoritative effective date for every event.
- Correct economics for cash/rights components of capital increases.
- Explanation of every missing date by official holiday, suspension, listing boundary or provider omission.
- Official API access terms, retention rights, commercial/derived-use rights, rate limits and service-level stability.
- Point-in-time publication/availability timestamps and correction/amendment linkage.
- Independent economic acceptance of the adjusted series.

## 3. Primary source choice for a fast, unified first pass

### TSETMC new REST API: documented capabilities and real limitations

Official launch reporting dated 2025-12-27 (1404/10/06) says the new TSETMC web service is REST-based, the old and new services coexist during transition, and new development is to use REST. The report says TSETMC aggregates information from TSE, IFB, Energy Exchange, Commodity Exchange and CODAL. The announced documentation URL is https://api.tsetmc.com/docs/. The page itself could not be opened by the research browser, but its documentation content is mirrored in the public GitHub repository [m-idasa/Documents](https://github.com/m-idasa/Documents). That repository's latest inspected commit is dcc57eb6dea36c036e55824bcfa676c7713ca829 (2025-09-28), authored using an @tsetmc.com email address; the commit is unsigned. Its BaseUrl.md specifies https://api.tsetmc.com, and its index says credentials are provided by TSETMC. Treat it as a high-confidence documentation mirror, while retaining the unsigned-commit caveat.

- Official launch report: https://armaneghtesadi.com/954797/1404/10/06/نسخه-جدید-وبسرویس-tsetmc-منتشر-شد/
- Documentation mirror: https://github.com/m-idasa/Documents
- Base URL: https://api.tsetmc.com
- Official documentation entry point: https://api.tsetmc.com/docs/

#### Authentication, roles and credit

The documented login is POST /Account/Login with a username/password. It returns a JWT and UTC expiry; subsequent requests use Authorization: Bearer <token>. The documentation explicitly says users must obtain credentials from TSETMC. This is not an anonymous public feed. Trade/InstTrade and Trade/TradeOneDayAll require named roles and apply CheckCredit. The error-code page lists -106 for credit retrieval failure and -105 when user credit is missing or zero. The documents do not publish a credit price, quota, credit-per-row formula, retention terms or redistribution licence. Therefore cost and permitted use remain unknown; do not purchase or run broad pulls until the provider states them.

#### Endpoint map relevant to this notebook

| Documented route | Documented payload | Research use | Limitation / validation still needed |
|---|---|---|---|
| POST /Instrument/Instrument | Symbol/instrument master by market flow; InsCode, InstrumentID, identity/symbol/company names, nominal price, share count, listing date and validity | Identity and market/board crosswalk | Must validate field meanings, historical snapshots and identifier continuity |
| POST /Instrument/InstrumentTseShare | Old/new share counts, date and InsCode by market flow | Detect share-count changes | Does not identify funding source, cash subscription price, right entitlement or economic terms |
| POST /Instrument/InstrumentsState | Current instrument status and reason | Current halt/restriction state | Absence of a row is documented as open; test this against known cases before relying on it |
| POST /Instrument/InstrumentStateChange | Instrument status changes for Inscode and Deven; status code, time and reason | Historical suspension/reopening timeline | Must test date coverage, event order and whether every transition is retained |
| POST /MarketInfo/NSCStart | Only the latest 20 market-open sessions, with DEven, HEven and NSCEnd | Recent session calendar and completed-session flag | Not a long-term historical calendar |
| POST /Trade/InstTrade | Daily data for one instrument over DateFrom/DateTo: PClosing, PDrCotVal, PriceFirst, PriceMin/Max, PriceYesterday, volume/value and trade count | Bounded historical raw-price candidate | Role + CheckCredit; maximum range/quota unknown; unit semantics need cross-check |
| POST /Trade/TradeOneDay | All instruments with at least one non-cancelled trade on one date | Daily market snapshot | Historical daily calls may require repeated date/flow requests |
| POST /Trade/TradeOneDayAll | All instruments on one date | Possible bulk daily acquisition | Role + CheckCredit; cost/quota unknown |
| POST /MarketInfo/Company and POST /MarketInfo/GroupState | Documented fields DEven/HEven/TseTitle/TseDesc/Flow; examples show a stop notice | Potential market/company notice discovery | Both docs use nearly identical stop-notice examples despite different names; do not assume semantics until live fixtures confirm |
| POST /Index/Indexb2 | Daily index fields including net-cash-return index and a cash-dividend aggregate | Contextual index-level check | Not an issuer-level dividend ledger or per-share adjustment source |

#### What the new REST documentation does not establish

No documented new-REST endpoint was found in this documentation set for:
- issuer-level DPS/cash-dividend event history and entitlement/ex-date;
- capital-increase funding composition (reserves vs cash/receivables vs mixed), subscription price or rights terms;
- rights-instrument price/history and rights conversion lifecycle;
- split/reverse-split, merger, demerger or security conversion terms;
- an official per-instrument adjusted-price history or a complete adjustment-factor ledger;
- historical event correction/amendment lineage or a durable historical trading calendar beyond the 20 latest sessions.

The InstrumentTseShare endpoint is useful evidence of share-count changes, but a share ratio alone cannot calculate the theoretical ex-right price of a cash capital increase. The Indexb2 net cash-return/index dividend fields are aggregate index measures, not a replacement for company-level DPS evidence.

**Documentation quality warning:** the InstTrade field table describes QTotCap as volume in one place, whereas TSETMC's other documented/observed schemas use QTotTran5J for traded volume and QTotCap for traded value/turnover. Do not normalize either field until a same-date live response is reconciled against the already tested CDN history and the exact field definition is confirmed.

**Crucial interface distinction:** the recently tested https://cdn.tsetmc.com/api/ endpoints are a separate, older reverse-engineered interface. Their successful HTTP responses do not prove the authenticated REST service's access, schema, quotas, pricing or rights. Likewise, the new REST documentation does not retroactively make the CDN endpoint contract official.

**Decision status:** AUTHENTICATED_PRIMARY_MARKET_DATA_CANDIDATE — PARTIAL_EVENT_COVERAGE; COST_AND_RIGHTS_UNKNOWN. Use it first for instrument identity, share-count changes and status history if owner credentials/role and legal terms are available. Use its priced endpoints only after the credit schedule and terms are known. It is not a complete standalone corporate-action/adjustment source and is not accepted for scoring or backtesting.

### CODAL's narrowly defined role

Use CODAL only as the **linked primary disclosure evidence** when TSETMC points to an issuer event or when a material event's terms must be proved: general-meeting resolution, approved capital increase and its funding composition, DPS/cash dividend, subscription price/rights, merger/spin-off terms, and corrected/amended disclosures.

Do not make CODAL a second broad polling project at this stage. The existing CODAL adapter is candidate-only and its Jalali publication-time, update-time and amendment semantics are unresolved. Capture the actual notice identifier/URL and original document, then verify the relevant fields and timestamps from that notice. This remains necessary because the inspected new-REST documentation does not document issuer-level DPS, cash-rights pricing or complete capital-increase terms.

### Sources deliberately not selected for this notebook

Do not add Fandai, Tindex, TGJU, GDELT, FRED, World Bank, Telegram/social feeds or a paid market-data vendor to this event-correction pilot:
- they do not replace official issuer/market event evidence;
- earlier project reviews already documented limited history, failed probes, uncertain reuse terms or unrelated asset coverage for several of them;
- another source would widen the work without resolving the specific TSETMC event/date/price-basis blockers.

A separately licensed independent adjusted-price reference may be considered later **only** if official TSETMC chart/API reconciliation remains ambiguous and rights are documented. It is not a prerequisite for the first event inventory.

## 4. Exact event taxonomy — include only what can change price basis or explain a missing/changed observation

### A. Corporate actions that may change per-share price basis

These must be recorded individually; do not collapse them into a generic capital_change event.

1. **Cash dividend / DPS:** approved per-share distribution, ex-dividend/effective date, record date and payment date. Distinguish declared, approved, payable and paid amounts.
2. **Capital increase from reserves/retained earnings or bonus shares:** old/new share counts and effective date.
3. **Capital increase from cash contribution / receivables:** old/new shares, subscription price, rights issue, rights trading/expiry and payment terms. The old/new share ratio alone is insufficient.
4. **Mixed-source capital increase:** split each funding component and calculate only after all components are evidenced.
5. **Stock split / reverse split / nominal-value or share-unit conversion:** ratio and effective date; distinguish a real share-count conversion from a simple display-unit change.
6. **Rights distribution or separate rights instrument:** link the right's own identity and lifecycle; do not merge its price series into the ordinary share.
7. **Merger, demerger, spin-off, conversion or exchange of securities:** predecessor/successor identifiers, conversion ratio, consideration and effective date. If terms/value cannot be reconciled, end one series and start another rather than fabricate continuity.
8. **Rights/security conversion event (including conversion of rights into ordinary shares):** record the rights instrument, entitlement, conversion/exercise ratio, cash paid and effective date; do not merge the rights-price series into ordinary-share prices without a documented conversion.

### B. Market-state and identity events that explain dates or price observations but are not automatic adjustment factors

1. Official non-trading day / market holiday / exceptional closure.
2. Trading suspension, restriction, halt and reopening; record exact status and effective session.
3. IPO / first trading date, relisting, delisting and end-of-history boundary.
4. Symbol, ISIN, insCode, issuer, board/market or instrument-type change; preserve a dated identity crosswalk.
5. No-trade day, zero-volume/stale carried price, cancelled/corrected trade, auction/opening call or abnormal trading session.
6. Price limit, tick-size or market-rule change. Record the rule regime; it is not a corporate-action factor.
7. Quote denomination / Rial–Toman / nominal-value display scale change. This is a unit normalization with its own evidence, not a return adjustment.

A holiday has no price observation to adjust. A suspension is not a zero return. A reopening gap may be a genuine market repricing and must not be smoothed away.

### C. Explicitly out of scope as mechanical price adjustments

- Company profit/EPS/revenue/production increases or decreases.
- Monthly operating reports and sales margins.
- FX, inflation, interest rates, commodity prices, industry cycles and macro policy.
- News, management changes, shareholder transactions, buy/sell queues and sentiment.

These can be fundamental or explanatory research inputs later. They do not mechanically alter the historical number of shares or the cash entitlement per share. Record them in the separate fundamental/news research stream only when that stream is commissioned; do not expand this adjustment notebook to collect them now.

## 5. Canonical event record and time model

One row per **economic event**, with source observations stored as linked evidence records. Required fields:

| Field | Meaning / rule |
|---|---|
| event_key | Stable internal key; never use nearest-date match as identity |
| primary_ins_code, isin, issuer_id, symbol_at_event | Identity crosswalk at the effective date; preserve historic values |
| event_class, event_subtype | Use the taxonomy in §4 |
| source_system, source_event_id, notice_tracing_no, document_url | Exact source/event/document references |
| published_at_source_text, published_at_utc, updated_at, retrieved_at_utc | Preserve raw source text; only normalize when Jalali calendar/time-zone semantics and amendments are proven |
| decision_date, record_date, ex_date, effective_date, payment_date | Separate dates; never substitute announcement date for effective date |
| status | proposed / approved / effective / paid / cancelled / corrected / unknown |
| old_shares, new_shares, cash_per_share, subscription_price, rights_ratio, consideration | Typed event payload; null when not evidenced |
| price_factor_source, factor_formula, factor_value, factor_direction | Store provider factor and independently derived factor separately |
| unit_currency, price_scale | Explicit price and quantity units at event |
| raw_response_sha256, document_sha256, parser_version | Reproducible lineage |
| evidence_status, review_status, review_note | See controlled states below |

Controlled evidence states:
- DISCOVERED_UNVERIFIED
- IDENTITY_VERIFIED
- TERMS_VERIFIED
- EFFECTIVE_DATE_VERIFIED
- ECONOMIC_FORMULA_VERIFIED
- CROSS_SOURCE_RECONCILED
- ACCEPTED_FOR_CANDIDATE_SERIES
- REJECTED
- CONFLICT
- UNKNOWN

A candidate match within ±7 days may create a review suggestion only. It must never merge or deduplicate two events, change an effective date, or create an adjustment factor. Link by exact source event/notice identifier, verified security identity and the source's documented reference. Calendar offsets are diagnostic metadata, not join keys.

## 6. Price and return treatment rules

Keep three distinct outputs:

1. **Raw traded-price series:** immutable source OHLCV; never rewrite.
2. **Price-return adjusted series:** adjusts only verified mechanical changes to the per-share price basis; clearly records whether cash dividends are excluded.
3. **Total-return series:** includes verified cash distributions under a documented reinvestment/entitlement convention. Never label a total-return series as a price series.

Event-specific rules:
- **Cash dividend:** verify approved DPS, ex-date, entitlement and whether the source's adjusted chart incorporates cash distributions. Do not use a declared or proposed dividend as paid/entitled cash.
- **Cash capital increase:** calculate theoretical ex-right price only after old/new shares, subscription price, rights entitlement and effective date are verified. The simple old/new-share ratio is not sufficient.
- **Reserve/bonus capital increase or split:** use verified conversion ratios, effective date and instrument continuity.
- **Mixed increases:** calculate components separately and reconcile their combined theoretical price.
- **Merger/spin-off/security conversion:** use documented conversion/consideration terms; otherwise quarantine the boundary.
- **Volume:** never multiply volume by a total-return price factor. A share-count conversion may require a separate volume transformation, with its own formula and validation.
- **Suspension/holiday/no-trade:** do not insert a synthetic price or return. Attach market-state evidence and keep the observation missing/stale as appropriate.

Store the TSETMC factor, TSE Client factor and independently reconstructed factor in separate columns. Do not combine them until the event economics are proven.

## 7. Bounded investigation plan — three-symbol pilot only

### Step 1 — Verify the selected REST contract (one bounded pass)

Retrieve and archive, without credentials:
- the official api.tsetmc.com/docs/ document/OpenAPI description;
- service host, auth/account requirements, quotas, terms/use restrictions and version;
- endpoint catalog and response schemas for instrument master, historical daily data, market/session state, market messages/notices, dividends/distributions, capital changes, price adjustments and history revisions (only those that exist in the documented API);
- whether the service returns or links CODAL notice IDs/documents and whether its data cover historical events or only current state.

Record access from the owner's intended Iranian network as VPN OFF and separately record any documented regional restrictions. Do not evade access controls. Do not guess undocumented routes if the docs remain unavailable.

### Step 2 — Reuse the already captured pilot files

Use existing local source snapshots and event outputs for فولاد, وغدیر and پارسیان. Record their SHA-256 values and retrieval times. Do not redownload identical history. Resolve the contradictory raw-chart audit described in §2.2 before using its historical scale/precision conclusions.

### Step 3 — Create the event inventory

For each pilot security, list every source-discovered event by exact identifier and subtype. Link the TSETMC event to a CODAL notice only when the source document/notice reference, instrument identity and event terms agree. Preserve unmatched events and conflicting duplicates as separate review rows.

### Step 4 — Build the market-session timeline

For all candidate-history date gaps and apparent stale/zero-trade observations, classify only as:
- scheduled non-trading day/holiday;
- exceptional market closure;
- suspension/restriction;
- listing/relisting/delisting boundary;
- no trade/stale carried observation;
- source omission;
- unresolved.

Use the documented market calendar and instrument-status/messages endpoints if present. A date match to a nearby notice is not sufficient; retain evidence URL/ID and exact effective session.

### Step 5 — Reconcile a small, predeclared sample before expanding

For each symbol, review:
- at least one no-action interval;
- each distinct corporate-action subtype actually present;
- the oldest unresolved event cluster;
- at least one suspension/reopening or long date gap, if present;
- one recent event for which full disclosure terms are available.

Do not spend time manually reviewing every event before the endpoint/schema and subtype mapping are understood. Expand to all events only after the sample demonstrates the correct extraction logic.

### Step 6 — Calculate only evidence-backed factors

For each accepted event, retain:
- source factor and source rule;
- independent terms-based formula and input fields;
- effective date;
- resulting factor direction and compounding order;
- reconciliation difference against the TSETMC adjusted chart;
- an explicit reason for any residual difference.

Do not use a blanket ±7-day overlap suppression. Do not fit factors to make the chart match. If the official chart's convention is unknown or revised, mark the interval unresolved.

## 8. Acceptance criteria for the three pilot symbols

A symbol is accepted only for the specific date range and series type that pass all applicable checks:

1. Security identity and historic continuity are evidenced for every interval.
2. Every observed corporate action is classified; unmatched source events and unresolved date gaps are visible.
3. Relevant issuer terms and exact effective dates are verified from original notices or equivalent primary evidence.
4. Price units, Rial/Toman convention, display scale, raw/adjusted status and OHLC field semantics are confirmed.
5. Raw daily prices reconcile to the selected source for the same dates/fields; conflicting diagnostic reports are resolved.
6. Every accepted adjustment factor can be reproduced from preserved inputs and documented event terms.
7. Adjusted chart reconciliation is reported using exact price ticks/absolute tolerances as well as relative error; low-price historical rows must not be judged only by relative percentage.
8. Suspensions, holidays, no-trade days, first/last listing dates and corrections are classified without synthetic prices.
9. Retrieval time, publication/update time and point-in-time availability semantics are preserved.
10. Applicable rights for access, storage, internal research, derivatives and redistribution are explicitly reviewed.

Failure of one interval does not automatically reject the whole instrument: quarantine only the unsupported range, but do not bridge it with an invented factor.

## 9. Current source and task decisions

| Item | Decision |
|---|---|
| Primary authenticated market-data candidate | TSETMC new REST — documentation mirror inspected; credentials, roles/credit, exact rights and live three-symbol contract test remain open |
| Existing CDN REST routes | Reuse captured data; candidate-only; do not equate them with the new official service |
| CODAL | Targeted original-notice verification only; existing adapter remains quarantined until time/revision semantics are solved |
| TSE Client 2.27.6 | Diagnostic reference implementation only; not the legal/source-of-truth authority |
| Fandai / vendor feeds | Not selected; no subscription or API purchase for this task |
| Macro, news, sentiment and social feeds | Excluded from this notebook |
| Adjustment algorithm | Not selected; only after the event ledger and price semantics are verified |
| Production/scoring/backtest | Remain disabled |

## 10. Source references and known limitations

1. TSETMC new REST launch report (2025-12-27 / 1404-10-06): https://armaneghtesadi.com/954797/1404/10/06/نسخه-جدید-وبسرویس-tsetmc-منتشر-شد/
2. Official TSETMC REST documentation entry point: https://api.tsetmc.com/docs/
3. Documentation content mirror, with latest inspected commit and author metadata: https://github.com/m-idasa/Documents/commit/dcc57eb6dea36c036e55824bcfa676c7713ca829
4. Core mirror pages: https://github.com/m-idasa/Documents/blob/main/Authentication.md, https://github.com/m-idasa/Documents/blob/main/Instrument.md, https://github.com/m-idasa/Documents/blob/main/InstrumentTseShare.md, https://github.com/m-idasa/Documents/blob/main/InstrumentStateChange.md, https://github.com/m-idasa/Documents/blob/main/NSCStart.md, https://github.com/m-idasa/Documents/blob/main/InstTrade.md, https://github.com/m-idasa/Documents/blob/main/TradeOneDayAll.md, https://github.com/m-idasa/Documents/blob/main/Company.md
5. Existing repository acceptance record and owner action: https://github.com/yarsalam/marketsage/issues/40
6. Community-maintained reverse-engineered CDN endpoint catalog, useful only for discovery/schema hypotheses—not the authenticated REST contract: https://github.com/amirziveh/tsetmc-skill/blob/master/references/api-endpoints.md
7. Existing source contracts and quarantine rules: IRAN_SOURCE_ACCEPTANCE.md, SOURCE_ACCEPTANCE_EVIDENCE.md, user/analysis-engine/source_registry.py, and user/analysis-engine/source_acceptance.py.

**Final rule:** a source response, successful parser, validGPLRatio=true, exact raw-price match or chart similarity is not sufficient by itself. The evidence chain is: verified security → verified event and terms → verified effective date → reproducible factor → reconciled history → documented rights and point-in-time availability. Until then, remain candidate-only.


## 11. Comparative audit of public extraction implementations

**Review date:** 2026-11-12  
**Purpose:** reuse working extraction and parsing ideas without importing an unverified adjustment rule. This is a static code/fixture review plus comparison with the owner's previously reported pilot aggregates. No live requests, new downloads, local candidate-data changes or factor calculations were performed in this review.

### 11.1 Projects inspected and evidence strength

| Project | Revision inspected | What was inspected | Evidence level for this pilot |
|---|---|---|---|
| [Fazel94/yfinance-ir](https://github.com/Fazel94/yfinance-ir) | latest repository commit observed: `c36745e568b5aa7631813dbcd41d96c8af92315e`, 2026-10-11 | TSETMC adapter, adjustment logic in `history.py`, conventions/data-source docs, unit tests and Foulad event fixtures | **Direct Foulad fixture overlap** (23 price-adjustment rows + 12 share-change rows); not a verified event ledger and not a direct row-hash comparison to the owner's local snapshot |
| [msmahdinejad/iran-bourse-mcp](https://github.com/msmahdinejad/iran-bourse-mcp) | latest repository commit observed: `02d6373cc29190bde428bb9114f73f212c0b49a8`, 2026-11-11 | market-wide event-calendar implementation, CODAL parser, source/quirk documentation, recorded fixtures and calendar tests | **Strong method/edge-case evidence**, but the inspected test fixtures exercise other symbols; no direct three-pilot-symbol event fixture was established |
| MarketSage local three-symbol work | owner terminal results already recorded in §2.2 | existing TSETMC CDN event counts and TSE Client comparisons | **Pilot aggregate evidence**; row-level event payloads and saved hashes are not currently available in this review context for a fresh exact re-comparison |

The two public projects are community implementations, not TSETMC/CODAL source-of-truth authorities. Their GitHub code, test results and fixture data do not establish MarketSage's rights to redistribute upstream market data.

### 11.2 Foulad: a concrete overlap with yfinance-ir

The inspected yfinance-ir fixtures contain:

| Fixture | Rows | Instrument | Event-date span |
|---|---:|---|---|
| `tsetmc_adjust_folad.json` | 23 | InsCode `46348559193224090` | 2009-06-23 to 2026-08-03 |
| `tsetmc_sharechange_folad.json` | 12 | InsCode `46348559193224090` | 2011-02-14 to 2026-03-30 |

These counts and the InsCode agree with the owner's previously reported Foulad `GetPriceAdjustList` (23) and `GetInstrumentShareChange` (12) results. The fixture contains actual event payload fields, including `dEven`, `pClosing`, `pClosingNotAdjusted`, `numberOfShareOld` and `numberOfShareNew`. It is useful as a second preserved example of the legacy CDN response shape.

**What this does not prove:** the owner's original raw JSON files were not available here for a byte/hash comparison. Matching counts and instrument identity are strong overlap indicators, not proof that the two snapshots are byte-identical, complete, or independently verified. The Foulad fixture also does not supply the issuer's CODAL resolution or capital-increase funding source.

A previous owner-side offline audit of the Foulad snapshot recorded 12 share-change rows and 23 price-adjustment rows, with five exact-date overlaps and six share changes having a price-adjustment date within ±7 calendar days. The same audit listed seven share-change dates not paired within yfinance-ir's ±3-day rule:

- 2020-01-12
- 2021-05-24
- 2022-08-09
- 2023-03-19
- 2024-02-27
- 2025-03-12
- 2026-03-30

This list is a diagnostic derived from the previously supplied Foulad audit, not proof that all seven are bonus issues or that their nearest price-adjustment row is related. The 2022-08-09 share-change date is six calendar days after a 2022-08-03 price-adjustment row; the other dates are farther away in the supplied diagnostic. **CODAL terms and the exact effective session must decide the event type, not the proximity rule.**

### 11.3 yfinance-ir: useful extraction, unsafe default classification

The inspected implementation uses these two legacy TSETMC feeds:

- `GetPriceAdjustList`: uses `pClosing / pClosingNotAdjusted` as a price ratio and applies the ratio to bars strictly before the event date.
- `GetInstrumentShareChange`: provides old/new share counts and event date.

Its current event classification works as follows:

1. A price-adjustment row with no share-change row within ±3 calendar days is classified as a cash dividend; the cash amount is inferred from the difference between the two reference prices.
2. A share-change row found within ±3 calendar days is linked to that price-adjustment row and exposed as a split/share-change event.
3. **Every share-count change left unpaired after that search is treated as a bonus issue**, with an `old/new` historical-price factor.

The project documentation itself warns that this last assumption over-adjusts a cash-funded rights issue because the TSETMC share-count feed does not reveal the funding source. This is not a minor edge case: the Foulad audit above has seven share-change rows outside the ±3-day association rule. If the same implementation is used as-is, those rows are mechanically classified as bonus issues even though their funding composition has not been evidenced here.

The project's tests demonstrate the arithmetic and output shape, including synthetic cases for cash adjustment, a paired share-count change and an unpaired bonus issue. Those tests are valuable for regression coverage, but the unpaired-bonus test asserts the same assumption; it does not prove that a real Iranian rights issue can safely be classified that way.

**MarketSage decision:** reuse the endpoint wrappers, schema examples, immutable raw-response approach and parser/test ideas. Do **not** reuse its automatic "unpaired share increase = bonus issue" decision or its adjusted series as a MarketSage accepted series. An unpaired share change must remain `DISCOVERED_UNVERIFIED` until a primary notice establishes funding type, subscription price, entitlement, rights terms and effective date.

### 11.4 iran-bourse-mcp: stronger event discovery and market-state handling, still not economic proof

The inspected `calendar_events.py` separates two market-wide feeds by exchange flow:

- `Instrument/GetInstrumentShareChangeByFlow/{flow}/{top}`: share-count changes with old/new quantities, date and instrument identity.
- `ClosingPrice/GetPriceAdjustByFlow/{flow}/{top}`: price-adjustment observations with adjusted/unadjusted reference prices; symbol identity is nested under `instrument`, while the top-level `insCode` can be zero.

Its useful event-discovery safeguards include:

- **Temporary share-count round trips:** detect a temporary decrease followed by restoration to approximately the previous count within ten days (the documented observed examples were restored within one to eight days, with a 1% ratio tolerance). These are tagged as bookkeeping/round-trip pairs rather than treated as genuine capital decreases.
- **Rights instruments:** zero-share records are labelled as rights-symbol lifecycle events rather than ordinary capital increases/decreases.
- **Extreme price ratios:** factors outside its configured 0.1–10 range are flagged for investigation rather than silently accepted.
- **Coverage reporting:** output records the date coverage of the share-change and price-adjustment feeds and warns when an adjustment list may be truncated.
- **CODAL separation:** it explicitly says the market feeds do not contain DPS, AGM/ex-dividend details, rights exercise price or subscription deadlines; those terms require the linked issuer notice.

Its tests use recorded market responses dated 2026-11-04 plus synthetic edge cases. They cover round-trip detection, rights-symbol handling, genuine decreases, multiple flows, extreme factors and truncation. The recorded examples in the inspected tests include other symbols (for example لبوتان، غچین، شستا، کرازی و تاصیکو), not فولاد، وغدیر or پارسیان. Thus the implementation demonstrates useful market-wide handling patterns, but its fixture tests do **not** independently reconcile our three pilot event ledgers.

There is a second caution in its source notes: the project says `GetPriceAdjustList` misses some capital-increase price adjustments (it cites Foulad's 2026-03-30 share-count change from 1.5T to 1.935T shares) and describes inferring a candidate adjustment from a discontinuity between `priceYesterday` and the previous `pClosing`. The same notes acknowledge that this continuity method can fail over silent/no-trade days and that older history sometimes lacks the required continuity. That is useful for **finding an unresolved candidate**, not for asserting the economic event type or accepting a factor.

**MarketSage decision:** reuse the distinction between genuine share changes, temporary round trips and rights-symbol lifecycle records; reuse per-flow coverage reporting, explicit truncation warnings and the CODAL-linked evidence workflow. Do not copy its inferred price-discontinuity factor into the canonical adjustment ledger as an accepted factor. It remains a candidate diagnostic requiring original event terms and independent reconciliation.

### 11.5 Side-by-side decision

| Capability | yfinance-ir | iran-bourse-mcp | MarketSage rule |
|---|---|---|---|
| Raw TSETMC event-feed access | Per-instrument CDN wrappers | Market-wide, flow-based wrappers | Preserve exact upstream payload and its retrieval metadata |
| Foulad sample fixture | Yes: 23 price-adjust + 12 share-change records | No direct Foulad fixture established in inspected tests | Treat yfinance fixture as a schema/overlap reference, not a second economic authority |
| Vaghdir / Parsian direct fixture comparison | No direct event fixtures found in inspected yfinance tree | No direct fixture test established for either pilot symbol | Keep their prior counts as owner evidence; obtain exact raw JSON snapshots before claiming row-level external comparison |
| Share-count round-trip handling | No dedicated round-trip classification in inspected rule | Explicit pair detection and tests | Adopt as a *candidate classification*, then verify with identity, exact dates and market records |
| Rights-symbol separation | Not established in inspected adjustment rule | Explicitly handled | Preserve separate rights security identity and lifecycle |
| Unpaired share increase | Assumes bonus issue | Labels increase/decrease by counts; does not establish funding source | Never infer funding source from share counts alone |
| Adjustment-factor generation | Applies feed ratios and inferred unpaired-share ratios | Parses provider adjustment ratios and documents a separate discontinuity inference | Keep provider ratios separate from independently reconstructed, terms-based factors; no inference is accepted automatically |
| CODAL role | Includes filing parser/search and statement extraction | Links original filings and parses structured/plain letters | Use exact notice/TracingNo and original resolution to verify economic terms, dates and amendments |

### 11.6 Impact on the three-symbol pilot

| Symbol | Existing owner-side result | Public implementation comparison now possible | Current interpretation |
|---|---|---|---|
| فولاد | 23 price-adjust rows; 12 share-change rows; TSE Client comparison 23/23 and 12/12 in the prior ±7-day diagnostic | yfinance-ir provides 23 + 12 Foulad fixture rows for the same InsCode and event-feed schema; no hash-level comparison to the owner's raw files | Direct fixture overlap is confirmed at instrument/count level. The seven unpaired-by-±3-day share changes are unresolved event classifications, not proven bonus issues. |
| وغدیر | 25 price-adjust rows; 7 share-change rows; prior TSE Client diagnostic 13/25 and 3/7 | No direct yfinance-ir fixture in the inspected tree; no iran-bourse-mcp test fixture specific to the pilot symbol | No row-by-row public implementation reconciliation yet. Obtain the exact saved raw payloads and original notices before comparing individual rows. |
| پارسیان | 18 price-adjust rows; 9 share-change rows; prior TSE Client diagnostic 12/18 and 7/9 | No direct yfinance-ir fixture in the inspected tree; no iran-bourse-mcp test fixture specific to the pilot symbol | No row-by-row public implementation reconciliation yet. Obtain the exact saved raw payloads and original notices before comparing individual rows. |

The prior ±7-day TSE Client percentages above remain discovery diagnostics only. They do not become stronger evidence merely because a third-party project uses ±3-day association. No event is merged, removed or reclassified by calendar proximity in this notebook.

### 11.7 Reuse decision and next evidence needed

1. **Reuse, do not copy wholesale:** yfinance-ir's TSETMC/CODAL transport and payload parsing examples; iran-bourse-mcp's round-trip, rights-symbol and market-flow coverage handling; MarketSage's own provenance, quarantine and evidence-ledger gates.
2. **Reject as a decision rule:** classifying every unpaired share increase as a bonus issue; inferring a factor from a price gap/priceYesterday discontinuity without event terms; treating a test fixture or successful HTTP response as economic verification.
3. **For فولاد:** compare the complete local raw event JSON hashes and row payloads against the public 23/12 fixtures when those exact local files are available; then resolve the seven unpaired share-count dates from original CODAL notices.
4. **For وغدیر and پارسیان:** reuse the existing captured raw TSETMC event payloads and TSE Client records; do not redownload them just to reproduce counts. Compare exact event identifiers, dates and ratios, and link each unresolved event to an original CODAL notice. The required source payloads were not present in the reviewed Library artifacts, so this notebook does not claim those row-level comparisons were performed.
5. **For all three:** retain TSETMC price-adjust ratios, share-count changes, TSE Client diagnostics and terms-based independent calculations in separate fields. A disagreement produces `CONFLICT` or `UNKNOWN`, not an averaged factor.

### 11.8 Sources inspected

8. yfinance-ir TSETMC adapter: https://github.com/Fazel94/yfinance-ir/blob/main/yfinance_ir/sources/tsetmc.py
9. yfinance-ir adjustment and history logic: https://github.com/Fazel94/yfinance-ir/blob/main/yfinance_ir/history.py
10. yfinance-ir event conventions: https://github.com/Fazel94/yfinance-ir/blob/main/docs/conventions.md
11. yfinance-ir source limitations: https://github.com/Fazel94/yfinance-ir/blob/main/docs/data-sources.md
12. yfinance-ir Foulad event fixtures: https://github.com/Fazel94/yfinance-ir/tree/main/tests/fixtures
13. yfinance-ir history tests: https://github.com/Fazel94/yfinance-ir/blob/main/tests/test_history.py
14. iran-bourse-mcp event calendar implementation: https://github.com/msmahdinejad/iran-bourse-mcp/blob/main/src/iran_bourse_mcp/calendar_events.py
15. iran-bourse-mcp source/quirk notes: https://github.com/msmahdinejad/iran-bourse-mcp/blob/main/docs/DATA_SOURCES.md
16. iran-bourse-mcp recorded fixture and event-calendar tests: https://github.com/msmahdinejad/iran-bourse-mcp/blob/main/tests/test_calendar_events.py
17. iran-bourse-mcp CODAL parser: https://github.com/msmahdinejad/iran-bourse-mcp/blob/main/src/iran_bourse_mcp/codal_reports.py

**Final rule:** a public extractor demonstrates a method, not the economic truth of the event. Reuse parsers and robust edge-case handling, but the accepted evidence chain remains verified instrument identity → exact source event/document → terms and effective date → reproducible independent factor → reconciled historical series → reviewed data rights and point-in-time availability. No source, event, adjusted series or investment use is approved by this comparative audit.
