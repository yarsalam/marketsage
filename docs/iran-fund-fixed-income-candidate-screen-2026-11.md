# Iran fund NAV and secondary fixed-income candidate screen — 2026-11-05

**Status:** documentation-only discovery. No source is approved for automated collection, research-engine use, backtesting, scoring, ranking, or production.
**Scope:** Iranian mutual-fund/ETF NAV and AUM data, secondary-market bonds/sukuk/treasury bills, and a commercial data-vendor alternative.
**Network boundary:** public documentation and third-party project descriptions only. No provider API, site JSON, account, proxy, package installation, or dataset request was made.

## Executive disposition

Three additional candidates were identified:

1. **FIPIRAN public fund pages** — a newly published unofficial read-only wrapper describes public fund data for roughly 500 Iranian funds, including NAV, returns, fund size, unit flows, investor mix and manager metadata. It reports NAV in Rial per unit, fund size in billion Toman, and up to 60 evenly spaced history points. This is a useful fund-universe/NAV discovery lead, but not a complete daily history or an accepted API contract.
2. **Iran Fara Bourse (IFB) public pages/web service** — an unofficial read-only wrapper describes secondary-market treasury bills, sukuk and bonds, with daily price/YTM history, coupon schedules, maturity, issuer, quotes/order books and yield curves. It reports prices in Rial, YTM in percent per year and Jalali dates. This is a stronger lead for secondary-market fixed income than the CBI auction-PDF archive, but its exact history depth, endpoint contract, release timestamps and reuse rights remain unknown.
3. **Investats commercial data/API** — a vendor advertises Iranian equities, ETFs/funds, OHLCV, fund AUM/NAV/flows and other financial datasets. Its public pages self-report substantial aggregate coverage, including a daily AUM dataset for 298 funds. This is not free data; no quote, contract, sample download or license was obtained.

None of these sources was probed or integrated. The third-party MCP projects' MIT code licenses do not grant rights to the underlying exchange/fund data.

## Candidate comparison

| Candidate | Potential role | Evidence reported by public discovery material | Critical unknowns | Disposition |
|---|---|---|---|---|
| FIPIRAN (fipiran.ir) | Fund identity, NAV, fund size, flows, investor mix; potentially gold/fixed-income/equity fund monitoring | Unofficial `fipiran-mcp` README reports about 500 funds, no API key/account for public pages, daily NAV history with at most 60 evenly spaced points; NAV Rial/unit, fund size billion Toman, returns percent per period (not annualized) | Complete per-fund history, frequency and missing dates; issue/redemption NAV versus exchange price; first-publication and correction timestamps; stable IDs and TSETMC mapping; distribution/fee treatment; rate limits, terms and commercial/model-use rights | Candidate-only; useful for discovery and slow-frequency cross-check, not accepted as a daily backtest feed |
| Iran Fara Bourse (ifb.ir) | Secondary-market fixed-income prices, YTM, coupons, maturities, liquidity and yield-curve context | Unofficial `ifb-mcp` README reports daily price/YTM history, instrument/coupon details, quotes/order books, yield curves and no API key/account; price Rial, YTM percent/year, dates Jalali; site reportedly responds only to Iranian networks | Exact API/base path and schema; per-instrument history depth; clean/dirty price and accrued interest; day-count/compounding and settlement conventions; first-publication/revision times; liquidity/turnover completeness; rights | High-priority contract-discovery candidate; not an accepted price/yield feed |
| Investats (commercial) | Paid alternative for Iranian equities, ETFs/funds, AUM/NAV/flows and OHLCV | Vendor pages claim 5+ years of financial history and 2B+ rows. AUM article claims 899,314 rows for 298 funds from 2008-08-11 to 2026-09-08 with daily updates. OHLCV comparison article claims 3,107,029 rows across 5,218 symbols from 1979-12-25 to 2026-09-14. These are vendor-reported aggregate figures. | Per-symbol/per-fund coverage; missing dates and survivorship; field schema and units; release/correction history; source lineage; API authentication/rate limits/SLA; price, contract and data/model/display/redistribution rights | Vendor quote/sample candidate only; explicitly not free; no purchase or connection authorized |

