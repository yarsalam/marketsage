# MarketSage — Pull Request Register

## Live repository / PR audit — 2026-11-11 14:51 UTC (authoritative)

Read-only GitHub state. This section supersedes the older snapshots below. No workflow was dispatched or rerun and no local runner was used in this audit.

- Repository visibility: `public` / `private=false` (owner confirmation remains in [Issue #49](https://github.com/yarsalam/marketsage/issues/49)); no visibility change.
- Default branch `main`: `4c4b032196137af4658ea2c28e38a21605ee923b`, committed 2026-11-07 19:55:51 UTC.
- Active ruleset [#26789479](https://github.com/yarsalam/marketsage/rules/26789479): PR required, one approval, seven required contexts, deletion/non-fast-forward blocked, no bypass actors; strict status freshness false and stale approvals not dismissed. Legacy branch-protection API returned 403.
- Main CI triggers: push, pull_request, daily schedule `17 3 * * *`, workflow_dispatch. Default permission `contents: read`; issue-write is job-scoped. Per-PR/ref concurrency cancels superseded runs; job timeouts are explicit. No workflow-level retry, independent stale/queued-run observer, external notification outside the hosted pool, custom artifact-retention override or CI artifact upload was found. The failure notifier shares the GitHub-hosted runner pool.
- Main's current `ci.yml` lacks the required context `Test provider-neutral control plane` even though the ruleset requires it. The context is supplied on infrastructure PR #74/#71; main-derived PRs without another provider for that context remain blocked.
- Main scheduled CI run [#43008951957](https://github.com/yarsalam/marketsage/actions/runs/43008951957) succeeded on exact main SHA `4c4b032...` on 2026-11-11, starting 11:04:56 UTC (about 7h48 after the 03:17 UTC cron). This is scheduled CI evidence, not a scheduled worker canary or punctuality proof.

### All currently open pull requests (live API snapshot)

| PR | State / draft | Base ← head | Mergeability | Exact-head checks / handling |
|---|---|---|---|---|
| [#81](https://github.com/yarsalam/marketsage/pull/81) | open / Draft | `main` ← `a659fa038dc84b000c5a01b20b234d5e31f54ff3` | mergeable; blocked | MarketSage CI push/PR runs #42672776200, #42672784245 failed; Project Operating System push run #42672776329 also failed, while its PR run #42672784044 succeeded. Product/auth work frozen. |
| [#80](https://github.com/yarsalam/marketsage/pull/80) | open / Draft | `main` ← `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | mergeable; blocked | Exact run #42644847236: 6 success, 2 skipped. Product/admin work frozen. |
| [#79](https://github.com/yarsalam/marketsage/pull/79) | open / Draft | `main` ← `14001bdb5a03775b9772bf9cfea1d169a68f8113` | mergeable; blocked | Exact run #42643250744: 6 success, 2 skipped. Product/auth work frozen. |
| [#78](https://github.com/yarsalam/marketsage/pull/78) | open / Draft | `main` ← `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | mergeable; blocked | Exact Project Operating System/CI runs #42644297705, #42644297868, #42644283033 completed successfully. Its schedule is not active on main. |
| [#77](https://github.com/yarsalam/marketsage/pull/77) | open / Draft | `main` ← `67356939f65224a580c915fd2caa0ea52d8d09a9` | mergeable; blocked | Exact run #42624038512 completed; provider-neutral control-plane required context is absent. No action outside infrastructure scope. |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | open / Draft | `main` ← `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10` | mergeable; blocked | 73 ahead / 0 behind main. Exact push #42589280185 and PR #42589290385 succeeded; 110 control-plane tests and CI helper tests passed; product jobs scope-skipped. Parent infrastructure PR; no merge. |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | open / Draft | `main` ← `72c57608e8270d999d1e9f2005b47ea56cb893a7` | mergeable; blocked | Exact push #42621957914 and PR #42621965739 succeeded. Research/data work frozen. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | open / Draft | `infra/provider-neutral-control-plane-2026-11` ← `ad0f07d0d3b2a1a195857030274dcb254d82b03f` | mergeable; clean | 111 ahead / 0 behind base #74. Exact push #42980157072 and PR #42980163912 succeeded; 174 control-plane tests and 36 CI helper tests passed; product jobs scope-skipped. No Docker acceptance on this current head. Keep Draft; no merge. |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | open / ready | `main` ← `54fbf4a364a91b4e8d834fdcec0245d079440982` | mergeable; blocked | Exact run #42408717730: 6 success, 2 skipped; provider-neutral required context absent. No action in this infrastructure task. |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | open / Draft | `infra/provider-neutral-control-plane-2026-11` at `7d0736f47cd19344233973d31fb1c1b4d1a3a95f` ← `25ce24283e35dd7e55eb8545c590a047606643ee` | not mergeable; dirty | Zero exact-head check runs. Keep draft; no duplicate docs branch. |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | open / ready | `feat/tindex-free-data-connector` ← `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | mergeable; clean | 10/10 exact-head check runs successful. Research/data work frozen. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | open / ready | `main` at `3d4e2a97da70ae5564a5252048fcb2e2971bd6e5` ← `162692f1a377ec8445ed958db4cc1171d4cafc47` | mergeable; blocked | 5/5 exact-head checks successful. Data/evidence work frozen. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | open / ready | `fix/gdelt-fred-tindex-current-docs` ← `0cb94fd24f531162d4a3d403f9749789ce6f1797` | mergeable; unstable | 5/6 exact-head checks passed; `tsetmc-smoke` failed by prior ConnectTimeout (run #39261959033). Parked; do not repeat the same request from the same environment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | open / ready | `main` at `07f2e968257ef868a5efbab36f379ee487658577` ← `1d90726c593b0818982407c309ff13301798f5b3` | not mergeable; dirty | 15/15 listed exact-head checks successful, but base/head are dirty/diverged. Never merge without separate explicit owner approval. PR #14 is already integrated into #6. |

### Closed SQLite reference and owner gates

- PR #54 is **closed, Draft, unmerged**; head `e8f7d8add3df577120b92b8927c590aece001509`, with zero GitHub check runs. Issue #55 records 16/16 owner-run tests on that exact SHA. Compared with current #74 head, the branches are diverged (PR #74 is 44 commits ahead; PR #54 contains 8 commits not on #74; merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`). No merge/reopen.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) remains open for the five exact Chabokan wheel SHA-256 hashes; do not repeat the 30/30 install/test run.
- [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is closed: public-repository standard hosted CI was selected as the zero-additional-spend path; no spending-cap increase or paid runner.
- [Issue #55](https://github.com/yarsalam/marketsage/issues/55) is closed after the exact-head 16/16 SQLite unit validation. This does not prove distributed or operational recovery.
- [Issue #49](https://github.com/yarsalam/marketsage/issues/49) remains OPEN / NOT COMPLETE. Visibility confirmation is still an owner action. The exact PR #71 code-head push/PR validation already completed via normal events; this audit did not dispatch or rerun anything.

### Issue #49 acceptance posture — NOT COMPLETE

| Criterion | Evidence | Status |
|---|---|---|
| Push/PR validation on exact head | PR #71 code head `ad0f07d...`; runs #42980157072 and #42980163912; 174 control-plane tests | PASS for this exact code head |
| Scheduled default-branch run | main run #43008951957, exact main SHA `4c4b032...` | PASS for scheduled CI only; worker schedule not active |
| Concurrency/queue/idempotency/retry/failure | deterministic coordinator/outbox/orchestrator tests, including restart, ambiguity, duplicate delivery, bounded provider attempts and no-effect failover | PARTIAL; fake adapters, not real provider side effects |
| Timeout/cancellation | workflow/job timeout and superseded-run cancellation are configured; unit-level task deadlines/cancellation exist | PARTIAL; no live failure-injection drill |
| Hung/stale-run detection | deterministic snapshot assessment and watchdog code | NOT PROVEN operationally; no independent poller |
| Two independent real backends | fake adapters only; CircleCI config not connected and no second provider registered | NOT PROVEN |
| Isolated worker | prior Docker canary #42507288970 on earlier SHA `7d7c6b1...`; current head has no Docker canary | PARTIAL |
| Worker-loss/restart recovery | unit tests and SQLite backup/restore tests | PARTIAL; no persistent-host loss/restart drill or off-host restore |
| Independent notification | self-hosted worker notifier uses hosted runner; CI notifier shares hosted pool | PARTIAL; no external observer for hosted-pool outage |
| Permissions/cost/runbook | read-only default, scoped issue-write, pinned Actions, bounded jobs, zero-cost decision and host/runbook docs | PARTIAL; wheel hashes and owner visibility confirmation remain |
| Human merge gate | active ruleset requires one review + seven contexts, no bypass; strict freshness false, stale approvals retained | PARTIAL; required context missing on main's current CI |
| 24-hour stability / end-to-end two-backend canary | no qualifying window or real second backend | NOT PROVEN |

No 24/7 readiness claim is permitted. No PR was merged, no provider/account/secret was registered, no hosted workflow was dispatched/rerun, no local workflow was dispatched, no paid resource was activated, and no product/data/investment work was performed in this audit.


## Historical automation evidence — 2026-11-09 (superseded by live audit above)

- Main `4c4b032196137af4658ea2c28e38a21605ee923b` has a successful scheduled run [42610905309](https://github.com/yarsalam/marketsage/actions/runs/42610905309) and push run [42408566585](https://github.com/yarsalam/marketsage/actions/runs/42408566585). The schedule was successful but started at 11:40 UTC for a 03:17 UTC cron.
- PR #71's last fully validated code head was `7d7c6b1d9eb97d6070651c8b5cda41db9753a78f`: 170 control-plane tests and a successful Docker sandbox acceptance. Later PR #71 changes intentionally carry `[skip ci]`; no exact-head result exists for them.
- PR #74 exact head `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10` passed 110 control-plane tests in run #42589290385.
- The active ruleset #26789479 requires one human approval and seven checks, blocks deletion/force-push, has no bypass actors, and does not require strict base freshness. The ruleset is active; the legacy branch-protection read is unavailable to the connected integration.
- `.github/workflows/ci.yml` uses push/PR/schedule/manual triggers, read-only default permissions, job-scoped issue-write permissions, per-ref concurrency cancellation, and job timeouts. It has no bounded workflow-level retry. Its failure reporter shares the GitHub-hosted runner pool.
- `docker-worker-acceptance.yml` is now daily and main-push-only; `self-hosted-worker-acceptance.yml` remains manual-only. The new static workflow-policy tests are not yet executed on the changed head.
- CircleCI configuration is present but no account/pipeline is connected. No independent failure observer or persistent worker service is active. Fake-adapter tests do not prove a live second backend.
- Issue #52: Chabokan-only install and 30 tests passed; exact wheel hashes remain outstanding. Issue #53 and #55 are closed. PR #54 is closed unmerged. Issue #63 is closed with the live ruleset verified.
- No 24/7 readiness claim is permitted. No merge, local dispatch, hosted dispatch/rerun, provider registration, secret creation, spending, release, deployment, or investment operation was performed.


**Snapshot date:** 2026-11-09  
**Repository:** yarsalam/marketsage (PUBLIC per live GitHub API; visibility confirmation tracked in Issue #49)  
**Main HEAD:** 4c4b032196137af4658ea2c28e38a21605ee923b  
**Infrastructure PRs:** #74 parent integration; #71 durable outbox/worker    
**Integration PR:** [#6](https://github.com/yarsalam/marketsage/pull/6), feat/tindex-free-data-connector  
**Pinned integration code HEAD:** 1d90726c593b0818982407c309ff13301798f5b3 (current PR #6 head; main local workflow remains pinned to 819f8b4028469cb0d498098fec88545a18ebacc6 until PR #41 is adopted)

## Open PRs — live API snapshot 2026-11-09

| PR | State / draft | Base ← head | Mergeability / divergence | Exact-head evidence | Handling |
|---|---|---|---|---|---|
| [#77](https://github.com/yarsalam/marketsage/pull/77) | open / draft | `main` ← `safety/research-only-output-gates-2026-11` | mergeable=true; blocked | [42624038512](https://github.com/yarsalam/marketsage/actions/runs/42624038512), exact head `67356939...`, all five required build/test jobs passed | Leave untouched; outside infrastructure scope. |
| [#74](https://github.com/yarsalam/marketsage/pull/74) | open / draft | `main` ← `infra/provider-neutral-control-plane-2026-11` | mergeable=true; blocked; 73 ahead / 0 behind main | [42589290385](https://github.com/yarsalam/marketsage/actions/runs/42589290385), exact head `237af3ba...`, 110 control-plane tests passed; broad jobs scope-skipped | Parent infrastructure PR; no merge. |
| [#73](https://github.com/yarsalam/marketsage/pull/73) | open / draft | `main` ← `research/market-coverage-workspace-2026-11` | mergeable=true; blocked | Push [42621957914](https://github.com/yarsalam/marketsage/actions/runs/42621957914) and PR [42621965739](https://github.com/yarsalam/marketsage/actions/runs/42621965739) passed on exact head `72c57608...` | Leave untouched; research work is frozen by current Issue #49 priority. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | open / draft | `infra/provider-neutral-control-plane-2026-11` ← `infra/durable-provider-dispatch-outbox-2026-11` | mergeable=true at API snapshot; compare showed 103 ahead / 11 behind base | Prior exact head `7d7c6b1...`: [42507293048](https://github.com/yarsalam/marketsage/actions/runs/42507293048) passed 170 tests; [42507288970](https://github.com/yarsalam/marketsage/actions/runs/42507288970) Docker worker canary passed. New config/test commits are not validated. | Keep draft. Reconcile base and obtain owner-authorized exact-head validation before review/merge. |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | open / ready | `main` ← Dependabot Actions update | mergeable=true; blocked | [42408717730](https://github.com/yarsalam/marketsage/actions/runs/42408717730), exact head `54fbf4a3...`, five required jobs passed | No auto-merge; no action in this infrastructure task. |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | open / draft | `infra/provider-neutral-control-plane-2026-11` ← `docs/parallel-workstream-decomposition-2026-11` | mergeable=null; unknown | No checks on exact head `25ce2428...` | Leave as draft; no duplicate documentation branch. |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | open / ready | `feat/tindex-free-data-connector` ← research candidate screen | mergeable=true; clean | [42062133299](https://github.com/yarsalam/marketsage/actions/runs/42062133299), exact head `da803a1c...`, five jobs passed | Leave untouched; data work is frozen. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | open / ready | `main` ← governance/evidence sync | mergeable=true; blocked | [42063679856](https://github.com/yarsalam/marketsage/actions/runs/42063679856), exact head `162692f1...`, five jobs passed | Documentation review only; no local dispatch. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | open / ready | `fix/gdelt-fred-tindex-current-docs` ← `research/iran-free-data-smoke` | mergeable=true; unstable | TSETMC smoke [39261959033](https://github.com/yarsalam/marketsage/actions/runs/39261959033) failed by connection timeout; older broad CI passed | Parked. Do not repeat the same live request from the same environment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | open / ready | `main` ← `feat/tindex-free-data-connector` | mergeable=false; dirty | Older exact-head CI passed on `1d90726c...`; current base/head divergence is unresolved | **Never merge without separate explicit owner approval.** |


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
| [#54](https://github.com/yarsalam/marketsage/pull/54) | Closed unmerged (draft); last head `e8f7d8add3df577120b92b8927c590aece001509`. Issue #55 records 16/16 exact-head SQLite tests. Newer SQLite/outbox/orchestrator code is in PR #71. |

## Current integration graph

main
- #27 merged: local staged-dataset validator
- #31 merged: governance adoption
- #32 merged: integrated local TSETMC candidate workflow
- #34 merged: memory-bounded/cgroup-aware candidate batches; owner re-dispatch pending; checks out immutable PR #6 integration commit 819f8b4028469cb0d498098fec88545a18ebacc6

PR #6 remains open and must not be merged to main without separate explicit owner approval. PR #8 remains parked. PR #54 is closed unmerged; its prior 16/16 validation does not validate the newer PR #71 head.

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

## Live GitHub register audit — 2026-11-08 (supersedes all older snapshots above)

**Live default branch:** `main`  
**Exact main HEAD:** `4c4b032196137af4658ea2c28e38a21605ee923b` (commit timestamp `2026-11-07T19:55:51Z`).  
**Repository visibility:** GitHub API reports `public`, not private. Issue #53 records a prior explicit owner decision to keep it public. The latest execution request calls it private; no visibility change was made. Owner confirmation is required before treating either statement as current intent.  
**Issue #49 remains OPEN.** Ordinary product/data/research/backtest work is paused again under the latest execution instruction; the earlier comment recording product restart is superseded for this checkpoint.

### All currently open PRs (live API snapshot)

| PR | State | Draft | Base | Head | Exact-head evidence / handling |
|---|---|---:|---|---|---|
| [#73](https://github.com/yarsalam/marketsage/pull/73) | open | yes | `main` | `714fa2318afa1ed135b12fd52bef18e407db4b2c` | Push and PR CI substantive jobs passed (runs [42467762926](https://github.com/yarsalam/marketsage/actions/runs/42467762926), [42467764733](https://github.com/yarsalam/marketsage/actions/runs/42467764733)); product scope is paused under #49; leave untouched. |
| [#71](https://github.com/yarsalam/marketsage/pull/71) | open | yes | `infra/provider-neutral-control-plane-2026-11` | exact governance/code checkpoint `3ffab7d0451630e174377a562dc67c51591e29b1`; current docs-only refresh follows it | Exact-head push CI [42489505405](https://github.com/yarsalam/marketsage/actions/runs/42489505405) and PR CI [42489508263](https://github.com/yarsalam/marketsage/actions/runs/42489508263) both passed all seven substantive jobs; provider-neutral tests and CI-helper tests passed. Docker worker acceptance [42489505355](https://github.com/yarsalam/marketsage/actions/runs/42489505355) passed. The manual-only local workflow policy regression was included and passed; no self-hosted run was triggered. Prior self-hosted acceptance [42465921813](https://github.com/yarsalam/marketsage/actions/runs/42465921813) failed before the first workflow step on attempt 2; log artifact unavailable. Hosted Docker acceptance watchdog remains DEGRADED because provider health is UNKNOWN. Keep draft/open. |
| [#62](https://github.com/yarsalam/marketsage/pull/62) | open | no | `main` | `54fbf4a364a91b4e8d834fdcec0245d079440982` | Seven substantive checks passed in run [42408717730](https://github.com/yarsalam/marketsage/actions/runs/42408717730); Dependabot update, no merge performed. |
| [#61](https://github.com/yarsalam/marketsage/pull/61) | open | yes | `infra/provider-neutral-control-plane-2026-11` | `25ce24283e35dd7e55eb8545c590a047606643ee` | No exact-head check runs returned. Documentation decomposition only; do not duplicate or merge while #49 is open. |
| [#51](https://github.com/yarsalam/marketsage/pull/51) | open | no | `feat/tindex-free-data-connector` | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | Five substantive jobs passed in run [42062133299](https://github.com/yarsalam/marketsage/actions/runs/42062133299); non-infrastructure data work is paused. |
| [#41](https://github.com/yarsalam/marketsage/pull/41) | open | no | `main` | `162692f1a377ec8445ed958db4cc1171d4cafc47` | Five jobs passed in run [42063679856](https://github.com/yarsalam/marketsage/actions/runs/42063679856); governance synchronization remains open and its state document must not be treated as the live source of truth. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | open | no | `fix/gdelt-fred-tindex-current-docs` | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | Known TSETMC smoke failure/ConnectTimeout. Parked; do not repeat the same request from the same environment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | open | no | `main` | `1d90726c593b0818982407c309ff13301798f5b3` | Five substantive checks passed in run [42061863597](https://github.com/yarsalam/marketsage/actions/runs/42061863597). **Never merge to main without separate explicit owner approval.** |

### Closed coordinator PR and owner validation

- PR [#54](https://github.com/yarsalam/marketsage/pull/54) is **closed and not merged**, draft flag retained; head `e8f7d8add3df577120b92b8927c590aece001509`. Do not reopen/merge it as a duplicate. The exact-head owner validation is recorded in Issue [#55](https://github.com/yarsalam/marketsage/issues/55): 16/16 tests passed, exit 0. The later PR #71 branch modifies/integrates the coordinator lifecycle.
- Issue #53 is closed: the owner chose public visibility and standard public hosted runners as the zero-cost path. No paid runner, plan change, or spending-cap increase is recorded.
- Issue #52 remains open for the Chabokan-only isolated wheel install and hash-lock evidence on exact integration commit `2776d9c6e17d24d09a809c07549100e4f2c3c2ae`.
- Issue #57 is the worker-runtime/local acceptance handoff. Exact self-hosted run #42465921813 failed before workflow steps; owner-side Runner diagnostics are required.
- Issue #63 remains an owner action. Live ruleset #26789479 is active on `refs/heads/main`, but it requires **10 approving reviews**; the branch-protection endpoint itself returned 403 to this integration. The owner must verify the intended approval count and administrator/bypass semantics.

### Live default-branch Actions audit

- `.github/workflows/ci.yml` on main has `push` (main/deploy/**/research/**/ci/**/infra/**), `pull_request` (main/deploy/**/infra/**), daily `schedule` at `03:17 UTC`, and `workflow_dispatch`.
- A real successful default-branch schedule run exists: [42471588681](https://github.com/yarsalam/marketsage/actions/runs/42471588681), on main SHA `4c4b032196137af4658ea2c28e38a21605ee923b`, conclusion `success`.
- CI uses global `contents: read`; job-level permissions add only the PR/issue reads or issue-comment write required by the provenance/failure-notice jobs. Actions are pinned to full 40-character SHAs.
- CI concurrency is keyed by PR number/ref and cancels superseded runs. Observed rapid-push runs were cancelled, but there is no independent observer for a hosted run stuck before job start or for a provider-wide hosted-runner outage.
- Job timeouts are bounded (5–40 minutes). CI has no automatic job retry; the task scheduler has a tested bounded retry budget. No explicit artifact upload or custom log-retention override is present.
- The CI failure reporter runs on the same GitHub-hosted runner pool it monitors and cannot report a total outage of that pool. The local self-hosted worker reporter runs on GitHub-hosted `ubuntu-latest`, so it is independent of the local runner pool, but still depends on GitHub-hosted capacity.
- The Docker worker acceptance workflow in PR #71 uses GitHub-hosted `ubuntu-latest`, a 15-minute timeout, no-network container, and a 15-minute schedule; because it exists only on a non-default PR branch, its schedule is **not active** yet. The self-hosted acceptance workflow has been changed to owner-confirmed `workflow_dispatch` only; it must not run on push or schedule.
- No dedicated independent 24/7 server runner is provisioned. The laptop runner is not an always-on service. The 24-hour observation window has not been completed.

### Main ruleset and human gate

Ruleset [#26789479](https://github.com/yarsalam/marketsage/rules/26789479) is active and targets `refs/heads/main`. It blocks branch deletion and non-fast-forward updates, requires a pull request, and requires these seven checks: `analysis`, `user-backend`, `user-frontend`, `admin-workspace`, `production-images`, `Test provider-neutral control plane`, and `Test CI automation helpers`. It also requires **10 approvals**. Its explicit bypass actor list is empty; administrator bypass behavior was not independently verified. The ruleset collection is readable, but the classic branch-protection endpoint is not accessible to this integration (403). Owner action remains in [#63](https://github.com/yarsalam/marketsage/issues/63).

### Issue #49 acceptance posture — NOT COMPLETE

| Criterion | Evidence | Status |
|---|---|---|
| Event-driven push/PR exact-head CI | PR #71 prior code head has successful push/PR CI; corrected manual-only head awaits exact-head checks | PARTIAL |
| Successful default-branch scheduled run | Main schedule run #42471588681 on exact main SHA | PASS for scheduled CI only; not yet a scheduled worker/orchestrator canary |
| Two independent real backends | Two deterministic fake adapters only; no independently operated real backends | NOT PROVEN |
| No duplicate external side effects | 164-test suite includes fake/restart/failover paths; no external side-effect ledger on two real backends | PARTIAL / NOT PROVEN |
| Hung/stale recovery, timeout/cancel/retry | Durable lease/fencing/watchdog/scheduler tests exist; no full live 24/7 failure-injection window | PARTIAL |
| Real isolated worker | Hosted Docker worker acceptance succeeded; local self-hosted acceptance failed before workflow steps | PARTIAL |
| Independent health/failure notification | Local-worker failure notifier succeeded on hosted runner; CI notifier shares the hosted pool; watchdog reported provider UNKNOWN | PARTIAL |
| Least privilege, cost guardrails, runbook | Workflow permissions, pinned actions, zero-cost public runner, sandbox policy and runbook are documented; owner review remains | PARTIAL |
| 24-hour continuous observation | No qualifying window | NOT PROVEN |

No PR was merged, no workflow was manually dispatched or rerun by this audit, no provider/account/secret was registered, and no product/data/investment work was performed.


## PR #71 base reconciliation — 2026-11-08

- [PR #74](https://github.com/yarsalam/marketsage/pull/74) now reconciles the provider-neutral base with main at `6dcfe5780d021cb3eb4ee2c0701003f8db39b7a0`. It remains Draft/open and requires exact-head CI/review; no merge to main was performed.
- PR #71 is being updated as a two-parent merge on its own branch: retain implementation head `0afb73c43dfbb0726f42d33f87e09966aa1254a9` as first parent and include the reconciled base `6dcfe5780d021cb3eb4ee2c0701003f8db39b7a0` as second parent.
- The updated PR #71 tree preserves its changed worker/outbox paths and the new base's direct-main detector, combined CI workflow and reconciled automation guide. Its own governance state/register files are refreshed without discarding the worker-specific evidence.
- Exact-head PR/push CI and hosted Docker acceptance on the original PR #71 head passed 164/164 control-plane tests, but this does not validate the refreshed merge head. New exact-head CI is required.
- Issue #52 Chabokan-only install/test evidence is **30/30 passing** on the recorded target commit; only exact hash-lock/reproducibility remains open.
- The local Worker Acceptance failure before its first workflow step remains distinct from the later successful offline TSETMC validator runs. Keep local dispatch manual and owner-confirmed.
- Issue #49 remains **NOT COMPLETE** until the independent host/worker, observer recovery, operational failure drills and 24-hour observation criteria are evidenced.


## Live PR inventory — 2026-11-10 14:41 UTC

This inventory supersedes older open-PR snapshots above. All refs and checks below were read from GitHub at this audit. No PR was merged, closed, marked ready, or auto-merged.

| PR | State / target | Exact head | Exact-head evidence / handling |
|---|---|---|---|
| #81 | Draft, `main` | `a659fa038dc84b000c5a01b20b234d5e31f54ff3` | MarketSage CI run #42672784245 failed; Project Operating System PR run #42672784044 succeeded. Frozen; no infrastructure action. |
| #80 | Draft, `main` | `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | Listed exact-head checks succeeded in #42644847236. Frozen product/admin work. |
| #79 | Draft, `main` | `14001bdb5a03775b9772bf9cfea1d169a68f8113` | Listed exact-head checks succeeded in #42643250744. Frozen product/auth work. |
| #78 | Draft, `main` | `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | Exact Project Operating System/CI runs #42644297705, #42644297868 and #42644283033 succeeded. Its schedule is not on main. |
| #77 | Draft, `main` | `67356939f65224a580c915fd2caa0ea52d8d09a9` | Run #42624038512 has successful listed jobs, but required provider-neutral control-plane context is absent. Frozen; no action. |
| #74 | Draft, `main` | `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10` | Exact Push #42589280185 and PR #42589290385 passed the infrastructure control-plane and CI-helper tests; product jobs scope-skipped. Keep Draft. |
| #73 | Draft, `main` | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | Exact runs #42621957914 and #42621965739 succeeded. Frozen research work. |
| #71 | Draft, base `infra/provider-neutral-control-plane-2026-11` | `e8785b177f93a569ce031496d1043026979828d3` | Zero exact-head check runs and zero workflow runs. Base recorded at `6dcfe5780d021cb3eb4ee2c0701003f8db39b7a0`; current PR #74 head is 11 commits ahead of that base. PR #71 and #74 heads diverge (108 ahead / 11 behind from the common base). Reconcile before review; do not merge. |
| #62 | Open, non-Draft, `main` | `54fbf4a364a91b4e8d834fdcec0245d079440982` | Listed checks succeeded in #42408717730; required provider-neutral control-plane context is absent. Dependabot PR; no action under infrastructure freeze. |
| #61 | Draft, base infrastructure branch | `25ce24283e35dd7e55eb8545c590a047606643ee` | No exact-head checks; mergeability false. Reconcile only after the primary infrastructure branch is settled. |
| #51 | Open, non-Draft, base `feat/tindex-free-data-connector` | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | Listed exact-head checks succeeded. Research/data-source work remains frozen. |
| #41 | Open, non-Draft, `main` | `162692f1a377ec8445ed958db4cc1171d4cafc47` | Listed exact-head checks succeeded. Data/governance work remains frozen. |
| #8 | Open, non-Draft, base `fix/gdelt-fred-tindex-current-docs` | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | Exact `tsetmc-smoke` check failed; other listed checks succeeded. Parked after ConnectTimeout; never repeat the same request from the same environment. |
| #6 | Open, non-Draft, `main` | `1d90726c593b0818982407c309ff13301798f5b3` | Listed checks succeeded, but PR is not mergeable against its recorded base. Never merge to main without separate explicit owner approval. PR #14 is already integrated into #6. |

## Closed infrastructure reference

- PR #54 is closed, Draft, and unmerged (head `e8f7d8add3df577120b92b8927c590aece001509`; mergeability false). Issue #55 records 16/16 exact-head SQLite coordinator tests with exit code 0. This is unit-test evidence only, not merge approval or distributed/operational proof.
- Issue #52 remains open for five Chabokan wheel SHA-256 hashes. Issue #53 is closed with the public-repository zero-cost hosted-CI decision. Issue #55 is closed after exact-head validation.
- Main remains `4c4b032196137af4658ea2c28e38a21605ee923b`; active ruleset #26789479 requires a PR, one review and seven contexts. Do not alter rulesets from this automation.

## Infrastructure acceptance status

- Main's scheduled CI run #42806341738 succeeded on exact main SHA `4c4b032196137af4658ea2c28e38a21605ee923b` on 2026-11-10. This proves scheduled CI execution, not scheduled worker execution; the observed start was about eight hours after the configured cron time.
- PR #74's exact-head infrastructure tests passed, but PR #71's current exact head has no checks and is diverged from PR #74.
- The Docker worker, daemon, watchdog, dispatch outbox and CircleCI adapter remain branch-only. CircleCI is configuration only; no account/integration/provider activation is evidenced. The self-hosted acceptance workflow remains manual-only and its generic runner selector must be narrowed before any authorized local dispatch.
- No live two-provider canary, independent notification path, persistent server, worker-loss recovery canary, or 24-hour stability proof exists. 24/7 readiness is **NOT PROVEN**.
- No hosted workflow was dispatched/rerun and no local workflow was dispatched during this audit. This documentation-only commit uses `[skip ci]`; it has no exact-head CI validation and must remain unmerged pending the owner's explicit bounded hosted-run authorization.

Owner handoffs remain in [Issue #49](https://github.com/yarsalam/marketsage/issues/49) (visibility confirmation and bounded exact-head hosted-run authorization) and [Issue #52](https://github.com/yarsalam/marketsage/issues/52) (wheel hashes). Do not create duplicate issues.
