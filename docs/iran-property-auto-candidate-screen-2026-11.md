# Iran property and automobile data candidate screen — 2026-11-05

**Status:** documentation-only discovery. No property or automobile price source is accepted for backtesting, scoring, ranking, or production.

**Question:** Can Iran property or vehicle markets be represented by public, historically complete, point-in-time and legally usable data that measures an investable asset price rather than a macro proxy or issuer operating statistic?

## Executive result

No current, verified, transaction-based property or vehicle price series passed the evidence gate in this screen.

- Property: the Central Bank of Iran (CBI) provides useful CPI and annual macro context, and its Tehran housing reports contain historical transaction aggregates. The transaction-report series stops after Mordad 1403 because the bank lost access to raw records during the registry migration. The current property-price feed is therefore blocked.
- Automobile: CODAL disclosures provide useful issuer-level production, sales quantities and reported sales amounts for major listed automakers. These are operating/fundamental data, not a market-wide new- or used-car price index.
- The Statistical Center of Iran (SCI) remains a candidate for CPI/housing/rent and other monthly macro tables, but the portal timed out in this review environment. Its series-level units, publication/vintage metadata and reuse terms were not verified.

The asset universe is not narrowed by this result. These candidates remain visible, but no proxy is silently promoted to an investable price series.

## 1. Property and housing

### 1.1 CBI monthly urban CPI — macro context only

