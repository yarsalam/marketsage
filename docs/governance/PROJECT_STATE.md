# MarketSage — Current Project State

**Snapshot date:** 2026-11-04  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Integration PR:** #6, `main` ← `feat/tindex-free-data-connector`  
**Integration HEAD:** `a2e19c156f226241a34658d32d25e93173c99a5d`  
**Post-#23 integration CI:** PR run `41793156231` passed all five required job types on exact head `a2e19c156f226241a34658d32d25e93173c99a5d`; PR #23's exact-head run `41792758377` passed all five jobs before merge.  
**Current posture:** engineering integration is consolidated, but no data source has passed full acceptance and no representative investment strategy has passed empirical validation.

## Executive status

- PR #1 application baseline is on `main`; no production deployment occurred.
- PRs #7, #9, #13, #14, #16, #17 and #18 are merged into PR #6 in dependency order.
- PR #6 remains open and **must not be merged into `main` without explicit owner approval**.
- PR #19 source-evidence refresh is merged into #6 at `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; its exact-head run `41598599936` and post-merge #6 run `41598989190` passed all five required job types.
- PR #20 TSETMC identity crosswalk passed all five required job types on exact head `c58cde2c87c698ec4a33a58ff2d3caeeecd70569` (run `41600402263`) and was merged into #6 at `4191dd3715173265193163e30281ab555b9d12fb`. Both post-merge runs `41601055518` (push) and `41601064135` (pull_request) subsequently passed all five job types.
- PR #21 corrected stale Tindex quota wording and added a mocked regression test. All five required exact-head job types passed on `7c52b11a6cc3e41fb214114d95b2d4df70f28fa9` (run `41601260850`); it was merged into #6 at `21c591223c9e7d61e6046a06f51522e979530f08`.
- PR #22 added five official global source candidates (ECB, US Treasury, EIA, SEC EDGAR and IMF) with rights/time/history caveats and fail-closed registry tests. All five required job types passed on exact head `6eff5daf8c2b86a96015992d3f9d3f17beacab82` in PR run `41602083315` and push run `41602045431`; it was merged into #6 at `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`. Both post-merge runs `41602459792` and `41602467771` passed all five job types.
- PR #23 reconciled the current Tindex quota evidence: official docs rechecked 2026-11-04 publish 3 requests/minute and 300 requests/day per account, while the MarketSage client retains its stricter local 1/minute and 100-success/day cap. Its exact-head run `41792758377` passed all five jobs; it merged into #6 at `a2e19c156f226241a34658d32d25e93173c99a5d`, and post-merge PR run `41793156231` passed all five jobs.
- PR #8 remains parked after the GitHub-hosted TSETMC live request timed out. Do not repeat that request from the same environment.
- PR #15 governance remains Draft; its documents are updated through PR #23 and now record the private-repository branch-protection plan blocker, but the PR is not merged.
- The governance documents referenced in this state file currently exist on PR #15's `governance/execution-constitution-v1` branch; PR #15 is still Draft and these files are not present on the default `main` branch. They are therefore a working continuity record, not yet an adopted default-branch policy.
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
       ├─ #18 monthly-calendar continuity validation  [merged]
       ├─ #19 source-evidence refresh                   [merged]
       ├─ #20 TSETMC identity crosswalk                 [merged]
       ├─ #21 Tindex quota wording correction           [merged]
       ├─ #22 official global source candidates         [merged]
       └─ #23 Tindex quota evidence reconciliation     [merged]

