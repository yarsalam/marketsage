# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Status:** PR #1 baseline is in main. Tindex/FRED fixes, Iranian dashboard and broad free-dataset discovery are integrated in the open #6 integration branch. The TSETMC integrated acceptance pipeline is the last pending downstream PR.

## Verified repository state

- Repository visibility is `private`.
- PR #1 integrated the application baseline into `main`; no deployment occurred.
- PR #6 remains open and unmerged to `main` under the explicit owner boundary. Its current head is `d6a0eb0a8633e9223787e8582da046d923eb0c26`.
- PR #7 was merged into #6; PR #9 was merged into #6; PR #13 was merged into #6.
- PR #14 is rebased directly onto #6. Its current head is `4bd179263f55b90854d00f1ea3b1287da0393b03`; required checks are still running after the rebase.
- PR #13 passed all five required CI job types on its exact pre-merge head and was merged into #6.
- All inspected branches remain unprotected. The connected GitHub integration cannot configure repository settings or branch protection.
- No local Runner is registered. The local data directory has not been inspected in this GitHub-only pass.

## Current integration graph

```text
main
  └─ #6 feat/tindex-free-data-connector [open; never merge to main without explicit owner approval]
       ├─ #7 priority-source fixes               [merged]
       ├─ #9 Iranian market dashboard            [merged]
       ├─ #13 free-dataset discovery             [merged]
       └─ #14 TSETMC acceptance pipeline         [open; fresh CI running]

#8 research/iran-free-data-smoke — parked network diagnostic
#15 governance — documentation PR, Draft
```

## PR status — observed 2026-11-02

| PR | Base ← head | State | Checks / handling |
|---|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` ← `deploy/production-readiness` | Merged | Application baseline integrated; no deployment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open, unmerged | Current head `d6a0eb0a8633e9223787e8582da046d923eb0c26`; analysis/backend/frontend/admin checks passed; production image checks running. Keep open at main boundary. |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 branch | Merged | Tindex documented route/history updates, safe FRED network diagnostics, regression tests and strict 1/minute + 100/day client guard. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old fix branch ← `research/iran-free-data-smoke` | Open, parked | Standard CI passed; separate live TSETMC probe timed out from GitHub-hosted runner. Do not repeat from same network. |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 branch | Merged | Iranian market dashboard and research-only readiness/staging configuration; all five unique required CI job types passed before merge. |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 branch | Merged | Free-dataset discovery, source catalog, candidate audit/ingestion tools; all five required CI job types passed on exact head before merge. |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 branch ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Current head `4bd179263f55b90854d00f1ea3b1287da0393b03`; analysis/frontend/backend/admin checks passed or are completing; production-image checks queued at snapshot. Merge after all required checks pass. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Open, Draft | Updated constitution allows independent work in parallel. Keep Draft until governance adoption/enforcement decision. |

CI results apply only to exact head commits. Do not merge #14 until fresh required checks are green. PR #6 stays open; there is no deployment or scoring authorization.

## Changes made in this execution pass

1. PR #1 merged into `main` as a code-baseline integration; no deployment.
2. PR #6 retargeted to `main` and kept open/unmerged.
3. PR #7 reconciled with the conservative Tindex quota implementation and merged into #6.
4. CI triggers expanded to run on feature/fix branches and relevant PR targets.
5. PR #9 rebased and merged into #6 after green CI.
6. PR #13 rebased and merged into #6 after green CI.
7. PR #14 rebased onto the resulting #6 head; CI is running on the updated head.

## Parallel work policy

A dependency blocker does not freeze independent work. These tasks can progress in parallel with integration:

- audit existing data manifests and sanitized evidence without repeating previous probes;
- screen candidate data sources across Iranian and global assets;
- review rights, units, timestamps, historical coverage and independent reconciliation;
- prepare the six-month monthly-decision evaluation protocol, risk/cost assumptions and baselines;
- perform separately scoped engineering that does not conflict with current integration changes.

Local dataset inventory remains unverified because this session has no access to the owner's local data directory and there is no trusted local Runner. Do not claim it was audited.

## Operating constraints

- Investment scoring/ranking remains fail-closed; no real-money trades or portfolio allocation.
- Reachability and green CI do not constitute data-source acceptance or strategy validation.
- Merging to `main` does not authorize deployment.
- PR #6 must not be merged into `main` without explicit owner approval.
- No local Runner registration before trusted-workflow and least-privilege data-access controls are reviewed.
- Keep raw datasets, credentials and private captures outside Git.

## Next actions

1. Complete fresh CI on #14; correct only a demonstrated defect.
2. Merge #14 into #6 if all required checks pass; update status docs.
3. Continue independent candidate-source/evidence screening and strategy evaluation preparation.
4. Inspect local evidence only through a trusted, restricted execution path; otherwise mark local-data evidence blocked.
5. Evaluate the investment objective based on out-of-sample net risk-adjusted performance against baselines, including transaction costs, slippage, drawdown and look-ahead controls.
6. Keep #6 at the main boundary pending explicit owner authorization. No deployment is implied.
