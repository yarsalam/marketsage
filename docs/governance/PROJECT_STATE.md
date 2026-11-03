# MarketSage — Current Project State

**Snapshot date:** 2026-11-03  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Integration PR:** #6, `main` ← `feat/tindex-free-data-connector`  
**Integration HEAD:** `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`  
**Post-#19 integration CI:** run `41598989190` completed successfully on exact head `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; all five required job types succeeded.  
**Current posture:** engineering integration is consolidated, but no data source has passed full acceptance and no representative investment strategy has passed empirical validation.

## Executive status

- PR #1 application baseline is on `main`; no production deployment occurred.
- PRs #7, #9, #13, #14, #16, #17 and #18 are merged into PR #6 in dependency order.
- PR #6 remains open and **must not be merged into `main` without explicit owner approval**.
- PR #19 source-evidence refresh is merged into #6 at `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; its exact-head run `41598599936` passed all five required job types. The new post-merge #6 run `41598989190` is queued.
- PR #20 is the next integration PR, adding a fail-closed candidate identity crosswalk to the PR #14 TSETMC runner. Its exact head is `c58cde2c87c698ec4a33a58ff2d3caeeecd70569`; run `41600402263` is in progress. Do not merge until all five required job types pass on this exact head.
- PR #8 remains parked after the GitHub-hosted TSETMC live request timed out. Do not repeat that request from the same environment.
- PR #15 governance remains Draft; its documents are updated on the governance branch, but the PR is not merged.
- No production deployment, source approval, investment ranking/scoring activation, portfolio allocation or real-money trade occurred.

## Verified integration graph

```text
main
  └─ #6 feat/tindex-free-data-connector [open; never merge to main without explicit owner approval]
       ├─ #7 Tindex/FRED fixes                         [merged]
       ├─ #9 Iran market dashboard                     [merged]
       ├─ #13 free-dataset discovery                   [merged]
       ├─ #14 integrated offline TSETMC acceptance     [merged]
       ├─ #16 source-evidence reconciliation           [merged]
       ├─ #17 Stage 4 cost-sensitivity correction      [merged]
       └─ #18 monthly-calendar continuity validation  [merged]

#8  research/iran-free-data-smoke                    [open; parked]
#15 governance/execution-constitution-v1              [open; Draft]
#19 research/2026-11-03-source-evidence-refresh       [merged into #6]
#20 fix/tsetmc-identity-crosswalk-discovery            [open; CI in progress]
```

| PR | Exact result | State |
|---|---|---|
| #1 | Application baseline merged to `main`; no deployment | Merged |
| #6 | Head `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; post-#19 run `41598989190` passed all five required job types | Open; do not merge to main |
| #7 | Tindex/FRED corrections and strict 1/minute + 100/day guard | Merged into #6 |
| #8 | GitHub-hosted TSETMC live request timed out to `cdn.tsetmc.com` | Open; parked |
| #9 | Iranian market dashboard and read-only research endpoints | Merged into #6 |
| #13 | Free-dataset discovery/catalog and candidate audit tools | Merged into #6 |
| #14 | Exact-head run `41401668921` passed all five required job types; merge `f267c49efcbf72e7ddc17099ff93f38ade269a7b` | Merged into #6 |
| #15 | Governance constitution/state/register and Runner trust boundary | Open; Draft |
| #16 | Exact-head CI passed; merge `77d25986627664b6482e515fbd4bd9791a041797` | Merged into #6 |
| #17 | Exact-head CI passed; merge `c821f6423ee5734590b4852eb5fab307834f0b51` | Merged into #6 |
| #18 | Exact-head CI passed; merge `d468d06eb0fb4adcc90f04be38a61f4f1164ad57` | Merged into #6 |
| #19 | Exact-head run `41598599936` passed all five required job types; merge `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b` | Merged into #6 |
| #20 | Head `c58cde2c87c698ec4a33a58ff2d3caeeecd70569`; run `41600402263` in progress | Open; do not merge until all five required job types pass on this exact head |

## Source and dataset evidence

This section distinguishes committed documentation and previously shared sanitized owner-run summaries from direct local access. No local raw dataset was read or re-audited in this GitHub-only execution.

### TSETMC — Iran equities and listed funds

