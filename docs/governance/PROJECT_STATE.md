# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Status:** Base application is in main. The Tindex/FRED fixes are integrated into the open #6 branch; downstream Iranian-data PRs have been rebased onto the current integration base and are being validated.

## Verified repository state

- Repository visibility is `private`.
- PR #1 integrated the application baseline into `main`. This was a Git merge only; no production deployment occurred.
- PR #6 targets `main` and is still open/unmerged by explicit owner boundary. Its current branch includes the fixes formerly in PR #7.
- PR #7 was merged into the PR #6 feature branch, not into `main`.
- All inspected branches remain unprotected. The connected GitHub integration cannot configure repository settings or branch protection.
- No local Runner has been registered. Its security boundary must be implemented before local datasets can be accessed through automated jobs.
- Local uncommitted files and the owner's private data directory have not been inspected in this GitHub-only pass.

## Current integration graph

```text
main
  └─ #6 feat/tindex-free-data-connector
       ├─ includes #7 priority-source fixes (already merged into this branch)
       └─ #9 feature/iran-live-data-dashboard
            ├─ #13 free-dataset-discovery-acceptance
            └─ #14 tsetmc-integrated-acceptance-pipeline

#8 research/iran-free-data-smoke — separate diagnostic PR; keep parked
#15 governance — documentation PR; remains Draft pending final governance/branch controls
```

## PR status — observed 2026-11-02

| PR | Current branch / base | State | Checks / handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open, unmerged | Clean; all five unique CI job types passed. Do not merge to main without explicit owner authorization. |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | `feat/tindex-free-data-connector` | Merged | Merged at `3b5d8a67bcaae6234afa9b4a1d71cd7c2ad7cb47`; Tindex API fixes and sanitized FRED network diagnostics are now in #6. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | Old fix branch ← `research/iran-free-data-smoke` | Open, parked | Five standard CI jobs passed; the separate live TSETMC probe failed with `ConnectTimeout` to `cdn.tsetmc.com` from GitHub-hosted runner. Not evidence of a code failure or a blocker to unrelated work. |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | `feat/tindex-free-data-connector` ← `feature/iran-live-data-dashboard` | Open | Current head `1acbc172d79403fa614d040e6c55c443157f7beb`; analysis/backend/frontend/admin checks passed; production image checks still running at snapshot. |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | `feature/iran-live-data-dashboard` ← `feature/free-dataset-discovery-acceptance` | Open | Current head `ae9a1072b2a8c1d7748b5159acc76f46999cc073`; analysis/backend/frontend/admin checks passed; production image checks still running at snapshot. |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | `feature/iran-live-data-dashboard` ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Current head `6fdc2805849561ede14b9c6d7ace303d5113457d`; analysis/backend/frontend/admin checks passed; production image checks still running at snapshot. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Open, Draft | Updated governance documents; keep Draft until final adoption and private-branch enforcement decision. |

Check status applies only to the listed head commits. The remaining production-image checks must complete successfully before merging the corresponding downstream PRs.

## Changes made in this execution pass

1. Merged PR #1 into `main` as a code-baseline integration; no deployment.
2. Retargeted PR #6 to `main`; kept it open/unmerged.
3. Reconciled PR #7 with the newer PR #6 Tindex quota implementation (1 request/minute, 100 successful requests/day), retained the documented indicator/history API changes and FRED sanitized error handling, then merged #7 into #6.
4. Corrected CI triggers so pull requests targeting feature/fix branches are validated; retained the free-dataset validation step and staging configuration checks.
5. Rebased/synchronized PR #9, #13 and #14 onto the current dependency chain, preserving their separate code changes.

## Work that can proceed in parallel

A dependency blocker does not stop unrelated work. These workstreams may proceed in parallel as separate, bounded tasks:

- audit existing local datasets and manifests without rerunning prior probes;
- broaden candidate-source discovery across Iranian and global assets;
- review source rights, coverage, unit/timestamp semantics and independent-reference options;
- prepare the evaluation protocol and baseline comparisons without activating production scoring;
- continue CI and integration of the dependent PR chain in its prescribed order.

Local dataset inspection is not yet completed because this session has no access to the owner's laptop data directory and no trusted local Runner is installed. Do not claim it has been audited.

## Operating constraints

- Investment scoring/ranking remains fail-closed; no real-money trades or allocation changes.
- Endpoint reachability or green CI does not constitute data-source acceptance.
- Merging code into `main` is not authorization to deploy.
- PR #6 remains unmerged into `main` until the owner explicitly authorizes it.
- No self-hosted Runner registration before trusted-workflow and least-privilege controls are reviewed.
- Keep raw datasets, credentials and private captures outside Git; use manifests and hashes.

## Next execution order

1. Let the current CI complete for #9, #13 and #14; fix only a demonstrated failure.
2. Merge #9 into the #6 integration branch after all required checks pass.
3. Merge #13 and #14 sequentially into the #9/dashboard branch, updating and validating the sibling after the first merge.
4. Continue independent source/data inventory work in parallel; do not wait for the whole PR chain to finish.
5. Keep #6 open at the main boundary until explicit owner authorization; no deployment is implied.
