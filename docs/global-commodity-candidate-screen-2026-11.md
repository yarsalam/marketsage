# Global commodity candidate screen — World Bank Pink Sheet — 2026-11-04

**Status:** documentation-only candidate review. No adapter, automated download, default probe, research-engine use or scoring eligibility is added.  
**Scope:** monthly global commodity prices and indices for energy, precious metals and other commodity families.  
**Network boundary:** official public documentation only; no workbook download or provider API request was made.

## Executive disposition

The World Bank Commodity Markets page lists a Pink Sheet data section with separate monthly and annual XLS workbooks. On 2026-11-04, the page displayed an **October 2026** monthly-price workbook link and a next-update date of **2026-11-03**; no newer monthly workbook link was visible in the page snapshot reviewed. The actual workbook could not be parsed in this review, so its exact observation end date, series count, per-series units, coverage start and missing-value conventions are not certified here.

This is a useful candidate for **monthly global commodity regime context** (for example, gold, silver, crude oil and natural gas benchmarks), not a daily trading-price feed and not a substitute for an executable spot/futures series.

## Official access and temporal evidence

- Official landing page: https://www.worldbank.org/en/research/commodity-markets
- The page's "Pink Sheet" table links separately to:
  - monthly prices (XLS);
  - annual prices (XLS);
  - monthly commodity-price report PDFs.
- The monthly workbook link is discovered from the official landing page. Its document URL contains a versioned/hash-like path; do not hardcode an old file URL as a permanent endpoint.
- The page snapshot reviewed on 2026-11-04 labels the monthly workbook "October 2026" and shows "Next update: November 3, 2026". It did not expose a newer workbook link in the retrieved page. Do not infer that October's observation data were available on October 31, or that the workbook includes October observations, from the release label alone.
- The XLSX link could not be parsed by the documentation-review tool, and a direct download was not completed. The workbook's exact row/column layout, units row, source/description metadata, coverage by series and missing-value tokens remain unverified.
- No documented stable REST/SDMX API for the Pink Sheet workbook was established in this review. Treat it as a periodically published workbook until a documented machine-readable contract is verified.

## Rights and attribution

Official references:

- World Bank Commodity Markets page: https://www.worldbank.org/en/research/commodity-markets
- World Bank Dataset Terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets
- World Bank Data Access and Licensing: https://datacatalog.worldbank.org/public-licenses

The World Bank's Data Access and Licensing page states that CC BY 4.0 is the default for datasets produced by the World Bank and distributed as open data, and that this license permits commercial reuse with attribution and change notices. The same page explicitly describes exceptions: third-party datasets may use other licenses or require separate permission.

Therefore, do not infer that every commodity row in the Pink Sheet is covered by one blanket license. Before use, inspect the workbook's per-series source/description metadata and preserve attribution. The data-specific dataset terms linked from the Commodity Markets page govern the relevant dataset; general website content terms are not a substitute for that check.

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

Reviewed 2026-11-04 from the official World Bank Commodity Markets page and World Bank dataset licensing pages. The page listed an October 2026 monthly workbook and a 2026-11-03 next-update date. The workbook itself was not downloaded or parsed, no API key was used, and no foreign provider live-data request or laptop network request was made.
