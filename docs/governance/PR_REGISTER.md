# MarketSage — Pull Request Register

**Snapshot date:** 2026-11-07  
**Repository:** yarsalam/marketsage (Private)  
**Main HEAD:** 07e641670ceab22496ef976a584934464570fd9a  
**Integration PR:** [#6](https://github.com/yarsalam/marketsage/pull/6), feat/tindex-free-data-connector  
**Pinned integration code HEAD:** 1d90726c593b0818982407c309ff13301798f5b3 (current PR #6 head; main local workflow remains pinned to 819f8b4028469cb0d498098fec88545a18ebacc6 until PR #41 is adopted)

## Open PRs

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