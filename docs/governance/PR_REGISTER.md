# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (Private)

This register reflects direct reads of GitHub PR metadata, branch refs and check-runs. CI success is not source acceptance or strategic approval.

## Open PRs

| PR | Base ← head | State | Current handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open | Retargeted to main; clean and 5 CI jobs passed; remains unmerged |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | `feat/tindex-free-data-connector` ← `fix/gdelt-fred-tindex-current-docs` | Open | **Blocked:** dirty/non-mergeable; reconcile branch divergence |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Open | Park: `tsetmc-smoke` failed; smoke is not data acceptance |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `fix/gdelt-fred-tindex-current-docs` ← `feature/iran-live-data-dashboard` | Open | After #7; clean, standard CI passed |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/iran-live-data-dashboard` ← `feature/free-dataset-discovery-acceptance` | Open | After #9; integrate sequentially with #14 |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/iran-live-data-dashboard` ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | After #9; update/revalidate after sibling integration |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Draft | Governance only; hold until final adoption |

## Merged PRs

| PR | Merged into | Title |
|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` | Integrate MarketSage application baseline into main (no deployment) |
| [#2](https://github.com/yarsalam/marketsage/pull/2) | `deploy/production-readiness` | Add leakage-aware research backtest baseline and data-contract tests |
| [#3](https://github.com/yarsalam/marketsage/pull/3) | `deploy/production-readiness` | Add quality-gated Iranian market data contracts |
| [#4](https://github.com/yarsalam/marketsage/pull/4) | `deploy/production-readiness` | Validate admin workspace and clarify production gates |
| [#5](https://github.com/yarsalam/marketsage/pull/5) | `deploy/production-readiness` | Add point-in-time data-lineage foundation |
| [#10](https://github.com/yarsalam/marketsage/pull/10) | `feature/iran-live-data-dashboard` | Validate TSETMC adjusted history for فولاد |
| [#11](https://github.com/yarsalam/marketsage/pull/11) | `feature/iran-live-data-dashboard` | Audit and normalize seller-provided StreamData CSV exports |
| [#12](https://github.com/yarsalam/marketsage/pull/12) | `feature/iran-live-data-dashboard` | Add Tindex historical candle ingestion |

## Integration sequence

```text
main → #6 → #7 → (#8, #9) → (#13, #14)
```

The PRs are stacked. Integrate one step at a time, update the next branch after each base change, and do not merge #8 while its smoke check fails. For #13/#14, merge one, update its sibling, and validate the new head.

## Rules

- CI green does not mean a source is accepted or that the investment strategy is validated.
- Do not merge dependent PRs in parallel.
- Do not close a PR until its useful commits are confirmed integrated or safely preserved.
- Do not begin new feature work until the current integration blocker is resolved.
- Update this register and `PROJECT_STATE.md` after each PR transition.
