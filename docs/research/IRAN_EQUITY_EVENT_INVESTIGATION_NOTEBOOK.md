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
