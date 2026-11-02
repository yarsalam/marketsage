# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Status:** Application baseline integrated into main. The Tindex/FRED and Iranian dashboard work has been consolidated into the open #6 integration branch. Two independent research additions are being validated against that same base.

## Verified repository state

- Repository visibility is `private`.
- PR #1 integrated the application baseline into `main`; no production deployment occurred.
- PR #6 remains open and unmerged to `main` under the explicit owner boundary. It now contains the formerly separate #7 Tindex/FRED fixes and the formerly separate #9 Iranian market dashboard.
- PR #7 was merged into #6. PR #9 was subsequently merged into #6.
- PR #13 and #14 are now independent sibling PRs based directly on the updated #6 branch. Their scopes do not overlap at the source-file level reviewed before this rebase.
- All inspected branches remain unprotected. The connected GitHub integration cannot configure repository settings or branch protection.
- No local Runner has been registered. Its trusted-workflow boundary must be implemented before local datasets can be accessed through automated jobs.
- This pass did not inspect local uncommitted files or the owner's private data directory.

## Current integration graph

```text
main
  └─ #6 feat/tindex-free-data-connector  [open; do not merge into main without owner approval]
       ├─ #7 priority-source fixes       [merged into #6]
       ├─ #9 Iranian dashboard            [merged into #6]
       ├─ #13 free-dataset discovery      [open; CI running]
       └─ #14 TSETMC acceptance pipeline [open; CI running]

#8 research/iran-free-data-smoke — separate diagnostic PR; parked
#15 governance — documentation PR; remains Draft
```

## PR status — observed 2026-11-02

| PR | Base ← head | State | Checks / handling |
|---|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` ← `deploy/production-readiness` | Merged | Application baseline integrated; no deployment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open, unmerged | Current head `2495d881c8b410ed2e74f7b2ec1858ecbed6702a`; clean/mergeable. New checks after #9 integration are running. Keep open at the main boundary. |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 branch | Merged | Merge commit `3b5d8a67bcaae6234afa9b4a1d71cd7c2ad7cb47`; API fixes, FRED diagnostics, regression tests and strict Tindex quota guard retained. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old fix branch ← `research/iran-free-data-smoke` | Open, parked | Standard CI passed; only the GitHub-hosted live TSETMC request failed with `ConnectTimeout` to `cdn.tsetmc.com`. Not a code defect demonstrated and not a blocker to unrelated work. |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 branch | Merged | Merged after all five unique CI job types passed; merge commit `2495d881c8b410ed2e74f7b2ec1858ecbed6702a`. No deployment. |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 branch ← `feature/free-dataset-discovery-acceptance` | Open | Current head `1398ca3369c85f8ef6142f87e58aa2923b3852dd`; analysis/backend/frontend/admin jobs passed; production-image checks running. |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 branch ← `feature/tsetmc-integrated-acceptance-pipeline` | Open | Current head `9a6b5109c938d47cd123145c5e02a6078af16613`; checks queued/running after base update. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Open, Draft | Constitution now explicitly permits independent research work in parallel with sequential integration. |

CI results refer only to the listed head commits. Merge #13/#14 after the new-base checks pass; merge them sequentially into #6. PR #6 remains unmerged into `main` without explicit owner authorization.

## Changes made in this execution pass

1. Merged PR #1 into `main` as a code-baseline integration; no deployment.
2. Retargeted #6 to `main`; kept it open/unmerged.
3. Reconciled #7 with the updated #6 Tindex quota implementation (1 request/minute, 100 successful requests/day), retained official documented endpoint/history support and sanitized FRED errors, then merged #7 into #6.
4. Corrected CI triggers to validate PRs targeting feature/fix branches.
5. Rebased #9 onto the consolidated #6 base and merged #9 into #6 after all five unique CI job types passed.
6. Rebased #13 and #14 directly onto the current #6 base; both are undergoing fresh CI.

## Parallel work policy

A dependency blocker does not freeze unrelated work. These workstreams can proceed independently while PR CI/integration continues:

- inspect existing datasets and manifests, avoiding duplicate downloads/probes;
- broaden candidate-source screening across Iranian and global assets;
- review source rights, historical coverage, unit/timestamp semantics and independent references;
- prepare the evaluation protocol, baselines and risk/cost metrics;
- continue narrowly scoped engineering tasks that do not overlap the active integration changes.

Local data inventory has **not** been performed in this GitHub-only pass because this session does not have access to the owner's local data directory and no trusted local Runner is installed. Do not claim otherwise.

## Operating constraints

- Investment scoring/ranking remains fail-closed; no real-money trades or allocation changes.
- Endpoint reachability or green CI does not constitute data-source acceptance.
- Merging code into `main` is not authorization to deploy.
- PR #6 remains unmerged into `main` until explicit owner authorization.
- No local Runner registration before trusted-workflow and least-privilege controls are reviewed.
- Keep raw datasets, credentials and private captures outside Git; use manifests and hashes.

## Next actions

1. Complete the fresh CI for #13 and #14; fix only a demonstrated failure.
2. Merge #13 into #6; then update and validate #14 against the resulting #6 head and merge it.
3. Keep #6 open at the main boundary.
4. Start the independent candidate-data/evidence inventory in parallel; use an approved local execution path when local files are required.
5. Retain #8 as a diagnostic item unless a live request from the intended Iranian runtime produces new evidence.