- A previously shared owner-run report dated 2026-10-23 records **1,220 raw archives, 1,220 normalized histories and 1,677,202 history rows**.
- An earlier whole-corpus candidate build reports **128 candidate series, 167,912 feature rows and 151,784 forward-label rows**. The report marks feature rows `research_only=1`, `adjusted_returns_allowed=0`, `scoring_allowed=0`, `backtest_approved=0`; forward labels remain research-only and not scoring-eligible. The forward-label artifact metadata reported zero distinct dates, so row count does not prove valid label chronology.
- The same sanitized report lists **48,902 corporate-action rows** and **48,059 date-gap rows** in review queues. These are extracted candidate rows, not independently verified events or gaps.
- A separate earlier diagnostic of a then-current `run_tsetmc_acceptance_pipeline.py` discovered 47 instruments, quarantined all 47 and emitted zero features/labels. Do not repeat that exact run blindly. Compare its version, root and discovery scope with the 1,220-history inventory before executing the merged PR #14 runner.
- The PR #14 integrated offline runner has **not** been run against the owner's 1,220-instrument corpus in this environment. It makes no network requests and requires explicit traceable evidence before research eligibility; it never approves scoring or backtests.
- Open gates: source rights; exact instrument/ISIN identity; raw-vs-adjusted close semantics; corporate-action completeness and economic correctness; calendar/suspension explanations for gaps; dividends/total-return and volume semantics; independent lawful reconciliation; point-in-time tradability.

### Other Iran candidates

- **Nerkhsanj:** prior owner-reported capture parsed 28 candidate keys / 91,245 rows. The reported audit flagged 182 adjacent moves >=20%, including 48 >=100%, concentrated in IQD, silver and Tether. IQD had a 373-day maximum gap; silver, Tether and Bitcoin had gaps up to 84 days. Keep IQD/silver/Tether excluded from feature generation; keep Bitcoin as a coverage warning. These are sanitized owner-reported summaries, not a fresh raw-data audit. Lineage, attribution, rights, units and independent reconciliation remain unresolved.
- **Tindex:** documented free-tier limits remain 1 request/minute and 100 successful requests/day, shared account-wide; history is capped at 100 days. Previously reviewed public docs distinguish TSE stock-price endpoints in Rial from other Markets & Indicators values in Toman since 2026-07-20 and describe a 1,644-active-instrument stock screener. Actual account-specific access is unverified; do not bulk-crawl or mix endpoint unit families.
- **CODAL:** discovery adapter only. Retrieval time is not publication time; original/corrected filing linkage, publication timestamps and automated-use rights remain unresolved.
- **TGJU / physical gold / free FX:** discovery candidates only. Automated collection rights, free-vs-official FX definition, quote side, units, timestamps and lawful independent reference remain unresolved.
- **Iran official macro:** Central Bank / Statistical Center remain candidates; machine-readable historical coverage, release time, revisions and definitions are not accepted.
- **Iran fixed income:** no accepted local security/yield series; price, coupon/cash-flow, maturity, day-count and historic yield contracts remain undefined.

### Global candidates

- **World Bank Indicators:** prior export reports 26 annual Iran CPI rows for 2000–2025; the non-null value count was not reported. Annual observation year is not release/availability time; revisions and series definitions must be preserved. It is macro context, not daily market pricing.
- **Binance Spot:** owner-reported Iran-network attempts returned HTTP 451 for BTCUSDT/ETHUSDT/SOLUSDT. Keep the route blocked; do not seek alternate hosts to bypass it. A separate small foreign sample is not multi-year coverage or rights acceptance.
- **Yahoo Finance:** existing proxy captures may support exploratory research only. Reuse existing captures; do not redownload without a changed acceptance question. Terms, adjustments, symbol/currency mapping, survivorship and point-in-time limitations remain open. US ETFs are not a representative Iran universe.
- **FRED/ALFRED:** API key/access was previously unavailable. Observation period and day-level vintage are not exact intraday release time; do not repeat the same probe until secure access/network changes.
- **GDELT:** prior HTTP 429 remains in cooldown. `seendate` is first-seen/index time, not publisher publication time. No validated Persian/English sentiment/event benchmark exists.
- **StreamData:** seller-provided, not free. Rights/contract, AYAR OHLC anomaly, units, timestamps and independent reconciliation remain unresolved.

## Stage 4 — backtest readiness and evidence

