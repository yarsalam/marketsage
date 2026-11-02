# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (Private)

## Open PRs

| PR | Base ← head | State | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open | Current head includes #7 and #9; clean/mergeable. Keep unmerged into main under owner boundary. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old fix branch ← `research/iran-free-data-smoke` | Open | Parked diagnostic; live TSETMC request timed out from GitHub-hosted runner. |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 branch ← `feature/free-dataset-discovery-acceptance` | Open | Current head `1398ca3369c8...`; fresh CI in progress after rebase. |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 branch ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Current head `9a6b5109c938...`; fresh CI in progress after rebase. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Draft | Governance; keeps branch enforcement and Runner controls explicit. |

## Merged PRs relevant to the integration chain

| PR | Merged into | Result |
|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` | Application baseline integrated; no deployment |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 feature branch | Tindex documented endpoints/history, FRED network diagnostics, tests, strict quota guard |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 feature branch | Iranian dashboard, candidate ingestion, research-only readiness and staging configuration |
| [#2](https://github.com/yarsalam/marketsage/pull/2) | deployment branch | Backtest baseline |
| [#3](https://github.com/yarsalam/marketsage/pull/3) | deployment branch | Iranian market data contracts |
| [#4](https://github.com/yarsalam/marketsage/pull/4) | deployment branch | Admin workspace CI and production-gate audit |
| [#5](https://github.com/yarsalam/marketsage/pull/5) | deployment branch | Point-in-time lineage |
| [#10](https://github.com/yarsalam/marketsage/pull/10) | dashboard branch | TSETMC adjustment investigation |
| [#11](https://github.com/yarsalam/marketsage/pull/11) | dashboard branch | StreamData audit |
| [#12](https://github.com/yarsalam/marketsage/pull/12) | dashboard branch | Tindex candle ingestion |

## Current integration graph

```text
main → #6 (open; deliberately not merged to main)
        ├─ #7 [merged]
        ├─ #9 [merged]
        ├─ #13 [open; CI]
        └─ #14 [open; CI]

#8 is a separate parked network smoke.
```

## Execution rule

Dependent PR merges are sequential, but independent data inventory, source evaluation, methodology work and separately scoped engineering may proceed in parallel. A blocked smoke probe does not freeze unrelated work.

After each PR transition, update this register and `PROJECT_STATE.md`. CI success is not data-source acceptance, investment approval or deployment approval.
