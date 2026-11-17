# MarketSage — Pull Request Register

**Live snapshot:** 2026-11-17 14:25 UTC  
**Repository:** yarsalam/marketsage (GitHub API: Public; current owner request: Private; mismatch unresolved)  
**Default branch:** main — `4c4b032196137af4658ea2c28e38a21605ee923b` (commit time 2026-11-07 19:55:51 UTC)  
**Active infrastructure PR:** [#74](https://github.com/yarsalam/marketsage/pull/74) — Draft/open/unmerged  
**Issue #49:** OPEN / NOT COMPLETE / NOT 24/7 READY

## Live open-PR inventory — 2026-11-17 14:25 UTC

All head SHAs and Check Run counts below were read from GitHub for the current open PR heads. Duplicate Push/PR contexts are counted separately; skipped/cancelled/queued checks are not test successes.

| PR | State / Draft | Base branch | Exact head SHA | Mergeable | Exact-head checks | Handling |
|---|---|---|---|---|---:|---|
| [#82](https://github.com/yarsalam/marketsage/pull/82) | open / Draft | main | `fc1ffe89b2de8c0ec2221a416043bb186933bb3e` | yes | 18: 13 success, 4 skipped, 1 cancelled | Research hold; no workflow dispatch/rerun. Historical worker run #43940587342 is now cancelled; zero artifacts. |
| [#81](https://github.com/yarsalam/marketsage/pull/81) | open / Draft | main | `8d49042b520b78a877a5032bb9cf2e6f45e6169e` | yes | 17: 12 success, 5 skipped | Product/integration work paused. |
| [#80](https://github.com/yarsalam/marketsage/pull/80) | open / Draft | main | `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | yes | 8: 6 success, 2 skipped | Product/admin work paused. |
| [#79](https://github.com/yarsalam/marketsage/pull/79) | open / Draft | main | `14001bdb5a03775b9772bf9cfea1d169a68f8113` | yes | 8: 6 success, 2 skipped | Product/auth work paused. |
| [#78](https://github.com/yarsalam/marketsage/pull/78) | open / Draft | main | `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | yes | 10: 8 success, 2 skipped | Strategy/product work paused. |
| [#77](https://github.com/yarsalam/marketsage/pull/77) | open / Draft | main | `67356939f65224a580c915fd2caa0ea52d8d09a9` | yes | 8: 6 success, 2 skipped | Product safety feature work paused. |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | open / Draft | main | `9a439b389b530ae2008e3d864b369fb8d3d73f87` (code parent of this docs-only update) | yes | 20: 6 success, 14 skipped | Existing infrastructure path. Exact Push #43891676244 and PR #43891687575 passed on this code SHA. New documentation-only commit is `[skip ci]` and has no check claim. |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | open / Draft | main | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | yes | 16: 12 success, 4 skipped | Research work paused. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | open / Draft | PR #74 branch | `e630517c7e2916ed58b7568b0ebbbf1d390b86ce` | no | 0 | Existing outbox/worker/watchdog path. Diverged from current #74 head: 117 ahead / 123 behind; merge base `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10`. Do not merge or duplicate. |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | open / Ready | main | `54fbf4a364a91b4e8d834fdcec0245d079440982` | yes | 8: 6 success, 2 skipped | Dependabot update; retain review gate. |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | open / Draft | PR #74 branch | `25ce24283e35dd7e55eb8545c590a047606643ee` | no | 0 | Documentation branch; no exact-head checks. |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | open / Ready | PR #6 branch | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | yes | 10: all success | Data-source work paused. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | open / Ready | main | `162692f1a377ec8445ed958db4cc1171d4cafc47` | yes | 5: all success | Evidence/data workflow paused. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | open / Ready | fix/gdelt-fred-tindex-current-docs | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | yes | 6: 5 success, 1 failure | Parked after known TSETMC ConnectTimeout; do not repeat from same environment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | open / Ready | main | `1d90726c593b0818982407c309ff13301798f5b3` | no | 15: all success | Do not merge without separate explicit owner approval. PR #14 is already integrated into #6. |

## Current runs, ruleset and workflow audit

- Main Schedule [#44078801678](https://github.com/yarsalam/marketsage/actions/runs/44078801678) succeeded on main SHA `4c4b032...` at 2026-11-17 11:58:27 UTC, but ran analysis, backend, frontend, admin, production-images and CI helper jobs. It did not run the provider-neutral control-plane test job. Main's scheduled workflow is therefore active but not infrastructure-only.
- PR #74 exact code SHA `9a439b389b530ae2008e3d864b369fb8d3d73f87`: Push [#43891676244](https://github.com/yarsalam/marketsage/actions/runs/43891676244) and Pull Request [#43891687575](https://github.com/yarsalam/marketsage/actions/runs/43891687575) both succeeded. Scope classifier, provider-neutral control-plane tests and CI helper tests succeeded; product/production jobs were skipped. These results do not transfer to the documentation-only follow-up commit.
- Active ruleset [#26789479](https://github.com/yarsalam/marketsage/rules/26789479): one approving review, seven required status contexts, deletion/non-fast-forward protections, no bypass actors, strict freshness disabled, stale-review dismissal disabled. Legacy branch-protection endpoint returned 403; its state is unverified.
- Main `.github/workflows/ci.yml` remains the pre-freeze workflow. PR #74 contains the infrastructure-only scope classifier and schedule gate, but is not merged. PR #74 workflow triggers: push, pull_request, schedule (03:17 UTC), workflow_dispatch; top-level contents:read; job-level issue-write only for direct-main provenance/failure notification; per-PR/ref concurrency with cancel-in-progress; bounded 2–15 minute job timeouts.
- No explicit GitHub Actions retry policy, stale/queued-run detector, hung-job detector, artifact-retention override, or independent notification provider was observed. Failure notification runs on `ubuntu-latest`, the same GitHub-hosted runner pool. The provider-neutral watchdog/worker code has no deployed independent host evidence.
- PR #71's server-worker workflow is workflow_dispatch-only, requires explicit owner confirmation, a dedicated `marketsage-server-worker` label and a 20-minute timeout. No server Runner registration/online state or worker-loss/restart drill is proven. Its Docker canary remains branch-only; it is not active on main. Its failure notifier also uses `ubuntu-latest`.
- Previous queued-job safety action: [run #43940587342](https://github.com/yarsalam/marketsage/actions/runs/43940587342) is now cancelled; artifact listing returned zero. Do not rerun.
- PR #54 is closed, Draft, unmerged at `e8f7d8add3df577120b92b8927c590aece001509`; Issue #55 records 16/16 owner-run tests on this exact SHA. Current comparison to PR #74 is diverged, 8 ahead / 167 behind (merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`); no GitHub checks. Keep closed/unmerged.
- Issues: [#49](https://github.com/yarsalam/marketsage/issues/49) OPEN; [#52](https://github.com/yarsalam/marketsage/issues/52) OPEN (five Chabokan wheel hashes); [#53](https://github.com/yarsalam/marketsage/issues/53) CLOSED; [#55](https://github.com/yarsalam/marketsage/issues/55) CLOSED (16/16 exact-head SQLite unit tests only); [#59](https://github.com/yarsalam/marketsage/issues/59) OPEN.
- No workflow dispatch/rerun, local Runner operation, merge, auto-merge, release, deployment, provider registration, secret creation, spending, visibility change, data operation or investment action occurred.

> This live snapshot supersedes the historical open-PR inventory and prior checkpoints below; they remain for traceability.

---

**Snapshot date:** 2026-11-16 14:50 UTC  
**Repository:** yarsalam/marketsage (live API reports Public; current owner request says Private; mismatch unresolved)  
**Main HEAD:** 4c4b032196137af4658ea2c28e38a21605ee923b (last commit 2026-11-07 19:55:51 UTC)  
**Active infrastructure PR:** [#74](https://github.com/yarsalam/marketsage/pull/74), infra/provider-neutral-control-plane-2026-11  
**Latest infrastructure code commit in this snapshot:** 63b82232106ba2949e0e24be290dd0e7ed716d6d (static scheduled-scope contract test; not executed)  
**Issue #49:** OPEN / NOT COMPLETE / NOT 24/7 READY

## Latest live open-PR snapshot — 2026-11-16 14:50 UTC

Exact-head counts below are GitHub Check Runs at the listed SHA; duplicate push and pull-request contexts are counted separately. A queued, cancelled, or pre-step run is not a successful test.

| PR | State / Draft | Base | Exact head | Exact-head checks | Current handling |
|---|---|---|---|---:|---|
| [#82](https://github.com/yarsalam/marketsage/pull/82) | open / Draft | main | f3b402f4fa57bcfbcf724e88f0182c3a6732f70e | 20: 18 success, 2 queued | Research hold; current owner instruction supersedes prior Goal 2 reopen. Queued historical-market-state jobs have no steps. |
| [#81](https://github.com/yarsalam/marketsage/pull/81) | open / Draft | main | 8d49042b520b78a877a5032bb9cf2e6f45e6169e | 17 success | Product/integration scope paused. |
| [#80](https://github.com/yarsalam/marketsage/pull/80) | open / Draft | main | 241241ee91f2dc944e0dc407bb6c5d1c409bc520 | 8 success | Product/admin scope paused. |
| [#79](https://github.com/yarsalam/marketsage/pull/79) | open / Draft | main | 14001bdb5a03775b9772bf9cfea1d169a68f8113 | 8 success | Product/auth scope paused. |
| [#78](https://github.com/yarsalam/marketsage/pull/78) | open / Draft | main | 47030f24d2d0491cb53eac5b089ff1dd4a15eccc | 10 success | Strategy/product scope paused. |
| [#77](https://github.com/yarsalam/marketsage/pull/77) | open / Draft | main | 67356939f65224a580c915fd2caa0ea52d8d09a9 | 8 success | Product safety feature scope paused. |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | open / Draft | main | code commit 63b82232106ba2949e0e24be290dd0e7ed716d6d | 0 | Active infrastructure path. New static schedule-gate test is authored but unexecuted; no exact-head CI evidence. |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | open / Draft | main | 72c57608e8270d999d1e9f2005b47ea56cb893a7 | 16 success | Research scope paused. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | open / Draft | PR #74 branch | e630517c7e2916ed58b7568b0ebbbf1d390b86ce | 0 | Existing outbox/worker/watchdog implementation. Diverged: 117 ahead / 122 behind PR #74 code commit 63b8223; do not merge or duplicate. |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | open / Ready | main | 54fbf4a364a91b4e8d834fdcec0245d079440982 | 8 success | Dependabot update; retain normal review gate. |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | open / Draft | PR #74 branch | 25ce24283e35dd7e55eb8545c590a047606643ee | 0 | Documentation work; no exact-head checks. |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | open / Ready | PR #6 branch | da803a1c69ba6524f7cc27d7b0cc4a3d4397df28 | 10 success | Data-source screening paused. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | open / Ready | main | 162692f1a377ec8445ed958db4cc1171d4cafc47 | 5 success | Evidence/data workflow scope paused. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | open / Ready | fix/gdelt-fred-tindex-current-docs | 0cb94fd24f531162d4a3d403f9749789ce6f1797 | 6: 5 success, 1 failed | Parked after known TSETMC ConnectTimeout; do not repeat from the same environment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | open / Ready | main | 1d90726c593b0818982407c309ff13301798f5b3 | 15 success | Never merge without separate explicit owner approval. PR #14 is already integrated into #6. |

### Latest run and policy evidence

- Main scheduled CI [#43858518666](https://github.com/yarsalam/marketsage/actions/runs/43858518666) succeeded on main 4c4b032..., but executed analysis, backend, frontend, admin and production-image jobs. The 03:17 UTC schedule started 8h14m31s late; it does not prove an infrastructure-only schedule or 24/7 operation.
- PR #82 MarketSage CI push [#43879956884](https://github.com/yarsalam/marketsage/actions/runs/43879956884) and PR [#43879976086](https://github.com/yarsalam/marketsage/actions/runs/43879976086) succeeded on its exact head but ran product/research jobs. Its separate integrity push [#43879956767](https://github.com/yarsalam/marketsage/actions/runs/43879956767) and PR [#43879975992](https://github.com/yarsalam/marketsage/actions/runs/43879975992) have a completed integrity job and a queued historical-market-state job with no steps.
- Active main ruleset [#26789479](https://github.com/yarsalam/marketsage/rules/26789479): one approving review; seven required status contexts; deletion/non-fast-forward blocked; no bypass actors; strict status freshness disabled; stale-review dismissal disabled. Legacy branch-protection endpoint is not readable through the current integration.
- Main .github/workflows/ci.yml remains the pre-freeze workflow. PR #74's version has an infrastructure-only scope classifier and schedule gate, but it is unmerged and unvalidated. Main therefore continues to execute product/research jobs on push/PR/schedule events.
- Main local TSETMC workflows are workflow_dispatch only, require owner actor/confirmation and use laptop-specific self-hosted labels. No local workflow was dispatched.
- PR #71 contains the daily Docker worker canary (04:43 UTC) and a manual-only dedicated-server worker workflow, but these workflows are not on main and no independent persistent server or real canary was proven. Its failure notifier uses ubuntu-latest, the same GitHub-hosted runner pool; it is not an independent failure domain.
- Across the audited workflow set: top-level permissions are read-only with job-level issue-write only where needed; concurrency and per-job timeouts exist; no GitHub Actions retry policy or artifact-retention override was found. The code watchdog is not deployed on an independent host. No 24-hour observation, worker-loss recovery, independent alert path, second-provider run, or end-to-end canary is proven.
- [Issue #49](https://github.com/yarsalam/marketsage/issues/49) remains open. [Issue #52](https://github.com/yarsalam/marketsage/issues/52) remains open for Chabokan wheel hashes. [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is closed. [Issue #55](https://github.com/yarsalam/marketsage/issues/55) is closed with 16/16 owner-run tests for the exact PR #54 head. [Issue #59](https://github.com/yarsalam/marketsage/issues/59) remains open.
- PR #54 is **closed, Draft, unmerged** at e8f7d8add3df577120b92b8927c590aece001509; keep it closed. Its 16/16 owner test evidence does not establish branch reconciliation or operational acceptance.
- No hosted/local workflow was dispatched or rerun; no merge, release, deployment, provider registration, secret creation, spending, visibility change, data operation or investment action occurred.

> The historical open-PR inventory and earlier snapshots below are retained for traceability only; this live snapshot supersedes their stale state, validation and blocker descriptions.

## Historical open PR inventory (superseded)


| PR | Target | Scope / current state | Handling |
|---|---|---|---|
| [#6](https://github.com/yarsalam/marketsage/pull/6) | main ← feat/tindex-free-data-connector | Integrated research/data-source work; pinned integration head 819f8b4028469cb0d498098fec88545a18ebacc6; required five-job CI passed on exact post-#30 head | Keep open. **Do not merge to main without explicit owner approval.** |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | research/iran-free-data-smoke | GitHub-hosted TSETMC live request timed out | Parked. Do not repeat the same request from the same environment. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | main | Governance/evidence synchronization and corrected local workflow pin; exact-head run 42063679856 passed all five jobs | Open; no local dispatch; keep pending review during infrastructure-first priority. |\n| [#50](https://github.com/yarsalam/marketsage/pull/50) | main | CI timeouts/concurrency/schedule/failure reporter; exact head 9098f110... failed before steps with runner ID 0 in run 42176190919 | Open; do not merge; no further hosted runs while Actions budget is USD 0. |\n| [#51](https://github.com/yarsalam/marketsage/pull/51) | integration #6 | Iran property/automobile candidate screen; exact-head run 42062133299 passed five jobs | Open; ordinary data work paused under Issue #49; do not merge/extend in this phase. |
| [#54](https://github.com/yarsalam/marketsage/pull/54) | infra/provider-neutral-control-plane-2026-11 | Draft single-host SQLite coordinator; head e8f7d8add3df577120b92b8927c590aece001509; 16 tests, five lease-renewal tests pending exact-head execution; base has advanced and mergeability is unknown | Keep draft/open. Prior head passed 11/11 owner-run tests; current-head validation tracked in [Issue #55](https://github.com/yarsalam/marketsage/issues/55). Reconcile with current base before review/merge; no hosted dispatch while [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is open. |



## Merged to main

| PR | Result |
|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | Application baseline; no production deployment |
| [#27](https://github.com/yarsalam/marketsage/pull/27) | Manual-only staged TSETMC inventory/checksum validator; merged at 7e669749d2615bc0f2a9d6f557bb99f8e7bd0767 |
| [#31](https://github.com/yarsalam/marketsage/pull/31) | Clean adoption of the five governance documents; merged at 46d3a541b7fa176b5a8c5693a0c46feb8bb9b3fc |
| [#32](https://github.com/yarsalam/marketsage/pull/32) | Manual-only integrated TSETMC candidate workflow; merged at 11f9de85c13f3ee8bd61e6eb7aea64992a7271d4. Exact PR head 2df9e5fc523307a08894c8077210e8584aa4adcb passed all five jobs in run 41911051358. Awaiting owner manual dispatch. |
| [#34](https://github.com/yarsalam/marketsage/pull/34) | Memory-bounded/cgroup-aware TSETMC execution; merged at 554fe2200ccb3a523442b0e241e81a748becfa44. Exact PR head dcf32f46b524daf3ac63e9937962cd02948ca2f8 passed all five required jobs in run 41913385729; analysis reported 109 passed, 7 warnings. Owner re-dispatch pending. |

## Merged into integration PR #6

PRs #7, #9, #13, #14, #16, #17, #18, #19, #20, #21, #22, #23, #24, #28, #29 and #30 are merged into the integration branch in dependency order. Exact-head and post-merge CI results are recorded in their PRs. They do not constitute data-source approval or strategy acceptance.

- [#14](https://github.com/yarsalam/marketsage/pull/14) — integrated offline TSETMC candidate-acceptance pipeline; code is pinned for local execution at 819f8b4028469cb0d498098fec88545a18ebacc6.
- [#20](https://github.com/yarsalam/marketsage/pull/20) — v2 TSETMC identity crosswalk and ambiguity quarantine.
- [#22](https://github.com/yarsalam/marketsage/pull/22) — official global source candidates (ECB, Treasury, EIA, SEC, IMF).
- [#23](https://github.com/yarsalam/marketsage/pull/23) — Tindex quota evidence reconciliation while retaining the stricter local guard.
- [#24](https://github.com/yarsalam/marketsage/pull/24) — Binance Spot HTTP 451 hard block.
- [#28](https://github.com/yarsalam/marketsage/pull/28) — Iran official macro/transfer-FX/policy-rate/bond-auction candidate screen.
- [#29](https://github.com/yarsalam/marketsage/pull/29) — World Bank Pink Sheet benchmark candidate.
- [#30](https://github.com/yarsalam/marketsage/pull/30) — Stage 4 downside/tail-risk and portfolio-mechanics diagnostics.

## Closed / superseded

| PR | Result |
|---|---|
| [#15](https://github.com/yarsalam/marketsage/pull/15) | Closed as superseded; its divergent branch was not merged. Its five governance documents were adopted through clean PR #31. |
| [#26](https://github.com/yarsalam/marketsage/pull/26) | Closed as duplicate/superseded documentation branch. |

## Current integration graph

main
- #27 merged: local staged-dataset validator
- #31 merged: governance adoption
- #32 merged: integrated local TSETMC candidate workflow
- #34 merged: memory-bounded/cgroup-aware candidate batches; owner re-dispatch pending; checks out immutable PR #6 integration commit 819f8b4028469cb0d498098fec88545a18ebacc6

PR #6 remains open and must not be merged to main without explicit owner approval. PR #8 remains parked.

## Release and capital-risk guardrails

- No data source currently passes the complete acceptance gate for investment scoring.
- Stage 4 remains exploratory; the 2023-10-31 through 2024-03-31 fold reporting +240.89% requires asset-level attribution from the exact original input dataset.
- Do not inspect or tune against the locked final holdout.
- A local Runner/checksum/workflow success does not approve a source, backtest, ranking, probability or investment recommendation.
- No production scoring, broker access, portfolio allocation or real-money trade is authorized. Any capital-risk action requires separate explicit owner approval.


## Infrastructure-first status — 2026-11-06

- Priority issue: [#49](https://github.com/yarsalam/marketsage/issues/49). Ordinary MarketSage product/data/research work is paused until the provider-independent execution system is proven.
- Current main: `07e641670ceab22496ef976a584934464570fd9a`. Current integration PR #6 head: `1d90726c593b0818982407c309ff13301798f5b3`. PR #14 is already merged into #6; PR #6 remains open and must not be merged to main without explicit owner approval.
- PR #50 exact head `9098f110f615d46adbfa49f37e644000b832feb0` has no valid CI result: run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919) and its bounded rerun failed before steps with runner ID 0. GitHub Actions usage/budget is at USD 0; no further hosted dispatch is permitted until quota reset is verified or separately authorized.
- PR #41 exact-head run [42063679856](https://github.com/yarsalam/marketsage/actions/runs/42063679856) passed all five jobs but remains open; it updates the main workflow pin and evidence/governance records. No local dispatch occurred.
- PR #51 exact-head run [42062133299](https://github.com/yarsalam/marketsage/actions/runs/42062133299) passed all five jobs but remains open; it is non-infrastructure data work and is paused.
- PR #48 merged into #6 at `1d90726c593b0818982407c309ff13301798f5b3`; the Stage 4 provenance change does not substitute for rerunning the exact local dataset.
- Active infrastructure branch: `infra/provider-neutral-control-plane-2026-11`; mirror-probe hardening is recorded in commit `82a0a6d1a3c2d4fc8c1232f6675d63bf9`. Its current work includes architecture/provider evaluation, task manifest/schema, in-memory lifecycle fixtures, runbook and mirror probe. No PR or CI run has been opened for it; the branch is intentionally outside the current hosted-CI push filters while the Actions budget is blocked.
- The local manifest/lifecycle tests have not run from a clean checkout because dependency bootstrap stopped before test discovery. Six new offline tests for the mirror probe passed in an isolated temporary harness only; actual owner-network reachability remains unverified.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) records the exact owner action to run the bounded HTTPS-only mirror probe on the actual worker network and return its sanitized output/exit code.
- No paid provider, Oracle workaround, private-code transfer, merge, deployment, investment scoring, backtest approval or trading is authorized.

**Infrastructure readiness:** NOT PROVEN. Do not label the system 24/7-ready until durable queue/outbox, leases/heartbeats/fencing, dispatch reconciliation, worker-loss recovery, provider failover without duplicate side effects, budget stops, observable health/stuck-run detection and a clean end-to-end canary are demonstrated.


### Additional infrastructure validation and observability findings — 2026-11-06

- `infra/control_plane/lifecycle.py` and `test_lifecycle.py`: 9/9 tests passed in an isolated temporary harness. This is not a clean checkout or durable coordinator acceptance. `test_manifest` remains unexecuted because the `jsonschema` dependency bootstrap failed.
- `test_probe_package_mirrors.py`: 6/6 offline tests passed in an isolated temporary harness. Actual owner-network mirror probe remains tracked by [Issue #52](https://github.com/yarsalam/marketsage/issues/52).
- PR #50's failure-notification job is in the same GitHub Actions runner pool. Run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919) shows the notifier failed before steps with the other jobs, so it cannot report a pool-wide allocation outage. Independent health monitoring must run on a separately verified execution path.


- The Python mirror probe rejects non-HTTPS/user-info URLs, rejects redirect downgrades, and caps each package page at one HTTPS redirect (12 initial requests; at most 24 total). Nine offline tests passed in an isolated harness only. Owner-network probe remains pending Issue #52.


### Additional owner-action handoff — 2026-11-06

- [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is the owner-only verification gate for GitHub Actions included-minute availability, reset date, repository/account enablement and the current USD 0 spending cap. It explicitly requests no spend increase, plan change or visibility change. Do not dispatch or rerun hosted workflows until the owner confirms that a zero-cost included allowance is available and authorizes one bounded exact-head validation attempt.


### Live GitHub Actions audit — 2026-11-06 16:05 UTC

- The default-branch `.github/workflows/ci.yml` still has only push and pull-request triggers; it has no schedule, concurrency guard or explicit job timeouts. The proposed daily schedule in PR #50 is therefore **not active** on main. The Actions API returned no scheduled workflow runs.
- PR #50 exact head `9098f110f615d46adbfa49f37e644000b832feb0` has not produced a valid test result. Run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919), attempt 2, shows all five hosted test/build jobs and the failure reporter ended before step 1 with runner ID 0 and zero steps; production-images was skipped. This is runner allocation/capacity evidence, not a code-level test result.
- The failure reporter cannot report a pool-wide outage because it shares the same hosted runner pool. Do not dispatch/rerun hosted Actions until the owner completes [Issue #53](https://github.com/yarsalam/marketsage/issues/53); keep the zero-dollar spend boundary unchanged.
- PR #14 is already merged into integration PR #6. PR #6 remains open and must not be merged to main without explicit owner approval. PR #8 remains parked; its GitHub-hosted TSETMC timeout must not be repeated from the same environment.


### Infrastructure branch evidence — 2026-11-06

- Active branch: `infra/provider-neutral-control-plane-2026-11`; latest verified state includes the lifecycle identity-collision correction and regression test.
- The exact `lifecycle.py` and `test_lifecycle.py` files passed 10/10 in a temporary isolated harness (exit 0). This is not a clean checkout, CI, durable queue, or restart-recovery proof.
- No PR has been opened for this branch because the manifest/lifecycle clean-checkout gate is not complete. Do not trigger hosted Actions while the zero-cost quota status is unresolved.
- Owner handoffs: [Issue #52](https://github.com/yarsalam/marketsage/issues/52) for actual worker-network mirror probing; [Issue #53](https://github.com/yarsalam/marketsage/issues/53) for GitHub Actions included-minute/account restriction verification without changing the USD 0 spending cap.


- Follow-up lifecycle hardening on the infrastructure branch: task-ID collisions now fail closed, and terminal failure publication is fenced by the current lease owner/token. Exact lifecycle tests passed 11/11 in a temporary isolated harness (source/test commit `0ad3e7323a7e20779017a47854f33c1b21c6321d`); no clean-checkout or CI result is claimed. No PR opened and no hosted Actions dispatch performed.


### Infrastructure-first audit — 2026-11-07

- Main remains at `07e641670ceab22496ef976a584934464570fd9a` (latest commit message: sanitized local TSETMC diagnostics). The branch API reports `protected=false`; required status checks are not enforced.
- Main's current `.github/workflows/ci.yml` still has push/PR triggers only, hosted `ubuntu-latest` jobs, and repository-wide `contents: read`. It has no schedule, concurrency group or explicit job timeouts. The three local TSETMC workflows remain manual-only and self-hosted.
- PR #50 remains open, non-draft and mergeable at head `9098f110f615d46adbfa49f37e644000b832feb0`. Exact-head run `42176190919` (attempt 2) failed before any steps started: six jobs failed with no step records; `production-images` was skipped. This is consistent with a runner-allocation failure and is not a code-test result or proof of a billing cause. Earlier head run `42065906808` passed all seven jobs, but it does not validate the current head.
- PR #41, #51, #8 and #6 remain open; the current repository search returned five open PRs total. PR #41 and #51 have recorded successful exact-head CI runs; #8 remains parked after the known hosted TSETMC timeout; #6 remains unmerged and requires separate explicit owner approval. No PR was merged.
- Provider-neutral infrastructure branch: `infra/provider-neutral-control-plane-2026-11`. Provider landscape was revalidated from official pricing/limits pages and updated at commit `1ef5aa0d863685e75289a787737b10c498e92f2e`. The update corrects the Buildkite Free allowance, confirms CircleCI's Free quota and GitLab's 400 hosted-runner minutes, and evaluates Cloudflare Workers/D1/Queues as a metadata/control-plane candidate only—not a build runner. Google Cloud e2-micro is too constrained for primary CI and requires a billing account; Temporal Cloud credits are time-limited.
- The Oracle Free Tier signup returned a provider compliance/export notice. Treat Oracle as unavailable unless its official compliance process clears the account; no VPN, identity, address, region or account workaround is permitted.
- Owner gates remain: Issue #52 for a real-network HTTPS mirror probe (exact script commit `99b25dc24daa8606514bd9910e883ef136cf5d7f`) and Issue #53 for remaining account-level Actions restriction details. No hosted Actions dispatch/rerun, paid activation, private-code transfer, PR opening, merge, deploy or local workflow dispatch was performed in this audit.
- Infrastructure readiness remains **NOT PROVEN**. The coordinator is still a test fixture, not a durable queue/outbox or running independent control plane; no clean-checkout manifest/lifecycle test, process-restart recovery, cross-provider failover or external health canary has been demonstrated.


## Owner-action handoffs

- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) — Chabokan-only isolated wheel installation and hash-locked dependency validation. Novin-only installation and 28/28 tests passed on the recorded prior commit.
- [Issue #53](https://github.com/yarsalam/marketsage/issues/53) — verify included GitHub Actions minutes, reset and account/repository restrictions without changing the USD 0 spending cap. Hosted dispatch remains paused.
- [Issue #55](https://github.com/yarsalam/marketsage/issues/55) — run the exact current PR #54 head and confirm all 16 SQLite coordinator tests; prior 11/11 evidence applies only to the preceding commit.

## Infrastructure checkpoint — 2026-11-07

- PR #54 current head `e8f7d8add3df577120b92b8927c590aece001509` adds fenced lease renewal and five tests to the 11-test SQLite coordinator baseline. Current-head execution is pending; no CI result is claimed.
- The SQLite coordinator is a single-host persistence increment, not an operating control plane. Provider dispatch, transactional outbox, worker service, periodic heartbeat, health/stuck-run monitor, restart orchestration, backup/restore, disk-full/corruption recovery, independent canary and end-to-end failover remain unproven.
- Main remains `07e641670ceab22496ef976a584934464570fd9a`; PR #50's schedule/concurrency changes are not active until safely merged. Its current exact head lacks a valid hosted CI result because jobs failed before starting. No further hosted dispatch is allowed before Issue #53 is resolved.
- PR #14 is already integrated into PR #6. PR #6 remains unmerged to main pending explicit owner approval. PR #8 remains parked. Ordinary data/research PRs remain paused while Issue #49 is the first priority.
- No paid usage, external provider registration, local workflow dispatch, production deployment, investment scoring, broker access, trading or capital allocation was performed.

## Live infrastructure integration checkpoint — 2026-11-08

This section supersedes older status snapshots above when they conflict with current GitHub state.

| PR | Current role | Exact evidence / handling |
|---|---|---|
| [#74](https://github.com/yarsalam/marketsage/pull/74) | Draft integration of the provider-neutral control-plane base into main | This merge commit reconciles integration source `2776d9c6e17d24d09a809c07549100e4f2c3c2ae` with main `4c4b032196137af4658ea2c28e38a21605ee923b`. Keep Draft until exact-head PR CI and complete diff review pass. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | Durable outbox, orchestrator, Docker Worker, daemon and Watchdog follow-up stacked on the integration branch | Head `0afb73c43dfbb0726f42d33f87e09966aa1254a9`; exact PR CI passed 164/164 control-plane tests and hosted Docker worker acceptance passed. Rebase/reconcile this stacked PR against the newly updated base, then re-run exact-head checks. Keep Draft. |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | Parallel workstream decomposition documentation | Draft and stacked on the integration branch; refresh/reconcile its base before review. |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | Market Coverage Workspace product increment | Draft; ordinary product dispatch remains gated by Issue #49. Its earlier exact-head CI success does not authorize merge. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | Existing integrated data-source work | Open; never merge to main without the owner's separate explicit approval. |

- PR #50 CI hardening and PR #70 direct-main provenance detection are already included in main commit `4c4b032...`; do not recreate them as duplicate PRs.
- Main's successful scheduled run is [42471588681](https://github.com/yarsalam/marketsage/actions/runs/42471588681). The direct-main detector is detection only.
- Active main ruleset #26789479 requires PRs and seven checks and blocks deletion/non-fast-forward updates; 10 approving reviews remain to be corrected by the owner.
- Issue #49 remains OPEN. The current PR #71 tests prove deterministic fake-backend/outbox behavior, not external provider independence, continuous server availability or 24-hour resilience.
- No auto-merge, release, deployment, paid resource, local workflow dispatch, provider activation, market-data source approval, investment scoring, broker or trading permission is granted.


## Live open-PR inventory — 2026-11-13 14:49 UTC

This inventory supersedes the earlier open-PR table above. All rows are open; mergeability is the live PR API result, not merge authorization. Exact-head checks are read from the current head SHA. A skipped check is not a pass.

| PR | Draft | Base ref | Exact head SHA | Mergeable | Exact-head checks |
|---|---:|---|---|---:|---|
| [#82](https://github.com/yarsalam/marketsage/pull/82) | yes | `main` | `880a1b1d683b4c3992743c5f046be2c80920c7cf` | yes | 16; all successful across Push/PR; non-infrastructure research hold; old main CI ran analysis and production-image jobs |
| [#81](https://github.com/yarsalam/marketsage/pull/81) | yes | `main` | `a659fa038dc84b000c5a01b20b234d5e31f54ff3` | yes | 8; all completed successful |
| [#80](https://github.com/yarsalam/marketsage/pull/80) | yes | `main` | `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | yes | 8; all completed successful |
| [#79](https://github.com/yarsalam/marketsage/pull/79) | yes | `main` | `14001bdb5a03775b9772bf9cfea1d169a68f8113` | yes | 8; all completed successful |
| [#78](https://github.com/yarsalam/marketsage/pull/78) | yes | `main` | `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | yes | 10; all completed successful |
| [#77](https://github.com/yarsalam/marketsage/pull/77) | yes | `main` | `67356939f65224a580c915fd2caa0ea52d8d09a9` | yes | 8; all completed successful |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | yes | `main` | `24b95c204749b74ba2f382f4dd528d6463173dc9` | yes | 20 records across exact Push and PR runs; infra checks passed; product checks skipped |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | yes | `main` | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | yes | 16; all completed successful |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | yes | `infra/provider-neutral-control-plane-2026-11` | `e630517c7e2916ed58b7568b0ebbbf1d390b86ce` | yes | **0 checks / 0 workflow runs**; 117 ahead / 2 behind current base; stale and unvalidated |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | no | `main` | `54fbf4a364a91b4e8d834fdcec0245d079440982` | yes | 8; all completed successful |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | yes | `infra/provider-neutral-control-plane-2026-11` | `25ce24283e35dd7e55eb8545c590a047606643ee` | no | **0 checks**; non-mergeable |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | no | `feat/tindex-free-data-connector` | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | yes | 10; all completed successful; ordinary data work remains frozen |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | no | `main` | `162692f1a377ec8445ed958db4cc1171d4cafc47` | yes | 5; all completed successful |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | no | `fix/gdelt-fred-tindex-current-docs` | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | yes | 6; `tsetmc-smoke` failed, five other checks succeeded; keep parked and do not repeat the same timeout request |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | no | `main` | `1d90726c593b0818982407c309ff13301798f5b3` | no | 15; all completed successful; **never merge without separate explicit owner approval** |

### Closed infrastructure PR retained for reference

- [PR #54](https://github.com/yarsalam/marketsage/pull/54): closed, Draft, unmerged; exact head `e8f7d8add3df577120b92b8927c590aece001509`; no GitHub check runs. [Issue #55](https://github.com/yarsalam/marketsage/issues/55) records 16/16 owner-run tests on this exact head (exit 0). Current base comparison is 8 ahead / 46 behind, merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`; prior 11/11 evidence applies only to its earlier commit.

### Current workflow evidence and owner gates

- Main HEAD remains `4c4b032196137af4658ea2c28e38a21605ee923b`. Latest successful default-branch schedule is [#43414337932](https://github.com/yarsalam/marketsage/actions/runs/43414337932), 2026-11-13, but it ran analysis, backend, frontend, admin, production-image and CI-helper jobs about 7h49m after cron. It is not a worker canary.
- PR #74 exact-head Push [#43379843888](https://github.com/yarsalam/marketsage/actions/runs/43379843888) and PR [#43379849607](https://github.com/yarsalam/marketsage/actions/runs/43379849607) both succeeded on `24b95c204749b74ba2f382f4dd528d6463173dc9`. This does not validate PR #71.
- [Issue #49](https://github.com/yarsalam/marketsage/issues/49) remains open. [Issue #52](https://github.com/yarsalam/marketsage/issues/52) remains open for five Chabokan wheel hashes. [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is closed by the public zero-additional-spend decision. [Issue #55](https://github.com/yarsalam/marketsage/issues/55) is closed for exact-head SQLite unit tests only. [Issue #59](https://github.com/yarsalam/marketsage/issues/59) remains open for schedule/orchestration acceptance.
- No hosted workflow was dispatched or rerun; no local workflow, Runner, or Provider was activated. No merge, release, deployment, secret, paid resource, or visibility change occurred.
- Main still lacks the Goal 1 CI freeze. PR #74 contains it but remains Draft/open. PR #71 is stale/unvalidated and remains Draft/open. No 24/7 claim is permitted.


## Live open-PR and exact-head inventory — 2026-11-14 14:19 UTC

This inventory supersedes the 2026-11-13 inventory above. GitHub currently reports 15 open PRs: 14 owner-authored PRs plus Dependabot PR #62. Draft/state/base/head/mergeability values below are from the current PR metadata surface where available. The combined-status endpoint returned no legacy status contexts for the inspected heads; the run evidence below is from the PR-triggered workflow-run lookup for each exact SHA (first page only).

| PR | Draft | Base | Exact head SHA | Mergeable | Exact-head PR-event evidence / handling |
|---|---:|---|---|---:|---|
| [#82](https://github.com/yarsalam/marketsage/pull/82) | yes | main | `0be59fc582e5e782fed2be2cdd6c3b39fab55940` | yes | PR run [#43447301963](https://github.com/yarsalam/marketsage/actions/runs/43447301963) success; research scope hold remains; do not advance while #49 is open |
| [#81](https://github.com/yarsalam/marketsage/pull/81) | yes | main | `a659fa038dc84b000c5a01b20b234d5e31f54ff3` | yes | PR runs #42672784044 success and #42672784245 failure; the retrieved job summary for the failed run exposed successful jobs/steps only; no rerun initiated |
| [#80](https://github.com/yarsalam/marketsage/pull/80) | yes | main | `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | yes | PR run #42644847236 success; product scope remains paused |
| [#79](https://github.com/yarsalam/marketsage/pull/79) | yes | main | `14001bdb5a03775b9772bf9cfea1d169a68f8113` | yes | PR run #42643250744 success; product scope remains paused |
| [#78](https://github.com/yarsalam/marketsage/pull/78) | yes | main | `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | yes | PR runs #42644297705 and #42644297868 success; product/strategy scope remains paused |
| [#77](https://github.com/yarsalam/marketsage/pull/77) | yes | main | `67356939f65224a580c915fd2caa0ea52d8d09a9` | yes | PR run #42624038512 success; product scope remains paused |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | yes | main | `b7ec545b83e370faaeeaf8960f4bf4ea70d43018` | yes | **0 exact-head PR runs / 0 combined-status entries**. Prior code head `24b95c204749b74ba2f382f4dd528d6463173dc9` passed Push #43379843888 and PR #43379849607; not transferable |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | yes | main | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | yes | PR run #42621965739 success; product/research scope remains paused |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | yes | infra/provider-neutral-control-plane-2026-11 | `e630517c7e2916ed58b7568b0ebbbf1d390b86ce` | no | **0 exact-head PR runs / 0 combined-status entries**; current compare with #74: 117 ahead / 4 behind, diverged; reconcile only after owner gate and then revalidate |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | no | main | `54fbf4a364a91b4e8d834fdcec0245d079440982` | not exposed | PR run #42408717730 success; exact head is Dependabot's actions/checkout 7.0.1 update; live mergeability was not returned by the connected PR metadata surface |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | yes | infra/provider-neutral-control-plane-2026-11 | `25ce24283e35dd7e55eb8545c590a047606643ee` | no | 0 exact-head PR runs / 0 combined-status entries; non-mergeable |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | no | feat/tindex-free-data-connector | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | yes | PR run #42062133299 success; ordinary data work remains frozen |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | no | main | `162692f1a377ec8445ed958db4cc1171d4cafc47` | yes | PR run #42063679856 success; data/research scope remains frozen |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | no | fix/gdelt-fred-tindex-current-docs | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | yes | No PR-event run returned for this exact head. Keep parked after the known TSETMC ConnectTimeout; do not repeat from the same environment |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | no | main | `1d90726c593b0818982407c309ff13301798f5b3` | no | PR run #42061367000 success; **never merge to main without separate explicit owner permission** |

### Current integration and SQLite branch relationships
- PR #74 is Draft/open, 77 ahead / 0 behind main at head `b7ec545b83e370faaeeaf8960f4bf4ea70d43018`. The current head has no exact-head workflow evidence.
- PR #71 is Draft/open, non-mergeable, 117 ahead / 4 behind the current PR #74 head; merge base `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10`. Its current head has no exact-head workflow evidence.
- PR #54 is **closed, Draft, unmerged** at `e8f7d8add3df577120b92b8927c590aece001509`. Issue #55 records 16/16 exact-head owner tests, exit 0; no GitHub check runs exist for this closed PR head. Comparing that SHA with PR #74 reports 8 ahead / 48 behind, merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`.
- The separate `infra/sqlite-durable-coordinator-reconciled-2026-11` branch is still diverged from PR #74: 3 ahead / 23 behind, merge base `a02946bd1fa524dbf1bd6e104b15bad224345b1b`. Do not treat the 16-test result as branch-integration or operational evidence.

### Workflow audit — current main versus infrastructure branch
- Main `.github/workflows/ci.yml`: push/PR/schedule/manual triggers; daily cron `17 3 * * *`; `ubuntu-latest`; workflow-level `contents: read`; per-ref concurrency and cancellation; timeouts 25/30/30/30/40/5/5 minutes; no explicit retry policy, stale-run observer, artifact upload or custom retention. Sanitized failure/provenance notifications use job-scoped `issues: write` but execute in the same GitHub-hosted runner pool.
- Main still runs analysis/research-backtest, backend, frontend, admin and production-image jobs. The Goal 1 freeze exists only on the PR #74 branch and is not active on main.
- Last confirmed main schedule: [#43414337932](https://github.com/yarsalam/marketsage/actions/runs/43414337932), 2026-11-13, success. It ran the five product/research/build job classes and was recorded as starting about 7h49m after the 03:17 UTC cron. No complete repository run-listing API is exposed by the current connected tool surface; the 2026-11-14 scheduled event is not independently confirmed.
- PR #74 `ci.yml` adds fail-closed scope classification and provider-neutral tests; non-infrastructure scopes fail before product commands. Its daily schedule is not active until this branch reaches main. Its failure notifier excludes pull_request events.
- PR #71 Docker canary is branch-only (not on main), configured for main push, daily 04:43 UTC and manual dispatch, with `ubuntu-latest`, 15-minute timeout, concurrency cancellation and a no-network sandbox. Its failure notifier shares the GitHub-hosted pool.
- PR #71 self-hosted acceptance is manual-only, owner/confirmation/exact-branch guarded, requires `marketsage-server-worker`, timeout 20 minutes, and non-cancelling serialization. No independent server runner is registered or proven online. Failure notification uses `ubuntu-latest`, not an external alert provider.
- Health observer code is deterministic/read-only assessment only; no independent polling service, alert delivery, observer HA or restart/outage drill is proven. CircleCI config has no real connected project/run. SQLite remains single-host. No 24-hour observation or end-to-end second-provider canary is proven.
- The infrastructure dependency manifest remains un-hash-locked; Issue #52 contains the existing owner action for five Chabokan wheel hashes. Issue #53 is closed (zero-cost public-hosted CI decision); Issue #55 is closed (16/16 exact-head SQLite tests); Issue #59 remains open.

### Protection, cost and owner gates
- The latest active-branch state document records ruleset #26789479 as active but reports 10 required approvals; an earlier live audit reported one. The current connector has no ruleset/branch-protection read action, so current approvals, required contexts, bypass behavior and human merge gate are BLOCKED for fresh verification.
- Repository metadata reports Public, conflicting with the current request's "private" description. Do not change visibility; owner confirmation remains in Issue #49.
- Issue #49 already records the owner action to authorize one bounded exact-head hosted validation. Issue #53 is closed, but no separate authorization for a new hosted run was given in this execution; do not dispatch/rerun.
- No local dispatch, hosted dispatch/rerun, merge, auto-merge, release, deployment, provider registration, secret creation, spending, visibility change or product/data/investment work occurred.
- This register is a live snapshot from the connected surfaces, not a complete Actions run-history export. Empty combined-status responses are not proof of success.



## Live PR audit — 2026-11-15 14:47 UTC

This snapshot supersedes older PR status rows above for current open/closed state, base/head, mergeability and exact-head checks. GitHub Check Run counts refer to the exact HEAD SHA and count duplicate contexts from separate events.

| PR | State | Draft | Base | Head SHA | Mergeable | Exact-head Check Runs |
|---|---|---:|---|---|---:|---|
| [#82](https://github.com/yarsalam/marketsage/pull/82) | open | yes | main | `1cdeb07f10d1b5bbc56ff519d50835cff8c0aa6e` | yes | 20: 14 success, 4 skipped, 1 queued, 1 cancelled |
| [#81](https://github.com/yarsalam/marketsage/pull/81) | open | yes | main | `8d49042b520b78a877a5032bb9cf2e6f45e6169e` | yes | 17; success/skipped only |
| [#80](https://github.com/yarsalam/marketsage/pull/80) | open | yes | main | `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | yes | 8: 6 success, 2 skipped |
| [#79](https://github.com/yarsalam/marketsage/pull/79) | open | yes | main | `14001bdb5a03775b9772bf9cfea1d169a68f8113` | yes | 8: 6 success, 2 skipped |
| [#78](https://github.com/yarsalam/marketsage/pull/78) | open | yes | main | `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | yes | 10: 8 success, 2 skipped |
| [#77](https://github.com/yarsalam/marketsage/pull/77) | open | yes | main | `67356939f65224a580c915fd2caa0ea52d8d09a9` | yes | 8: 6 success, 2 skipped |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | open | yes | main | `52e8191e58306c15a0073da0148cf155c0fcf384` | yes | 0; no exact-head validation |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | open | yes | main | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | yes | 16: 12 success, 4 skipped |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | open | yes | PR #74 | `e630517c7e2916ed58b7568b0ebbbf1d390b86ce` | no | 0; 117 ahead / 6 behind current base |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | open | no | main | `54fbf4a364a91b4e8d834fdcec0245d079440982` | yes | 8: 6 success, 2 skipped |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | open | yes | PR #74 | `25ce24283e35dd7e55eb8545c590a047606643ee` | no | 0 |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | open | no | PR #6 | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | yes | 10: all success |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | open | no | main | `162692f1a377ec8445ed958db4cc1171d4cafc47` | yes | 5: all success |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | open | no | `fix/gdelt-fred-tindex-current-docs` | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | yes | 6: 5 success, 1 failed (`tsetmc-smoke`); parked |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | open | no | main | `1d90726c593b0818982407c309ff13301798f5b3` | no | 15: all success; do not merge without separate explicit owner approval |

### Infrastructure PRs and related closed PR
- [PR #74](https://github.com/yarsalam/marketsage/pull/74) is the existing infrastructure integration path. Its current head has no checks; the previous code-head results do not transfer.
- [PR #71](https://github.com/yarsalam/marketsage/pull/71) contains the existing durable outbox/worker/watchdog work. It is based on #74 but diverged (117 ahead / 6 behind; merge base `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10`) and has no exact-head checks. Do not create a duplicate worker/observer PR; do not merge.
- [PR #54](https://github.com/yarsalam/marketsage/pull/54) is **closed, Draft, unmerged** at `e8f7d8add3df577120b92b8927c590aece001509`. Issue #55 records 16/16 owner-run tests on this exact SHA; prior 11/11 belongs to an earlier commit. The SQLite branch is 8 ahead / 50 behind #74, diverged from merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`; it has zero GitHub check runs. Keep closed/unmerged.
- PR #14 is already integrated into #6; no repeat merge. PR #8 remains parked; do not repeat the known TSETMC timeout request.

### Current run evidence relevant to Goal 1
- Default-branch scheduled CI: [#43706919338](https://github.com/yarsalam/marketsage/actions/runs/43706919338), 2026-11-15, success on main `4c4b032196137af4658ea2c28e38a21605ee923b`; it executed analysis/research-backtest, backend, frontend, admin, and production-image jobs. It is not an infrastructure-only schedule.
- PR #82 exact head `1cdeb07f10d1b5bbc56ff519d50835cff8c0aa6e`: MarketSage CI Push [#43715142643](https://github.com/yarsalam/marketsage/actions/runs/43715142643) and PR [#43715149785](https://github.com/yarsalam/marketsage/actions/runs/43715149785) succeeded, but ran out-of-scope product/research jobs. Separate Iran Equity Evidence Integrity run [#43715149800](https://github.com/yarsalam/marketsage/actions/runs/43715149800) remains queued for `historical-market-state` with no steps; record as queued/stale observation, not code failure.
- The PR #82 Goal 1 scope hold was reaffirmed in comment [#6890753010](https://github.com/yarsalam/marketsage/pull/82#issuecomment-6890753010), but the branch advanced again afterwards. It remains Draft/open/unmerged; no research approval is implied.
- Active main ruleset #26789479 currently reports one required approving review and seven required checks, no bypass actors, strict status freshness disabled, and stale-approval dismissal disabled. Legacy branch-protection read returned 403.

### Owner actions and stop conditions
- Issue #49 remains open. Existing owner actions: confirm the public/private visibility intent and separately authorize one bounded exact-head hosted validation when ready. No dispatch or rerun occurred.
- Issue #52 remains open for five Chabokan wheel SHA-256 values; no repeated install/test.
- Issue #53 is closed (public/zero-additional-spend decision). Issue #55 is closed (16/16 exact-head SQLite test only). Issue #59 remains open for orchestration acceptance.
- No local/hosted dispatch or rerun, merge, auto-merge, release, deployment, provider registration, secret creation, spending, visibility change, or product/data/investment work occurred.

**Issue #49: OPEN / NOT COMPLETE / NOT 24/7 READY.**


## Current owner priority checkpoint — 2026-11-16 07:30 UTC

- **Goal 1 only:** infrastructure, governance and synthetic tests. Goal 2/3 remain paused.
- **PR #74:** Draft/open/unmerged; current head requires a separately authorized exact-head hosted validation after the governance correction. Do not infer success from earlier SHAs.
- **PR #71:** Draft/open; branch comparison is diverged (117 ahead / 118 behind its PR #74 base). No automatic reconciliation or merge.
- **PR #82:** Draft/open; research/data scope remains on hold. No additional commits, review request, data/analysis workflow, or merge.
- **PR #6:** open; never merge without separate explicit owner approval.
- **main:** still runs product/research/production jobs on Schedule; the freeze is not yet active on the default branch.
- No workflow dispatch/rerun, local Runner operation, provider request, data acquisition, merge, deployment, secret, spending or visibility change is authorized in this checkpoint.

