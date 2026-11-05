# Global commodity candidate screen — World Bank Pink Sheet — 2026-11-05

**Status:** documentation-only candidate review. No adapter, automated download, default probe, research-engine use or scoring eligibility is added.  
**Scope:** monthly global commodity prices and indices for energy, precious metals and other commodity families.  
**Network boundary:** official public documentation only; the November PDF was inspected, but the monthly XLSX workbook was not downloaded and no provider API request was made.

## Executive disposition

The World Bank Commodity Markets page now lists a **November 2026** monthly-price XLS workbook and November PDF. The official PDF is dated **2026-11-03**, contains monthly averages through **October 2026**, and the landing page reports latest prices published on 2026-11-03 with the next update due 2026-12-02. Thus the release label is one month later than the latest observation month. The XLSX workbook itself remains unparsed, so its full history, exact series count, row layout and missing-value conventions are not certified.

This is a useful candidate for **monthly global commodity regime context** (for example, gold, silver, crude oil and natural gas benchmarks), not a daily trading-price feed and not a substitute for an executable spot/futures series.

## Official access and temporal evidence

- Official landing page: https://www.worldbank.org/en/research/commodity-markets
- The page's "Pink Sheet" table links separately to:
  - monthly prices (XLS);
  - annual prices (XLS);
  - monthly commodity-price report PDFs.
- The monthly workbook link is discovered from the official landing page. Its document URL contains a versioned/hash-like path; do not hardcode an old file URL as a permanent endpoint.
- The page snapshot reviewed on 2026-11-05 labels the XLS workbook "November 2026", shows "Latest Commodity Prices Published (11/03/2026)", and shows "Next update: December 2, 2026". The linked November PDF is itself dated November 3 and its monthly columns run through October 2026. Record at least the observation month (October), document/release date (November 3), and first-seen retrieval time separately. Do not backdate October values to October 31.
- The monthly XLSX link could not be parsed by the documentation-review tool and a direct download attempt failed. The separate official November PDF was parsed. It documents monthly average units/benchmarks including Brent crude in USD/barrel, gold and silver in USD/troy ounce, copper in USD/metric ton, and European natural gas in USD/MMBtu. Its descriptions specify, for example, gold as a spot average of daily rates, silver as the London afternoon fixing, and the crude-oil average as an equally weighted average of Brent, Dubai and WTI. The XLSX workbook's full row/column layout, historical coverage by series, missing-value tokens and exact revision history remain unverified.
- No documented stable REST/SDMX API for the Pink Sheet workbook was established in this review. Treat it as a periodically published workbook until a documented machine-readable contract is verified.

## Rights and attribution

Official references:

- World Bank Commodity Markets page: https://www.worldbank.org/en/research/commodity-markets
- World Bank Dataset Terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets
- World Bank Data Access and Licensing: https://datacatalog.worldbank.org/public-licenses

The World Bank Data summary terms state that World Bank Data Catalog datasets are generally available for commercial and non-commercial reuse under CC BY 4.0 unless dataset/indicator metadata says otherwise. They require attribution to the World Bank and data providers, prohibit implying endorsement, and explicitly exclude third-party material unless the originator permits reuse. The November PDF's source list names third parties including Bloomberg Finance L.P., S&P Global, FAO, USDA and market/industry organizations; its footer also carries an "Official Use Only" marking. That marking is not by itself a complete license determination, but it is a material clearance flag.

Therefore, the generic CC BY default is not sufficient to clear the full Pink Sheet for commercial redistribution. Before any commercial or model use, inspect the workbook's per-series source/description metadata, obtain any required originator permission, clarify the PDF's "Official Use Only" marking with the World Bank where relevant, and preserve the required attribution. Do not commit or redistribute the workbook while this remains unresolved.

## Required series-level contract

Before any workbook is downloaded into a collection pipeline:

1. Discover the current monthly workbook URL from the official Commodity Markets page; record retrieval time, release label, URL, file hash and workbook version.
2. Parse the workbook's description/metadata for each selected commodity: publisher/upstream source, benchmark definition, geography, quotation basis, unit, currency and any third-party attribution or license.
3. Keep nominal price, real price, price index and annual average as separate data kinds.
4. Preserve the published unit exactly (for example, USD per troy ounce, USD per barrel or USD per energy unit where those are the workbook's actual labels); never infer units from a ticker or hardcode a generic commodity conversion.
5. Store observation month separately from workbook publication/first-seen time. Monthly values must not be treated as available at the end of the labelled month unless the release calendar proves that.
6. Capture each monthly workbook as an immutable vintage and diff revisions to prior months. The current workbook alone is not sufficient for historical point-in-time replay if old observations can be revised.
7. Audit each series' actual first/last month, missing months, discontinuations and methodology changes. A workbook-level date span is not proof that every commodity has that coverage.
8. Reconcile overlapping months with an independent official series where the benchmark and units truly match; do not splice different benchmarks or providers.
9. Keep these monthly benchmark series separate from daily EIA spot statistics, exchange-traded futures, ETF prices and local Iran gold/FX prices.

## MarketSage disposition

- Add `global.world_bank_commodity_prices` as a research-only candidate.
- Use only for low-frequency global commodity context after workbook, unit, release-vintage and rights gates pass.
- No automated workbook fetch, API adapter, schedule, default probe or raw workbook commit is authorized by this screen.
- All rows remain `candidate_requires_validation`, `used_by_research_engine=false`, `approved_for_production=false`, and excluded from scoring.
- The candidate does not prove performance or availability of a locally tradable gold, silver, oil or gas instrument in Iran.

## Review record

Reviewed 2026-11-05 from the official World Bank Commodity Markets page, November 2026 Pink Sheet PDF dated 2026-11-03, and World Bank dataset terms. The PDF confirms monthly observations through October 2026 and selected benchmark units; the XLSX workbook was not downloaded or parsed. No API key or provider API was used. The source remains candidate-only pending workbook-level history, per-series rights and point-in-time vintage checks.
