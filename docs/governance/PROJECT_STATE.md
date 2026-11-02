# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `597e74d126b509188c7fa7d80eb765eb6c80238b`  
**Status:** Repository recovery and PR-stack consolidation required before further product implementation.

## Verified repository state

- Repository visibility is `private`.
- `main` is not the current application integration branch. Its latest commit is `597e74d` ("Add empty user-frontend directory", 2026-10-15); it contains only the initial repository skeleton and does not yet contain the implemented application stack.
- `deploy/production-readiness` is 87 commits ahead of `main` and is the base branch of PR #1. It contains the first integrated application stack and PRs #2–#5 were merged into it.
- Branch listing reports all inspected branches as unprotected. No required protection is currently active.
- The main branch has no CI workflow in its current tree. CI checks are present on the feature/deployment branches.
- The GitHub connection can inspect and update repository files and PR metadata, but cannot configure repository settings or branch protection.
- A prior ruleset settings read returned a plan-related HTTP 403. Do not assume private-branch enforcement is available on the current plan.
- The governance branch is `governance/execution-constitution-v1`; its PR is #15 and remains Draft.
- This snapshot does not inspect local uncommitted files or the owner's private research-data directory.

## Active PR stack — verified 2026-11-02

| PR | Base ← head | State | Mergeability | Latest observed checks | Handling |
|---|---|---|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` ← `deploy/production-readiness` | Open, Draft | Clean | Five unique CI jobs passed (duplicate runs also present) | First code-baseline integration; distinguish merging code from deploying it |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `deploy/production-readiness` ← `feat/tindex-free-data-connector` | Open | Clean | 5/5 passed | Depends on #1 |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | `feat/tindex-free-data-connector` ← `fix/gdelt-fred-tindex-current-docs` | Open | **Dirty / not mergeable** | 5/5 passed | Resolve branch divergence before merge |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | Open | Unstable | Standard CI passed; `tsetmc-smoke` failed | Park pending failure diagnosis; smoke is not source acceptance |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `fix/gdelt-fred-tindex-current-docs` ← `feature/iran-live-data-dashboard` | Open | Clean | 5 unique CI jobs passed (duplicate runs also present) | Depends on #7 |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/iran-live-data-dashboard` ← `feature/free-dataset-discovery-acceptance` | Open | Clean | 5/5 passed | Integrate after #9; then revalidate its sibling |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/iran-live-data-dashboard` ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Clean | 5/5 passed | Integrate after #9 and sequentially with #13 |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Open, Draft | Clean | No check runs on this documentation-only head | Keep Draft until repository baseline and operating controls are corrected |

Check results above describe the observed commits only. Any new commit requires its own CI result. Green CI does not approve data sources, investment scoring, or deployment.

## Recently merged PRs and their actual integration branches

| PR | Merged into | Subject |
|---|---|---|
| #2 | `deploy/production-readiness` | Leakage-aware research backtest baseline and data-contract tests |
| #3 | `deploy/production-readiness` | Quality-gated Iranian market data contracts |
| #4 | `deploy/production-readiness` | Admin workspace CI and production-gate clarification |
| #5 | `deploy/production-readiness` | Point-in-time data-lineage foundation |
| #10 | `feature/iran-live-data-dashboard` | TSETMC adjusted-history validation probe |
| #11 | `feature/iran-live-data-dashboard` | StreamData CSV audit and normalization |
| #12 | `feature/iran-live-data-dashboard` | Tindex historical candle ingestion |

## Dependency order

The current PR graph is stacked, not independent:

```text
main
  └─ #1 → deploy/production-readiness
       └─ #6 → feat/tindex-free-data-connector
            └─ #7 → fix/gdelt-fred-tindex-current-docs
                 ├─ #8 → research/iran-free-data-smoke      [failed smoke]
                 └─ #9 → feature/iran-live-data-dashboard
                      ├─ #13 → feature/free-dataset-discovery-acceptance
                      └─ #14 → feature/tsetmc-integrated-acceptance-pipeline
```

Do not merge these PRs in parallel or retarget them all at once. Integrate from the root forward, update the next PR against the new base, and rerun only checks affected by that update. PR #13 and #14 are siblings; merge one, then update and validate the other.

## Strategic evidence inherited from prior project records

The following are prior reported findings, not a fresh audit of local data:

- TSETMC فولاد: 4,250 raw rows; 285 raw OHLC violations and 41 remaining in the adjusted candidate; 23 adjustment events examined. This is an anomaly investigation, not certified adjusted history.
- TSETMC and CODAL were reachable in a prior VPN-off probe. Reachability does not establish data acceptance; CODAL publication timestamp semantics remained unresolved.
- Tindex historical candle access was reported to have an approximately 100-day provider limit, insufficient by itself for a six-month backtest.
- StreamData CSV exports were audited for AYAR, BTCUSDT, 18K gold and free-market USD; units, time/timezone and market semantics remain unresolved.
- Yahoo-derived global proxy data and an initial momentum/backtest foundation exist, but are not a certified, point-in-time, tradable investment universe.
- Investment scoring/ranking remains fail-closed. No profitability claim or future-return guarantee is established.

## Operating constraints

1. No investment scoring/ranking activation or real-money trade execution.
2. No data source becomes accepted because an endpoint responds or CI passes.
3. No production deployment is implied by merging code into `main`.
4. No local Runner registration until its trusted-workflow boundary and restricted data access are validated.
5. Keep raw data, credentials and private captures outside Git; use manifests and hashes.
6. Do not repeat a test unless the code, data hash, configuration, environment or relevant dependency changed.

## Next ordered work

1. **Recover the trunk:** review PR #1 as a code-baseline integration, explicitly separate code merge from any production deployment, and resolve its Draft gate.
2. **Integrate the stack in order:** #6, resolve #7's divergence, then #9. Do not merge #8 while its smoke check is failing.
3. **Integrate the two research additions:** merge #13 or #14 first, update the sibling onto the new base, and validate it once.
4. **Correct governance:** keep PR #15 Draft until its snapshot/register is accurate and the branch/runner enforcement choice is recorded.
5. **Resume product work:** once the integration base is coherent, the next strategic task is a broad candidate-data screen and the local evidence inventory—not more connector code or repeated test packs.

## Current stop point

No feature PR has been merged or closed by this snapshot. No Forgejo migration, Runner installation, scoring activation or production deployment has been performed.
