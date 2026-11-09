# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-09  
**Repository:** yarsalam/marketsage (Public; revalidated through GitHub repository metadata)  
**Main HEAD:** 4c4b032196137af4658ea2c28e38a21605ee923b  
**Integration PR:** [#6](https://github.com/yarsalam/marketsage/pull/6), feat/tindex-free-data-connector  
**Pinned integration code HEAD:** 819f8b4028469cb0d498098fec88545a18ebacc6

## Open PRs

| PR | Target | Scope / current state | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | main ← feat/tindex-free-data-connector | Integrated research/data-source work; pinned integration head 819f8b4028469cb0d498098fec88545a18ebacc6; required five-job CI passed on exact post-#30 head | Keep open. **Do not merge to main without explicit owner approval.** |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | research/iran-free-data-smoke | GitHub-hosted TSETMC live request timed out | Parked. Do not repeat the same request from the same environment. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | infra/durable-provider-dispatch-outbox-2026-11 | Durable outbox, coordinator, sandbox worker and watchdog; Draft, open. Latest one-off local dataset acceptance #42482678959 succeeded, but 24/7/independent-host acceptance remains unproven. | Parked and non-blocking. No Runner dispatch, paid host or merge without separate approval. |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | main ← infra/provider-neutral-control-plane-2026-11 | Provider-neutral CI/control-plane foundation; Draft and open. Current patch intentionally blocks product CI during a previous infrastructure-first freeze. | Parked. Do not merge unchanged; product CI must remain enabled. |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | main ← research/market-coverage-workspace-2026-11 | Market Coverage, canonical instrument registry, series mapping, instrument-specific freshness and typed temporal price snapshots; snapshot serialization added after exact-head CI for `ffd4f279...` and is being revalidated. | Active product PR; awaits exact-head CI and owner review. Not merged or deployed. |



## Active product issues

- [Issue #75](https://github.com/yarsalam/marketsage/issues/75) — Canonical instrument and market-universe registry; implementation is included in PR #73 and awaits PR acceptance.
- [Issue #72](https://github.com/yarsalam/marketsage/issues/72) — Product Phase 1: evidence-first Market Coverage Workspace. Its implementation is tracked in Draft PR #73.

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

PR #6 remains open and must not be merged to main without explicit owner approval. PR #8 remains parked. PRs #71 and #74 remain Draft and unmerged; #74 must not be merged unchanged because it blocks product CI. PR #73 is the active product PR; exact-head push and PR CI both passed, and it awaits review/acceptance.

## Release and capital-risk guardrails

- No data source currently passes the complete acceptance gate for investment scoring.
- Stage 4 remains exploratory; the 2023-10-31 through 2024-03-31 fold reporting +240.89% requires asset-level attribution from the exact original input dataset.
- Do not inspect or tune against the locked final holdout.
- A local Runner/checksum/workflow success does not approve a source, backtest, ranking, probability or investment recommendation.
- No production scoring, broker access, portfolio allocation or real-money trade is authorized. Any capital-risk action requires separate explicit owner approval.
