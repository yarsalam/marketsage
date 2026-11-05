# Iran official source candidate screen — 2026-11-05

**Status:** documentation-only candidate review. No source is approved for production scoring, research-engine use, or backtest admission by this screen.  
**Scope:** Central Bank of Iran (CBI), Statistical Center of Iran (SCI), national open-data catalog, and official Iranian exchange candidates.  
**Network boundary:** public documentation pages only; no provider API, account endpoint, dataset download, or laptop-side live probe was executed.

## Executive disposition

The CBI public website exposes several useful official macro and policy-statistics families. A separate TSETMC announcement also points to a newly documented REST web-service path, but its contract and rights could not yet be verified. The strongest current candidates are:

1. CBI Economic Time Series Database (TSD): more than 1,000 annual variables from 1338 onward, exposed through HTML and Excel according to the CBI's own description.
2. CBI official exchange-rate page: daily currency-transfer rates calculated from the previous business day's transactions in the currency-transfer hall. This is **not** the Iranian free-market cash USD rate.
3. CBI policy-rate page: weekly interbank, repo-floor, standing lending and deposit rates, with Jalali observation dates and percentage units.
4. CBI government Islamic-securities auction archive: dated PDF auction-result documents. These are primary-market auction records, not secondary-market bond prices or total-return histories.
5. TSETMC official REST web-service documentation path: announced in December 2025, but the documentation endpoint was inaccessible in this review and no authentication, pricing, history, rights or rate-limit contract is established.

All five remain candidates. The reviewed pages do not establish a stable public API contract, exact publication timestamps, full revision/vintage semantics, or permission for automated commercial/model use. The CBI footer states that the site's material and moral rights belong to the CBI; no blanket reuse license was identified in this review.

## 1. Central Bank of Iran

### 1.1 Economic Time Series Database (TSD)

The CBI's own TSD description states that it contains more than 1,000 important economic variables, at annual frequency, from year 1338 onward, available in Persian and English through Excel and HTML. Its stated subject areas include national accounts, industry/mining, housing/construction, transport, agriculture, energy, external sector, monetary/credit variables, securities market, government finance, price indices, social statistics, and labour/employment.

- Official description: https://www.cbi.ir/page/4275.aspx
- The description links to the TSD viewer at https://tsdview.cis.cbi.ir/.
- The viewer request timed out in the documentation-review environment on 2026-11-04. This is not evidence that the provider is down in the owner's network, and no data/API request was made.
- The CBI page describes HTML/Excel access, not a documented REST/SDMX API. Exact series identifiers, frequency exceptions, units, base-year changes, revision policy, release timestamps and historical vintages must be inspected per series.
- Annual observations are suitable only for low-frequency macro context. They must not be expanded into daily observations or treated as daily tradable prices.
- The TSD landing page alone does not prove that every series has a continuous history, a usable machine-readable download, or point-in-time publication metadata.

**Disposition:** retain under the existing `iran.official_macro` candidate. No adapter, scheduled probe, or scoring eligibility is added.

### 1.2 Official exchange-rate page

The CBI's exchange-rate page states that its transfer rate is calculated from the previous business day's currency-transfer transactions in the transfer hall of the Iran Currency and Gold Exchange. The page displays a Jalali quote date and currency rows. Some currency codes explicitly carry denomination multipliers (for example, JPY100, IQD100 and KRW1000).

- Official page: https://www.cbi.ir/exrates/rates_fa.aspx
- This is an official transfer/centralized-market rate. It must not be labelled or substituted for the free-market cash/bazaar rate.
- The previous-business-day calculation means the displayed date is not sufficient to infer an exact intraday observation or publication timestamp.
- The CBI states that the Iranian currency unit is Rial. Nevertheless, endpoint-level quote basis and each code's denomination multiplier must be preserved and validated before normalization; do not silently divide by ten or assume all rows are per one currency unit.
- The page links to historical exchange-rate views, but full history depth, correction behavior, stable download format and automated-access rights were not established in this review.

