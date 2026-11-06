# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-06  
**Repository:** yarsalam/marketsage (Private)  
**Main HEAD:** 07e641670ceab22496ef976a584934464570fd9a  
**Integration PR:** [#6](https://github.com/yarsalam/marketsage/pull/6), feat/tindex-free-data-connector  
**Pinned integration code HEAD:** 1d90726c593b0818982407c309ff13301798f5b3 (current PR #6 head; main local workflow remains pinned to 819f8b4028469cb0d498098fec88545a18ebacc6 until PR #41 is adopted)

## Open PRs

| PR | Target | Scope / current state | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | main ← feat/tindex-free-data-connector | Integrated research/data-source work; pinned integration head 819f8b4028469cb0d498098fec88545a18ebacc6; required five-job CI passed on exact post-#30 head | Keep open. **Do not merge to main without explicit owner approval.** |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | research/iran-free-data-smoke | GitHub-hosted TSETMC live request timed out | Parked. Do not repeat the same request from the same environment. |\n| [#41](https://github.com/yarsalam/marketsage/pull/41) | main | Governance/evidence synchronization and corrected local workflow pin; exact-head run 42063679856 passed all five jobs | Open; no local dispatch; keep pending review during infrastructure-first priority. |\n| [#50](https://github.com/yarsalam/marketsage/pull/50) | main | CI timeouts/concurrency/schedule/failure reporter; exact head 9098f110... failed before steps with runner ID 0 in run 42176190919 | Open; do not merge; no further hosted runs while Actions budget is USD 0. |\n| [#51](https://github.com/yarsalam/marketsage/pull/51) | integration #6 | Iran property/automobile candidate screen; exact-head run 42062133299 passed five jobs | Open; ordinary data work paused under Issue #49; do not merge/extend in this phase. |



## Merged to main

| PR | Result |
|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | Application baseline; no production deployment |
| [#27](https://github.com/yarsalam/marketsage/pull/27) | Manual-only staged TSETMC inventory/checksum validator; merged at 7e669749d2615bc0f2a9d6f557bb99f8e7bd0767 |
| [#31](https://github.com/yarsalam/marketsage/pull/31) | Clean adoption of the five governance documents; merged at 46d3a541b7fa176b5a8c5693a0c46feb8bb9b3fc |
| [#32](https://github.com/yarsalam/marketsage/pull/32) | Manual-only integrated TSETMC candidate workflow; merged at 11f9de85c13f3ee8bd61e6eb7aea64992a7271d4. Exact PR head 2df9e5fc523307a08894c8077210e8584aa4adcb passed all five jobs in run 41911051358. Awaiting owner manual dispatch. |
| [#34](https://github.com/yarsalam/marketsage/pull/34) | Memory-bounded/cgroup-aware TSETMC execution; merged at 554fe2200ccb3a523442b0e241e81a748becfa44. Exact PR head dcf32f46b524daf3ac63e9937962cd02948ca2f8 passed all five required jobs in run 41913385729; analysis reported 109 passed, 7 warnings. Owner re-dispatch pending. |

## Merged into integration PR #6

PRs #7, #9, #13, #14, #16, #17, #18, #19, #20, #21, #22, #23, #24, #28, #29 and #30 are merged into the integration branch in dependency order. Exact-head and post-merge CI results are recorded in their PRs. They do not constitute data-source approval or strategy acceptance.

- [#14](https://github.com/yarsalam/marketsage/pull/14) — integrated offline TSETMC candidate-acceptance pipeline; code is pinned for local execution at 819f8b4028469cb0d498098fec88545a18ebacc6.
- [#20](https://github.com/yarsalam/marketsage/pull/20) — v2 TSETMC identity crosswalk and ambiguity quarantine.
- [#22](https://github.com/yarsalam/marketsage/pull/22) — official global source candidates (ECB, Treasury, EIA, SEC, IMF).
- [#23](https://github.com/yarsalam/marketsage/pull/23) — Tindex quota evidence reconciliation while retaining the stricter local guard.
- [#24](https://github.com/yarsalam/marketsage/pull/24) — Binance Spot HTTP 451 hard block.
- [#28](https://github.com/yarsalam/marketsage/pull/28) — Iran official macro/transfer-FX/policy-rate/bond-auction candidate screen.
- [#29](https://github.com/yarsalam/marketsage/pull/29) — World Bank Pink Sheet benchmark candidate.
- [#30](https://github.com/yarsalam/marketsage/pull/30) — Stage 4 downside/tail-risk and portfolio-mechanics diagnostics.

## Closed / superseded

| PR | Result |
|---|---|
| [#15](https://github.com/yarsalam/marketsage/pull/15) | Closed as superseded; its divergent branch was not merged. Its five governance documents were adopted through clean PR #31. |
| [#26](https://github.com/yarsalam/marketsage/pull/26) | Closed as duplicate/superseded documentation branch. |

## Current integration graph

main
- #27 merged: local staged-dataset validator
- #31 merged: governance adoption
- #32 merged: integrated local TSETMC candidate workflow
- #34 merged: memory-bounded/cgroup-aware candidate batches; owner re-dispatch pending; checks out immutable PR #6 integration commit 819f8b4028469cb0d498098fec88545a18ebacc6

PR #6 remains open and must not be merged to main without explicit owner approval. PR #8 remains parked.

## Release and capital-risk guardrails

- No data source currently passes the complete acceptance gate for investment scoring.
- Stage 4 remains exploratory; the 2023-10-31 through 2024-03-31 fold reporting +240.89% requires asset-level attribution from the exact original input dataset.
- Do not inspect or tune against the locked final holdout.
- A local Runner/checksum/workflow success does not approve a source, backtest, ranking, probability or investment recommendation.
- No production scoring, broker access, portfolio allocation or real-money trade is authorized. Any capital-risk action requires separate explicit owner approval.


## Infrastructure-first status — 2026-11-06

- Priority issue: [#49](https://github.com/yarsalam/marketsage/issues/49). Ordinary MarketSage product/data/research work is paused until the provider-independent execution system is proven.
- Current main: `07e641670ceab22496ef976a584934464570fd9a`. Current integration PR #6 head: `1d90726c593b0818982407c309ff13301798f5b3`. PR #14 is already merged into #6; PR #6 remains open and must not be merged to main without explicit owner approval.
- PR #50 exact head `9098f110f615d46adbfa49f37e644000b832feb0` has no valid CI result: run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919) and its bounded rerun failed before steps with runner ID 0. GitHub Actions usage/budget is at USD 0; no further hosted dispatch is permitted until quota reset is verified or separately authorized.
- PR #41 exact-head run [42063679856](https://github.com/yarsalam/marketsage/actions/runs/42063679856) passed all five jobs but remains open; it updates the main workflow pin and evidence/governance records. No local dispatch occurred.
- PR #51 exact-head run [42062133299](https://github.com/yarsalam/marketsage/actions/runs/42062133299) passed all five jobs but remains open; it is non-infrastructure data work and is paused.
- PR #48 merged into #6 at `1d90726c593b0818982407c309ff13301798f5b3`; the Stage 4 provenance change does not substitute for rerunning the exact local dataset.
- Active infrastructure branch: `infra/provider-neutral-control-plane-2026-11`; it is 26 commits ahead of main before this update. Its current work includes architecture/provider evaluation, task manifest/schema, in-memory lifecycle fixtures, runbook and mirror probe. No PR or CI run has been opened for it; the branch is intentionally outside the current hosted-CI push filters while the Actions budget is blocked.
- The local manifest/lifecycle tests have not run from a clean checkout because dependency bootstrap stopped before test discovery. Six new offline tests for the mirror probe passed in an isolated temporary harness only; actual owner-network reachability remains unverified.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) records the exact owner action to run the bounded HTTPS-only mirror probe on the actual worker network and return its sanitized output/exit code.
- No paid provider, Oracle workaround, private-code transfer, merge, deployment, investment scoring, backtest approval or trading is authorized.

**Infrastructure readiness:** NOT PROVEN. Do not label the system 24/7-ready until durable queue/outbox, leases/heartbeats/fencing, dispatch reconciliation, worker-loss recovery, provider failover without duplicate side effects, budget stops, observable health/stuck-run detection and a clean end-to-end canary are demonstrated.
