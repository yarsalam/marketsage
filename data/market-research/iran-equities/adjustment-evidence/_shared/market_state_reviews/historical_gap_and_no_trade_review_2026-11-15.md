# Historical Market-State, Long-Gap and No-Trade Review

**Review date:** 2026-11-15  
**Scope:** TSETMC daily-history pilot for وغدیر (Vaghdir), فولاد (Foolad) and پارسیان (Parsian).  
**Status:** Research-only; unresolved market-state intervals remain quarantined. No price adjustment, imputation, deletion or interval acceptance was performed.

## 1. Executive result

This review checked the three previously flagged long calendar gaps against the imported TSETMC raw-chart snapshots, the existing daily-history audit, and available historical secondary records.

The evidence supports these conclusions:

1. The imported daily history and the separately archived TSETMC raw-chart observations match exactly on every shared date and all compared raw fields. The comparison covers 5,383 Vaghdir dates, 4,266 Foolad dates and 3,539 Parsian dates.
2. The daily-history files contain an additional 305 Vaghdir, 414 Foolad and 327 Parsian records that are absent from the corresponding transaction/chart date sets. These counts align with the previously audited zero-activity observations. They must be preserved as source observations and classified; they must not be silently dropped or forward-filled into a transaction series.
3. The Vaghdir gaps of 173 and 121 calendar days are confirmed as gaps in the archived TSETMC raw-chart date sequence. Their cause is **not established** by primary market-status or issuer evidence in the reviewed repository.
4. The Foolad 43-day gap is also present in the archived raw-chart sequence. A contemporary secondary page reports a suspension on 19 Shahrivar 1387, but the TSETMC chart archive contains a traded observation on 13 September 2008 (23 Shahrivar 1387), after that reported date. This is a material date conflict. The stop date and status chronology must therefore remain unresolved until the original exchange status record is obtained.
5. Parsian's largest calendar gap in the archived raw-chart series is 10 days. This review did not establish a suspension or a market-wide closure for those dates.
6. No evidence reviewed here establishes that the Vaghdir gaps were caused by war, a country-wide exchange closure or another exceptional market closure. No such explanation is assigned.

**Disposition:** all three long-gap cases remain `UNRESOLVED_MARKET_STATE`; zero-activity rows remain preserved as `NO_TRADE_OR_STALE_PRICE_CANDIDATE`. None of these findings is an adjustment factor.

## 2. Method and limits

- Compared the imported daily histories with the separately archived decoded TSETMC raw-chart CSVs by exact trading date and raw price/volume fields.
- Read the endpoint rows surrounding each long gap; calendar-day differences are not interpreted as missing exchange sessions.
- Used secondary historical pages only as search leads and coverage cross-checks. They are not substitutes for TSETMC/Exchange status messages, issuer disclosures or official session calendars.
- Did not infer a halt from the absence of price rows, a price discontinuity, a vendor's sparse coverage or proximity to a news item.
- No original historical `InstrumentStateChange` response, complete official session calendar, or primary stop/reopening notice for the reviewed dates was present in the committed evidence set.
- The raw-chart CSV Git blob IDs below are repository object identifiers, not SHA-256 file digests.

## 3. Gap-by-gap findings

### 3.1 Vaghdir — 2006-09-05 to 2007-02-25 (173 calendar days)

| Evidence date | Raw-chart close | Raw-chart volume | Observation |
|---|---:|---:|---|
| 2006-09-05 | 3,992 | 20 | Extremely small reported volume at the last observation before the gap |
| 2007-02-25 | 3,397 | 1,786,236 | First archived chart observation after the gap |
| 2007-02-26 | 3,330 | 931,480 | Subsequent observed trading day |

The date gap is present in the archived TSETMC raw-chart sequence. The final pre-gap row has only 20 units of volume, which is consistent with very thin activity but does not establish a suspension or a halt.

The secondary BourseEye annual history for 1385 describes 86 recorded trading days over 5 Farvardin–21 Esfand 1385 and shows observations in mid-Shahrivar and again in Esfand. This supports the conclusion that the secondary history itself has sparse coverage in that year; it does not identify the official reason for the missing interval and must not be treated as a complete exchange calendar.

**Classification:** `UNRESOLVED_SYMBOL_LEVEL_NON_OBSERVATION_OR_SOURCE_COVERAGE`  
**Not established:** official suspension start/end, issuer reason, exchange-wide closure, war-related closure, or a corporate action explaining the interval.

### 3.2 Vaghdir — 2008-01-20 to 2008-05-20 (121 calendar days)

