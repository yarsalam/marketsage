# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (Private)

## Open PRs

| PR | Base ← head | State | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open | Clean; 5 CI job types passed; contains merged #7; remains unmerged into main under owner boundary |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old fix branch ← `research/iran-free-data-smoke` | Open | Parked diagnostic; TSETMC live request timed out from GitHub runner |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `feat/tindex-free-data-connector` ← `feature/iran-live-data-dashboard` | Open | Current head `1acbc172...`; core checks green; production-image jobs pending |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/iran-live-data-dashboard` ← `feature/free-dataset-discovery-acceptance` | Open | Current head `ae9a1072...`; core checks green; production-image jobs pending |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/iran-live-data-dashboard` ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Current head `6fdc2805...`; core checks green; production-image jobs pending |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Draft | Governance docs; pending final adoption and branch-enforcement plan |

## Merged PRs relevant to the integration chain

| PR | Merged into | Result |
|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` | Application baseline integrated; no deployment |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 feature branch | Tindex documented routes/history, safe FRED network errors, tests; retained 1/minute and 100/day quota guard |
| [#2](https://github.com/yarsalam/marketsage/pull/2) | deployment branch | Backtest baseline |
| [#3](https://github.com/yarsalam/marketsage/pull/3) | deployment branch | Iranian market data contracts |
| [#4](https://github.com/yarsalam/marketsage/pull/4) | deployment branch | Admin workspace CI and production-gate audit |
| [#5](https://github.com/yarsalam/marketsage/pull/5) | deployment branch | Point-in-time lineage |
| [#10](https://github.com/yarsalam/marketsage/pull/10) | dashboard branch | TSETMC adjustment investigation |
| [#11](https://github.com/yarsalam/marketsage/pull/11) | dashboard branch | StreamData audit |
| [#12](https://github.com/yarsalam/marketsage/pull/12) | dashboard branch | Tindex candle ingestion |

## Current integration order

```text
main → #6 (open; not yet merged to main)
        └─ #9 (pending production-image checks)
             ├─ #13 (pending production-image checks)
             └─ #14 (pending production-image checks)

#7 is already merged into #6.
#8 is a separate network smoke diagnostic and is parked.
```

## Execution rule

Keep dependent merges sequential. Independent data inventory, source evaluation, and research preparation may continue in parallel when their scope is isolated. A blocked smoke probe does not freeze unrelated work.

After each PR transition, update this register and `PROJECT_STATE.md`. CI success is not data-source acceptance, investment approval, or deployment approval.
