# MarketSage — Global Official Source Candidate Screen

**Review date:** 2026-11-03  
**Scope:** official, machine-readable candidates for global macro, FX, rates, energy and issuer events  
**Evidence mode:** official documentation review only; no API probes, no local data access, no credentials used  
**Decision:** five candidates added to the catalog/registry as research-only. None is approved for production scoring.

This screen separates four questions: (1) is a documented machine-readable access path available, (2) what history and temporal metadata exist, (3) what reuse/attribution constraints are documented, and (4) whether the series represents a tradable price or only macro/event context. Public or free access is not a general redistribution license.

## Candidate triage

| Priority | Source | Best MarketSage role | Access and history evidence | Rights / temporal caveat | Disposition |
|---|---|---|---|---|---|
| 1 | ECB Data Portal SDMX | Daily reference FX, euro-area yields and macro context | Public HTTPS SDMX 2.1 service; daily reference exchange-rate history is documented since 1999. Queries support date bounds, `updatedAfter` deltas and `includeHistory` for previous data versions. | Public ESCB statistics may be reused free with attribution and without modifying the statistics/metadata; third-party data are excluded without permission. Revisions still need point-in-time replay. Reference FX is not an executable bid/ask quote. | Highest-value next macro/FX candidate. One exact series and bounded date window only after access/VPN preconditions. |
| 2 | US Treasury daily interest-rate XML | USD yield curve, bill and real-yield context; potential US risk-free benchmark input | Official XML feed guide lists daily par yields from 1990, bill rates from 2002, long-term rates from 2000 and real-yield data from 2003. Default response is 300 rows; all-history retrieval is paginated from page 0. | The feed gives daily observation dates, not yet a verified publication/availability timestamp or immutable vintage. Par yields are not bond prices or total-return indexes. Reuse terms need explicit review. | Strong candidate for a carefully defined USD rates series; not an Iran fixed-income substitute. |
| 3 | EIA API v2 | Oil/energy regime variables: petroleum, natural gas, electricity, production, inventories and trade | Free API v2; registration/API key required. Series vary across hourly, weekly, monthly and annual frequency. API v2 supports date, frequency and facet filters; bulk downloads do not require a key. | API use is subject to EIA Terms of Service. EIA government information is generally public domain with acknowledgment, but third-party contributed/licensed material may remain protected. Release calendar, revisions and series units must be audited. Energy statistics are not necessarily tradable oil-price series. | Strong macro/energy candidate after secure key setup and one-series contract audit. |
| 4 | SEC EDGAR submissions and XBRL APIs | US issuer filings, fundamentals and corporate-event context | Public `data.sec.gov` submissions/XBRL APIs require no API key. EDGAR public indexes extend to 1994Q3; company submissions include at least one year or 1,000 recent filings, with additional history files. APIs update through the day. | Fair Access: at most 10 requests/second per user across machines; declare a descriptive User-Agent and avoid unclassified bots. Acceptance time and public availability are distinct; SEC guidance says documents often appear 1–3 minutes after acceptance, with no guarantee. Post-acceptance corrections/deletions can alter later indexes. | High-value issuer-event candidate, but not a market-price feed. Verify field mapping, amendments, XBRL contexts/units and replay semantics. |
| 5 | IMF Data API (SDMX 2.1/3.0) | International macro, balance-of-payments and monetary statistics | IMF documents SDMX 2.1 and 3.0 APIs. The public API page directs users to a Swagger explorer that requires a beta portal account. | The account requirement for API exploration does not establish anonymous endpoint access or the exact authentication/quota contract. Dataflow history, revision/vintage, release time, reuse rights and country/series definitions remain unresolved. | Medium-priority discovery candidate. Resolve API access and one dataflow contract before any probe or adapter. |

## Source-specific acceptance contracts

### ECB Data Portal