| Evidence date | Raw-chart close | Raw-chart volume | Observation |
|---|---:|---:|---|
| 2008-01-20 | 1,644 | 4,030 | Last archived chart observation before the gap |
| 2008-05-20 | 1,644 | 11,878,333 | First archived chart observation after the gap |
| 2008-05-21 | 1,600 | 1,750,065 | Subsequent observed trading day |

The start row corresponds to 30 Dey 1386 and the first post-gap row to 31 Ordibehesht 1387. BourseEye's secondary yearly history says its Vaghdir page has 106 recorded trading days from 18 Farvardin to 30 Dey 1386 and 150 from 31 Ordibehesht to 28 Esfand 1387. The secondary source therefore independently shows the same broad coverage boundary. It still does not establish why Vaghdir has no archived observations in between.

The same closing value (1,644) on the two endpoints must not be interpreted as proof that the security was continuously tradable or that the period had zero economic return. It is only the equality of two observed endpoint fields separated by 121 calendar days.

**Classification:** `UNRESOLVED_SYMBOL_LEVEL_NON_OBSERVATION_OR_SOURCE_COVERAGE`  
**Not established:** suspension/reopening chronology, official reason, issuer disclosure, market-wide closure or war-related cause.

### 3.3 Foolad — 2008-09-13 to 2008-10-26 (43 calendar days)

| Evidence date | Raw-chart close | Raw-chart volume | Observation |
|---|---:|---:|---|
| 2008-09-08 | 3,701 | 7,663,666 | Trading before the gap |
| 2008-09-13 | 3,197 | 4,206,058 | Last archived observation before the gap; non-zero activity |
| 2008-10-26 | 2,200 | 18,805,891 | First archived observation after the gap; non-zero activity |
| 2008-10-29 | 2,338 | 347,203 | Subsequent observed trading day |

The last-to-first observed close change is:

`(2,200 / 3,197) - 1 = -31.19%` (approximately).

This is an observed market-price change across a long interval without an archived Foolad chart row. It is **not** a corporate-action factor and must not be smoothed, backfilled or automatically attributed to a dividend/capital increase.

A contemporary secondary blog page dated 28 Shahrivar 1387 reports that Foolad's symbol was stopped on 19 Shahrivar 1387, citing recent share-price movements, global steel-price declines, domestic iron-ore price changes and uncertainty over the steel employees' pension-fund contribution. However, the archived TSETMC raw chart has a non-zero-volume observation on 13 September 2008 (23 Shahrivar 1387), four days after the reported stop date. The secondary report and the transaction-date evidence therefore conflict on the effective stop chronology. Possible explanations cannot be selected without the original status record; this review does not assume the report date or the chart row is wrong.

**Classification:** `UNRESOLVED_STATUS_DATE_CONFLICT`  
**Required evidence:** original TSETMC instrument status transitions and/or official exchange/issuer notice giving the exact stop, reopening and first eligible trading session. Keep the 31.19% observed price change separate from adjustment calculations.

## 4. Parsian — no long gap over 10 calendar days in this scan

The archived Parsian raw-chart sequence has no consecutive-observation gap greater than 10 calendar days in the reviewed scan. This is a limited statement about the archived series only. It does not prove there were no shorter suspensions, no-trade sessions, stale observations or data omissions. The current record remains subject to the same source-status and market-calendar checks as the other pilots.

## 5. Zero-activity records and chart reconciliation

The prior read-only daily-history audit found the following zero-volume/zero-trade candidate records:

| Symbol | Daily-history rows | Zero-activity candidate rows | Raw-chart dates shared with daily history | Daily-history dates absent from raw chart |
|---|---:|---:|---:|---:|
| Vaghdir | 5,688 | 305 | 5,383 | 305 |
| Foolad | 4,680 | 414 | 4,266 | 414 |
| Parsian | 3,866 | 327 | 3,539 | 327 |
| **Total** | **14,234** | **1,046** | **13,188** | **1,046** |

For the 20 sampled zero-activity records per symbol in the daily-history audit, closing-price observations were carried at the prior reference/close while volume, trade count and traded value were zero. The sample supports a stale/no-trade interpretation for those examples, not an unqualified statement about every row's cause.

For all shared dates, the archived chart comparison reports exact agreement (100%) for the compared raw open/high/low/last/close/volume fields:
- Vaghdir: 5,383 / 5,383 shared dates.
- Foolad: 4,266 / 4,266 shared dates.
- Parsian: 3,539 / 3,539 shared dates.

This establishes strong raw-field reconciliation on shared dates. It does **not** prove that the daily-history source contains a complete trading calendar, explain the additional zero-activity rows, or establish suspension dates. Do not delete these records from the immutable raw layer. A derived transaction-only view may exclude them only under a documented, separately tested filter and must retain a trace back to the raw source row.

## 6. Source register and reproducibility anchors

### Committed evidence files

