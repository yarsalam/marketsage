# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-03  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Integration target:** PR #6 branch `feat/tindex-free-data-connector`
**Current integration HEAD:** `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`
**Post-#22 CI:** push run `41602459792` is queued on exact head `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`.

## Open PRs

| PR | Base ← head | Current head / CI | State and handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`; post-#22 push run `41602459792` queued | Open; do not merge to `main` without explicit owner approval. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Live TSETMC request timed out from GitHub-hosted runner | Open; parked. Do not repeat the same network request from that environment. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Governance docs refreshed through PR #22 merge; PR remains Draft | Open; Draft; no merge/adoption transition made in this execution. |


## Merged PRs relevant to the integration path

| PR | Merged into | Result |
|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` | Application baseline; no deployment |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 feature branch | Conservative Tindex quota, documented route/history updates, FRED safe diagnostics and tests |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 feature branch | Iranian market dashboard, read-only research endpoints and staging configuration |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 feature branch | Free-dataset discovery, catalog and candidate audit/ingestion tools |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 feature branch | Integrated offline TSETMC acceptance pipeline; exact-head run `41401668921` passed all five required job types; merge `f267c49efcbf72e7ddc17099ff93f38ade269a7b` |
| [#16](https://github.com/yarsalam/marketsage/pull/16) | #6 feature branch | Source-evidence reconciliation; merge `77d25986627664b6482e515fbd4bd9791a041797` |
| [#17](https://github.com/yarsalam/marketsage/pull/17) | #6 feature branch | Stage 4 cost-sensitivity scenario correction; merge `c821f6423ee5734590b4852eb5fab307834f0b51` |
| [#18](https://github.com/yarsalam/marketsage/pull/18) | #6 feature branch | Monthly calendar continuity gate; exact-head CI passed all five required job types; merge `d468d06eb0fb4adcc90f04be38a61f4f1164ad57` |
| [#19](https://github.com/yarsalam/marketsage/pull/19) | #6 feature branch | Source-evidence reconciliation; merge `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b` |
| [#20](https://github.com/yarsalam/marketsage/pull/20) | #6 feature branch | TSETMC v2 identity crosswalk, ambiguity quarantine and SHA-256 provenance; all five exact-head jobs passed; merge `4191dd3715173265193163e30281ab555b9d12fb` |
| [#21](https://github.com/yarsalam/marketsage/pull/21) | #6 feature branch | Tindex quota-report consistency correction; all five exact-head jobs passed; merge `21c591223c9e7d61e6046a06f51522e979530f08` |
| [#22](https://github.com/yarsalam/marketsage/pull/22) | #6 feature branch | Five official global source candidates; all five required exact-head jobs passed in PR and push runs; merge `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f` |

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
       └─ #22 [merged]

#8  [open; parked network diagnostic]
#15 [open; Draft governance]
```

## Independent evidence notes — 2026-11-03

- PR #19 is merged into #6 at `2fea1c2e8f73fe3b7768f4f2e0d3da36ce27248b`; its exact-head run passed all five job types. It updates the source catalog and acceptance matrix using committed docs and previously shared sanitized summaries only. No network request or local raw-file audit was performed.
- PR #20 addressed a static discovery limitation: the integrated runner now reads the preferred v2 `instrument_details.jsonl` crosswalk for candidate identity, never combines v1/v2, hashes the file and keeps identity evidence/research/scoring fail-closed. All five required exact-head CI jobs passed on `c58cde2c87c698ec4a33a58ff2d3caeeecd70569`; merge into #6 is `4191dd3715173265193163e30281ab555b9d12fb`.
- PR #21 corrected stale discovery-script wording that referred to three requests/minute despite the connector's 1 request/minute and 100 successful requests/day guard. All five exact-head jobs passed; merge into #6 is `21c591223c9e7d61e6046a06f51522e979530f08`. No provider request was made.
- PR #22 screened five official global candidates: ECB Data Portal (SDMX history/update metadata and reuse terms), US Treasury XML (daily yield history/pagination), EIA API v2 (key/ToS/public-domain and third-party distinction), SEC EDGAR (no key, 10 req/s, declared User-Agent, acceptance vs availability and corrections), and IMF SDMX (beta account for Swagger; endpoint auth/vintage/rights unresolved). It adds source-specific acceptance contracts and tests that all five candidates remain fail-closed. No live data API was contacted. Both exact-head PR run `41602083315` and push run `41602045431` passed all five required jobs; merge into #6 is `b3fd6af1b40a3d9693feade7f9ad820bd3cfa69f`. Post-merge run `41602459792` is queued.
- The prior TSETMC owner-run report records 1,220 raw archives / 1,220 normalized histories / 1,677,202 history rows, plus 128 candidate series, 167,912 research-feature rows and 151,784 forward-label rows. All candidates remain research-only and fail-closed; the forward-label artifact reports zero distinct dates. Corporate-action and date-gap queues (48,902 and 48,059 rows) are candidate review queues, not verified evidence.
- The PR #14 integrated runner has not been run on the owner's 1,220-instrument corpus. An earlier separate diagnostic found only 47 instruments and quarantined all 47; compare exact code/root/discovery scope before any new local run.
- Nerkhsanj owner-reported audit: 182 adjacent changes >=20%, 48 >=100%, concentrated in IQD/silver/Tether; IQD gap up to 373 days and silver/Tether/Bitcoin up to 84 days. IQD/silver/Tether remain excluded; Bitcoin remains a coverage warning.
- Tindex unit families must remain separate: previously reviewed public docs described TSE stock endpoints in Rial and other Markets & Indicators values in Toman since 2026-07-20. The 100-day history cap and 1/minute + 100-success/day account quota do not support a bulk 1,644-symbol six-month history crawl; configured-account access remains unverified.
- Stage 4 still has no accepted representative, permissioned, point-in-time out-of-sample result. The previously recorded 240.89% six-month fold requires attribution; do not tune against the locked holdout.
- No Runner is registered; branch protection/rulesets cannot be configured through the connected GitHub integration in the current account.
- PR #8 remains parked after GitHub-hosted TSETMC ConnectTimeout. PR #6 remains open and unmerged to `main`; post-#21 runs `41601942608` and `41601948914` both passed all five required jobs. PR #21 and PR #22 are merged; post-#22 run `41602459792` is queued.

## Local Runner activation gate

The least-privilege trust boundary is specified in `docs/governance/LOCAL_RUNNER_TRUST_BOUNDARY.md`. No Runner is registered. Owner-side branch protection/ruleset, dedicated unprivileged account, restricted data/output directories and repository-scoped ephemeral Runner registration are required before local data execution.

## Execution policy

Merge dependent PRs sequentially after all required jobs pass on the exact current head. Independent source screening, evidence review and methodology work may proceed in parallel. A blocked network smoke does not freeze unrelated work. Update this register and `PROJECT_STATE.md` after each material transition. CI green is not source acceptance, strategy validation or deployment authorization.