**Disposition:** candidate for official FX/macro context only. Keep separate from free-market FX; require unit, quote-direction, Jalali-calendar, lag, history, corrections and rights checks before collection.

### 1.3 Weekly policy-rate series

The CBI policy-rate page shows a weekly table with Jalali dates and percentage columns for the interbank rate, minimum repo rate, standing lending facility and standing deposit facility. The page displayed dated weekly observations for 1405 at the time of review.

- Official page: https://www.cbi.ir/PolicyRates/policyrates_fa.aspx
- These are policy/interbank-rate observations, not bond prices, fund NAVs or guaranteed executable investment yields.
- The displayed observation date is available, but exact first-publication time, revisions, historical vintage behavior and a stable machine-readable contract remain unverified.
- Keep percentage units explicit and distinguish the interbank rate from the repo floor and standing-facility corridor.

**Disposition:** candidate macro/rates context under `iran.official_macro`; no trading-price or bond-total-return use.

### 1.4 Government Islamic-securities auction results

The CBI's Islamic-securities section links to a dated archive of government Islamic-securities auction results. The current listing includes weekly dated PDF notices/results (for example, 1405/08/02 and preceding weekly dates).

- Official archive: https://www.cbi.ir/category/21038.aspx
- The archive is evidence of primary-market issuance/auction reporting. It is not a continuous secondary-market price series and does not, by itself, establish an instrument's total return.
- Before any structured use, each PDF must be mapped to instrument identity, auction/settlement date, maturity, accepted amount, price/yield convention, coupon/cash-flow schedule, and any amendments or corrections.
- Do not mix auction yield, coupon rate, yield-to-maturity, fund NAV and secondary-market price as if they were the same variable.
- The archive is PDF-oriented in the reviewed page; a stable machine-readable API, complete historical depth and reuse rights were not established.

**Disposition:** add as a separate `iran.cbi.bond_auction_results` candidate for primary-market context only. It does not close the fixed-income secondary-market price/history gap.

## 2. TSETMC official REST service — new contract-discovery candidate

A Tasnim report dated 1404/10/06 (2025-12-27), quoting TSETMC, says that a new REST API web service was released alongside the older SOAP service. The report says both services would remain supported until further notice, while future development would be provided through REST, and links to the service documentation at `https://api.tsetmc.com/docs/`.

- Secondary report quoting TSETMC: https://www.tasnimnews.ir/fa/news/1404/10/06/3481080/نسخه-جدید-وب-سرویس-tsetmc-منتشر-شد
- Documentation URL cited by the announcement: https://api.tsetmc.com/docs/
- The documentation host/path was inaccessible to this review environment. This is not evidence that the service is unavailable from the owner's intended Iran network; no provider request, account login or credential attempt was made.
- The exact API host/base path, OpenAPI contract, authentication, subscription/pricing, request limits, endpoint families, historical depth, units, price-adjustment semantics, observation/availability timestamps, corrections and commercial/model-use terms remain unknown.
- Do not assume this newly announced service is the same as the reverse-engineered public CDN endpoints currently used by the repository's TSETMC adapter. Do not silently relabel the existing adapter as an official API client.
- The announcement and documentation link do not themselves grant collection, retention, redistribution or commercial rights. Obtain the service terms and any required agreement before any persistent or derived use.

**Disposition:** prioritize a documentation/contract review from the intended Iran network before any new live probe. If the official REST contract and rights are verified, compare it against the current reverse-engineered adapter for identity, history, units, adjustments and release semantics. No adapter switch, probe, source approval or scoring eligibility is added by this screen.

## 3. Other Iranian official portals and exchanges

The following official destinations were identified for follow-up, but no machine-readable series contract was verified in this screen:

