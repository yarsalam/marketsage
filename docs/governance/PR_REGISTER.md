# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-02  
**Source:** GitHub repository `yarsalam/marketsage` recent-PR listing.

This register prevents parallel, forgotten, or duplicated implementation paths. Update it whenever a PR changes state. A PR is not considered strategically accepted merely because it is merged.

## Open PRs at snapshot

| PR | Branch | Title | Current handling |
|---|---|---|---|
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/tsetmc-integrated-acceptance-pipeline` | Add integrated offline TSETMC acceptance pipeline | Hold for dependency and strategy review; no merge by this register |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/free-dataset-discovery-acceptance` | Add free dataset discovery and acceptance workflow | Hold for dependency and strategy review |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `feature/iran-live-data-dashboard` | Add Iranian market-data dashboard and persistent Tindex ingestion | Hold; UI is not a strategic acceptance result |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | `research/iran-free-data-smoke` | Add bounded Iranian TSETMC live data smoke | Hold; smoke test only |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | `fix/gdelt-fred-tindex-current-docs` | Fix priority data-source acceptance for GDELT, FRED and Tindex | Hold for integrated acceptance review |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `feat/tindex-free-data-connector` | feat: add conservative Tindex free-tier connector | Hold; provider cap and evidence limits must remain explicit |
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `deploy/production-readiness` | Prepare MarketSage user stack for controlled deployment | Draft; not a strategic data/model outcome |

## Recently merged PRs at snapshot

| PR | Branch | Title | Strategic interpretation |
|---|---|---|---|
| [#12](https://github.com/yarsalam/marketsage/pull/12) | `feature/tindex-historical-candles` | Add Tindex historical candle ingestion | Candidate data-ingestion capability; provider history and semantics limitations remain |
| [#11](https://github.com/yarsalam/marketsage/pull/11) | `feature/vendor-streamdata-csv-ingestion` | Audit and normalize seller-provided StreamData CSV exports | Data-quality audit; no source approval |
| [#10](https://github.com/yarsalam/marketsage/pull/10) | `feature/tsetmc-adjustment-validation` | Validate TSETMC adjusted history for فولاد | Adjustment investigation; not full historical-data acceptance |
| [#5](https://github.com/yarsalam/marketsage/pull/5) | `feat/point-in-time-data-lineage` | Add point-in-time data lineage foundation | Reusable data lineage capability; source acceptance still separate |
| [#4](https://github.com/yarsalam/marketsage/pull/4) | `ci/admin-workspace-validation` | Validate admin workspace and clarify production gates | Engineering validation, not investment-strategy evidence |
| [#3](https://github.com/yarsalam/marketsage/pull/3) | `feature/iran-market-data-providers` | Add quality-gated Iranian market data contracts | Data contract foundation, not live source acceptance |
| [#2](https://github.com/yarsalam/marketsage/pull/2) | `research/data-backtest-validation` | Add leakage-aware research backtest baseline and data-contract tests | Baseline methodology, not verified profitability |

## Operating rule

- Maintain one canonical active implementation PR at a time.
- Before selecting it, inspect base/head commit ancestry and changed files of all open PRs.
- Do not merge several stacked or competing PRs just to clear the queue.
- Close or park duplicate/obsolete PRs only after confirming that their useful commits are already integrated or preserved elsewhere.
- Every PR state transition must be reflected here and in `PROJECT_STATE.md`.