## 1. FIPIRAN fund NAV and fund metadata

Discovery reference: the unofficial [fipiran-mcp repository](https://github.com/sepehr071/fipiran-mcp) describes itself as a read-only wrapper for public JSON used by FIPIRAN pages, not an official or affiliated API client. Its README reports:

- roughly 500 Iranian mutual funds and ETFs;
- fund search, fund details, fund types, manager data, NAV, returns, size, allocation, investor mix and flow history;
- no API key or account for the public pages;
- `fp_history` returns up to 60 evenly spaced points, not an unrestricted daily tape;
- NAV is reported in Rial per unit, fund size in billion Toman, and returns as percent per period (not annualized);
- the site reportedly answers Iranian network lines only; foreign access may require an Iran-side route.

The wrapper is a discovery aid, not a source contract. Its MIT license covers the wrapper code, not FIPIRAN's underlying data. The direct FIPIRAN site and its terms could not be reviewed in this environment; no live request was attempted.

**Required before reconsideration**

1. Verify the publisher/site identity and obtain the site's own access, automated collection, retention, attribution, redistribution and commercial/model-use terms.
2. Identify stable fund keys (including registration/group identifiers) and map them to TSETMC instrument IDs without relying on display names alone.
3. Distinguish issuance NAV, redemption NAV, unit price, exchange-traded market price, AUM, unit count, net subscriptions/redemptions and investor mix.
4. Confirm Rial/Toman and scale for every field; do not convert the NAV and AUM fields using one assumed multiplier.
5. Measure actual history per fund, not the aggregate count; record missing dates, frequency, stale values, suspensions, corrections and fund inception/termination.
6. Establish observation date versus first-publication/retrieval time and whether historical corrections/vintages can be replayed.
7. Reconcile selected overlapping dates against separately reviewed TSETMC/issuer disclosures and fund reports.
8. Account for distributions, fees, capital changes and fund-specific return methodology before calculating total return.

**Disposition:** retain as a public-site candidate only. The 60-point history limit is insufficient evidence for daily volatility, drawdown, liquidity or a six-month daily walk-forward backtest. No adapter or default probe is added.

## 2. IFB secondary-market bonds, sukuk and treasury bills

Discovery reference: the unofficial [ifb-mcp repository](https://github.com/sepehr071/ifb-mcp) describes a read-only wrapper over public IFB pages and a web service; it explicitly says it is not affiliated with Iran Fara Bourse. Its README reports:

- treasury bills, sukuk, participation papers and other bonds ranked by yield to maturity;
- instrument details, issuer/guarantor, coupon rate and payment schedule;
- live price, volume, order book, daily price and YTM history;
- yield curves, bond indices, announcements and market statistics;
- no API key/account for the public pages;
- prices in Rial, yields in percent per year and dates in Jalali format;
- the site reportedly responds only from Iranian networks;
- YTM is described as computed by IFB from the last trade.

This candidate could address a material gap left by the CBI government-securities auction archive: the CBI archive is primary-market auction evidence, whereas IFB may expose secondary-market traded prices and yields. Do not conflate them.

The wrapper's MIT license does not license the underlying IFB data. The official IFB contract, automated-access policy, full history, correction policy and commercial/model-use rights were not verified; no provider request or package installation was performed.

**Required before reconsideration**

1. Verify the official IFB endpoint, service owner, API schema, access conditions, request limits and whether the web service is supported for automated use.
2. Obtain stable instrument identifiers and preserve board/market distinctions; do not identify securities by Persian display name alone.
3. Verify Rial quote basis, price scale, clean versus dirty price, accrued interest, settlement date and any minimum denomination.
4. Recompute selected YTM values independently from the actual cash-flow schedule, last trade price, coupon dates, maturity, day-count, compounding and settlement convention.
5. Keep coupon rate, current yield, YTM, auction yield and realized holding-period return as distinct fields.
6. Measure per-instrument daily history, volume/turnover, bid/ask spread, stale prices, suspended periods, maturity/roll-off and missing observations.
7. Establish first-publication timestamps, revisions, corrections and point-in-time instrument eligibility.
8. Review issuer/guarantor, credit/default/call risk, payment events and corporate actions; a displayed YTM is not a guaranteed realized return.
9. Obtain explicit rights for collection, retention, derived analytics, internal model use, display and redistribution.

**Disposition:** high-priority documentation/contract-discovery candidate for fixed income, but not yet a validated or tradable return series. No adapter, default probe or scoring eligibility is added.

## 3. Investats commercial alternative

Public vendor material at [investats.net](https://investats.net/) advertises an API/data service spanning Iranian shares, ETFs/funds, OHLCV, fund AUM/NAV/flows, currencies and other datasets. Its published material claims:

- more than 5 years of financial history, 475+ shares/funds, and 2B+ rows at the platform level;
- an AUM-funds dataset with 899,314 rows for 298 fund symbols, dated 2008-08-11 through 2026-09-08, updated daily;
- an OHLCV dataset with 3,107,029 rows across 5,218 symbols, dated 1979-12-25 through 2026-09-14.

These are vendor-published aggregate claims, not independently verified coverage for every symbol or fund. The AUM dataset is not automatically a total-return series, and aggregate start/end dates do not prove uninterrupted history for any individual instrument.

**Required before any procurement decision**

- Written quote, subscription model, API authentication and rate limits.
- A representative sample for selected equities, gold funds, fixed-income funds and other intended asset classes.
- Per-instrument coverage matrix, missing-date report, schema/data dictionary, unit/currency definitions and update schedule.
- Historical correction/backfill and point-in-time release policy.
- Source lineage and independent reconciliation rights.
- Contractual permission for storage, internal investment research/model use, derived metrics, display, redistribution, retention after termination and deletion obligations.
- SLA, uptime, support, change notice and incident handling.

**Disposition:** vendor alternative only. It is not classified as free; no quote, purchase, account or API connection is authorized by this screen.

## 4. Acceptance gates and research-engine boundary

For every candidate, the common gates remain:

1. publisher identity and stable series/instrument definition;
2. frequency, calendar, Jalali conversion and market-session conventions;
3. units, currency, scale, quote direction and denomination;
4. observation date versus first publication, retrieval and correction timestamps;
5. complete per-series history, missing periods, suspensions and survivorship;
6. revision/vintage replay sufficient for point-in-time backtests;
7. independent overlapping-date reconciliation;
8. collection, storage, attribution, internal model use, derived-data, display and redistribution rights;
9. realistic transaction costs, spreads, market depth, settlement and executable availability;
10. separation of fund NAV, exchange-traded fund price, bond price, YTM, auction yield and realized total return.

No new source is wired into the research engine or default probe runner by this screen. Existing CBI auction PDFs remain primary-market context only; FIPIRAN NAV is not a substitute for exchange price; IFB's displayed YTM is not a realized return. All source, feature, backtest, scoring and ranking gates remain fail-closed.

## 5. Review record

Reviewed 2026-11-05 from public discovery material:

- FIPIRAN site: https://fipiran.ir/
- Unofficial FIPIRAN wrapper: https://github.com/sepehr071/fipiran-mcp
- Iran Fara Bourse: https://www.ifb.ir/
- Unofficial IFB wrapper: https://github.com/sepehr071/ifb-mcp
- Investats provider site: https://investats.net/
- Investats fund AUM/NAV API article: https://investats.net/blog/investment-funds-api-nav-performance-mtum8rn2
- Investats API provider comparison/OHLCV article: https://investats.net/blog/iranian-stock-api-providers-comparison-mu29k9ls

No provider API, live site JSON, account, token, proxy, VPN route, package install or raw dataset was used. A documentation timeout or a wrapper's claim about network reachability is not evidence of provider outage or permission to bypass access restrictions.
