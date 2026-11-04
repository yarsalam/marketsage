# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-04  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch HEAD:** `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`  
**Integration target:** PR #6 branch `feat/tindex-free-data-connector`
**Current integration HEAD:** `21552b719513d72f7fc10eff1efa11651c3d8530`
**Post-#28 CI:** PR run `41847126900` and push run `41847115366` are in progress on exact integration head `21552b719513d72f7fc10eff1efa11651c3d8530`; the exact PR #28 head passed all five required jobs in run `41846337902`.

## Open PRs

| PR | Base ← head | Current head / CI | State and handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | `21552b719513d72f7fc10eff1efa11651c3d8530`; PR run `41847126900` / push run `41847115366` in progress after PR #28 | Open; do not merge to `main` without explicit owner approval. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Live TSETMC request timed out from GitHub-hosted runner | Open; parked. Do not repeat the same network request from that environment. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Owner-approved manual-only Runner exception, PR #27 workflow merged, latest host package-location correction and owner action documented | Open; Draft; adoption pending. |


## Closed PRs

| PR | Result |
|---|---|
| [#26](https://github.com/yarsalam/marketsage/pull/26) | Closed as a duplicate/superseded documentation branch; its two governance updates were fast-forwarded onto PR #15. No merge to `main`. |

## Merged PRs relevant to the integration path

| PR | Merged into | Result |
|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` | Application baseline; no deployment |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 feature branch | Conservative Tindex quota, documented route/history updates, FRED safe diagnostics and tests |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 feature branch | Iranian market dashboard, read-only research endpoints and staging configuration |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 feature branch | Free-dataset discovery, catalog and candidate audit/ingestion tools |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 feature branch | Already merged at `f267c49efcbf72e7ddc17099ff93f38ade269a7b`; exact-head run `41401668921` and post-merge run `41404741827` each passed all five required job types |
| [#16](https://github.com/yarsalam/marketsage/pull/16) | #6 feature branch | Source-evidence reconciliation; merge `77d25986627664b6482e515fbd4bd9791a041797` |
| [#17](https://github.com/yarsalam/marketsage/pull/17) | #6 feature branch | Stage 4 cost-sensitivity scenario correction; merge `c821f6423ee5734590b4852eb5fab307834f0b51` |
| [#18](https://github.com/yarsalam/marketsage/pull/18) | #6 feature branch | Monthly calendar continuity gate; exact-head CI passed all five required job types; merge `d468d06eb0fb4adcc90f04be38a61f4f1164ad57` |
| [#19](https://github.com/yarsalam/marketsage/pull/19) | #6 feature branch | Source-evidence reconciliation; merge `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b` |
| [#20](https://github.com/yarsalam/marketsage/pull/20) | #6 feature branch | TSETMC v2 identity crosswalk, ambiguity quarantine and SHA-256 provenance; all five exact-head jobs passed; merge `4191dd3715173265193163e30281ab555b9d12fb` |
| [#21](https://github.com/yarsalam/marketsage/pull/21) | #6 feature branch | Tindex quota-report consistency correction; all five exact-head jobs passed; merge `21c591223c9e7d61e6046a06f51522e979530f08` |
| [#22](https://github.com/yarsalam/marketsage/pull/22) | #6 feature branch | Five official global source candidates; all five required exact-head jobs passed in PR and push runs; merge `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f` |
| [#23](https://github.com/yarsalam/marketsage/pull/23) | #6 feature branch | Reconciled Tindex's published 3/minute + 300/day account quota with the unchanged stricter local 1/minute + 100-success/day guard; exact-head run `41792758377` passed all five jobs; merge `a2e19c156f226241a34658d32d25e93173c99a5d` |
| [#24](https://github.com/yarsalam/marketsage/pull/24) | #6 feature branch | Removed the owner-reported HTTP 451 Binance route from default probes and hard-blocked explicit discovery selection with zero requests; exact-head run `41796133083` and post-merge run `41796506276` passed all five required jobs; merge `e19d65840d9112362209a23ea53c7fcf608c0720` |

## Current integration graph

```text
main
  └─ #6 [open; do not merge to main without explicit owner approval]
       ├─ #7  [merged]
       ├─ #9  [merged]
       ├─ #13 [merged]
       ├─ #14 [merged]
       ├─ #16 [merged]
       ├─ #17 [merged]
       ├─ #18 [merged]
       ├─ #19 [merged]
       ├─ #20 [merged]
       ├─ #21 [merged]
       ├─ #22 [merged]
       ├─ #23 [merged]
       └─ #24 [merged]

#8  [open; parked network diagnostic]
#15 [open; Draft governance]
```

## Independent evidence notes — 2026-11-04

- PR #19 is merged into #6 at `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; its exact-head run passed all five job types. It updates the source catalog and acceptance matrix using committed docs and previously shared sanitized summaries only. No network request or local raw-file audit was performed.
- PR #20 addressed a static discovery limitation: the integrated runner now reads the preferred v2 `instrument_details.jsonl` crosswalk for candidate identity, never combines v1/v2, hashes the file and keeps identity evidence/research/scoring fail-closed. All five required exact-head CI jobs passed on `c58cde2c87c698ec4a33a58ff2d3caeeecd70569`; merge into #6 is `4191dd3715173265193163e30281ab555b9d12fb`.
- PR #21 corrected stale discovery-script wording that referred to three requests/minute despite the connector's 1 request/minute and 100 successful requests/day guard. All five exact-head jobs passed; merge into #6 is `21c591223c9e7d61e6046a06f51522e979530f08`. No provider request was made.
- PR #22 screened five official global candidates: ECB Data Portal (SDMX history/update metadata and reuse terms), US Treasury XML (daily yield history/pagination), EIA API v2 (key/ToS/public-domain and third-party distinction), SEC EDGAR (no key, 10 req/s, declared User-Agent, acceptance vs availability and corrections), and IMF SDMX (beta account for Swagger; endpoint auth/vintage/rights unresolved). It adds source-specific acceptance contracts and tests that all five candidates remain fail-closed. No live data API was contacted. Both exact-head PR run `41602083315` and push run `41602045431` passed all five required jobs; merge into #6 is `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`. Both post-merge runs `41602459792` and `41602467771` passed all five required jobs on the exact integration head.
- The prior TSETMC owner-run report records 1,220 raw archives / 1,220 normalized histories / 1,677,202 history rows, plus 128 candidate series, 167,912 research-feature rows and 151,784 forward-label rows. All candidates remain research-only and fail-closed; the forward-label artifact reports zero distinct dates. Corporate-action and date-gap queues (48,902 and 48,059 rows) are candidate review queues, not verified evidence.
- The PR #14 integrated runner has not been run on the owner's 1,220-instrument corpus. An earlier separate diagnostic found only 47 instruments and quarantined all 47; compare exact code/root/discovery scope before any new local run.
- Nerkhsanj owner-reported audit: 182 adjacent changes >=20%, 48 >=100%, concentrated in IQD/silver/Tether; IQD gap up to 373 days and silver/Tether/Bitcoin up to 84 days. IQD/silver/Tether remain excluded; Bitcoin remains a coverage warning.
- Tindex unit families must remain separate: the official English and Persian developer pages rechecked 2026-11-04 publish 3 requests/minute and 300 requests/day per account, with one active token; HTTP 429 rejections do not consume the daily quota. MarketSage keeps the stricter local 1 request/minute and 100-success/day cap. The 100-day history cap and distinct Rial/Toman endpoint families still do not support a bulk 1,644-symbol six-month history crawl; configured-account access, units and rights remain unverified.
- Stage 4 still has no accepted representative, permissioned, point-in-time out-of-sample result. The previously recorded 240.89% six-month fold requires attribution; do not tune against the locked holdout.
- Binance Spot is now hard-blocked in the discovery runner after owner-reported Iran-network HTTP 451; default probes exclude it and explicit selection returns zero requests. No alternate host is used.
- Static Stage 4 review (2026-11-04): the backtest uses prior-month signals, next-month returns, L1 turnover costs and pre-holdout folds/locked holdout with equal-weight and cash baselines; six-month labels are inventory-only. The evaluator's complete monthly panel does not prove source rights, survivorship control, corporate-action correctness, point-in-time availability or executable liquidity. The existing fold-attribution script is ready but awaits the same pinned local dataset/config; it was not run.
- Owner approved the manual-only compensating-control model on 2026-11-04; this does not equal protected-branch enforcement. Runner remains unregistered/offline pending actual workflow inventory/review and final activation checks.
- PR #8 remains parked after GitHub-hosted TSETMC ConnectTimeout. PR #6 remains open and unmerged to `main`. PR #21, #22, #23 and #24 are merged; PR #24 exact-head run `41796133083` and post-merge PR run `41796506276` passed all five required jobs.

## Merged to main outside the integration PR

| PR | Target | Result |
|---|---|---|
| [#27](https://github.com/yarsalam/marketsage/pull/27) | `main` | Manual-only offline TSETMC dataset validator workflow; merged at `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`. All five required CI jobs passed on exact PR head `c60edd0f16244ab12e6602b9247e4174567f6081` in run `41833221157`. It does not register/start a Runner or execute the full PR #14 pipeline. |
| [#28](https://github.com/yarsalam/marketsage/pull/28) | #6 integration branch | Iran official CBI macro/transfer-FX/policy-rate and government bond-auction candidate screen; exact-head run `41846337902` passed all five jobs; merge `21552b719513d72f7fc10eff1efa11651c3d8530`; post-merge CI in progress |



## Local Runner activation gate

The owner selected the manual-only compensating-control model in Issue [#25](https://github.com/yarsalam/marketsage/issues/25) on 2026-11-04. This is not equivalent to GitHub private branch protection/ruleset enforcement; live branch metadata reports `main.protected=false`.

### GitHub workflow inventory and review — 2026-11-04

- On `main`, `.github/workflows/ci.yml` runs all jobs on `ubuntu-latest`; no existing general CI job targets self-hosted.
- The PR #8 TSETMC smoke workflow on the integration branch also uses `ubuntu-latest`; it remains parked after the GitHub-hosted ConnectTimeout. Do not repeat the same network request from that environment.
- PR #27 was statically reviewed and merged to `main` at `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`. Its workflow has only `workflow_dispatch`, default-branch/owner/explicit-confirmation gates, exact custom labels `marketsage-local,marketsage-research`, `contents: read`, full-SHA-pinned checkout, no secrets, provider probes or artifact upload, and a bounded standard-library validator. All five required jobs passed on exact PR head in run `41833221157`.
- PR #27 validates the staged dataset inventory and 8,801 SHA-256 entries; it does not yet execute the full PR #14 integrated TSETMC acceptance pipeline. That is a later, separately reviewed workload.
- The owner must review the exact current `main` SHA and workflow before the first dispatch. Merge of PR #27 does not register/start the Runner and does not authorize dispatch.

### Owner-host evidence — corrected from latest terminal output (2026-11-04)

- Account: `marketsage-runner`, UID 110/GID 119, home `/var/lib/marketsage-runner`, shell `nologin`; member only of its own group and not in `sudo`, `docker`, `lxd` or `adm`.
- Latest terminal output shows the full 228,071,396-byte v2.338.2 archive in `/home/nima/actions-runner`, with extracted files also present there. The extracted `config.sh`/`run.sh` timestamps are 2026-10-26, so their version/correspondence to the newer archive is not verified.
- `/opt/actions-runner/marketsage` currently contains only a 9,719,808-byte partial archive; extracted `config.sh` and `run.sh` are absent. The designated Runner installation is therefore incomplete. The personal directory also contains `.env`, `.path` and `_diag`; do not copy those into the dedicated Runner installation.
- No Runner process or installed/loaded Runner service was found in the latest terminal output. The Runner is not registered or online. The registration token previously pasted into chat must never be reused.
- Dataset staged at `/srv/marketsage/data/tsetmc_history_20261022`: 8,801 source files plus `SHA256SUMS` and `STAGING_README.txt`, 8,803 files total. Prior owner-reported checks verified all source hashes, read access and denied dataset writes; separate output-directory writes passed.
- These are owner-supplied terminal results, not an independent penetration test. They do not prove workflow safety, network-egress containment, kernel security or protection against arbitrary workflow code.

### Remaining owner gates

1. Verify the full local archive SHA-256 against the published digest and freshly extract it under `/opt/actions-runner/marketsage` as `marketsage-runner`; do not copy personal environment files or old diagnostics.
2. Apply service/workspace isolation, dedicated `_work`, cleanup and emergency disable/unregister procedure.
3. Run the final no-credentials/no-process host audit; register a repository-scoped Runner with a fresh locally entered token and custom labels `marketsage-local,marketsage-research`.
4. Owner reviews the exact current `main` workflow/commit and manually confirms the bounded offline dataset validator.
5. Review its sanitized result, then add/review a separate manual workflow for the full PR #14 offline pipeline. Do not conflate the validator with that pipeline.

No local job, source approval, backtest admission, investment scoring, production deployment, broker access or trading is authorized by this setup.

## Execution policy

Merge dependent PRs sequentially after all required jobs pass on the exact current head. Independent source screening, evidence review and methodology work may proceed in parallel. A blocked network smoke does not freeze unrelated work. Update this register and `PROJECT_STATE.md` after each material transition. CI green is not source acceptance, strategy validation or deployment authorization.