| Candidate | Intended role | Evidence and current limitation | Disposition |
|---|---|---|---|
| Statistical Center of Iran — https://www.amar.org.ir | CPI/PPI, labour, national accounts, household and regional statistics | Official portal identified; direct page fetch timed out in this review environment. API, downloadable format by series, release/vintage metadata and reuse terms remain unverified. | Candidate only; no adapter or probe. |
| National Open Data Catalog — https://data.gov.ir | Cross-agency public datasets | Official catalog identified; direct page fetch timed out in this review environment. No API contract, dataset-level license, resource persistence or revision policy was verified. | Catalog discovery only; each publisher/resource must be checked independently. |
| Iran Fara Bourse — https://www.ifb.ir | Listed fixed-income instruments, funds and secondary-market history | Official destination identified; no stable history endpoint, instrument master, cash-flow schema or reuse contract verified in this review. | Candidate only; do not infer a usable bond-price feed. |
| Iran Mercantile Exchange — https://www.ime.co.ir | Commodity contracts, delivery and transaction statistics | Official destination identified; no stable machine-readable historical price/volume contract or rights terms verified in this review. | Candidate only; keep contract, delivery grade, unit and settlement semantics explicit. |
| Iran Energy Exchange — https://www.irenex.ir | Energy products and electricity/hydrocarbon market statistics | Official destination identified; direct fetch was unavailable in this review environment. No historical API, product-level units, publication times or reuse terms verified. | Candidate only; electricity and energy statistics are not substitutes for oil-futures prices. |

A timeout in this review environment is an evidence limitation, not proof of provider outage or absence of data. Do not convert it into a claim that an official portal has no data.

## 4. Fixed-income gap remains open

The CBI auction archive improves primary-market context but does not provide an accepted investable fixed-income series. A usable fixed-income instrument record still needs, at minimum:

- stable instrument identifier and issuer;
- instrument type (government sukuk, participation certificate, corporate debt, deposit certificate, or fund);
- clean/dirty price and quote unit, if traded;
- coupon and cash-flow dates, maturity and settlement conventions;
- yield definition (coupon, current yield, yield-to-maturity, yield-to-call, or auction yield);
- distribution/corporate-action treatment and fund NAV versus exchange-price separation;
- point-in-time publication and correction history;
- complete historical coverage, liquidity/turnover and executable-cost assumptions;
- source collection, storage, redistribution and commercial/model-use permission.

Until these are established, fixed income remains unavailable/not-rankable. A weekly auction result or policy rate must not be presented as a tradable bond return.

## 5. Cross-source acceptance gates

For every candidate above, require:

1. publisher identity and series definition;
2. exact frequency and calendar, including Jalali-to-Gregorian conversion where relevant;
3. unit, currency, quote direction, scale and denomination multiplier;
4. observation date versus first publication, retrieval and revision timestamps;
5. historical depth, missing periods, corrections and vintage availability;
6. lawful collection, storage, attribution, derived-data and commercial/model-use rights;
7. independent overlapping-date reconciliation where a lawful reference exists;
8. explicit distinction between macro observations, official FX, free-market FX, primary auctions, secondary-market prices and fund NAVs.

No new source is wired into the research engine or default probe runner by this screen. All source and scoring gates remain fail-closed.

## 6. Review record

Reviewed on 2026-11-05 from public documentation pages and a secondary report quoting TSETMC:

- CBI homepage and statistics directory: https://www.cbi.ir/
- CBI TSD description: https://www.cbi.ir/page/4275.aspx
- CBI official exchange rates: https://www.cbi.ir/exrates/rates_fa.aspx
- CBI policy rates: https://www.cbi.ir/PolicyRates/policyrates_fa.aspx
- CBI government Islamic-securities auction archive: https://www.cbi.ir/category/21038.aspx
- Tasnim report quoting TSETMC's REST-service announcement (2025-12-27): https://www.tasnimnews.ir/fa/news/1404/10/06/3481080/نسخه-جدید-وب-سرویس-tsetmc-منتشر-شد
- TSETMC service documentation path cited by the announcement: https://api.tsetmc.com/docs/

No API key, account token, provider API, laptop network, VPN route, dataset download or raw local file was used. The TSETMC documentation endpoint could not be inspected here; its authentication, commercial terms and service contract remain unknown. The project's rule to remind the owner to enable VPN before any future foreign live-source request remains unchanged.
