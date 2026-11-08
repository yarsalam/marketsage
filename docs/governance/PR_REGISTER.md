# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-05  
**Repository:** yarsalam/marketsage (Private)  
**Main HEAD at last inspection:** 07e641670ceab22496ef976a584934464570fd9a (after PR #38 merged)  
**Integration PR:** [#6](https://github.com/yarsalam/marketsage/pull/6), feat/tindex-free-data-connector  
**Pinned TSETMC pipeline implementation:** 1dc6894c0823f6ffe77d27fd866576f5115a042c (v1.1.1)  
**Integration branch HEAD:** 1d90726c593b0818982407c309ff13301798f5b3 (PR #48 merged; post-merge CI run 42061367000 in progress)

## Open PRs

| PR | Target | Scope / current state | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | main ← feat/tindex-free-data-connector | Diverged integration branch, 415 commits ahead / 10 behind main at latest comparison; offline pipeline execution pin is v1.1.1 commit `1dc6894c0823f6ffe77d27fd866576f5115a042c` | Keep open. **Do not merge to main without explicit owner approval.** |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | research/iran-free-data-smoke | GitHub-hosted TSETMC live request timed out | Parked. Do not repeat the same request from the same environment. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | main | Governance/state sync and corrected manual workflow pin to TSETMC pipeline v1.1.1 commit `1dc6894c0823f6ffe77d27fd866576f5115a042c` | Open. Exact-head CI must pass before merge; this PR does not dispatch the local workflow. |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | feat/tindex-free-data-connector (PR #6 integration branch) | Documentation-only screen of Iran property/auto sources; adds CBI CPI, historical housing-report and CODAL automaker-operation candidate entries, all fail-closed | Open. Exact-head five-job CI pending; no provider request, adapter, price-series approval or scoring. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | main | Governance/state sync and correction of the manual local workflow's immutable pipeline pin to v1.1.1 `1dc6894c0823f6ffe77d27fd866576f5115a042c` | Open. Run 42055777260 passed all five jobs on the preceding head; this new state-sync update requires fresh exact-head CI. No dispatch is performed. |




## Merged to main

| PR | Result |
|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | Application baseline; no production deployment |
| [#27](https://github.com/yarsalam/marketsage/pull/27) | Manual-only staged TSETMC inventory/checksum validator; merged at 7e669749d2615bc0f2a9d6f557bb99f8e7bd0767 |
| [#31](https://github.com/yarsalam/marketsage/pull/31) | Clean adoption of the five governance documents; merged at 46d3a541b7fa176b5a8c5693a0c46feb8bb9b3fc |
| [#32](https://github.com/yarsalam/marketsage/pull/32) | Manual-only integrated TSETMC candidate workflow; merged at 11f9de85c13f3ee8bd61e6eb7aea64992a7271d4. Exact PR head 2df9e5fc523307a08894c8077210e8584aa4adcb passed all five jobs in run 41911051358. Awaiting owner manual dispatch. |
| [#34](https://github.com/yarsalam/marketsage/pull/34) | Memory-bounded/cgroup-aware TSETMC execution; merged at 554fe2200ccb3a523442b0e241e81a748becfa44. Exact PR head dcf32f46b524daf3ac63e9937962cd02948ca2f8 passed all five required jobs in run 41913385729; analysis reported 109 passed, 7 warnings. |
| [#35](https://github.com/yarsalam/marketsage/pull/35) | Governance sync after the memory-bounded Runner correction; merged to main. |
| [#36](https://github.com/yarsalam/marketsage/pull/36) | Sanitized record of local run 41914919555; merged to main. |
| [#37](https://github.com/yarsalam/marketsage/pull/37) | TSETMC evidence-remediation plan; merged to main. |
| [#38](https://github.com/yarsalam/marketsage/pull/38) | Sanitized read-only local TSETMC input-inventory diagnostics; merged at `07e641670ceab22496ef976a584934464570fd9a` after all five required CI job types passed in run `42031417400`. Manual-only; not dispatched. |

## Merged into integration PR #6

PRs #7, #9, #13, #14, #16, #17, #18, #19, #20, #21, #22, #23, #24, #28, #29, #30 and #39 are merged into the integration branch in dependency order. Exact-head and post-merge CI results are recorded in their PRs. They do not constitute data-source approval or strategy acceptance.

- [#14](https://github.com/yarsalam/marketsage/pull/14) — integrated offline TSETMC candidate-acceptance pipeline; original implementation was pinned at 819f8b4028469cb0d498098fec88545a18ebacc6; PR #39's classification correction at `1dc6894c0823f6ffe77d27fd866576f5115a042c` is the current v1.1.1 execution pin proposed by PR #41.
- [#20](https://github.com/yarsalam/marketsage/pull/20) — v2 TSETMC identity crosswalk and ambiguity quarantine.
- [#22](https://github.com/yarsalam/marketsage/pull/22) — official global source candidates (ECB, Treasury, EIA, SEC, IMF).
- [#23](https://github.com/yarsalam/marketsage/pull/23) — Tindex quota evidence reconciliation while retaining the stricter local guard.
- [#24](https://github.com/yarsalam/marketsage/pull/24) — Binance Spot HTTP 451 hard block.
- [#28](https://github.com/yarsalam/marketsage/pull/28) — Iran official macro/transfer-FX/policy-rate/bond-auction candidate screen.
- [#29](https://github.com/yarsalam/marketsage/pull/29) — World Bank Pink Sheet benchmark candidate.
- [#30](https://github.com/yarsalam/marketsage/pull/30) — Stage 4 downside/tail-risk and portfolio-mechanics diagnostics.
- [#39](https://github.com/yarsalam/marketsage/pull/39) — TSETMC discovery identity-conflict classification fix; merged at `1dc6894c0823f6ffe77d27fd866576f5115a042c` after all five required job types passed in run `42050542208`.
- [#48](https://github.com/yarsalam/marketsage/pull/48) — Stage 4 exact Git/worktree provenance and report/input hash sidecar; merged at `1d90726c593b0818982407c309ff13301798f5b3` after corrected exact-head CI passed all five required job types in run `42060466294`; post-merge CI run `42061367000` is in progress. Source provenance remains unverified.
- [#43](https://github.com/yarsalam/marketsage/pull/43) — World Bank Pink Sheet November 2026 PDF release/units/revision/rights refresh; merged into integration after all five required job types passed in run `42051901501`.
- [#45](https://github.com/yarsalam/marketsage/pull/45) — TSETMC official REST-service candidate screen, with the November Pink Sheet record preserved; merged at `cbe585efe26ee129370b39e6bd983e709aecf55c` after all five required job types passed in run `42055449340`.
- [#46](https://github.com/yarsalam/marketsage/pull/46) — FIPIRAN fund NAV, IFB secondary fixed-income and commercial Investats candidate screen; merged at `0857a48ad9db6c5dab13ae0eca95354639d47324` after all five required job types passed in run `42056363087`.

## Closed / superseded

| PR | Result |
|---|---|
| [#15](https://github.com/yarsalam/marketsage/pull/15) | Closed as superseded; its divergent branch was not merged. Its five governance documents were adopted through clean PR #31. |
| [#26](https://github.com/yarsalam/marketsage/pull/26) | Closed as duplicate/superseded documentation branch. |
| [#42](https://github.com/yarsalam/marketsage/pull/42) | Closed as stale-base duplicate; the same World Bank source refresh was reapplied to the updated integration head in PR #43. |
| [#44](https://github.com/yarsalam/marketsage/pull/44) | Closed as stale-base TSETMC REST candidate PR; the same changes were reapplied on the updated integration head in PR #45. |

## Current integration graph

main
- #27 merged: local staged-dataset validator
- #31 merged: governance adoption
- #32 merged: integrated local TSETMC candidate workflow
- #34 merged: memory-bounded/cgroup-aware candidate batches
- #38 merged: read-only aggregate diagnostics of existing local TSETMC input inventories; manual-only and not dispatched

PR #39 merged into PR #6's integration branch at `1dc6894c0823f6ffe77d27fd866576f5115a042c` after five required job types passed in run `42050542208`. The first local candidate run (41914919555) used the previous v1.1.0 pipeline; the corrected v1.1.1 implementation changes classification only. PR #41 updates main's manual workflow pin to the corrected commit and requires owner review before a future dispatch.

PR #43 (World Bank Pink Sheet refresh), PR #45 (TSETMC official REST-service candidate screen), PR #46 (FIPIRAN/IFB/Investats candidate screen) and PR #48 (Stage 4 run-manifest provenance) are merged into the integration branch. PR #44 is closed as superseded by #45. PR #51 (Iran property/auto candidate screen) is open; PR #41 (this governance/pin update) remains open; PR #38 is merged to main. PR #6 remains open, 414 commits ahead and 10 behind main at the latest comparison, and must not be merged to main without explicit owner approval. PR #8 remains parked. The latest local candidate run completed, but 47/47 candidates remain quarantined. Owner evidence actions are tracked in [Issue #40](https://github.com/yarsalam/marketsage/issues/40).

## Release and capital-risk guardrails

- No data source currently passes the complete acceptance gate for investment scoring.
- Stage 4 remains exploratory; the 2023-10-31 through 2024-03-31 fold reporting +240.89% requires asset-level attribution from the exact original input dataset.
- The exact-hash attribution of that +240.89% fold requires the owner's local original CSV; the action, command, hash and acceptance criteria are tracked in [Issue #47](https://github.com/yarsalam/marketsage/issues/47). Do not reconstruct or substitute the dataset.
- PR #48 is merged into integration at `1d90726c593b0818982407c309ff13301798f5b3`; the corrected exact-head CI passed all five required job types in run `42060466294`. The historical Stage 4 report still requires a new run using the exact original CSV and matching hash; no replacement dataset is acceptable.
- Do not inspect or tune against the locked final holdout.
- The local run 41914919555 completed candidate-only using pipeline v1.1.0: 47 quarantined, 0 research-eligible, 0 input-file read errors and 7 discovery identity conflicts. PR #39 merged the v1.1.1 classification correction into integration; the historical run itself is unchanged and no candidates were promoted.
- A local Runner/checksum/workflow success does not approve a source, backtest, ranking, probability or investment recommendation.
- No production scoring, broker access, portfolio allocation or real-money trade is authorized. Any capital-risk action requires separate explicit owner approval.