#8  research/iran-free-data-smoke                    [open; parked]
#15 governance/execution-constitution-v1              [open; Draft]
```

| PR | Exact result | State |
|---|---|---|
| #1 | Application baseline merged to `main`; no deployment | Merged |
| #6 | Head `a2e19c156f226241a34658d32d25e93173c99a5d`; post-#23 PR run `41793156231` passed all five required jobs | Open; do not merge to main |
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
| #20 | Exact-head run `41600402263` passed all five required job types; merge `4191dd3715173265193163e30281ab555b9d12fb` | Merged into #6 |
| #21 | Exact-head run `41601260850` passed all five required job types; merge `21c591223c9e7d61e6046a06f51522e979530f08` | Merged into #6 |
| #22 | PR run `41602083315` and push run `41602045431` passed all five required job types; merge `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f` | Merged into #6 |
| #23 | Exact-head run `41792758377` passed all five required jobs; merge `a2e19c156f226241a34658d32d25e93173c99a5d`; post-merge PR run `41793156231` passed all five jobs | Merged into #6 |

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
- **Tindex:** official English and Persian docs rechecked 2026-11-04 publish 3 requests/minute and 300 requests/day per account, with one active token; HTTP 429 rejections do not count toward the daily quota. MarketSage deliberately retains a stricter local cap of 1 request/minute and 100 successful requests/day. Indicator history/candles remain capped at 100 days. Docs distinguish TSE stock-price endpoints in Rial from other Markets & Indicators values in Toman since 2026-07-20 and describe a 1,644-active-instrument stock screener. Actual account-specific access, rights and unit reconciliation remain unverified; do not bulk-crawl or mix endpoint unit families.
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
- **New official global candidates (PR #22):** ECB SDMX for reference FX/yields/macros (supports `updatedAfter`/`includeHistory`, with attribution/no-modification and third-party exclusions); US Treasury XML for daily yields (observation date, pagination and reuse terms still need review); EIA API v2 for energy (registered key and ToS; public-domain/third-party distinction); SEC EDGAR for filings/XBRL (no key, 10 requests/sec and declared User-Agent; acceptance vs availability and corrections); IMF SDMX (Swagger account requirement; endpoint auth, quotas, vintages and rights unresolved). All five are catalog/registry candidates only, not wired into research, not default-probed and not approved.
- **StreamData:** seller-provided, not free. Rights/contract, AYAR OHLC anomaly, units, timestamps and independent reconciliation remain unresolved.

## Stage 4 — backtest readiness and evidence

- The existing exploratory Stage 4 report uses 78 monthly rows (2020-04 through 2026-09) across 11 global proxies/US ETFs and crypto assets. It is not a representative Iranian-market sample.
- It uses a 12-month final holdout (2025-10 through 2026-09), seven chronological six-month folds, monthly momentum, equal-weight monthly-rebalanced, equal-weight buy-and-hold and zero-return cash baselines.
- Full-period momentum result: 285.95% total return, 28.32% CAGR, 45.65% annualized volatility, 0.77 Sharpe and -40.15% maximum drawdown. Equal-weight monthly-rebalanced: 175.79% total return, 20.60% CAGR, 25.38% volatility, 0.86 Sharpe and -33.74% maximum drawdown. Higher nominal return did not produce the best recorded Sharpe or drawdown.
- The single 12-month holdout recorded momentum +30.57% vs equal-weight monthly +6.41%, but one year is too short to establish stable edge.
- A material six-month fold anomaly remains: approximately +240.89% for momentum from 2023-10 through 2024-03. Asset-level attribution and data integrity review have not been completed. Do not tune on or reinterpret the locked holdout.
- Cost assumptions in the exploratory report were 10 bps transaction cost + 25 bps slippage, with 25/50 bps higher-cost stress; slippage is an assumption, not measured execution. Annual risk-free rate was 0%.
- No permissioned, representative, point-in-time, net-of-realistic-cost out-of-sample strategy result has been accepted. No calibrated probability or validated AI prediction model exists.

### Static code review — 2026-11-04

- `research/backtest.py` validates a complete, finite, positive monthly price panel with unique, consecutive calendar months; momentum/volatility signals use data through the prior month-end and the following month's return is applied afterward. Transaction costs and slippage are charged on L1 gross traded-weight turnover (buys plus sells), including initial allocation.
- `research/evaluation.py` keeps a final holdout separate from pre-holdout chronological six-month folds and compares net momentum with monthly-rebalanced equal weight, equal-weight buy-and-hold and zero-return cash, plus predeclared higher-cost stress. Six-month forward labels are reported as inventory only, not as model predictions.
- The validation is structural, not provenance validation: the evaluator accepts a caller-supplied monthly CSV. Its complete-panel requirement does not resolve universe survivorship, source rights, corporate actions, point-in-time availability, currency comparability or executable liquidity. Those remain upstream acceptance gates.
- `scripts/analyze_stage4_fold.py` is available to attribute the 2023-10 to 2024-03 anomaly by selected assets/monthly returns and reconcile gross contributions. It has not been run because the exact permissioned local input is unavailable here; run it only against the same pinned dataset hash/configuration used for the recorded result.

## Local execution and Runner blocker

- No trusted local Runner is registered. The owner's local raw corpus and Stage 4 monthly input are not available to this execution.
- Owner-side host preparation reported on 2026-11-04: Ubuntu 26.04.1 LTS x86_64; dedicated `marketsage-runner` account created (UID 110/GID 119, only its own group, no `sudo` group); `/opt/actions-runner/marketsage` created as owner/group `marketsage-runner`, mode `0750`. The supplied shell output found no prior `config.sh`/`run.sh` or `$HOME/actions-runner*` installation. This is owner-reported host output, not an independent remote host audit.
- The Runner package has not been installed, configured or registered; no Runner is online, no research data directories have been exposed, and no workflow has been changed to use `self-hosted`. Account creation alone does not satisfy the trust boundary.
- The connected GitHub integration cannot configure or verify private repository rulesets/branch protection in the current account. GitHub's current plan docs say private-repository branch protection/rulesets require Pro, Team or Enterprise; moving to a Free Organization alone does not resolve this. The protection state therefore remains unverified through this connection.
- The Runner trust boundary is documented in `LOCAL_RUNNER_TRUST_BOUNDARY.md`. Before registration/activation, either private-repository branch protection must be available and verified, or the owner must explicitly approve a revised trust model with its residual risk. Restricted read/write data directories, repository-scoped Runner and a separate trusted `workflow_dispatch` workflow are also required.
- Until those controls are verified, local TSETMC acceptance, local event/gap-ledger review and empirical Stage 4 execution remain **BLOCKED**. No local audit is claimed.

## Independent work completed in this execution — 2026-11-04

- Reviewed the live repository, PR graph and governance documents.
- Confirmed PR #14 is already merged into #6 and the post-#18 #6 CI run passed all five required job types.
- Revalidated PR #14 live metadata: it is merged into #6 at `f267c49efcbf72e7ddc17099ff93f38ade269a7b`; exact-head run `41401668921` passed all five required jobs on head `4bd179263f55b90854d00f1ea3b1287da0393b03`. No second merge was needed. The current #6 head remains `a2e19c156f226241a34658d32d25e93173c99a5d`, and post-#23 run `41793156231` passed all five required jobs.
- Opened and merged PR #19 after all five exact-head CI job types passed. It refreshes the source catalog and evidence-led candidate triage, recording Nerkhsanj anomalies/quarantine, previous TSETMC whole-corpus evidence/scope mismatch, and Tindex Rial/Toman/account-scope constraints. No provider probe or local raw-data access occurred.
- Verified the source registry had 18 entries before the new global-source screen; PR #22 expands it to 22 registered entries, while the catalog grows from 13 to 18. The five new catalog entries are not default-probed, not wired into research and remain unapproved.
- Reviewed the Stage 4 protocol, empirical review and backtest code. No new empirical run was attempted because the permissioned local input is unavailable and the known extreme fold requires attribution, not a repeated blind run.
- Static review found the PR #14 discovery runner did not consume the corpus's preferred `corpus_reconciliation_v2/instrument_details.jsonl` ISIN → insCode map. PR #20 added unique candidate identity resolution, v2-over-v1 precedence, ambiguity quarantine and SHA-256 provenance; exact-head CI passed and it was merged at `4191dd3715173265193163e30281ab555b9d12fb`. It does not create identity evidence or enable research/scoring.
- PR #21 fixes two stale Tindex quota descriptions in `discover_free_datasets.py` that still referred to a three-request/minute limiter despite the connector enforcing 1 request/minute and 100 successful requests/day. Its exact-head CI passed all five job types and it was merged at `21c591223c9e7d61e6046a06f51522e979530f08`. No Tindex endpoint was contacted.
- PR #22 reviewed official documentation for ECB, US Treasury, EIA, SEC EDGAR and IMF; added five candidates, source-specific rights/time/history gates, and fail-closed regression tests. No data API was called, no key was used, and no adapter/default probe was added.
- Rechecked Tindex's official English and Persian API documentation on 2026-11-04. The published account quota is 3 requests/minute and 300 requests/day (429 responses do not consume the daily quota), not the older 1/100 snapshot. Updated the source catalog and registry to version 1.1.1 and exposed provider-published versus local-enforced quotas in status output; the local 1/100 guard was not relaxed. PR #23 passed all five exact-head jobs and merged into #6; no token or API request was used.
- Verified from GitHub's current plan documentation that private repositories need Pro/Team/Enterprise for branch protection/rulesets; a Free Organization does not remove this blocker. Updated the Runner trust-boundary document. Runner registration and local data access remain blocked pending an owner-approved plan or revised trust model.

## Operating constraints

- Investment source approval, ranking and scoring remain fail-closed.
- No real-money trades, portfolio allocation, broker integration or production deployment.
- Reachability, mocked tests, fixture tests and green CI do not establish source acceptance or profitability.
- Keep raw datasets, credentials and private captures outside Git.
- PR #8 remains parked; do not repeat the same GitHub-hosted TSETMC live probe.
- PR #6 remains open at the main boundary pending explicit owner approval.

## Next actions

1. PR #23 passed all five required job types on exact head `f400166fb184ee1d23ec3905a5d4f1c8a71f86e1` in run `41792758377` and merged into #6 at `a2e19c156f226241a34658d32d25e93173c99a5d`. Post-merge PR run `41793156231` passed all five required jobs on the exact integration head.
2. PR #22's post-merge runs `41602459792` and `41602467771` both passed all five required jobs on the preceding integration head `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`.
3. Keep PR #15 Draft and update this state/register after each material transition.
4. Resolve the Runner trust boundary before any local data execution; do not register a Runner on an unprotected branch or arbitrary PR workflow.
5. Once trusted local execution is available, compare the exact PR #14 runner/discovery scope with the earlier 47-instrument diagnostic and 1,220-history inventory, then run the integrated offline pipeline once against the designated corpus.
6. Review existing corporate-action/date-gap queues against official evidence; do not regenerate candidate histories or silently repair gaps.
7. Attribute the 2023-10 to 2024-03 Stage 4 outlier using the same dataset hash and code/config provenance; do not inspect the locked holdout for tuning.
8. Only after rights, units, timestamps, history, corporate actions, independent reconciliation and point-in-time gates pass, run a locked chronological evaluation with realistic costs/slippage, drawdown and predeclared baselines.
9. Do not merge PR #6 into `main` without explicit owner approval. No deployment or scoring activation is implied by any merge.
