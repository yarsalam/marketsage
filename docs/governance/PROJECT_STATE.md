# MarketSage — Current Project State

## Live infrastructure snapshot — 2026-11-09 (authoritative)

This snapshot supersedes the older dated snapshots below. The latest owner instruction reactivates Issue #49 as a hard gate; the issue body has been updated to record that instruction.

- **Default branch:** `main`; HEAD `4c4b032196137af4658ea2c28e38a21605ee923b`, committed `2026-11-07T19:55:51Z`.
- **Visibility:** the live GitHub API reports `private=false` / `public`. This conflicts with the current request's description of the repository as private. No visibility change was made. The owner confirmation handoff is recorded in Issue #49. Treat all repository content as public until resolved.
- **Main ruleset:** `main-protection` / `26789479`, enforcement active, target `refs/heads/main`; PR required, one approving review, seven required status checks, deletion and non-fast-forward updates blocked, no bypass actors, `current_user_can_bypass=never`. Strict required-status-check policy is false. Issue #63 is closed. The legacy branch-protection endpoint returned 403; the active ruleset read is the source of truth.
- **Infrastructure PR #74:** draft, base `main`, head `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10`, 73 commits ahead / 0 behind. Exact PR run [42589290385](https://github.com/yarsalam/marketsage/actions/runs/42589290385) passed the control-plane test job: 110 tests. Other broad jobs were scope-skipped, not failed. PR is not merged.
- **Infrastructure PR #71:** draft, base `infra/provider-neutral-control-plane-2026-11`. The tested code head `7d7c6b1d9eb97d6070651c8b5cda41db9753a78f` passed 170 control-plane tests in [42507293048](https://github.com/yarsalam/marketsage/actions/runs/42507293048), and the real Docker sandbox canary passed on the same SHA in [42507288970](https://github.com/yarsalam/marketsage/actions/runs/42507288970). The branch was 103 commits ahead / 11 behind its base at the last compare. Two repository-only commits then bounded the Docker canary cadence and added workflow-policy tests; the code head before this governance snapshot is `7cf9c5ddf8f4fd858064847e01ffc36a5565c5fc`. Those later commits intentionally skipped CI because no new hosted run was authorized. The 170-test and Docker results do **not** validate the later SHA.
- **PR #54 / SQLite:** PR #54 is closed and unmerged. Issue #55 is closed with 16/16 tests on exact commit `e8f7d8add3df577120b92b8927c590aece001509`. The newer SQLite coordinator/outbox/orchestrator implementation is in PR #71; its 170-test result applies only to the exact earlier PR #71 SHA above.
- **Main CI schedule:** `.github/workflows/ci.yml` has push, pull-request, daily schedule (`17 3 * * *`) and manual-dispatch triggers. Main SHA `4c4b032...` has a successful scheduled run [42610905309](https://github.com/yarsalam/marketsage/actions/runs/42610905309) on 2026-11-09 and a successful push run [42408566585](https://github.com/yarsalam/marketsage/actions/runs/42408566585). The scheduled run started at 11:40:32 UTC, well after the 03:17 UTC cron time; GitHub schedule timing is not an exact-time guarantee.
- **Workflow controls:** CI defaults to `contents: read`, with narrowly scoped `issues: write` in failure/provenance jobs; concurrency cancels superseded runs; jobs have explicit timeouts. There is no workflow-level retry policy. Failure reporters run on GitHub-hosted runners in the same hosted runner pool they monitor. The health observer is a deterministic snapshot assessor, not a deployed independent poller.
- **Docker canary cadence change:** PR #71 now limits the heavy Docker worker acceptance workflow to a daily schedule and `main` pushes; normal push/PR validation remains in `ci.yml`. A regression test was added for daily cadence and manual-only self-hosted triggers. The new test has not been run on the changed head.
- **Local worker boundary:** `self-hosted-worker-acceptance.yml` remains manual-only with explicit owner confirmation. No local workflow was dispatched. The laptop is not treated as always-on.
- **Provider and recovery evidence:** two-provider failover and side-effect deduplication tests use deterministic fake adapters. No real second provider is registered. The Docker sandbox has one successful ephemeral GitHub-hosted acceptance run, not a persistent independent worker service. SQLite is single-host. Crash/restart and lease recovery are covered by tests, not by a 24/7 server drill. The watchdog/health assessment code is not an independently deployed observer or notification path.
- **Independent failure domain:** `.circleci/config.yml` exists as a candidate adapter but no CircleCI account/pipeline is connected or verified. No notification path outside the GitHub-hosted runner pool is currently proven.
- **Owner gates:** Issue #52 records Chabokan-only install success (30/30 tests) on the recorded exact commit; only dependency wheel hash-locking remains. Issue #53 is closed by the public-repository zero-cost decision. Issue #55 is closed; Issue #63 is closed.
- **Execution boundary:** no hosted dispatch/rerun, local dispatch, provider registration, secret creation, paid usage, merge, release, deployment, market-data operation, product feature work, investment scoring/ranking, probability calibration, backtest approval, broker/trading, or capital allocation was performed in this snapshot.

**Readiness:** NOT 24/7-ready. Real independent provider execution, an external failure observer, persistent worker hosting, live recovery drills, and exact-head validation of the newest PR #71 changes remain unproven.


**Snapshot date:** 2026-11-09  
**Repository:** yarsalam/marketsage (PUBLIC per live GitHub API; visibility confirmation tracked in Issue #49)  
**Main HEAD:** 4c4b032196137af4658ea2c28e38a21605ee923b  
**Integration PR:** #6, feat/tindex-free-data-connector  
**Current integration HEAD:** 1d90726c593b0818982407c309ff13301798f5b3  
**Infrastructure PRs:** #74 (parent integration) and #71 (durable outbox/worker)  

**Pinned integration code commit:** 819f8b4028469cb0d498098fec88545a18ebacc6  
**Release posture:** research-only. No data source has passed the complete investment-source gate; no representative strategy has passed empirical validation; production ranking/scoring, broker access and trading remain disabled.

## Executive state

- PR #6 remains open and **must not be merged to main without explicit owner approval**. Its current integration code is used by the new local workflow only through the immutable commit SHA above.
- PR #8 remains parked after the GitHub-hosted TSETMC connection timeout. Do not repeat the same request from the same environment.
- PR #27 (manual-only staged-dataset validator), PR #31 (clean governance adoption), PR #32 (manual integrated TSETMC workflow) and PR #34 (memory-bounded local analysis) are merged to main. PR #15 was closed as superseded; its divergent branch was not merged.
- PRs #7, #9, #13, #14, #16–#24, and #28–#30 are integrated into PR #6 in dependency order. Their CI results do not approve data sources or the strategy.
- The governance constitution is adopted on main via PR #31. Active ruleset #26789479 protects main with required PR/check rules and deletion/non-fast-forward blocks. It requires one approving review and seven required checks; Issue #63 is closed. Strict required-status-check policy is false and no bypass actors are configured. The laptop Runner remains manual-only.

## Local Runner and first dataset gate

**Runner:** [redacted local runner id], repository-scoped to yarsalam/marketsage, version 2.338.2, labels marketsage-local and marketsage-research plus GitHub's standard labels.

**Service:** actions.runner.yarsalam-marketsage.[redacted local runner id].service, running as the unprivileged [redacted runner account] account and enabled at boot. The account is not in sudo, docker, lxd or adm; it cannot traverse the owner's home directory.

**Host access boundary:**
- Staged data: [redacted local path], files mode 0440, directories mode 2750; Runner read/traverse only.
- Output: [redacted local path], owned by Runner; the integrated-candidate workflow creates its dedicated output directory with mode 0700 and umask 077.
- Runner workspace/install is under [redacted local path]
- Service restrictions include ProtectHome=true, ProtectSystem=strict, PrivateTmp=true, NoNewPrivileges=true, kernel/module/control-group protections, the staged dataset in ReadOnlyPaths, and only the approved Runner/output paths in ReadWritePaths.
- RestrictSUIDSGID is not enabled. Its removal followed the observed GNU tar 1.35 Function not implemented checkout failure; a nested tar extraction regression test passed in a systemd sandbox with the other principal restrictions retained.
- Network egress is not blocked by these filesystem/systemd controls. Only reviewed manual workflows may run.

**First local validation:** workflow run [#41906518123](https://github.com/yarsalam/marketsage/actions/runs/41906518123), attempt 2, completed successfully on 2026-11-05. The run checked out the reviewed main commit 46d3a541b7fa176b5a8c5693a0c46feb8bb9b3fc and reported:
- 8,801 of 8,801 staged source-file SHA-256 entries verified;
- 1,268,527,673 source bytes verified;
- 2,493 instrument-universe rows inventoried;
- zero network requests and no dataset modification;
- scoring disabled and backtest approval disabled.

Attempt 1 failed while extracting actions/checkout; the host compatibility fix was applied and a targeted nested-tar test passed before attempt 2. The failed attempt is retained in run history; attempt 2 is the successful result.

**Interpretation:** this gate establishes staged-corpus inventory/checksum integrity only. It does not establish usage rights, correct raw/adjusted-price semantics, corporate-action correctness, independent price reconciliation, point-in-time availability, source acceptance or backtest eligibility.

## Next data task

PR #32 is merged to main at `11f9de85c13f3ee8bd61e6eb7aea64992a7271d4`. It adds a separate manual-only workflow for the PR #14 integrated offline TSETMC candidate-acceptance pipeline. It:
- checks out this workflow's exact manually selected main commit;
- checks out the integration implementation at the fixed SHA 819f8b4028469cb0d498098fec88545a18ebacc6;
- requires the owner confirmation input and the repository-scoped Runner labels;
- checks the staged dataset is readable and non-writable, checks the v2 identity crosswalk, bounds discovery size, requires at least 4 GiB effective available RAM (host and cgroup-aware) and 8 GiB free output disk, and refuses symlinks/out-of-dataset inputs;
- divides the discovered candidates into bounded batches of at most 32 instruments and 32 MiB of unique selected input files per batch; it rechecks RAM/disk before every batch and keeps each batch's detailed outputs local;
- makes no provider/network requests, changes no input file, and keeps row-level candidate outputs and local absolute paths on the laptop under the private output directory;
- prints only sanitized counts and fail-closed status flags to GitHub logs; no artifacts are uploaded.

The first integrated dispatch, run [41912248800](https://github.com/yarsalam/marketsage/actions/runs/41912248800), reached the local Runner and checked out both exact commits successfully, but stopped before candidate analysis with `insufficient_available_memory`: the original static 16 GiB gate was higher than the laptop's available memory. No candidate batch ran; the staged dataset remained read-only and the workflow made no provider requests. PR #34 adds bounded memory-aware batches and reports the measured host/cgroup memory and free disk. PR #34 merged to `main` at `554fe2200ccb3a523442b0e241e81a748becfa44` after all five exact-head CI jobs passed in run [41913385729](https://github.com/yarsalam/marketsage/actions/runs/41913385729); the analysis suite reported 109 passed and 7 warnings. A post-merge `main` push CI run is being checked separately. The owner must now manually dispatch again with `confirm_integrated_acceptance=true`. It prints aggregate decision/quarantine reason counts and price-semantics/identity counts only; detailed CSVs and row-level data remain local.

## Data-source acceptance

No source currently passes the complete gate for investment scoring. TSETMC is the first local technical acceptance workload, not an approved investment dataset. Required evidence includes:
- exact instrument identity and market/venue convention;
- source-use/storage rights;
- price/volume units and raw versus adjusted/total-return semantics;
- dates, trading calendar, publication/availability timestamps and revisions;
- missing intervals, suspensions, duplicates and structural quality;
- complete price-adjustment and share-change/corporate-action evidence;
- lawful independent reconciliation;
- point-in-time tradability and survivorship controls.

The staged corpus intentionally excludes the separate adjusted research-only candidate directory. Discovery/crosswalk mapping can identify candidates but cannot substitute for explicit identity evidence or approve a series. Missing evidence remains unknown or pending, not pass.

Other source posture remains unchanged: CODAL publication-time/correction linkage is unresolved; Tindex quotas and Rial/Toman endpoint families stay under the conservative local caps and separate unit handling; Binance Spot remains blocked after owner-reported HTTP 451; GDELT remains in cooldown after HTTP 429; Nerkhsanj IQD/silver/Tether remain excluded and Bitcoin remains a coverage warning; CBI/ECB/Treasury/EIA/SEC/IMF/World Bank candidates still require series-specific rights, units, history and point-in-time review.

## Stage 4 empirical posture

The existing Stage 4 report is exploratory, not accepted predictive validation. Its input universe was global proxies/US ETFs and crypto, not a representative Iranian-market universe. The report recorded a 240.89% six-month fold from 2023-10-31 to 2024-03-31 that requires asset-level attribution, while other folds lost money. The configured slippage values are assumptions, not measured execution costs. The latest 12-month holdout is too short to establish stable expected returns and must not be used to tune parameters.

The matching monthly-price CSV and its exact hash/configuration are not currently part of the staged TSETMC dataset. Do not reconstruct or substitute a different dataset and call the attribution reproducible. The locked holdout must remain untouched.

## Current decision and next actions

1. Owner manually dispatches the updated `.github/workflows/local-tsetmc-integrated-acceptance.yml` on `main` with `confirm_integrated_acceptance=true` and reviews the sanitized counts, decision statuses, quarantine reasons and reprocessing queue.
2. Resolve TSETMC evidence gaps (rights, identity, semantics/units, corporate actions, independent reference, calendars and point-in-time availability) against the local-only outputs; do not upload raw rows or candidate CSVs.
3. Obtain an immutable, permissioned and representative historical dataset before any locked walk-forward strategy evaluation.
4. Attribute the Stage 4 extreme fold only when the exact original monthly CSV/hash/config is available; do not tune on the final holdout.
5. Compare the six-month decision horizon against predeclared baselines using net returns, costs, liquidity, drawdown, uncertainty and point-in-time replay.
6. Keep source scoring, investment ranking, calibrated probabilities, production release, broker access and trading disabled until all relevant data and empirical gates pass. Any real-money allocation or trade still requires the owner's separate explicit approval.

**Investment-stage status: NOT READY.** A successful Runner job, parser, dataset hash audit, or integration CI run is not an investment approval.


## Infrastructure-first execution status — 2026-11-06 (supersedes ordinary next-data work until Issue #49 is accepted)

**Priority:** [Issue #49](https://github.com/yarsalam/marketsage/issues/49) is the active first priority. Ordinary product, source-screening, dataset, backtest and investment-analysis work is paused. Only work directly required to design, implement, secure and prove provider-independent execution may proceed.

- Default branch `main`: `07e641670ceab22496ef976a584934464570fd9a`.
- Integration PR #6 current head: `1d90726c593b0818982407c309ff13301798f5b3`. PR #14 is already merged into #6; no repeat merge is required. PR #6 remains open and must not be merged to main without separate explicit owner approval.
- PR #50 (cloud CI timeouts/concurrency/schedule/failure notice) remains open. Exact head `9098f110f615d46adbfa49f37e644000b832feb0`; run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919) and its bounded rerun failed before job steps with hosted runner ID 0. No step logs were available. This is an allocation/account-capacity failure, not a demonstrated code-test failure. GitHub Actions usage/budget is explicitly blocked at USD 0; do not trigger more hosted runs until included quota is confirmed reset or separate owner authorization exists.
- PR #41 is an open governance/workflow-pin synchronization PR; exact-head run [42063679856](https://github.com/yarsalam/marketsage/actions/runs/42063679856) passed all five required job types. It remains open for review; no local workflow was dispatched.
- PR #51 is an open documentation-only data candidate screen; exact-head run [42062133299](https://github.com/yarsalam/marketsage/actions/runs/42062133299) passed all five job types. Ordinary data work remains paused under Issue #49; do not merge or extend it during the infrastructure-first phase.
- PR #48 (Stage 4 provenance manifest) is merged into integration at `1d90726c593b0818982407c309ff13301798f5b3`. This does not mean the local original dataset was rerun or the unexplained fold was attributed.
- Provider-neutral work is on `infra/provider-neutral-control-plane-2026-11`; mirror-probe hardening is recorded in commit `82a0a6d1a3c2d4fc8c1232f6675d63bf9b29fce9`. It contains the architecture, provider landscape, strict task manifest/schema, in-memory fake-provider/lifecycle fixtures, operating runbook and Python mirror probe. No provider is registered and no paid resource is active.
- The latest owner-local validation attempt failed during dependency bootstrap before tests; the manifest and lifecycle test modules have not run from a clean checkout. The mirror probe is now HTTPS-downgrade-safe and has nine offline regression tests; those passed only in an isolated temporary harness, not on the owner network or from a clean repository checkout.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) is the owner-action handoff for running the bounded mirror probe on the actual worker network. Until that evidence exists, no mirror is selected and no dependency constraints are changed.
- Oracle signup returned an export/compliance denial. Do not bypass it by changing identity, address, location, VPN or using another person's account.
- The laptop Runner is registered and isolated for reviewed manual local workloads, but it is not an always-on control plane and does not establish 24/7 readiness. No local workflow is dispatched by this update.

**Current status:** infrastructure not ready; durable queue/outbox, real provider adapters, restart recovery, stale-run monitoring, independent backend failover and a clean end-to-end zero-cost canary remain unproven. Research scoring/ranking, backtest approval, production deployment and trading remain disabled.


### Additional infrastructure evidence — 2026-11-06

- The in-memory fake-provider/coordinator fixture was executed in an isolated temporary harness: 9/9 lifecycle tests passed. This is not a clean repository checkout or a durable/distributed coordinator test. The manifest test remains blocked on the `jsonschema` dependency bootstrap.
- The mirror probe has six offline regression tests, also passed only in a temporary harness. Actual worker-network reachability is still pending Issue #52.
- PR #50's failure reporter shares the GitHub Actions runner pool it monitors. In run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919), the reporter itself failed before steps with the other jobs. It cannot independently detect/report a provider-wide runner allocation outage; an external observer on a separately verified zero-cost path is required.


- Mirror-probe bound was tightened: 12 initial package-page GETs, at most one HTTPS redirect per page (24 total GETs maximum), 12-second timeout per request. Nine offline regression tests passed in a temporary harness only; no actual mirror reachability is established.


### Additional owner-action handoff — 2026-11-06

- [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is the owner-only verification gate for GitHub Actions included-minute availability, reset date, repository/account enablement and the current USD 0 spending cap. It explicitly requests no spend increase, plan change or visibility change. Do not dispatch or rerun hosted workflows until the owner confirms that a zero-cost included allowance is available and authorizes one bounded exact-head validation attempt.


### Live GitHub Actions audit — 2026-11-06 16:05 UTC

- The default-branch `.github/workflows/ci.yml` still has only push and pull-request triggers; it has no schedule, concurrency guard or explicit job timeouts. The proposed daily schedule in PR #50 is therefore **not active** on main. The Actions API returned no scheduled workflow runs.
- PR #50 exact head `9098f110f615d46adbfa49f37e644000b832feb0` has not produced a valid test result. Run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919), attempt 2, shows all five hosted test/build jobs and the failure reporter ended before step 1 with runner ID 0 and zero steps; production-images was skipped. This is runner allocation/capacity evidence, not a code-level test result.
- The failure reporter cannot report a pool-wide outage because it shares the same hosted runner pool. Do not dispatch/rerun hosted Actions until the owner completes [Issue #53](https://github.com/yarsalam/marketsage/issues/53); keep the zero-dollar spend boundary unchanged.
- PR #14 is already merged into integration PR #6. PR #6 remains open and must not be merged to main without explicit owner approval. PR #8 remains parked; its GitHub-hosted TSETMC timeout must not be repeated from the same environment.


### In-memory lifecycle fixture correction — 2026-11-06

- Fixed an identity-index consistency defect: `InMemoryCoordinator.enqueue` now rejects reuse of an existing `task_id` with a different idempotency key/input instead of overwriting the task-by-ID index.
- Added a regression test proving the original task remains addressable and a duplicate delivery with the same idempotency key still maps to the original logical task.
- Exact branch head for the code/test/contract change: `e19ddd8ac9367e841415122945189dd72a46521b`. The exact lifecycle source and tests passed **10/10** in a temporary isolated harness (exit 0); this is not a clean checkout or CI result.
- No durable storage was implemented. The manifest dependency/bootstrap and clean-checkout test gates remain open; do not proceed to the transactional outbox until those tests pass in an authorized zero-cost clean checkout.


### Fenced terminal-failure publication correction — 2026-11-06

- The in-memory coordinator's `mark_failed` now requires the active lease and checks owner plus fencing token. An expired worker cannot mark the task failed after a replacement worker reclaims it.
- Added a regression covering stale worker A versus current worker B; stale failure publication is rejected, and the current lease can still publish a terminal test failure.
- Exact lifecycle source/tests at `0ad3e7323a7e20779017a47854f33c1b21c6321d` passed **11/11** in a temporary isolated harness (exit code 0). This is not clean-checkout or CI evidence.
- Durable storage, transactional outbox and real provider adapters remain blocked until the manifest/lifecycle tests pass from a clean checkout under the zero-cost policy.


### Durable single-host coordinator and lease renewal — 2026-11-07

- Draft PR [#54](https://github.com/yarsalam/marketsage/pull/54) adds a standard-library SQLite coordinator on `infra/sqlite-durable-coordinator-2026-11`. Current head: `e8f7d8add3df577120b92b8927c590aece001509`; target branch: `infra/provider-neutral-control-plane-2026-11`.
- The component persists task/idempotency identity, state, lease owner/expiry, fencing token, result and terminal failure. It uses WAL, `synchronous=FULL`, bounded busy timeout and `BEGIN IMMEDIATE` transactions. Process-restart and separate-process claim-exclusion tests are included.
- Added `renew_lease`: only the active, unexpired owner/fencing-token pair can renew; stale/expired leases are rejected; the expiry is never shortened. This is a primitive only—no periodic heartbeat worker or real provider dispatch is connected.
- Owner exact-checkout validation of prior head `77d3a1a17d6f5e52b009c683cc369a5afac89eed` passed 11/11 tests. The current head adds five renewal tests (16 tests total); they have not yet been run. Exact-head owner validation is tracked in [Issue #55](https://github.com/yarsalam/marketsage/issues/55). PR #54 remains draft/open.
- The PR branch and base have diverged, and the base branch has advanced since the PR's recorded base SHA. The latest PR API response reports mergeability as unknown; reconcile the head with the current base and revalidate before any merge. No merge is authorized by this status update.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) now records that Novin-only isolated installation and 28/28 manifest/lifecycle/mirror tests passed on commit `99b25dc24daa8606514bd9910e883ef136cf5d7f`; a full Chabokan-only wheel installation and hash-locked dependency record remain pending.
- [Issue #53](https://github.com/yarsalam/marketsage/issues/53) remains the owner action for GitHub Actions included-minute/reset/restriction status. No hosted dispatch or rerun is allowed until the zero-cost quota gate is resolved.
- PR #50 remains unvalidated on its current head after runner-allocation failures before step 1. Its schedule and concurrency changes are not active on main. The failure reporter shares the same hosted pool and is not an independent outage monitor.

**Infrastructure readiness remains NOT PROVEN.** SQLite is single-host only; no transactional provider outbox, real provider adapter, worker service, periodic heartbeat, dispatch reconciliation, backup/restore, disk-full/corruption recovery, independent health canary, provider failover or end-to-end 24/7 recovery drill has been demonstrated. Ordinary product/data/research work remains paused under Issue #49. PR #6 remains open and must not be merged to main without explicit owner approval; PR #14 is already merged into #6; PR #8 remains parked.

## Live infrastructure checkpoint — 2026-11-08 (authoritative current snapshot)

This section supersedes every older infrastructure status and any stale main-SHA, repository-visibility, schedule, branch-protection, Actions-quota, PR #54/#55, or product-priority statement above.

### Repository and authority

- GitHub API reports repository visibility `public`; the latest owner prompt describes it as private. Issue #53 records a prior owner decision to keep it public. No visibility change was made. Owner confirmation is required before any change or further assumption.
- Default branch: `main`; exact HEAD `4c4b032196137af4658ea2c28e38a21605ee923b`, commit timestamp `2026-11-07T19:55:51Z`.
- Issue [#49](https://github.com/yarsalam/marketsage/issues/49) remains open and is the controlling priority. The latest execution instruction reimposes an infrastructure-first pause; the earlier Issue #49 comment recording a product restart is superseded for this checkpoint. Do not advance product/data/research/backtest work until #49 is accepted.
- PR #6 remains open and is not to be merged without separate explicit owner approval. PR #14 is already integrated into #6; no repeat merge. PR #8 remains parked after the known TSETMC ConnectTimeout.

### Event-driven and scheduled GitHub automation

- Main `.github/workflows/ci.yml` is active for pushes to `main`, `deploy/**`, `research/**`, `ci/**`, and `infra/**`; PRs targeting `main`, `deploy/**`, and `infra/**`; a daily `03:17 UTC` schedule; and manual `workflow_dispatch`.
- Exact default-branch scheduled evidence: run [42471588681](https://github.com/yarsalam/marketsage/actions/runs/42471588681), event `schedule`, branch `main`, SHA `4c4b032196137af4658ea2c28e38a21605ee923b`, conclusion `success`.
- CI uses global `contents: read`; the provenance detector has only the PR/issue permissions it needs, and the sanitized failure reporter has issue-comment write. External actions are pinned to immutable full commit SHAs.
- Concurrency groups are per PR/ref and cancel superseded runs. Job timeouts are bounded between 5 and 40 minutes. CI has no automatic retry; the provider-neutral task scheduler has a bounded retry budget covered by tests.
- No artifact upload or custom log-retention override is configured. The CI failure notifier depends on the same GitHub-hosted runner pool it monitors, so it cannot report a total outage of that pool. The local-worker failure notifier runs on GitHub-hosted capacity, independent of the local self-hosted pool but not independent of GitHub itself.
- GitHub Actions run history includes cancelled superseded commits; cancelled/queued/pre-step failures are not counted as successful validations.

### Branch protection and human merge gate

- Live ruleset ID `26789479`, name `main-protection`, is active and targets `refs/heads/main`.
- It blocks branch deletion and non-fast-forward updates, requires PRs, and requires seven status checks: `analysis`, `user-backend`, `user-frontend`, `admin-workspace`, `production-images`, `Test provider-neutral control plane`, and `Test CI automation helpers`.
- The ruleset currently requires **10 approving reviews**, which may make routine merges impractical. Its explicit bypass-actor list is empty; administrator bypass behavior was not independently verified. The classic branch-protection endpoint returned 403 to the connected integration, so no classic protection claim is made.
- Owner review of the 10-approval setting and bypass semantics is tracked in [Issue #63](https://github.com/yarsalam/marketsage/issues/63). No ruleset mutation was made by this automation.

### Durable coordinator, provider outbox and worker evidence

- PR [#71](https://github.com/yarsalam/marketsage/pull/71) is the active infrastructure implementation branch. Its implementation checkpoint is `0afb73c43dfbb0726f42d33f87e09966aa1254a9`; it includes the SQLite coordinator lifecycle, durable dispatch outbox, orchestrator, fake provider adapters, task registry, Docker sandbox worker, persistent daemon, health collector/watchdog and runbooks. The exact-head provider-neutral suite passed 164/164 tests and hosted Docker acceptance succeeded.
- On exact governance/code head `3ffab7d0451630e174377a562dc67c51591e29b1`, push CI [42489505405](https://github.com/yarsalam/marketsage/actions/runs/42489505405) and PR CI [42489508263](https://github.com/yarsalam/marketsage/actions/runs/42489508263) both passed all seven substantive jobs. The provider-neutral test job ran **164 tests** successfully. These tests use deterministic fake provider adapters; they are not evidence of two independently operated real backends.
- Hosted Docker worker acceptance [42465921830](https://github.com/yarsalam/marketsage/actions/runs/42465921830) succeeded on a GitHub-hosted runner: container UID 65532, network `none`, read-only checkout, no secrets, zero declared cost, task succeeded and output hash recorded. The same run's watchdog status was `degraded` because provider health remained `unknown`; it is not a full healthy-provider canary.
- Local self-hosted acceptance [42465921813](https://github.com/yarsalam/marketsage/actions/runs/42465921813), attempt 2, failed during GitHub's synthetic job setup before the first workflow step. The job log artifact was unavailable, so the underlying runner bootstrap error is not established. Owner host notes show Docker rootless/seccomp checks had succeeded, but that does not substitute for a completed Worker Acceptance.
- To prevent accidental use of the laptop runner, `.github/workflows/self-hosted-worker-acceptance.yml` was changed to owner-confirmed `workflow_dispatch` only, with no push or schedule trigger, and a regression test was added. Workflow change commit: `6f97d39e8136fc5c1971373fc763f6eecee11802`; test correction commit: `1b49ac3fa2ab09787331caf8f027311187e39e97`. The correction passed exact-head push CI [42489253646](https://github.com/yarsalam/marketsage/actions/runs/42489253646) and PR CI [42489256825](https://github.com/yarsalam/marketsage/actions/runs/42489256825). The later governance/code checkpoint `3ffab7d0451630e174377a562dc67c51591e29b1` also passed exact-head push and PR CI.
- The Docker worker acceptance workflow has a 15-minute timeout and a 15-minute schedule, but it exists only on PR #71's non-default branch; GitHub schedule events execute from the default branch, so this worker canary schedule is not active yet. Main's daily CI schedule is active, but it is not a scheduled execution of the persistent task daemon.

### SQLite PR #54 / Issue #55 reconciliation

- PR [#54](https://github.com/yarsalam/marketsage/pull/54) is closed and **not merged**. Its head is `e8f7d8add3df577120b92b8927c590aece001509`.
- Issue [#55](https://github.com/yarsalam/marketsage/issues/55) is closed with owner evidence that the exact PR #54 head passed **16/16 tests**, exit code 0. The older 11/11 result applies only to the prior head.
- Do not reopen or merge #54 as a duplicate; PR #71 contains subsequent coordinator integration work. The integration branch used as PR #71's base is divergent from main (merge base `07e641670ceab22496ef976a584934464570fd9a`; main has 2 commits not in that branch, and the integration branch has 61 commits not in main). No rebase/merge was performed.

### Owner-action gates

- [Issue #52](https://github.com/yarsalam/marketsage/issues/52): Chabokan-only isolated installation succeeded on `2776d9c6e17d24d09a809c07549100e4f2c3c2ae`, with 30/30 tests passing. Exact wheel-hash locking remains separate and incomplete.
- [Issue #57](https://github.com/yarsalam/marketsage/issues/57): local self-hosted acceptance failed before workflow steps; owner must inspect sanitized Runner diagnostic evidence for the precise pre-step failure. Do not repeat Docker installation or dispatch until the cause is known.
- [Issue #63](https://github.com/yarsalam/marketsage/issues/63): owner must review the active main ruleset's 10-approval requirement and confirm the intended human gate and administrator/bypass behavior.
- Issue #53 is closed and resolves the zero-cost hosted-runner quota gate for a public repository; no plan upgrade or spending-cap increase was used. Issue #55 is closed with exact-head 16/16 evidence.

### Issue #49 acceptance matrix — NOT COMPLETE

| Requirement | Current evidence | Status |
|---|---|---|
| Event-driven exact-head push/PR validation | Previous PR #71 code checkpoint green; manual-only correction head pending exact checks | PARTIAL |
| Scheduled default-branch run | Main daily schedule #42471588681 succeeded on exact main SHA | PASS for CI schedule only |
| Same task on two independent real backends | Two deterministic fake adapters only | NOT PROVEN |
| Lost response/restart without duplicate external effect | Durable outbox/reconciliation tests; no two-real-backend external effect ledger | PARTIAL / NOT PROVEN |
| Hung/stale recovery, timeout, cancellation and retry | Lease/fencing/watchdog/scheduler tests; no complete live failure-injection/24-hour window | PARTIAL |
| Real isolated worker | Hosted Docker sandbox canary passed; local self-hosted acceptance failed before steps | PARTIAL |
| Independent health and failure notification | Local-pool failure notifier ran on hosted pool; hosted-CI notifier shares its pool; watchdog reported provider UNKNOWN | PARTIAL |
| Least privilege, cost controls, runbook and merge gate | Controls and runbooks exist; ruleset approval count/bypass still needs owner review | PARTIAL |
| 24-hour observation and 24/7 readiness | No qualifying observation window; laptop is not always-on; no independent persistent server is provisioned | NOT PROVEN |

**Overall: Issue #49 is NOT COMPLETE. Do not claim 24/7 readiness.** No PR was merged, no workflow was manually dispatched or rerun by this automation, no provider/account/secret was registered, and no product/data/investment work was performed.


## Reconciled base update for PR #71 — 2026-11-08

- Integration PR #74's base branch now contains the true two-parent merge commit `6dcfe5780d021cb3eb4ee2c0701003f8db39b7a0`, preserving both the provider-neutral implementation and current mainline provenance/CI controls.
- PR #71's original implementation head `0afb73c43dfbb0726f42d33f87e09966aa1254a9` passed exact-head PR/push CI with **164/164** provider-neutral tests and hosted Docker worker acceptance. This is prior-head evidence; the refreshed base requires new exact-head validation.
- The PR #71 branch is now reconciled against base `6dcfe5780d021cb3eb4ee2c0701003f8db39b7a0` while retaining the PR's Docker worker, dispatch outbox, orchestrator, daemon, Watchdog, systemd units, tests and host runbook.
- Mainline `Detect direct main updates`, its tests, the combined control-plane CI job, and the merged GitHub automation operations guide are retained in the new base.
- This rebase/merge update does not merge PR #71 or PR #74 into main and does not change the local workflow's manual/owner-confirmed boundary.

**Current readiness remains NOT COMPLETE.** No independently operated external backends, separate persistent server worker, process-level outage drill, or full 24-hour observation window is evidenced. The scheduled CI heartbeat does not prove continuous worker uptime.