| Evidence | Repository path | Git blob/object ID |
|---|---|---|
| Vaghdir raw chart | `data/market-research/iran-equities/adjustment-evidence/_shared/official_chart_validation/vaghdir_official_chart_raw.decoded.csv` | `287ff48a8c636ec6cee0e22316ff2a2d5c2f7e6e` |
| Foolad raw chart | `data/market-research/iran-equities/adjustment-evidence/_shared/official_chart_validation/foolad_official_chart_raw.decoded.csv` | `8fee7ccdf94c7cb913507950230e79c726231b0f` |
| Parsian raw chart | `data/market-research/iran-equities/adjustment-evidence/_shared/official_chart_validation/parsian_official_chart_raw.decoded.csv` | `6998abdd5bb1ef61aa9ad12be199bc6e509ec52c` |
| Three-symbol raw-chart comparison | `data/market-research/iran-equities/adjustment-evidence/_shared/official_chart_validation/three_symbols_official_chart_comparison.json` | `3d33b846ca0081a8fb9cfefd11add2d6df17c668` |
| Identity audit | `data/market-research/iran-equities/adjustment-evidence/_shared/identity_integrity/tsetmc_event_feed_identity_audit_2026-11-15.json` | `f2b90a7577025b3b7d07ca1a2f05cf63af6de953` |

The imported daily raw files' SHA-256 digests are recorded in each symbol's `source-register.csv`; those raw files were not changed during this review.

### External historical locators (secondary; not status authority)

- BourseEye, Vaghdir 1385 history: https://bourseeye.com/stocks/137/%D9%88%D8%BA%D8%AF%DB%8C%D8%B1-%D8%B3%D8%B1%D9%85%D8%A7%DB%8C%D9%87-%DA%AF%D8%B0%D8%A7%D8%B1%DB%8C-%D8%BA%D8%AF%DB%8C%D8%B1-%D9%87%D9%84%D8%AF%DB%8C%D9%86%DA%AF/history?year=1385
- BourseEye, Vaghdir 1386 history: https://bourseeye.com/stocks/137/%D9%88%D8%BA%D8%AF%DB%8C%D8%B1-%D8%B3%D8%B1%D9%85%D8%A7%DB%8C%D9%87-%DA%AF%D8%B0%D8%A7%D8%B1%DB%8C-%D8%BA%D8%AF%DB%8C%D8%B1-%D9%87%D9%84%D8%AF%DB%8C%D9%86%DA%AF/history?year=1386
- BourseEye, Vaghdir 1387 history: https://bourseeye.com/stocks/137/%D9%88%D8%BA%D8%AF%DB%8C%D8%B1-%D8%B3%D8%B1%D9%85%D8%A7%DB%8C%D9%87-%DA%AF%D8%B0%D8%A7%D8%B1%DB%8C-%D8%BA%D8%AF%DB%8C%D8%B1-%D9%87%D9%84%D8%AF%DB%8C%D9%86%DA%AF/history?year=1387
- Contemporary secondary page, 28 Shahrivar 1387: https://tseblog.blogfa.com/1387/06 (contains the Foolad stop-date statement; contradicted by the later 13 September raw-chart trade row).

## 7. Required next evidence and processing steps

1. Obtain an authoritative historical market-session calendar for 1385–1387 and map dates to actual trading sessions. A Gregorian calendar-day gap alone cannot be converted into a number of missed sessions.
2. Obtain the original TSETMC instrument status-change records for these exact InsCodes and dates, including stop/reopening timestamps, status codes and reasons. The research notebook documents the TSETMC REST `InstrumentStateChange` endpoint as a candidate source, but live access/role/coverage and contractual terms remain unverified; no paid or credentialed call was made here.
3. Verify issuer-specific notices and exact notice identifiers for Vaghdir and Foolad. Where the status reason refers to a financial disclosure, link the notice and its amendments, not only a press summary.
4. Reconcile every zero-activity daily row against the official session calendar, symbol state and trade/cancellation messages. Keep separate flags for market closed, symbol halted, no execution, stale carried price, and source omission.
5. Only after the above, create a versioned derived market-state table. Do not alter raw source data.
6. Re-run the same checks for the full canonical instrument universe only after its dated, de-duplicated instrument master has been built.

## 8. Data and research gate

- Raw input layer: unchanged.
- Gap classification: unresolved as detailed above.
- Zero-activity rows: retained; classification pending.
- Corporate-action factors: none accepted by this review.
- Adjusted intervals: none newly approved.
- Investment analysis, forecast, ranking, backtesting and production release: not authorized by this report.

**Final disposition:** preserve the raw evidence, keep the affected intervals quarantined, and resolve the status-date conflicts from primary exchange/issuer records before calculating or accepting adjusted histories.
