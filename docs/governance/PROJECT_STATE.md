# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Status:** Initial application baseline is now integrated into `main`; the remaining feature stack is being consolidated sequentially.

## Verified repository state

- Repository visibility is `private`.
- PR #1 was merged into `main`. This brought the existing application/research code baseline into the default branch. **No production deployment occurred.**
- `main` now contains the baseline previously held on `deploy/production-readiness`.
- PR #6 was retargeted from `deploy/production-readiness` to `main`; GitHub currently reports it clean/mergeable. It remains open and unmerged.
- All inspected branches were reported unprotected. The GitHub connection cannot configure repository settings or branch protection.
- A prior ruleset settings read returned a plan-related HTTP 403. Do not assume private-branch enforcement is available on the current plan.
- No local Runner has been registered. Do not register one until the trusted-workflow boundary and restricted data access are validated.
- This snapshot does not inspect local uncommitted files or the owner's private research-data directory.

## Active PRs — verified 2026-11-02

| PR | Base ← head | State | Mergeability / checks | Handling |
|---|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open | Clean; 5/5 observed CI jobs passed | Retargeted to main; remains unmerged under prior owner restriction |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | `feat/tindex-free-data-connector` ← `fix/gdelt-fred-tindex-current-docs` | Open | **Dirty / not mergeable**; 5/5 checks passed | Resolve branch divergence before merge |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Open | Unstable; `tsetmc-smoke` failed | Park until the smoke failure is explained |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `fix/gdelt-fred-tindex-current-docs` ← `feature/iran-live-data-dashboard` | Open | Clean; 5 unique CI jobs passed | Depends on #7 |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/iran-live-data-dashboard` ← `feature/free-dataset-discovery-acceptance` | Open | Clean; 5/5 passed | After #9; integrate sequentially with #14 |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/iran-live-data-dashboard` ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Clean; 5/5 passed | After #9; update/revalidate after #13 or vice versa |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Open, Draft | Clean; no check runs on its documentation-only head | Hold until governance and enforcement choices are finalized |

CI results refer to the observed commit SHAs only. A changed commit requires fresh validation. Green CI does not imply source acceptance, investment approval or deployment readiness.

## Recently merged PRs

| PR | Merged into | Subject |
|---|---|---|
| #1 | `main` | Integrate MarketSage application baseline (no deployment) |
| #2 | `deploy/production-readiness` | Leakage-aware research backtest baseline and data-contract tests |
| #3 | `deploy/production-readiness` | Quality-gated Iranian market data contracts |
| #4 | `deploy/production-readiness` | Admin workspace CI and production-gate clarification |
| #5 | `deploy/production-readiness` | Point-in-time data-lineage foundation |
| #10 | `feature/iran-live-data-dashboard` | TSETMC adjusted-history validation probe |
| #11 | `feature/iran-live-data-dashboard` | StreamData CSV audit and normalization |
| #12 | `feature/iran-live-data-dashboard` | Tindex historical candle ingestion |

## Current integration order

```text
main
  └─ #6 → feat/tindex-free-data-connector
       └─ #7 → fix/gdelt-fred-tindex-current-docs
            ├─ #8 → research/iran-free-data-smoke       [failed smoke; park]
            └─ #9 → feature/iran-live-data-dashboard
                 ├─ #13 → feature/free-dataset-discovery-acceptance
                 └─ #14 → feature/tsetmc-integrated-acceptance-pipeline
```

#7 is the current dependency blocker. Do not merge its children before resolving it. #13 and #14 are siblings; merge one, update the other against the resulting base, then run the affected CI once.

## Strategic evidence inherited from earlier records

These are reported findings, not a new local-data audit:

- TSETMC فولاد: 4,250 raw rows; 285 raw OHLC violations and 41 in the adjusted candidate; 23 adjustment events examined. Not certified adjusted history.
- TSETMC and CODAL were reachable in a prior VPN-off probe. Reachability is not acceptance; CODAL publication timestamp semantics remained unresolved.
- Tindex historical candles were reported to have an approximately 100-day provider limit, insufficient alone for a six-month backtest.
- StreamData exports for AYAR, BTCUSDT, 18K gold and free-market USD were audited; units/timezone/market semantics remain unresolved.
- Yahoo-derived global proxies and an initial momentum/backtest foundation are not a certified, point-in-time tradable universe.
- Investment scoring/ranking remains fail-closed. No profitability claim or future-return guarantee is established.

## Operating constraints

1. No investment scoring/ranking activation or real-money trade execution.
2. No data source is accepted solely because an endpoint responds or CI passes.
3. Merging code into `main` is not authorization to deploy it.
4. No local Runner registration before trusted-workflow and least-privilege controls are tested.
5. Raw datasets, credentials and private captures stay outside Git; use manifests and hashes.
6. Re-run tests only after a material change to code, data hash, configuration, environment or dependencies.

## Next work

1. Resolve PR #7's divergence against the updated #6 base.
2. Revalidate and integrate #7; then integrate #9.
3. Integrate #13 and #14 sequentially, with one canonical integration PR at a time.
4. Keep #8 parked until its failing TSETMC smoke check is diagnosed.
5. After the stack is coherent, resume strategic work with the broad candidate-data screen and local evidence inventory—not another connector/test loop.