- The existing exploratory Stage 4 report uses 78 monthly rows (2020-04 through 2026-09) across 11 global proxies/US ETFs and crypto assets. It is not a representative Iranian-market sample.
- It uses a 12-month final holdout (2025-10 through 2026-09), seven chronological six-month folds, monthly momentum, equal-weight monthly-rebalanced, equal-weight buy-and-hold and zero-return cash baselines.
- Full-period momentum result: 285.95% total return, 28.32% CAGR, 45.65% annualized volatility, 0.77 Sharpe and -40.15% maximum drawdown. Equal-weight monthly-rebalanced: 175.79% total return, 20.60% CAGR, 25.38% volatility, 0.86 Sharpe and -33.74% maximum drawdown. Higher nominal return did not produce the best recorded Sharpe or drawdown.
- The single 12-month holdout recorded momentum +30.57% vs equal-weight monthly +6.41%, but one year is too short to establish stable edge.
- A material six-month fold anomaly remains: approximately +240.89% for momentum from 2023-10 through 2024-03. Asset-level attribution and data integrity review have not been completed. Do not tune on or reinterpret the locked holdout.
- Cost assumptions in the exploratory report were 10 bps transaction cost + 25 bps slippage, with 25/50 bps higher-cost stress; slippage is an assumption, not measured execution. Annual risk-free rate was 0%.
- No permissioned, representative, point-in-time, net-of-realistic-cost out-of-sample strategy result has been accepted. No calibrated probability or validated AI prediction model exists.

## Local execution and Runner blocker

- No trusted local Runner is registered. The owner's local raw corpus and Stage 4 monthly input are not available to this execution.
- The connected GitHub integration cannot configure or verify private repository rulesets/branch protection in the current account. All inspected branches remain unprotected.
- The Runner trust boundary is documented in `LOCAL_RUNNER_TRUST_BOUNDARY.md`. Before activation, owner-side branch protection, a dedicated unprivileged OS account, restricted read/write data directories, repository-scoped ephemeral Runner and a separate trusted `workflow_dispatch` workflow are required.
- Until those controls are verified, local TSETMC acceptance, local event/gap-ledger review and empirical Stage 4 execution remain **BLOCKED**. No local audit is claimed.

## Independent work completed in this execution — 2026-11-03

- Reviewed the live repository, PR graph and governance documents.
- Confirmed PR #14 is already merged into #6 and the post-#18 #6 CI run passed all five required job types.
- Opened and merged PR #19 after all five exact-head CI job types passed. It refreshes the source catalog and evidence-led candidate triage, recording Nerkhsanj anomalies/quarantine, previous TSETMC whole-corpus evidence/scope mismatch, and Tindex Rial/Toman/account-scope constraints. No provider probe or local raw-data access occurred.
- Verified the current source registry has 18 registered entries and every `approved_for_production` flag is false.
- Reviewed the Stage 4 protocol, empirical review and backtest code. No new empirical run was attempted because the permissioned local input is unavailable and the known extreme fold requires attribution, not a repeated blind run.
- Static review found the PR #14 discovery runner did not consume the corpus's preferred `corpus_reconciliation_v2/instrument_details.jsonl` ISIN → insCode map. PR #20 adds unique candidate identity resolution, v2-over-v1 precedence, ambiguity quarantine and SHA-256 provenance; it deliberately does not create identity evidence or enable research/scoring.

## Operating constraints

- Investment source approval, ranking and scoring remain fail-closed.
- No real-money trades, portfolio allocation, broker integration or production deployment.
- Reachability, mocked tests, fixture tests and green CI do not establish source acceptance or profitability.
- Keep raw datasets, credentials and private captures outside Git.
- PR #8 remains parked; do not repeat the same GitHub-hosted TSETMC live probe.
- PR #6 remains open at the main boundary pending explicit owner approval.

## Next actions

1. Complete all five required CI job types on exact PR #20 head `c58cde2c87c698ec4a33a58ff2d3caeeecd70569` (run `41600402263`); if all pass, merge #20 into #6 and verify the new #6 head and post-merge CI.
2. Update this state and the PR register with the exact PR #20 merge SHA and post-merge #6 CI result; keep PR #15 Draft.
3. Resolve the Runner trust boundary before any local data execution; do not register a Runner on an unprotected branch or arbitrary PR workflow.
4. Once trusted local execution is available, compare the exact PR #14 runner/discovery scope with the earlier 47-instrument diagnostic and 1,220-history inventory, then run the integrated offline pipeline once against the designated corpus.
5. Review existing corporate-action/date-gap queues against official evidence; do not regenerate candidate histories or silently repair gaps.
6. Attribute the 2023-10 to 2024-03 Stage 4 outlier using the same dataset hash and code/config provenance; do not inspect the locked holdout for tuning.
7. Only after rights, units, timestamps, history, corporate actions, independent reconciliation and point-in-time gates pass, run a locked chronological evaluation with realistic costs/slippage, drawdown and predeclared baselines.
8. Do not merge PR #6 into `main` without explicit owner approval. No deployment or scoring activation is implied by any merge.
