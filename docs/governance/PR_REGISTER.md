# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (Private)

## Open PRs

| PR | Base ← head | State | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open | Current branch includes #7, #9 and #13; image jobs running after #13 merge. Keep unmerged into main. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old fix branch ← `research/iran-free-data-smoke` | Open | Parked network diagnostic; TSETMC request timed out from GitHub-hosted runner. |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 branch ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Rebased after #13 merge; current head `4bd179263f55...`; fresh CI running. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Draft | Governance docs; includes parallel independent work policy. |

## Merged PRs relevant to the integration path

| PR | Merged into | Result |
|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` | Application baseline; no deployment |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 feature branch | Tindex and FRED fixes, tests and strict quota guard |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 feature branch | Iranian dashboard, read-only research endpoints and staging setup |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 feature branch | Free dataset discovery, source catalog and candidate audit tools |
| [#2](https://github.com/yarsalam/marketsage/pull/2) | deployment branch | Backtest baseline |
| [#3](https://github.com/yarsalam/marketsage/pull/3) | deployment branch | Iranian data contracts |
| [#4](https://github.com/yarsalam/marketsage/pull/4) | deployment branch | Admin CI and production gate |
| [#5](https://github.com/yarsalam/marketsage/pull/5) | deployment branch | Point-in-time lineage |
| [#10](https://github.com/yarsalam/marketsage/pull/10) | dashboard branch | TSETMC adjustment probe |
| [#11](https://github.com/yarsalam/marketsage/pull/11) | dashboard branch | StreamData audit |
| [#12](https://github.com/yarsalam/marketsage/pull/12) | dashboard branch | Tindex candle ingestion |

## Current integration graph

```text
main → #6 (open; not authorized to merge to main)
        ├─ #7 [merged]
        ├─ #9 [merged]
        ├─ #13 [merged]
        └─ #14 [open; fresh CI]
```

## Execution policy

Merge dependent PRs sequentially. Independent data inventory, source review and methodology work may proceed in parallel. A blocked network smoke does not freeze unrelated work. Update this register and `PROJECT_STATE.md` after each material transition. CI green is not source acceptance, strategy validation or deployment authorization.
