# MarketSage — Pull Request Register

## Live register override — 2026-11-09

Repository: `yarsalam/marketsage` (public). Default branch: `main`.  
Main HEAD at snapshot: `4c4b032196137af4658ea2c28e38a21605ee923b`.

| PR | Base | Head branch | Exact head | State | Handling |
|---|---|---|---|---|---|
| [#77](https://github.com/yarsalam/marketsage/pull/77) | main | safety/research-only-output-gates-2026-11 | `67356939f65224a580c915fd2caa0ea52d8d09a9` | Open, Draft; exact-head CI passed | Safety/UI work; not merged, deployed or user-flow accepted |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | main | infra/provider-neutral-control-plane-2026-11 | `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10` | Open, Draft | Provider-neutral infra foundation; independent track |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | main | research/market-coverage-workspace-2026-11 | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | Open, Draft; exact-head CI passed | Market coverage UI/API; not merged or user-flow accepted |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | infra/provider-neutral-control-plane-2026-11 | infra/durable-provider-dispatch-outbox-2026-11 | `e8785b177f93a569ce031496d1043026979828d3` | Open, Draft | Stacked; blocked on #74 integration |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | infra/provider-neutral-control-plane-2026-11 | docs/parallel-workstream-decomposition-2026-11 | `25ce24283e35dd7e55eb8545c590a047606643ee` | Open, Draft | Stacked; blocked on #74 integration |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | main | feat/tindex-free-data-connector | Existing integration head | Open | Do not merge without separate explicit owner approval |

Exact-head CI evidence recorded:
- PR #73: [run 42621965739](https://github.com/yarsalam/marketsage/actions/runs/42621965739) — passed on head `72c57608...`.
- PR #77: [run 42624038512](https://github.com/yarsalam/marketsage/actions/runs/42624038512) — passed on head `67356939...`.

Other open PRs must be reconciled from the live GitHub list before acting. PR #51, #41, #8 and #62 remain visible in GitHub; their current bases and intended dispositions must be verified before integration. Do not infer merge readiness from their existence.

**Integration constraints:** #73 and #77 both modify the user landing page and Sidebar. They must be reconciled into one coherent integration path; do not merge blindly. #71 and #61 depend on #74 and cannot be integrated first. Keep required approvals/rulesets intact. No PR is merged or deployed by this register update.

---

## Historical register (2026-11-05; superseded for live status)

**Snapshot date:** 2026-11-05  
**Repository:** yarsalam/marketsage (Private)  
**Main HEAD:** 554fe2200ccb3a523442b0e241e81a748becfa44  
**Integration PR:** [#6](https://github.com/yarsalam/marketsage/pull/6), feat/tindex-free-data-connector  
**Pinned integration code HEAD:** 819f8b4028469cb0d498098fec88545a18ebacc6

## Open PRs

| PR | Target | Scope / current state | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | main ← feat/tindex-free-data-connector | Integrated research/data-source work; pinned integration head 819f8b4028469cb0d498098fec88545a18ebacc6; required five-job CI passed on exact post-#30 head | Keep open. **Do not merge to main without explicit owner approval.** |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | research/iran-free-data-smoke | GitHub-hosted TSETMC live request timed out | Parked. Do not repeat the same request from the same environment. |



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
