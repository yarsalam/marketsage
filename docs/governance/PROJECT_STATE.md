# MarketSage — Current Project State

**Snapshot date:** 2026-11-04  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`  
**Integration PR:** #6, `main` ← `feat/tindex-free-data-connector`  
**Integration HEAD:** `21552b719513d72f7fc10eff1efa11651c3d8530`  
**Post-#28 integration CI:** PR run `41847126900` and push run `41847115366` both passed all five required job types on exact integration head `21552b719513d72f7fc10eff1efa11651c3d8530`.  
**Current posture:** engineering integration is consolidated, but no data source has passed full acceptance and no representative investment strategy has passed empirical validation.

## Executive status

- PR #1 application baseline is on `main`; no production deployment occurred.
- PRs #7, #9, #13, #14, #16, #17, #18, #19, #20, #21, #22, #23, #24 and #28 are merged into PR #6 in dependency order.
- PR #6 remains open and **must not be merged into `main` without explicit owner approval**.
- PR #28 added an Iran official-source candidate screen: CBI TSD annual macro, official transfer FX, weekly policy rates and government Islamic-securities auction PDFs. It added `iran.cbi.bond_auction_results`, bumped catalog/registry to 1.1.2 and added fail-closed tests. Exact-head PR run `41846337902` passed all five jobs; merged into #6 at `21552b719513d72f7fc10eff1efa11651c3d8530`; post-merge CI is in progress.
- PR #27 adds a separate manual-only offline dataset validator workflow and is merged to `main` at `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`; all five required CI jobs passed on exact PR head `c60edd0f16244ab12e6602b9247e4174567f6081` in run `41833221157`. It does not register or start a Runner.
- PR #19 source-evidence refresh is merged into #6 at `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; its exact-head run `41598599936` and post-merge #6 run `41598989190` passed all five required job types.
- PR #20 TSETMC identity crosswalk passed all five required job types on exact head `c58cde2c87c698ec4a33a58ff2d3caeeecd70569` (run `41600402263`) and was merged into #6 at `4191dd3715173265193163e30281ab555b9d12fb`. Both post-merge runs `41601055518` (push) and `41601064135` (pull_request) subsequently passed all five job types.
- PR #21 corrected stale Tindex quota wording and added a mocked regression test. All five required exact-head job types passed on `7c52b11a6cc3e41fb214114d95b2d4df70f28fa9` (run `41601260850`); it was merged into #6 at `21c591223c9e7d61e6046a06f51522e979530f08`.
- PR #22 added five official global source candidates (ECB, US Treasury, EIA, SEC EDGAR and IMF) with rights/time/history caveats and fail-closed registry tests. All five required job types passed on exact head `6eff5daf8c2b86a96015992d3f9d3f17beacab82` in PR run `41602083315` and push run `41602045431`; it was merged into #6 at `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`. Both post-merge runs `41602459792` and `41602467771` passed all five job types.
- PR #23 reconciled the current Tindex quota evidence: official docs rechecked 2026-11-04 publish 3 requests/minute and 300 requests/day per account, while the MarketSage client retains its stricter local 1/minute and 100-success/day cap. Its exact-head run `41792758377` passed all five jobs; it merged into #6 at `a2e19c156f226241a34658d32d25e93173c99a5d`, and post-merge PR run `41793156231` passed all five jobs.
- PR #24 removes Binance Spot from default probes and hard-blocks explicit discovery requests after owner-reported Iran-network HTTP 451; the runner returns `blocked_owner_reported_http_451` with `requests_attempted=0`. No network request or alternate route was used. Exact-head run `41796133083` passed all five required jobs; PR #24 merged into #6 at `e19d65840d9112362209a23ea53c7fcf608c0720`; post-merge run `41796506276` passed all five jobs.
- PR #8 remains parked after the GitHub-hosted TSETMC live request timed out. Do not repeat that request from the same environment.
- PR #15 governance remains Draft; its documents are being reconciled with PRs #27/#28 and the latest owner terminal evidence. They are not yet adopted on `main`.
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
       ├─ #23 Tindex quota evidence reconciliation     [merged]
       ├─ #24 Binance HTTP 451 probe hard block          [merged]
       └─ #28 Iran official macro/bond candidate screen   [merged]

