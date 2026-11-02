# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (Private)

This register reflects a direct read of PR metadata, branch refs and check-runs. A green CI result is not source acceptance or strategic approval.

## Open PRs

| PR | Base ← head | State | Current handling |
|---|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` ← `deploy/production-readiness` | Draft | Root code-baseline PR; review merge separately from production deployment |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `deploy/production-readiness` ← `feat/tindex-free-data-connector` | Open | Next after #1; clean, 5 CI jobs passed |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | `feat/tindex-free-data-connector` ← `fix/gdelt-fred-tindex-current-docs` | Open | **Blocked:** GitHub reports dirty/non-mergeable; update/reconcile branch first |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Open | Park: `tsetmc-smoke` check failed; do not treat smoke as acceptance |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `fix/gdelt-fred-tindex-current-docs` ← `feature/iran-live-data-dashboard` | Open | After #7; clean and standard CI passed |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/iran-live-data-dashboard` ← `feature/free-dataset-discovery-acceptance` | Open | After #9; merge sequentially with #14 |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/iran-live-data-dashboard` ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | After #9; update/revalidate after sibling integration |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Draft | Governance only; currently not ready to merge |

## Merged PRs

| PR | Merged into | Title |
|---|---|---|
| [#2](https://github.com/yarsalam/marketsage/pull/2) | `deploy/production-readiness` | Add leakage-aware research backtest baseline and data-contract tests |
| [#3](https://github.com/yarsalam/marketsage/pull/3) | `deploy/production-readiness` | Add quality-gated Iranian market data contracts |
| [#4](https://github.com/yarsalam/marketsage/pull/4) | `deploy/production-readiness` | Validate admin workspace and clarify production gates |
| [#5](https://github.com/yarsalam/marketsage/pull/5) | `deploy/production-readiness` | Add point-in-time data-lineage foundation |
| [#10](https://github.com/yarsalam/marketsage/pull/10) | `feature/iran-live-data-dashboard` | Validate TSETMC adjusted history for فولاد |
| [#11](https://github.com/yarsalam/marketsage/pull/11) | `feature/iran-live-data-dashboard` | Audit and normalize seller-provided StreamData CSV exports |
| [#12](https://github.com/yarsalam/marketsage/pull/12) | `feature/iran-live-data-dashboard` | Add Tindex historical candle ingestion |

## Branch/dependency map

```text
main → #1 → #6 → #7 → (#8, #9) → (#13, #14)
```

PRs are stacked. Keep one integration step active at a time. For #13/#14, merge one, update the sibling against the resulting base, and run the relevant CI once. Do not merge #8 until its failed smoke result is understood.

## Operating rules

- A PR is not accepted merely because its CI is green or it was merged.
- Do not merge several dependent PRs in parallel.
- Do not close a PR until its useful commits are confirmed integrated or safely preserved.
- Do not use `main` for new product work until the root baseline PR (#1) has been reviewed and integrated.
- Update this register and `PROJECT_STATE.md` after every PR state transition.