Official source: [CBI CPI summary PDF](https://www.cbi.ir/Newestdoc.aspx?dl=2&dn=0&id=1611).

The reviewed PDF is titled as the summary of consumer-price index results in Iran's urban areas. It is dated Tir 1405, reports observations through Khordad 1405, and uses base year 1400=100. Its group tables include “housing, water, electricity, gas and other fuels”.

**Use boundary:** this is household consumption inflation. It is not a house transaction-price index, a property capital-gain series, or a rental-yield series. The reviewed file is not current to the 1405-08 review date. A monthly macro feature would still require the full series, release timestamps, revision policy, and point-in-time vintages.

### 1.2 CBI Economic Time Series Database — long annual context

Official description: [CBI Economic Time Series Database](https://www.cbi.ir/page/4275.aspx).

CBI describes more than 1,000 annual economic variables from year 1338 onward, available through HTML and Excel. The stated coverage includes housing/construction, transport, national accounts, monetary variables and price indices.

**Use boundary:** annual macro/construction context only. The page does not establish a stable REST/SDMX contract, series-level property transaction prices, monthly frequency for the required series, revision/vintage semantics, or automated/commercial reuse permission. CBI's site footer states that all material and moral rights belong to CBI.

### 1.3 CBI Tehran housing transaction reports — historical only

The latest status statement located says CBI published monthly Tehran housing-market reports from Farvardin 1396 through Mordad 1403. From the second half of Shahrivar 1403, CBI lost access to raw transactions in the previous national real-estate registry. The reports stopped while access to the replacement “Self-Writer” and “Kateb” systems remained unavailable, including at the status statement dated 1404-09-12 (2025-12-03).

Reference: [CBI/IBENA status reported on 1404-09-12](https://armaneghtesadi.com/952283/1404/09/12/%D8%A8%D9%87%D8%B1%D9%88%D8%B2%D8%B1%D8%B3%D8%A7%D9%86%DB%8C-%DA%AF%D8%B2%D8%A7%D8%B1%D8%B4-%D8%AA%D8%AD%D9%88%D9%84%D8%A7%D8%AA-%D9%85%D8%B9%D8%A7%D9%85%D9%84%D8%A7%D8%AA-%D8%A8%D8%A7%D8%B2%D8%A7%D8%B1-%D9%85%D8%B3%DA%A9%D9%86-%D8%AF%D8%B1-%D8%A7%D9%86%D8%AA%D8%B8%D8%A7%D8%B1-%D8%A7%D8%AA%D8%B5%D8%A7%D9%84-%D8%A8%D9%87-%D8%B3%D8%A7%D9%85%D8%A7%D9%86%D9%87-%D9%87%D8%A7%DB%8C-%D8%AE%D9%88%D8%AF%D9%86%D9%88%DB%8C%D8%B3-%D9%88-%DA%A9%D8%A7%D8%AA%D8%A8/).

**Use boundary:** historical Tehran-only aggregate context through 1403-05. It has a material coverage break after 1403-05, does not cover all Iran, and is not a property-level transaction tape. It must not be forward-filled or treated as a current national price index. The status article is secondary reporting of the CBI/IBENA statement; original archived reports and their individual release dates, sample counts, methods, revisions and rights still need review.

### 1.4 SCI housing/rent statistics — candidate, not verified

Official portal: [Statistical Center of Iran](https://www.amar.org.ir).

Direct retrieval timed out in this review environment. No series-level workbook, stable API, units, exact observation history, first-publication timestamps, revisions or reuse terms were inspected. Third-party wrappers and mirrors are discovery clues only; they do not establish the official data contract or license. The SCI candidate remains blocked pending direct review from an accessible network and inspection of original tables.

## 2. Automobile and vehicle market

### 2.1 CODAL listed-automaker disclosures — issuer fundamentals, not market prices

Source portal: [CODAL](https://www.codal.ir).

A JETRO report dated 2025-08-13 compiles original CODAL disclosures for Iran Khodro, Pars Khodro and Saipa for Iranian year 1403. It reports production units, sales units and sales amounts; selected product tables also expose manufacturer-reported price/amount fields. The report notes that the local industry association had not published 2024 industry-wide production/sales statistics, while CODAL filings supplied company-level disclosures.

Reference: [JETRO — Iran vehicle production and major-company disclosures, 2025-08-13](https://www.jetro.go.jp/biz/areareports/2025/12940875b2aa9f23.html).

**Use boundary:** CODAL can support listed-automaker operating fundamentals and supply context. It does not by itself provide a representative market-wide transaction-price index for new or used vehicles. Sales amount divided by units is not a valid vehicle price index unless product/trim mix, taxes, discounts, delivery timing, contract terms and revenue recognition are reconciled. Production volume is not an investment return.

The generic CODAL candidate remains unapproved for automated collection. This screen does not run a CODAL query, download filings, or change the default probe policy.

### 2.2 OICA annual production — industry context only

Reference: [OICA Iran 2024 production statistics](https://oica.net/production_statistic/iran-2024/).

Annual national production counts can provide supply-cycle context. They are not new/used-car transaction prices, monthly price returns, or evidence of investable liquidity. OICA's series definitions, historical revisions and reuse terms would need separate review before automated/model use.

### 2.3 No verified used-car transaction-price feed

No public primary source with a verified, representative, executed-transaction price history for used vehicles passed this screen. Classified-ad asking prices must remain separate from completed transactions and are exposed to selection, stale-listing, duplicate-ad, trim, mileage, condition and location biases. Do not scrape listing sites until their access and commercial/model-use terms are reviewed.

## 3. Acceptance requirements before any price-series use

### Property
- Executed transaction price, not asking price; exact transaction date and first-publication time.
- City, district/neighborhood, property type, area, building age, floor, condition and transaction count.
- Currency and quote basis (Rial/Toman), price per square metre, fees/taxes and contract type.
- Mix-adjustment or repeat-sales methodology; sample-composition changes and low-volume periods.
- Full history, missingness, revisions, backfills, release calendar and immutable point-in-time vintages.
- Independent reconciliation and explicit permission for automated collection, retention, model use and commercial use.

### Automobile
- Executed transaction price, not listing price; new/used status and sale date.
- Make, model, trim, model year, mileage, condition, city, dealer/private sale and transaction count.
- Currency, Rial/Toman scale, taxes, fees, financing and delivery terms.
- Product-mix adjustment, duplicate/stale listing controls, revision history and point-in-time availability.
- Independent reference and explicit access, retention, model-use and commercial-use rights.

### Shared
Every series must have a source/series identifier, source owner, observation period, publication/first-availability timestamp, retrieval timestamp, timezone/calendar, unit and quote convention, correction/vintage policy, file hash, and rights disposition. Unknown is not pass.

## 4. Disposition

| Candidate | Current disposition | Permitted role now |
|---|---|---|
| CBI monthly urban CPI | Candidate; reviewed PDF only through Khordad 1405; rights and vintages unresolved | Macro inflation context only after series-level review |
| CBI Economic Time Series Database | Candidate; annual HTML/Excel, no accepted API or reuse license | Long-run annual macro/construction context |
| CBI Tehran housing reports | Historical-only; monthly reporting stopped after 1403-05 | Historical Tehran context only, after archive/method/rights review |
| SCI housing/rent tables | Blocked pending direct source inspection | None until original table and rights are verified |
| CODAL automaker disclosures | Candidate; original filing and correction/rights checks required | Issuer production/sales fundamentals, not vehicle prices |
| OICA production counts | Candidate annual supply context | Industry-cycle feature only after terms/history review |
| Used-car listings | Not accepted | No automated collection |

No new adapter, provider probe, dataset download, feature, backtest input, score, rank, production deployment or capital action is authorized by this screen. The broader asset universe remains open. All source and investment-scoring gates remain fail-closed.