#8  research/iran-free-data-smoke                    [open; parked]
#15 governance/execution-constitution-v1              [open; Draft]
```

| PR | Exact result | State |
|---|---|---|
| #1 | Application baseline merged to `main`; no deployment | Merged |
| #6 | Head `21552b719513d72f7fc10eff1efa11651c3d8530`; PR run `41847126900` and push run `41847115366` passed all five required jobs | Open; do not merge to main |
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
| #24 | Exact-head PR run `41796133083` and post-merge PR run `41796506276` passed all five required jobs; merge `e19d65840d9112362209a23ea53c7fcf608c0720` | Merged into #6 |
| #27 | Exact-head PR run `41833221157` passed all five required jobs; merge `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767` | Merged to `main`; manual-only workflow; Runner not registered |
| #28 | Exact-head PR run `41846337902` and post-merge PR/push runs `41847126900` / `41847115366` passed all five jobs; merge `21552b719513d72f7fc10eff1efa11651c3d8530` | Merged into #6 |

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
- **Binance Spot:** owner-reported Iran-network attempts returned HTTP 451 for BTCUSDT/ETHUSDT/SOLUSDT. PR #24 removes it from default probes and hard-blocks explicit discovery selection with zero requests; do not seek alternate hosts or retry without a changed access/legal basis. A separate small foreign sample is not multi-year coverage or rights acceptance.
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

- Dedicated account: `marketsage-runner`, UID 110/GID 119, shell `nologin`, member only of its own group and absent from `sudo`, `docker`, `lxd` and `adm`. The general `/home/nima` tree is not traversable by this account.
- Latest owner-provided terminal evidence corrects the earlier package-location note: `~/actions-runner/actions-runner-linux-x64-2.338.2.tar.gz` is 228,071,396 bytes and extracted files (`config.sh`, `run.sh`, `bin`, `externals`) are present in that personal directory. The extracted executable timestamps are from 2026-10-26, so their correspondence/version relative to the 2026-11-04 archive has not been verified.
- `/opt/actions-runner/marketsage` currently contains only a 9,719,808-byte partial archive; no extracted `config.sh` or `run.sh` is present there. The Runner is therefore **not installed in its designated location**. Do not copy the personal directory's `.env`, `.path` or `_diag` files into the dedicated installation.
- No Runner service or active Runner process was found in the latest owner-provided terminal output. No repository-level Runner is registered or online. A registration token previously pasted into chat is compromised and must never be reused; any registration must use a fresh token entered locally only.
- Dataset staged at `/srv/marketsage/data/tsetmc_history_20261022`: 8,801 source files plus `SHA256SUMS` and `STAGING_README.txt` (8,803 files total). The owner previously reported all 8,801 source-file hashes verified, adjusted research-only candidate series excluded, and source tree unchanged.
- Dataset files are `0440`, directories `2750`, group `marketsage-runner`. Owner-reported tests showed representative reads/hash/JSON/CSV checks passing, data writes denied, and a separate `/srv/marketsage/output` write/create/delete test passing. These remain owner-supplied terminal results, not an independent penetration test.
- The owner selected the manual-only compensating-control model in Issue [#25](https://github.com/yarsalam/marketsage/issues/25). This accepts residual risk but is not equivalent to private branch protection/rulesets. Live GitHub branch metadata still reports `main.protected=false`.
- Workflow inventory and review: `main` has `.github/workflows/ci.yml`, whose jobs run on `ubuntu-latest`; no existing general CI job targets self-hosted. The PR #8 TSETMC smoke workflow on the integration branch also uses `ubuntu-latest` and remains parked after ConnectTimeout. PR #27 adds the only local workflow: `workflow_dispatch` only, default-branch/owner/explicit-confirmation gates, labels `self-hosted, linux, x64, marketsage-local, marketsage-research`, `contents: read`, full-SHA-pinned checkout, no secrets, provider probes or artifact upload. It writes a sanitized validator report locally.
- PR #27's first workflow validates the staged dataset inventory and all 8,801 hashes; it does **not** yet execute the full PR #14 integrated TSETMC acceptance pipeline. That remains a later, separately reviewed workload after the first validator and host environment are verified.
- The GitHub-side workflow gate is complete, but the Runner must remain unregistered/offline until the full archive is hash-verified and freshly extracted under `/opt/actions-runner/marketsage`, service/workspace isolation is applied, and a final no-credentials/no-process audit passes. Owner action is tracked in [Issue #25](https://github.com/yarsalam/marketsage/issues/25).
- No local pipeline has run under GitHub Actions. Source approval, rights approval, backtest admission, ranking/scoring and production approval remain false/disabled.

## Independent work completed in this execution — 2026-11-04

- Reviewed the live repository, PR graph and governance documents.
- Revalidated PR #14 live metadata: it is merged into #6 at `f267c49efcbf72e7ddc17099ff93f38ade269a7b`; exact-head run `41401668921` passed all five required jobs on head `4bd179263f55b90854d00f1ea3b1287da0393b03`. No second merge was needed. The current #6 head is now `e19d65840d9112362209a23ea53c7fcf608c0720`; post-#24 run `41796506276` passed all five required jobs.
- PR #24 was opened after static review found the discovery script still default-probed Binance despite the owner-reported HTTP 451 block. The fix excludes it from defaults and hard-blocks explicit selection with zero requests; exact-head and post-merge CI each passed all five jobs.
- Opened and merged PR #19 after all five exact-head CI job types passed. It refreshes the source catalog and evidence-led candidate triage, recording Nerkhsanj anomalies/quarantine, previous TSETMC whole-corpus evidence/scope mismatch, and Tindex Rial/Toman/account-scope constraints. No provider probe or local raw-data access occurred.
- Verified the source registry had 18 entries before the new global-source screen; PR #22 expands it to 22 registered entries, while the catalog grows from 13 to 18. The five new catalog entries are not default-probed, not wired into research and remain unapproved.
- Reviewed the Stage 4 protocol, empirical review and backtest code. No new empirical run was attempted because the permissioned local input is unavailable and the known extreme fold requires attribution, not a repeated blind run.
- Static review found the PR #14 discovery runner did not consume the corpus's preferred `corpus_reconciliation_v2/instrument_details.jsonl` ISIN → insCode map. PR #20 added unique candidate identity resolution, v2-over-v1 precedence, ambiguity quarantine and SHA-256 provenance; exact-head CI passed and it was merged at `4191dd3715173265193163e30281ab555b9d12fb`. It does not create identity evidence or enable research/scoring.
- PR #21 fixes two stale Tindex quota descriptions in `discover_free_datasets.py` that still referred to a three-request/minute limiter despite the connector enforcing 1 request/minute and 100 successful requests/day. Its exact-head CI passed all five job types and it was merged at `21c591223c9e7d61e6046a06f51522e979530f08`. No Tindex endpoint was contacted.
- PR #22 reviewed official documentation for ECB, US Treasury, EIA, SEC EDGAR and IMF; added five candidates, source-specific rights/time/history gates, and fail-closed regression tests. No data API was called, no key was used, and no adapter/default probe was added.
- PR #28 screened CBI TSD, official transfer FX, weekly policy rates and government Islamic-securities auction PDFs. It documented the difference between official transfer FX and free-market FX, annual/weekly frequencies, Jalali/denomination-multiplier checks, PDF primary-market limitations and CBI reuse-rights uncertainty. The new bond-auction candidate remains disabled and fail-closed; no API request or dataset download occurred.
- Rechecked Tindex's official English and Persian API documentation on 2026-11-04. The published account quota is 3 requests/minute and 300 requests/day (429 responses do not consume the daily quota), not the older 1/100 snapshot. Updated the source catalog and registry to version 1.1.1 and exposed provider-published versus local-enforced quotas in status output; the local 1/100 guard was not relaxed. PR #23 passed all five exact-head jobs and merged into #6; no token or API request was used.
- On 2026-11-04 the owner approved the documented manual-only compensating-control model in Issue #25. The decision and accepted residual risk are appended to `DECISION_LOG.md`; `LOCAL_RUNNER_TRUST_BOUNDARY.md` records the exact limits and host evidence. This does not create private branch protection or claim equivalence.

## Operating constraints

- Investment source approval, ranking and scoring remain fail-closed.
- No real-money trades, portfolio allocation changes, broker integration or production deployment.
- Reachability, parser success, fixture tests and green CI do not establish source acceptance or profitability.
- Keep raw datasets, credentials and private captures outside Git.
- PR #8 remains parked; do not repeat the same GitHub-hosted TSETMC live probe from the same network.
- PR #6 remains open at the `main` boundary and must not be merged without explicit owner approval.
- The local Runner must remain unregistered/offline until the designated install is populated from the verified archive, service/workspace isolation and final host checks pass.

## Next actions

1. Verify the SHA-256 of the full local v2.338.2 archive against GitHub's published digest, then extract a fresh copy directly into `/opt/actions-runner/marketsage` as `marketsage-runner`; do not copy personal `.env`, `.path` or diagnostics.
2. Apply service/workspace isolation, a dedicated `_work` directory, cleanup and emergency stop/unregister procedure; confirm the service runs as `marketsage-runner` without sudo or privileged groups.
3. Perform a final local check for stale credentials/processes, then repository-scope register with a fresh token entered locally and custom labels `marketsage-local,marketsage-research`.
4. Before first dispatch, owner reviews the exact current `main` SHA and PR #27 workflow, then manually confirms the bounded offline dataset validator.
5. After the validator report is reviewed, add/review a separate manual workflow for the full PR #14 integrated offline TSETMC acceptance pipeline; compare discovery scope with the earlier 47-instrument diagnostic and 1,220-history inventory.
6. Continue source rights, units, quote convention, publication/revision timestamps, history and independent reconciliation review; do not silently repair data.
7. Attribute the 2023-10 to 2024-03 Stage 4 outlier using the same pinned dataset hash/configuration; do not inspect the locked holdout for tuning.
8. Run locked chronological evaluation only after source/data gates pass, with predeclared baselines, realistic costs/slippage, drawdown and point-in-time controls. Keep scoring/ranking/deployment/trading disabled.
9. Keep PR #15 Draft until its updated governance docs and required checks are reviewed. Do not merge PR #6 into `main` without explicit owner approval.


## Latest automation update — 2026-11-04 (World Bank candidate)

- Live GitHub review on 2026-11-04 confirmed the repository remains private. PR #14 was already merged into integration PR #6 at `f267c49efcbf72e7ddc17099ff93f38ade269a7b`; no repeat merge was performed.
- PR #29 (World Bank Commodity Markets Pink Sheet candidate) passed all five required CI job types on its exact head `3ec83742614bfc1ea283144c15b0063c8ecb51b6` in run `41848702070`, then was merged into PR #6 at `fb64e773387f3eb7270d0dd65d8e885c1f26ba0d`.
- The integration PR #6 now points to `fb64e773387f3eb7270d0dd65d8e885c1f26ba0d`. Post-merge PR run `41849790150` and push run `41849780257` were still in progress at the time of this note; do not treat integration CI as complete until all five jobs in both runs finish successfully.
- PR #29 registers `global.world_bank_commodity_prices` as a monthly/annual macro-context candidate only. The workbook itself was not downloaded or parsed; per-series benchmark/source, exact units, missing months, revision history, and first-availability timestamps remain unverified. It remains `candidate_requires_validation`, outside the research engine and production scoring.
- PR #15 remains Draft. These governance files are on `governance/execution-constitution-v1` and are not yet present on `main`; they remain a working continuity record, not adopted default-branch policy.
- PR #6 remains open. Do not merge it to `main` without explicit owner authorization. PR #8 remains parked after the prior GitHub-hosted TSETMC timeout; do not repeat the same request from that environment.
- Owner action remains tracked in Issue [#25](https://github.com/yarsalam/marketsage/issues/25). Latest terminal output reconfirms the complete 228,071,396-byte v2.338.2 archive and extracted files under `/home/nima/actions-runner`, but the extracted tree's correspondence to that archive is unverified; `/opt/actions-runner/marketsage` has only a 9,719,808-byte partial archive. No Runner process/service is active and no Runner is registered/online. Verify the archive SHA-256, freshly extract into the dedicated path as `marketsage-runner`, exclude personal `.env`, `.path`, and `_diag`, then complete isolation checks before using a fresh locally entered token. The token previously pasted into chat must never be reused.
- No production deployment, source approval, investment ranking/scoring, portfolio allocation, broker access, or real-money trade is authorized. Stage 4 still lacks a representative, permissioned, point-in-time out-of-sample result that establishes net risk-adjusted edge against baselines after costs and drawdown.


### Main/integration divergence after PR #29 — 2026-11-04

- Live compare reports main at 7e669749d2615bc0f2a9d6f557bb99f8e7bd0767 and integration PR #6 at fb64e773387f3eb7270d0dd65d8e885c1f26ba0d; the integration branch is 399 commits ahead and 2 commits behind main. The two main-only commits are the separate PR #27 manual-only offline validator workflow and its associated change. No automatic synchronization was attempted; assess the exact diff/conflicts before any future update.
- Both post-#29 integration CI runs passed all five required jobs. PR #6 remains open and unmerged to main.