Official references:
- [Data API help](https://data.ecb.europa.eu/help/api/data)
- [API overview](https://data.ecb.europa.eu/help/api/overview)
- [ESCB reuse policy](https://www.ecb.europa.eu/stats/ecb_statistics/governance_and_quality_framework/html/usage_policy.en.html)

Required before use:
1. Pin the exact dataflow, agency, version, frequency, dimensions and series key.
2. Record base/quote currency direction, unit, reference-rate convention and calendar.
3. Capture both observation period and first-seen/release/update time where available.
4. Test `updatedAfter` and `includeHistory=true` on one small series; verify whether prior versions are sufficient for the required point-in-time replay.
5. Preserve source attribution and do not modify ECB statistics/metadata when relying on the stated free-reuse policy; separately review any third-party series.

### US Treasury XML feeds

Official references:
- [Daily interest-rate XML feed](https://home.treasury.gov/treasury-daily-interest-rate-xml-feed)
- [XML feed changes](https://home.treasury.gov/developer-notice-xml-changes)
- [Interest-rate XML files](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rate-xml-files)

Required before use:
1. Choose one exact feed: par yield curve, bill rates, real yields or long-term rates. Do not merge definitions.
2. Map each maturity/tenor and percent/rate unit; preserve the provider's curve methodology.
3. Confirm pagination, schema changes and date coverage on a bounded year.
4. Determine publication/availability timing and correction behavior separately from the observation date.
5. Complete reuse/attribution review before persistent or derived use.

### EIA API v2

Official references:
- [API v2 technical documentation](https://www.eia.gov/opendata/documentation.php)
- [API Terms of Service](https://www.eia.gov/opendata/terms-of-service.php)
- [Copyrights and reuse](https://www.eia.gov/about/copyrights_reuse.php)

Required before use:
1. Obtain the key in local secret storage; never place it in Git, chat, URL logs or reports.
2. Accept and review the API Terms of Service for the intended use.
3. Select one exact series and record its geography, frequency, unit, seasonal adjustment and source methodology.
4. Establish the release calendar, publication lag, revisions and historical completeness.
5. Preserve attribution and distinguish government public-domain content from third-party protected materials.
6. Keep energy balance/inventory/production statistics separate from market-traded spot or futures prices.

### SEC EDGAR

Official references:
- [EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [Developer resources and Fair Access](https://www.sec.gov/about/developer-resources)
- [Accessing EDGAR data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [Webmaster FAQ: acceptance and availability timing](https://www.sec.gov/about/webmaster-frequently-asked-questions)

Required before use:
1. Start with one exact CIK and filing family; use the submissions API rather than crawling the whole site.
2. Set a descriptive User-Agent and enforce a repository-wide/account-wide limit no greater than 10 requests/second.
3. Store accession number, form, acceptance time, filing date, first observed public availability and amendment/correction state separately.
4. Verify the API field mapping against the original filing header; do not substitute filing date for acceptance timestamp.
5. Preserve XBRL context, unit, period, dimensions, amendment and restatement semantics.
6. Handle post-acceptance corrections/deletions and distinguish current data from what was available at each historical decision time.

### IMF SDMX

Official reference:
- [IMF Data APIs](https://data.imf.org/en/Resource-Pages/IMF-API)

Required before use:
1. Establish whether the selected dataflow can be accessed without the beta portal account, and document the exact authentication/quota contract.
2. Pin the dataflow, agency, version, series key, country, frequency and units.
3. Determine revision/vintage and release/availability semantics; do not assume SDMX observation periods are publication timestamps.
4. Review dataset-specific reuse conditions and preserve the original metadata.
5. Start with one dataflow and a short period; no broad catalog crawl.

## Integration and operating decision

- The catalog and source registry now include these five official-source candidates. All are `candidate_requires_validation`, `used_by_research_engine=false`, `approved_for_production=false`, and excluded from default live probes.
- No adapters, schedules, live probes or credentials were added in this review.
- Before any foreign live-source request, the operator must be reminded to turn VPN ON. This screen used official documentation pages only and did not contact data APIs.
- Candidate value is complementary, not interchangeable: ECB/Treasury provide reference rates, EIA/IMF provide macro context, and SEC provides issuer events/fundamentals. None fills the missing Iranian daily tradable-price history.
- A candidate can advance only after a bounded source-contract test, rights review, unit/time/history audit and independent reconciliation. A green parser or CI run cannot approve it.
- Investment ranking and source scoring remain fail-closed.
