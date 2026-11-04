# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-04  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Integration target:** PR #6 branch `feat/tindex-free-data-connector`
**Current integration HEAD:** `e19d65840d9112362209a23ea53c7fcf608c0720`
**Post-#24 CI:** PR run `41796506276` passed all five required job types on exact head `e19d65840d9112362209a23ea53c7fcf608c0720`; PR #24 exact-head run `41796133083` passed all five jobs before merge.

## Open PRs

| PR | Base ← head | Current head / CI | State and handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | `e19d65840d9112362209a23ea53c7fcf608c0720`; post-#24 PR run `41796506276` passed all five required jobs | Open; do not merge to `main` without explicit owner approval. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Live TSETMC request timed out from GitHub-hosted runner | Open; parked. Do not repeat the same network request from that environment. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Owner-approved manual-only Runner exception, completed dataset staging/hash verification and host permissions evidence added 2026-11-04 | Open; Draft; no merge/adoption transition made. |


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

## Local Runner activation gate

The owner selected the manual-only compensating-control model in Issue #25 on 2026-11-04. The decision and accepted residual risk are recorded in `docs/governance/DECISION_LOG.md` and `docs/governance/LOCAL_RUNNER_TRUST_BOUNDARY.md`. This does not provide or claim GitHub private branch protection/ruleset enforcement.

### Owner-host preparation and test evidence — 2026-11-04

- Account: `marketsage-runner`, UID 110/GID 119, home `/var/lib/marketsage-runner`, shell `nologin`; member only of its own group and not in `sudo`, `docker`, `lxd` or `adm`.
- Runner version 2.338.2 is installed under `/opt/actions-runner/marketsage`. No `.runner`, `.credentials` or `.credentials_rsaparams` markers, active Runner process, or installed/loaded service were found. It is not registered or online.
- Any registration token previously pasted into chat is compromised and must never be reused. A fresh token must be entered locally only, after the workflow gate is satisfied.
- Dataset staged at `/srv/marketsage/data/tsetmc_history_20261022`: 8,801 source files plus `SHA256SUMS` and `STAGING_README.txt`, 8,803 files total. Every source file hash was verified; adjusted research-only candidates were excluded and source files were not modified.
- Dataset group is `marketsage-runner`; files are `0440`, directories `2750`. Runner read/hash/JSON/CSV checks passed on representative raw, normalized, reports, pipeline metadata, discovery, reconciliation and acceptance files. Writes to the dataset were denied. Separate `/srv/marketsage/output` write/create/delete test passed.
- The general `/home/nima` tree is not traversable by the Runner account. No access to browser, SSH, credentials, Docker or personal project files has been granted.
- These results are owner-supplied terminal outputs; they verify tested filesystem permissions, not workflow safety, network egress policy, kernel security or arbitrary-code containment.
- Local Runner remains unregistered/offline. No workflow has been changed to `self-hosted`.

### Remaining gates

1. Inventory and inspect the exact current workflow files and every trigger, runner target, permission, action SHA, checkout ref and secret reference.
2. Add a separate manual-only `workflow_dispatch` workflow; keep all normal CI on GitHub-hosted runners.
3. Review exact workflow content and commit before each dispatch; use read-only token permission, no secrets, fixed trusted ref/SHA validation, serialization and sanitized output only.
4. Verify workspace cleanup, service isolation and emergency disable/unregister instructions.
5. Perform a final no-credentials/no-process host check, then repository-scope registration with a fresh locally entered token.

No local job, data scoring, backtest admission, production deployment, broker access or trading is authorized by this setup.

## Execution policy

Merge dependent PRs sequentially after all required jobs pass on the exact current head. Independent source screening, evidence review and methodology work may proceed in parallel. A blocked network smoke does not freeze unrelated work. Update this register and `PROJECT_STATE.md` after each material transition. CI green is not source acceptance, strategy validation or deployment authorization.
