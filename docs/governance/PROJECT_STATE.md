# MarketSage — Current Project State

**Snapshot date:** 2026-11-14 14:19 UTC  
**Repository:** yarsalam/marketsage (Public per live GitHub API; owner decision recorded in Issue #53)  
**Main HEAD:** 4c4b032196137af4658ea2c28e38a21605ee923b  
**Integration PR:** #6, feat/tindex-free-data-connector  
**Current integration HEAD:** 1d90726c593b0818982407c309ff13301798f5b3  
**Pinned integration code commit:** 819f8b4028469cb0d498098fec88545a18ebacc6  
**Release posture:** research-only. No data source has passed the complete investment-source gate; no representative strategy has passed empirical validation; production ranking/scoring, broker access and trading remain disabled.

## Current execution gate — 2026-11-14

Issue #49 is the hard execution gate under the owner's latest instruction. Ordinary product, feature, data-source screening, investment research, backtesting and analysis work remain paused. Goal 2 remains paused until Issue #49 is accepted. Historical sections below are retained as context only and do not authorize those workstreams.

## Executive state

- PR #6 remains open and **must not be merged to main without explicit owner approval**. Its current integration code is used by the new local workflow only through the immutable commit SHA above.
- PR #8 remains parked after the GitHub-hosted TSETMC connection timeout. Do not repeat the same request from the same environment.
- PR #27 (manual-only staged-dataset validator), PR #31 (clean governance adoption), PR #32 (manual integrated TSETMC workflow) and PR #34 (memory-bounded local analysis) are merged to main. PR #15 was closed as superseded; its divergent branch was not merged.
- PRs #7, #9, #13, #14, #16–#24, and #28–#30 are integrated into PR #6 in dependency order. Their CI results do not approve data sources or the strategy.
- The governance constitution is adopted on main via PR #31. The latest branch snapshot records ruleset #26789479 as active with PR/seven-check/deletion/non-fast-forward controls, but reports 10 required approvals; an earlier live audit reported one. This run could not re-read the live ruleset or branch-protection API through the connected GitHub surface. The approval count and current enforcement are therefore BLOCKED for fresh verification; do not treat either recorded count as current until verified. The laptop Runner remains manual-only and is not a server.

## Local Runner and first dataset gate

**Runner:** marketsage-local-01, repository-scoped to yarsalam/marketsage, version 2.338.2, labels marketsage-local and marketsage-research plus GitHub's standard labels.

**Service:** actions.runner.yarsalam-marketsage.marketsage-local-01.service, running as the unprivileged marketsage-runner account and enabled at boot. The account is not in sudo, docker, lxd or adm; it cannot traverse the owner's home directory.

**Host access boundary:**
- Staged data: /srv/marketsage/data/tsetmc_history_20261022, files mode 0440, directories mode 2750; Runner read/traverse only.
- Output: /srv/marketsage/output, owned by Runner; the integrated-candidate workflow creates its dedicated output directory with mode 0700 and umask 077.
- Runner workspace/install is under /opt/actions-runner/marketsage.
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

## Reconciled infrastructure checkpoint — 2026-11-08

This section supersedes older infrastructure snapshots in this file where they conflict with the current evidence. Earlier entries remain as historical audit records.

### Mainline CI and repository protection
- `main` is `4c4b032196137af4658ea2c28e38a21605ee923b`. The cloud CI includes bounded job timeouts, same-ref concurrency, immutable Action pins, failure notice, and main-update provenance detection.
- The daily schedule is active on main; successful scheduled event: [run 42471588681](https://github.com/yarsalam/marketsage/actions/runs/42471588681).
- The direct-main provenance detector is a detection/reporting control, not prevention; native ruleset protection remains necessary.
- Active ruleset #26789479 targets main, requires PRs and seven CI checks, blocks deletion and non-fast-forward updates, and has no configured bypass actors. It currently requires 10 approving reviews; owner adjustment remains open in Issue #63.
- The GitHub API currently reports the repository as public. The previous owner decision to keep it public for standard hosted CI is recorded in Issue #53; no visibility setting was changed by this integration.

### Provider-neutral control-plane implementation
- Integration source before reconciliation: `2776d9c6e17d24d09a809c07549100e4f2c3c2ae`. It contains the task manifest/schema, SQLite coordinator, transactional dispatch outbox, provider router, Docker worker, daemon, watchdog/collector and deterministic tests.
- PR #71 current implementation head: `0afb73c43dfbb0726f42d33f87e09966aa1254a9`. Exact-head Push CI [42489733190](https://github.com/yarsalam/marketsage/actions/runs/42489733190) and PR CI [42489735618](https://github.com/yarsalam/marketsage/actions/runs/42489735618) succeeded; the provider-neutral suite passed **164/164**. Hosted Docker worker acceptance [42489733159](https://github.com/yarsalam/marketsage/actions/runs/42489733159) succeeded.
- The test suite covers two deterministic fake backends, capacity rejection, lost/ambiguous submission response, crash/restart reconciliation at dispatch boundaries, bounded failover after definitive no-effect outcomes, and one shared idempotent simulated side effect. No live paid provider or independently operated external backend has been activated.
- Health-observer tests cover stale/missing/clock-skewed heartbeats, expired leases, unknown telemetry, provider outage classification and watchdog lease recovery. Process-level observer outage/restart and independent alert delivery still require operational proof.
- The task registry remains a deterministic selector; it is not yet a complete GitHub Issue/PR → task contract → durable lease → dispatcher → Worker → status integration.

### Local Runner boundary
- Owner-provided host checks report the dedicated Runner service active with zero restarts and successful HTTPS proxy connectivity from the restricted Runner account.
- Two later local offline TSETMC validator runs succeeded (runs [42482467531](https://github.com/yarsalam/marketsage/actions/runs/42482467531) and [42482678959](https://github.com/yarsalam/marketsage/actions/runs/42482678959)). These validate the staged-data validator only; they are not the self-hosted Docker Worker acceptance.
- The earlier self-hosted Worker Acceptance attempt [42465921813](https://github.com/yarsalam/marketsage/actions/runs/42465921813) failed before its first workflow step and its job log was unavailable. The local acceptance workflow remains manual and owner-confirmed. Do not infer Worker success from the offline validator runs.
- The laptop is not a persistent 24/7 host. A separate independently available Worker host and a full 24-hour observation window remain unproven.

### Dependency and owner-action updates
- Issue #52 records successful Chabokan-only dependency installation in a clean temporary environment and **30/30** tests on the specified integration commit. Exact wheel-hash locking remains a separate reproducibility item.
- Issue #63 records the active main ruleset and the still-impractical 10-approval configuration. Owner action remains necessary to set the intended approval count and verify bypass semantics.

**Current infrastructure verdict: NOT COMPLETE / NOT 24/7 ACCEPTED.** Preserve research-only posture. No data-source approval, production scoring, ranking, calibrated probability, backtest approval, broker, trading, deployment or capital allocation is enabled.


## Live infrastructure checkpoint — 2026-11-13 14:49 UTC

This checkpoint supersedes older status statements above where they conflict with the live GitHub API. It is a repository-only audit; no workflow was dispatched or rerun, no local runner was used, and no merge, deployment, provider registration, secret, billing, plan, or visibility change was made.

### Repository, default branch and protection

- Default branch: `main`.
- Main HEAD: `4c4b032196137af4658ea2c28e38a21605ee923b`, committed `2026-11-07T19:55:51Z`. Main has not advanced in this audit.
- GitHub repository metadata reports `visibility=public` and `private=false`. This conflicts with the latest owner request describing the repository as private. Issue #53 records the earlier explicit public/zero-additional-spend decision. No visibility change was made; treat all repository contents and history as public until the owner resolves the mismatch.
- Active ruleset [#26789479](https://github.com/yarsalam/marketsage/rules/26789479) targets main and requires a PR, one approval, and seven named status contexts; deletion and non-fast-forward updates are blocked; no bypass actors are configured and the connected integration reports `current_user_can_bypass=never`.
- The ruleset has `strict_required_status_checks_policy=false` and `dismiss_stale_reviews_on_push=false`. The branch API reports `protected=true`, while the legacy protection subobject reports `enabled=false` and no enforced legacy status contexts. The active ruleset is the available enforcement evidence; do not describe strict freshness or stale-review dismissal as enabled.
- Required contexts are `analysis`, `user-backend`, `user-frontend`, `admin-workspace`, `production-images`, `Test provider-neutral control plane`, and `Test CI automation helpers`. Main's current `.github/workflows/ci.yml` does not define `Test provider-neutral control plane`; the required-check mismatch remains.

### Main CI and scheduled execution

- Main workflow blob: `3b0bc36ae8f95c6b34c4afe6a1535716b421a864`. It has push, pull_request, daily schedule `17 3 * * *`, and workflow_dispatch triggers; workflow permissions are `contents: read`; same-ref concurrency cancels superseded runs; jobs have bounded timeouts.
- The three local TSETMC workflows on main are manual-only. No local workflow was dispatched.
- Latest confirmed main schedule: [run #43414337932](https://github.com/yarsalam/marketsage/actions/runs/43414337932), event `schedule`, exact main SHA `4c4b032...`, completed successfully on 2026-11-13. It ran `analysis`, `user-backend`, `user-frontend`, `admin-workspace`, `production-images`, and CI helper tests successfully. This is CI/test/build activity, not a worker canary.
- The run started at 11:06:20 UTC against the configured 03:17 UTC cron, approximately 7h49m20s late. GitHub Schedule is not a precise timer; no independent lateness alarm is active.
- Main's schedule still executes the product/research test suite and production-image build. This conflicts with the current infrastructure-first freeze. The freeze exists on PR #74's branch only and is not active on main.
- Latest observed workflow history also includes superseded Push/PR runs cancelled by concurrency and newer exact-head runs. Cancellation of superseded commits is not a test pass; only completed successful runs on the exact SHA count.

### Infrastructure PR evidence

- PR #74 is Draft/open on exact head `24b95c204749b74ba2f382f4dd528d6463173dc9`, based on main. It is currently mergeable but is not approved for merge. Exact Push run [#43379843888](https://github.com/yarsalam/marketsage/actions/runs/43379843888) and exact Pull Request run [#43379849607](https://github.com/yarsalam/marketsage/actions/runs/43379849607) both succeeded on that SHA. The two runs produced 20 check-run records in total: scope classification, provider-neutral control-plane tests, and CI helper tests passed; application/research/admin/production jobs were scope-skipped. This is exact-head GitHub-hosted CI evidence for PR #74 only.
- PR #74's CI workflow blob is `27c7378d9e4e64456403a98d9e3fe57029b808eb`. Its fail-closed classifier treats schedule as infrastructure-only and blocks unknown/mixed/product changes rather than executing product commands. This freeze is not on main.
- PR #71 is Draft/open on exact head `e630517c7e2916ed58b7568b0ebbbf1d390b86ce`, based on PR #74. Current branch comparison: 117 commits ahead and 2 behind the current PR #74 head `24b95c204749b74ba2f382f4dd528d6463173dc9`; GitHub reports mergeable, but the branch is stale. Its exact current head has **0 check runs and 0 workflow runs**. Do not merge; reconcile the base and obtain separately authorized exact-head validation before review or merge.
- PR #54 is **closed, Draft, unmerged** at `e8f7d8add3df577120b92b8927c590aece001509`. Issue #55 records the owner's exact-current-head result of 16/16 tests, exit code 0. The earlier 11/11 result belongs only to the prior head. Against current PR #74 base, the SQLite branch is diverged: 8 commits ahead, 46 behind, merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`. Keep it closed/unmerged; no current GitHub checks exist for that SHA.
- PR #82 is a new Draft research notebook and is outside Goal 1. A scope-hold comment already instructs no further research work. Nevertheless, its exact head `880a1b1d683b4c3992743c5f046be2c80920c7cf` received successful Push [#43445772521](https://github.com/yarsalam/marketsage/actions/runs/43445772521) and Pull Request [#43445786681](https://github.com/yarsalam/marketsage/actions/runs/43445786681) runs from the old main CI; analysis and production-image checks ran. This is evidence that the freeze is not enforced on main, not authorization to continue research.

### Owner-action and safety state

- [Issue #49](https://github.com/yarsalam/marketsage/issues/49) remains open and is the hard gate. Existing owner actions remain: resolve the public/private visibility mismatch and explicitly authorize one bounded exact-head hosted validation only when ready. This audit did not dispatch or rerun any hosted workflow.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) remains open for five Chabokan wheel SHA-256 values. The prior 30/30 install/test evidence is not repeated.
- [Issue #53](https://github.com/yarsalam/marketsage/issues/53) is closed on the public-repository zero-additional-spend decision; no spending-cap increase or paid resource is authorized.
- [Issue #55](https://github.com/yarsalam/marketsage/issues/55) is closed for exact-head 16/16 SQLite unit tests only; it does not resolve branch divergence or operational acceptance.
- [Issue #59](https://github.com/yarsalam/marketsage/issues/59) remains open for event/schedule orchestration acceptance.
- PR #6 remains open/non-mergeable and must never be merged without separate explicit owner approval. PR #14 is already integrated into #6. PR #8 remains parked after its known TSETMC ConnectTimeout; do not repeat that request from the same environment.
- No independent persistent server runner, second live backend, external observer/alert failure domain, real host-loss/restart drill, off-host restore drill, worker-loss recovery proof, end-to-end canary, or 24-hour observation window is established.

**Goal 1 verdict: OPEN / NOT COMPLETE / NOT 24/7 READY.** Ordinary product, data, research, investment-analysis, backtest, and source-expansion work remains paused.


## Live infrastructure audit — 2026-11-14 14:19 UTC

This section supersedes earlier status snapshots where they conflict with the live GitHub reads and the current owner instruction.

### Repository and default branch
- GitHub repository metadata reports `visibility=public`; the request describes it as private. No visibility change was made. Treat all repository history, issues, PRs and committed documents as public.
- Default branch: `main`.
- Main HEAD: `4c4b032196137af4658ea2c28e38a21605ee923b`, commit time `2026-11-07T19:55:51Z`. The repository commit search found no newer main commit.
- Issue #49 remains open. Issue #52 remains open for five Chabokan wheel hashes. Issue #53 is closed (public-repository / zero-additional-spend decision). Issue #55 is closed (16/16 exact-head SQLite unit tests). Issue #59 remains open for schedule/orchestration acceptance.

### Active infrastructure PRs
- PR #74 is Draft/open, base `main`, head `b7ec545b83e370faaeeaf8960f4bf4ea70d43018`, API mergeable=true, and 77 commits ahead / 0 behind main. Its exact current head has no PR workflow runs and no combined-status entries. The preceding code/configuration head `24b95c204749b74ba2f382f4dd528d6463173dc9` passed Push run [#43379843888](https://github.com/yarsalam/marketsage/actions/runs/43379843888) and PR run [#43379849607](https://github.com/yarsalam/marketsage/actions/runs/43379849607); those results do not validate the current documentation head.
- PR #71 is Draft/open, base `infra/provider-neutral-control-plane-2026-11`, head `e630517c7e2916ed58b7568b0ebbbf1d390b86ce`, API mergeable=false. Comparing it with the current #74 head reports 117 ahead / 4 behind, merge base `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10`. Its exact current head has no PR workflow runs and no combined-status entries. Prior 174-control-plane + 36-helper test evidence on `9b8bb01e0e2d2c81aebb014d8124c761bdf5219a` is not transferable.
- PR #54 is closed, Draft and unmerged at `e8f7d8add3df577120b92b8927c590aece001509`. Issue #55 records 16/16 owner-run tests, exit 0, on that exact head. Comparing that SHA with current PR #74 head reports 8 ahead / 48 behind, merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`. The separate `infra/sqlite-durable-coordinator-reconciled-2026-11` branch compares 3 ahead / 23 behind PR #74, status diverged, merge base `a02946bd1fa524dbf1bd6e104b15bad224345b1b`. Neither is merge-ready evidence.

### Workflow and operational audit
- Main `.github/workflows/ci.yml` has push and pull_request triggers, daily schedule `17 3 * * *`, and workflow_dispatch. It uses `ubuntu-latest`, workflow-level `contents: read`, per-ref concurrency with `cancel-in-progress: true`, and bounded job timeouts (25/30/30/30/40/5/5 minutes). Job-scoped issue write is used for sanitized failure/provenance comments. Third-party Actions are pinned to immutable SHAs.
- Main's current workflow still runs Analysis/research-backtest, backend, frontend, admin and production-image jobs. The Goal 1 infrastructure-only freeze is present on PR #74's branch, not on main.
- The last confirmed main schedule is [run #43414337932](https://github.com/yarsalam/marketsage/actions/runs/43414337932), 2026-11-13, success. Its job summary shows the five product/research/build jobs completed successfully. The prior recorded start was about 7h49m after the 03:17 UTC cron. This is scheduled CI, not a worker canary or punctuality guarantee.
- The connected GitHub surface exposes PR-triggered runs for a supplied SHA and job summaries for a known run, but not a complete repository workflow-run listing. The 2026-11-14 scheduled run is therefore not independently confirmed in this audit.
- No explicit workflow retry policy, independent stale/queued-run observer, external alert path, or custom artifact/log retention was found in the inspected main/infra CI workflows. Failure-notification jobs execute on GitHub-hosted runners, within the same hosted failure domain as cloud CI.
- PR #71's Docker worker canary is not on main. It is configured for main push, daily 04:43 UTC schedule and manual dispatch; it uses `ubuntu-latest`, a 15-minute timeout, per-ref cancellation, a no-network sandbox, and a same-hosted-pool failure notifier. Its schedule is not active from the default branch until the workflow reaches main.
- PR #71's self-hosted worker acceptance remains manual-only, exact-branch/owner/confirmation guarded, and requires `[self-hosted, linux, x64, marketsage-server-worker]`; it has a 20-minute timeout and serializes without cancelling an active run. No independent server runner registration or run is verified. Its failure notifier uses `ubuntu-latest`, not an external alert service.
- The health observer documentation explicitly describes deterministic read-only assessment primitives, not a running monitor. It does not poll APIs or create heartbeats. Deployment, external polling, alert delivery, observer HA and recovery remain unproven.
- CircleCI configuration exists on PR #71, but no connected project, OAuth activation or real second-provider run is evidenced. The SQLite coordinator remains single-host; no multi-host HA/split-brain guarantee is claimed.
- `requirements-infra.txt` is not yet hash-locked. Issue #52 already contains the exact owner action for five Chabokan wheel hashes; do not repeat the prior 30/30 install/test.

### Protection and access limitations
- The latest branch document reports 10 required approvals on ruleset #26789479; an earlier live audit reported one. The current connected GitHub tools expose no ruleset or branch-protection read action, so current settings, required contexts, bypass behavior and the human merge gate are BLOCKED for live verification.
- Runner inventory/online status, complete Actions quota/billing metadata, and secret metadata are not exposed. No secret values were requested or read.
- The complete run list is unavailable through the connected tool surface; no claim is made about a 2026-11-14 schedule run.
- No hosted workflow was dispatched or rerun, no local/manual-only workflow was dispatched, and no merge, provider registration, secret, spending, deployment, release or visibility change occurred.

### Acceptance of this documentation increment
- Scope: repository-only governance refresh on the existing PR #74 infrastructure branch.
- Acceptance test: re-fetch both governance files after writing and verify the new audit marker, exact main/PR heads, issue states and owner-gate links.
- Stop condition: do not dispatch/rerun any workflow or claim exact-head CI success for the documentation commits. The new PR #74 head remains unvalidated until the owner separately authorizes one bounded hosted run.
- Issue #49 remains OPEN / NOT COMPLETE / NOT 24/7 READY. Independent persistent host, independent observer/alert, worker-loss/restart recovery, backup/restore drill, second real provider, end-to-end canary and a 24-hour observation window remain unproven.


## Live infrastructure audit — 2026-11-15 14:47 UTC

This section supersedes prior audit snapshots for live GitHub facts. Historical entries are retained as history, not as current evidence.

### Repository, main, and protection
- Live repository metadata: default branch `main`; visibility `public` (`private=false`). Issue #53 records the earlier zero-additional-spend public-repository decision, while the current owner request calls the repository private. No visibility change was made. Treat all repository contents and history as public.
- Main HEAD remains `4c4b032196137af4658ea2c28e38a21605ee923b`, commit time `2026-11-07T19:55:51Z`.
- Active ruleset #26789479 targets `refs/heads/main`: PR required, **one approving review**, seven required contexts (`analysis`, `user-backend`, `user-frontend`, `admin-workspace`, `production-images`, `Test provider-neutral control plane`, `Test CI automation helpers`), deletion and non-fast-forward blocked, strict status freshness disabled, stale approvals not dismissed, no bypass actors; the API reports `current_user_can_bypass=never`. The legacy branch-protection endpoint returned 403, so this is a live ruleset read, not a branch-protection read.
- The main `.github/workflows/ci.yml` remains the pre-freeze workflow: push on main/deploy/research/ci/infra branches, PR targets main/deploy/infra, daily schedule `17 3 * * *`, and workflow_dispatch. Workflow permissions default to `contents: read`; issue-write and pull-request-read permissions are job-scoped. Same-ref concurrency cancels superseded CI; jobs have bounded timeouts; no workflow retry policy is defined. The failure notifier runs on the same GitHub-hosted runner pool and cannot report a pool-wide outage independently.
- Latest observed default-branch scheduled run: [#43706919338](https://github.com/yarsalam/marketsage/actions/runs/43706919338), event `schedule`, main SHA above, created `2026-11-15T11:01:57Z`, completed `11:03:41Z`, success. It ran analysis/research-backtest, backend, frontend, admin, and production-image jobs successfully. It started 7h44m57s after the configured 03:17 UTC cron. This is ordinary scheduled CI, not a worker canary, and proves the product/research freeze is **not active on main**.
- Main contains four workflow files: `ci.yml` and three manual-only local TSETMC workflows. The local workflows remain workflow_dispatch-only, owner-confirmed, and were not dispatched.

### Active infrastructure branches
- PR #74 remains Draft/open, base main, head `52e8191e58306c15a0073da0148cf155c0fcf384`, API mergeable=true, but its exact HEAD has **zero check runs**. Its `.github/workflows/ci.yml` blob is `27c7378d9e4e64456403a98d9e3fe57029b808eb`; it classifies scope fail-closed, preserves required context names, makes the scheduled path infrastructure-only, skips product jobs for allowlisted infrastructure changes, and fails closed for other scopes. This freeze exists only on PR #74's branch and is not active on main.
- PR #71 remains Draft/open, base PR #74, head `e630517c7e2916ed58b7568b0ebbbf1d390b86ce`, API mergeable=false, with **zero exact-head check runs**. Compare against current PR #74 base: 117 ahead / 6 behind, diverged, merge base `237af3ba7e0473aaa94e3fc5512d7f3b172d1c10`. PR #71 contains the worker/outbox/watchdog implementation, so no duplicate implementation was started. Reconciliation and exact-head validation remain blocked; do not merge.
- PR #54 is closed, Draft, unmerged at `e8f7d8add3df577120b92b8927c590aece001509`. Issue #55 records 16/16 owner-run SQLite tests on that exact SHA; the earlier 11/11 result applies only to its prior head. Compared with current PR #74 base, the SQLite branch is diverged: 8 ahead / 50 behind, merge base `99b25dc24daa8606514bd9910e883ef136cf5d7f`. No GitHub checks exist for that SHA. Keep it closed/unmerged; do not transfer the owner-run result to another commit.

### Scope-hold and current queued run
- PR #82 is Draft/open, research-only, current head `1cdeb07f10d1b5bbc56ff519d50835cff8c0aa6e`. It advanced after the existing Goal 1 scope-hold comment. Its current exact head has successful MarketSage CI Push run [#43715142643](https://github.com/yarsalam/marketsage/actions/runs/43715142643) and PR run [#43715149785](https://github.com/yarsalam/marketsage/actions/runs/43715149785); both ran analysis, backend, frontend, admin, and production-image jobs. This is out-of-scope activity, not approval. The existing hold remains in force; no research work was performed by this audit.
- Separate Iran Equity Evidence Integrity run [#43715149800](https://github.com/yarsalam/marketsage/actions/runs/43715149800) is still queued for job `historical-market-state`; its job record has no steps, while the independent `integrity` job completed successfully. At this audit time the queued run is over two hours old. Record it as a stale/queued-run observation only; it is **not** a code failure, and no runner-loss conclusion can be drawn from the available job record.

### Open PR inventory and exact-head checks
The 15 open PRs were read from GitHub. Check counts below are GitHub Check Runs on each exact current head (duplicate contexts from separate push/PR events are counted separately):

| PR | State | Draft | Base | Exact head | Mergeable | Exact-head checks |
|---|---|---:|---|---|---:|---|
| #82 | open | yes | main | `1cdeb07f10d1b5bbc56ff519d50835cff8c0aa6e` | yes | 20: 14 success, 4 skipped, 1 queued, 1 cancelled |
| #81 | open | yes | main | `8d49042b520b78a877a5032bb9cf2e6f45e6169e` | yes | 17; success/skipped only |
| #80 | open | yes | main | `241241ee91f2dc944e0dc407bb6c5d1c409bc520` | yes | 8: 6 success, 2 skipped |
| #79 | open | yes | main | `14001bdb5a03775b9772bf9cfea1d169a68f8113` | yes | 8: 6 success, 2 skipped |
| #78 | open | yes | main | `47030f24d2d0491cb53eac5b089ff1dd4a15eccc` | yes | 10: 8 success, 2 skipped |
| #77 | open | yes | main | `67356939f65224a580c915fd2caa0ea52d8d09a9` | yes | 8: 6 success, 2 skipped |
| #74 | open | yes | main | `52e8191e58306c15a0073da0148cf155c0fcf384` | yes | 0 |
| #73 | open | yes | main | `72c57608e8270d999d1e9f2005b47ea56cb893a7` | yes | 16: 12 success, 4 skipped |
| #71 | open | yes | PR #74 | `e630517c7e2916ed58b7568b0ebbbf1d390b86ce` | no | 0 |
| #62 | open | no | main | `54fbf4a364a91b4e8d834fdcec0245d079440982` | yes | 8: 6 success, 2 skipped |
| #61 | open | yes | PR #74 | `25ce24283e35dd7e55eb8545c590a047606643ee` | no | 0 |
| #51 | open | no | PR #6 | `da803a1c69ba6524f7cc27d7b0cc4a3d4397df28` | yes | 10: all success |
| #41 | open | no | main | `162692f1a377ec8445ed958db4cc1171d4cafc47` | yes | 5: all success |
| #8 | open | no | fix/gdelt-fred-tindex-current-docs | `0cb94fd24f531162d4a3d403f9749789ce6f1797` | yes | 6: 5 success, 1 failed (`tsetmc-smoke`); remains parked |
| #6 | open | no | main | `1d90726c593b0818982407c309ff13301798f5b3` | no | 15: all success; **never merge without separate explicit owner approval** |

PR #14 is already integrated into PR #6 and must not be re-merged. PR #8's known TSETMC ConnectTimeout must not be repeated from the same environment.

### Owner gates, limitations, and stop condition
- Issue #49 remains open and is the hard gate. Existing owner action: confirm the public/private visibility intent; existing owner action: explicitly authorize one bounded exact-head hosted validation only when ready. No hosted workflow was dispatched or rerun.
- Issue #52 remains open for the five Chabokan wheel hashes; prior Chabokan-only 30/30 install/test evidence is not repeated.
- Issue #53 is closed on the public/zero-additional-spend decision. No spending-cap increase or paid resource is authorized.
- Issue #55 is closed with 16/16 SQLite tests on the exact SHA above; this does not resolve branch divergence or operational acceptance.
- Issue #59 remains open for orchestration acceptance.
- Branch-protection API access returned 403; the live Ruleset API was readable. No secret inventory, billing metadata, or runner inventory was accessed.
- No independent persistent server runner, second live backend, off-host observer/alert failure domain, real worker-loss/restart drill, off-host restore drill, end-to-end canary, or 24-hour observation is established. No 24/7 claim is permitted.
- **BLOCKED:** exact-head hosted validation of PR #74/#71 requires explicit owner authorization. PR #71 base reconciliation has no safe repository-only operation available through the current connected surface; no local checkout or local execution is claimed. Continue only independent repository-only infrastructure work.
- No hosted/local dispatch or rerun, merge, auto-merge, release, deployment, provider registration, secret creation, spending, visibility change, or product/data/investment work occurred.

**Goal 1 / Issue #49: OPEN / NOT COMPLETE / NOT 24/7 READY.**


---

## Continuity safeguards implementation — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Issue:** #49  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Latest recorded commit at this state update:** `99055b46ea88a9281ed7c678310b71052912c0bc` (the subsequent state update itself creates a newer commit)  
**Status:** IN PROGRESS / NOT ACCEPTED

### Implemented on this branch (not yet runtime-validated)

- Added `infra/control_plane/safety_gate.py`: standard-library-only JSONL registry readers, duplicate artifact/request detection, unresolved-path recovery stop, run fingerprinting from code SHA + input hashes + parameters + environment, duplicate-run rejection, immutable input hash verification, output-path collision checks, and fail-closed work/scope preflight.
- Added `tests/infra/test_safety_gate.py` with synthetic tests for duplicate artifact IDs/hashes, duplicate acquisition, unresolved paths, deterministic run fingerprints, duplicate failed-run blocking, changed parameters, and research scope-lock rejection.
- Added `docs/governance/WORK_PROTOCOL.md` with mandatory session startup, work-type procedures (acquisition, corporate-action adjustment, audit/test, backup/restore), preflight and end-of-task requirements.
- Added `execution_policy.json` with `INFRA_ONLY` scope and research lock enabled.
- Added append-only registry/ledger files. Three previously recorded adjusted-candidate CSV identities are retained with their known SHA-256 values and `PATH_UNRESOLVED`; no path, size, request parameters, rights approval or backup status is invented. They must not be re-downloaded or reconstructed before recovery search.
- Added the unique work-item record `MS-20261116-CONTINUITY-001`.
- Extended the execution constitution to bind the detailed work protocol and machine-readable safety records.

### Validation and limitations

- GitHub confirmed each file commit and each changed file was read from the branch during implementation.
- No Python test command was run in this environment. The synthetic tests are authored but **NOT YET VERIFIED**.
- No CI workflow was dispatched or rerun. All implementation commits use `[skip ci]`; exact-head hosted validation still requires separate owner authorization.
- The safety gate is a reusable primitive. The PR #74 branch CI now includes the synthetic safety-gate test module in the existing required control-plane test job, and the scope classifier allowlists only the dedicated `tests/infra/` path. This CI change has not run on the new head. Existing acquisition/research entry points are **not yet wired to call preflight**; therefore this is not yet an enforced repository-wide gate.
- `RUN_LEDGER.jsonl` is initialized empty; prior historical runs have not been backfilled. A future run must be recorded before it can be safely deduplicated by this ledger.
- Durable 3-copy / 2-media / offline backup and restore proof are NOT implemented. No storage destination has been authorized or verified.
- The three candidate CSVs remain `PATH_UNRESOLVED`. No archive scan or restore was performed.

### Current owner gates / next permitted action

1. Continue repository-only infrastructure work on this branch: harden and test the gate, add schema validation, wire it into CI and relevant entry points without executing research.
2. Keep PR #74 Draft/open/unmerged. Do not dispatch/rerun CI until separately authorized.
3. Keep PR #82 Draft/open/unmerged and all research/data work locked.
4. Do not merge, deploy, change visibility, create secrets, spend, activate providers, or dispatch local workflows.

**Issue #49 remains OPEN / NOT COMPLETE / NOT 24/7 READY. Research remains LOCKED.**


### Follow-up implementation — CI test wiring (2026-11-16)

- Extended the existing PR #74 infrastructure test job to run `python -m unittest discover -s tests/infra -p 'test_safety_gate.py' -v`.
- Added only `tests/infra/` to the infrastructure path allowlist and added a classifier regression assertion for the safety-gate test path.
- Latest implementation commit: `e2f7ce5fdf613ce1941529d715418b99aa9da0ad`.
- Commits remain `[skip ci]`; the exact-head test job has NOT run. No dispatch/rerun was performed.
- Main remains unchanged; the infrastructure-only CI design remains only on PR #74 and is not active on main.


---

## Governance schema validation checkpoint — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Implementation head immediately before this state update:** `e9de35445793b6e7defb74cc44ebb1bf4bccc4c6`  
**Status:** IN PROGRESS / NOT ACCEPTED / NOT RUNTIME-VERIFIED

### Repository-only changes authored and read back from GitHub

- Added `schemas/governance-records-v1.schema.json` with strict Draft 2020-12 record definitions for artifact registry, run ledger, execution policy and active work item.
- Added `infra/control_plane/validate_governance.py`: validates schema correctness, canonical policy/work item, every JSONL record, unique artifact IDs/identities/hashes/acquisition fingerprints, unique run IDs/fingerprints, work-item authorization, action scope and research-lock consistency.
- Added `tests/infra/test_governance_validation.py` with synthetic regression cases for duplicate artifact identity/hash/request, unresolved-path safety, duplicate failed/successful run fingerprints and research-lock violations.
- Extended CI's existing infrastructure test job to invoke the canonical validator and the new synthetic test module.
- Added the new schema to the infrastructure-only CI allowlist and a classifier regression assertion.
- Updated the work item acceptance criteria and the canonical work protocol with the validator command and exact-evidence rule.

### Validation boundary

- All changed files were fetched back from the branch; GitHub returned successful file/commit responses.
- No Python test, schema-validation command or CI workflow was executed in this turn. The new implementation is **AUTHORED / NOT VERIFIED**.
- The commits were marked `[skip ci]`; no workflow dispatch/rerun occurred. Exact-head hosted validation remains blocked pending separate owner authorization.
- No data, provider, research or adjustment workflow was accessed. The research lock remains active.
- This checkpoint does not yet wire preflight into every existing acquisition/research entry point, backfill historical run evidence, or prove the three-copy/two-media/offline backup and restore policy.

### Next permitted action

Continue repository-only infrastructure work: audit the remaining execution entry points and add a fail-closed preflight adapter at safe boundaries without executing them; then add tests for missing/corrupt canonical records and immutable raw-file tampering. Exact-head CI validation still requires the separately recorded owner authorization.

**Issue #49: OPEN / NOT COMPLETE. PR #74: Draft/open/unmerged. PR #82: Draft/open/unmerged. Research: LOCKED. 24/7 readiness: NOT PROVEN.**


### Work-item status correction

- The canonical work item is now `IN_PROGRESS` (not merely `AUTHORIZED`); its status-note explicitly says the validator and tests are authored but not executed.
- Work-item update commit: `b687b34b97dab8c472f67590be9bd81f08b6b4cf`.


---

## Fail-closed workflow preflight checkpoint — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Implementation head before this state update:** `c2ea4d03c02bbf8ea16879a0f9399f7236a0f060`  
**Status:** IN PROGRESS / NOT ACCEPTED / NOT RUNTIME-VERIFIED

### Changes authored and read back

- Corrected `safety_gate.py` to accept the real 40-character Git commit SHA, permit the canonical work item while `IN_PROGRESS`, validate the execution policy's required fields/action allowlist, reject symlinked immutable artifact paths, and reject output paths that overlap immutable artifact paths in either direction.
- Added `verify_immutable_artifact`; registered immutable inputs are re-hashed and size-checked immediately before use.
- Added `infra/control_plane/preflight_cli.py`, a side-effect-free workflow adapter that fails closed before research/data steps.
- Added synthetic tests for valid active infrastructure preflight, missing/corrupt canonical records, immutable raw-file tampering, and workflow CLI behavior.
- Added preflight steps before data/output access in all three existing local TSETMC workflows: offline acceptance, integrated acceptance and sanitized diagnostics.
- Added exact workflow paths to the infrastructure-only CI allowlist and regression tests asserting each workflow's preflight precedes its data/output action.
- Updated the canonical protocol, work item and CI job to include the new adapter and test command.

### Validation boundary

- Modified files were fetched back from GitHub after writes.
- No Python tests or workflow were executed. All commits use `[skip ci]`; exact-head hosted checks remain zero/not available pending separate owner authorization.
- The workflow gates become effective only when this branch is integrated into the default branch. PR #74 remains Draft/open/unmerged.
- The CLI gate blocks current research actions under `INFRA_ONLY`; it is not a substitute for durable run reservation/append at future unlocked execution time.
- The Run Ledger remains empty; no historic run evidence was fabricated or backfilled.
- The three unresolved candidate CSV records remain unchanged. No provider, dataset, local Runner or research operation was accessed.

### Next permitted action

Continue repository-only work: add an explicit run-ledger reservation/finalization interface with concurrency-safe idempotency, and a contract test that proves failed runs remain reserved against identical retries. Then inspect backup/restore implementation gaps. Do not dispatch or rerun CI without separate owner authorization.

**Issue #49: OPEN / NOT COMPLETE. PR #74: Draft/open/unmerged. PR #82: Draft/open/unmerged. Research: LOCKED. 24/7 readiness: NOT PROVEN.**


---

## Append-only run reservation checkpoint — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Implementation head before this state update:** `cc84d6d42bb3557402dd801412ea059485dda465`  
**Status:** IN PROGRESS / NOT ACCEPTED / NOT RUNTIME-VERIFIED

### Changes authored and read back

- Added append-only run events to the governance schema: one `RESERVED` event and at most one `FINALIZED` event per run.
- Added `reserve_run`: an OS file lock protects the read/check/append transaction; any prior matching fingerprint blocks a new run, including an earlier failed or still-running reservation.
- Added `finalize_run`: appends one terminal event and refuses a second finalization; existing events are never edited.
- Added `preflight_and_reserve_run`: enforces preflight before the atomic reservation, plus the terminal finalization API.
- Removed the generic unguarded JSONL append helper from the safety module.
- Updated the governance validator to check event IDs, fingerprint ownership, reservation/finalization order, authorization, and one terminal event maximum.
- Added synthetic tests for failed-run retry blocking, one-time finalization, combined preflight/reservation and both event schema variants.
- Updated WORK_PROTOCOL and the active work item's acceptance criteria.

### Validation boundary

- Changed source, schema, tests, workflows and governance records were fetched back from GitHub after writes.
- No tests, Python commands or workflows were executed. All commits use `[skip ci]`; exact-head hosted checks remain absent pending separate owner authorization.
- This provides repository-side reservation primitives but does not yet persist run events automatically from every GitHub/local execution environment. The current RUN_LEDGER remains empty; no historical runs were invented or backfilled.
- A reserved run left without a final event intentionally blocks retry; a separately authorized recovery procedure is still needed for abandoned reservations.
- No real data, provider, local Runner, research or adjustment process was accessed. Candidate CSVs remain PATH_UNRESOLVED and unchanged.

### Next permitted action

Inspect and design the durable storage/restore layer for the canonical registry and ledger: define independent backup locations, append-only evidence export, integrity checks and a synthetic restore drill. Do not access local private paths or perform real backups until the owner authorizes that host-specific operation.

**Issue #49: OPEN / NOT COMPLETE. PR #74: Draft/open/unmerged. PR #82: Draft/open/unmerged. Research: LOCKED. 24/7 readiness: NOT PROVEN.**


---

## Backup/restore primitives checkpoint — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Implementation head before this state update:** `5834b9d44504167148aa4ac09fcd2b3485a4666b`  
**Status:** IN PROGRESS / NOT ACCEPTED / NOT RUNTIME-VERIFIED

### Changes authored and read back

- Added `infra/control_plane/backup_restore.py` with exclusive-create backup copies, source-before/after consistency checks, SHA-256/size verification, 3-2-1 metadata validation, and non-overwriting restore with post-restore verification.
- The 3-2-1 validator requires at least three distinct locations, two media, two failure domains and an offline attestation. The attestation is explicitly not treated as proof of physical disconnection.
- Added synthetic tests for valid topology, missing offline attestation, tampered copies, exact restore and no-overwrite behavior.
- Added the backup/restore test to the infrastructure CI job and documented the operator/host verification boundary.
- The previous checkpoint's append-only reservation/finalization and preflight integration remain in place.

### Validation boundary

- Source, tests and workflow changes were read back from GitHub.
- No backup or restore was run against real MarketSage data or private host paths.
- No Python test was executed. The latest commit query currently shows zero workflow runs and zero combined status entries; no manual dispatch/rerun was made.
- One documentation commit was created without the `[skip ci]` suffix; its current commit query also shows zero runs/statuses. All subsequent commits must continue to use `[skip ci]` unless separately authorized.
- No evidence yet proves three physical copies, two independent media, an offline device, a successful host restore, or durable automatic export of the registry/ledger.

### Next permitted action

Add a versioned backup-manifest schema and integrity validator for backup-copy records, then extend synthetic tests for manifest corruption and restore-set completeness. A real host backup/restore drill remains separately owner-authorized.

**Issue #49: OPEN / NOT COMPLETE. PR #74: Draft/open/unmerged. PR #82: Draft/open/unmerged. Research: LOCKED. 24/7 readiness: NOT PROVEN.**


---

## Versioned backup manifest checkpoint — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Implementation head before this state update:** `92639ff34d35be33781fcf3dabed513a15237663`  
**Status:** IN PROGRESS / NOT ACCEPTED / NOT RUNTIME-VERIFIED

### Changes authored and read back

- Added `schemas/backup-manifest-v1.schema.json` for immutable copy records and restore-drill evidence.
- Added `infra/control_plane/validate_backup_manifest.py` to validate the strict schema and cross-record consistency: same artifact/hash/size across copies, three locations, two media, two failure domains, offline attestation, unique copy paths and at least one successful matching restore record.
- Extended synthetic backup tests to validate a complete manifest and reject copy hash mismatch.
- Added the new schema to the infrastructure-only CI path allowlist and a classifier regression assertion.
- Updated WORK_PROTOCOL and the active work item's expected outputs/acceptance criteria.

### Validation boundary

- Files were fetched back from GitHub after changes.
- No tests or workflows were executed; no real backup, host path, or restore operation was performed.
- The manifest can validate an operator's offline attestation but cannot prove physical disconnection or independent media; that remains a host-level acceptance test.
- The canonical RUN_LEDGER remains empty. No historic records were invented.
- Research remains locked; candidate CSVs remain PATH_UNRESOLVED and untouched.

### Next permitted action

Perform a repository-only integrity audit of the complete governance toolchain: confirm schema/validator compatibility, every required test is included in CI, every local research workflow is preflight-gated, and no path/identifier can escape configured roots. Record only static/read-back evidence; runtime tests and host backup remain owner-gated.

**Issue #49: OPEN / NOT COMPLETE. PR #74: Draft/open/unmerged. PR #82: Draft/open/unmerged. Research: LOCKED. 24/7 readiness: NOT PROVEN.**


---

## Backup manifest integrity checkpoint — 2026-11-16

**Work ID:** `MS-20261116-CONTINUITY-001`  
**Branch:** `infra/provider-neutral-control-plane-2026-11`  
**Implementation head before this state update:** `92639ff34d35be33781fcf3dabed513a15237663`  
**Status:** IN PROGRESS / NOT ACCEPTED / NOT RUNTIME-VERIFIED

### Changes authored and read back

- Added `schemas/backup-manifest-v1.schema.json`, a strict versioned manifest schema for 3-2-1 copy records and restore-drill evidence.
- Added `infra/control_plane/validate_backup_manifest.py` to validate the schema and cross-record topology/identity invariants.
- The validator now re-hashes the actual backup-copy files and restored file, checks exact byte sizes, rejects symlinked evidence paths, verifies all copies belong to the same artifact/backup set, and requires restore evidence from one of the recorded copies.
- Added a synthetic manifest-validation test and allowlisted the schema as an infrastructure-only path.
- CI already includes the synthetic backup/restore test module.

### Static evidence only

- Relevant source, test, schema, workflow and protocol files were fetched back from the current branch.
- The three local TSETMC workflows contain a preflight command before their data/output step; the classifier and contract test include those workflow paths.
- The infrastructure CI file contains test commands for the safety gate, preflight CLI, backup/restore and governance validation suites.
- No Python tests, YAML parser, schema command or workflow was executed. These are source/read-back checks only.
- No real backup, restore, local path access, data operation or provider request occurred. Offline status remains an operator attestation until physically verified.

### Next permitted action

Complete the final static integrity audit, update the active PR/Issue checkpoint and preserve the research lock. Exact-head runtime validation, host backup/restore, and any merge remain separately gated.

**Issue #49: OPEN / NOT COMPLETE. PR #74: Draft/open/unmerged. PR #82: Draft/open/unmerged. Research: LOCKED. 24/7 readiness: NOT PROVEN.**

---

## Live continuity audit — 2026-11-16 (Work ID: MS-20261116-CONTINUITY-001)

- Re-read the active branch protocol, execution constitution, policy, active work item, artifact registry and run ledger before further work.
- Current policy remains `INFRA_ONLY`; `research_locked=true`. Allowed actions are infrastructure, governance and synthetic tests only. No provider request, dataset read, research calculation, workflow dispatch/rerun, local Runner job, merge or deploy was performed.
- Existing artifact registry contains the three known adjusted-candidate CSV identities and expected SHA-256 values. All remain `PATH_UNRESOLVED`; no archive recovery scan or replacement acquisition was attempted. `RUN_LEDGER.jsonl` remains empty; no historic run was fabricated.
- Inspected the exact-head CI evidence referenced by Issue #49. Run [#43794311916](https://github.com/yarsalam/marketsage/actions/runs/43794311916) completed scope classification and CI-helper tests successfully, then failed in the workflow-preflight CLI test. Later steps in that job were skipped. This is an observed CI failure, not a successful acceptance run.
- Static comparison identified a deterministic error-order mismatch: the locked-scope test expects `project_scope_locked`, but preflight previously returned the allowlist error first. Corrected the check order in `infra/control_plane/safety_gate.py` in commit `c8c1b1c87c75f7425e6a3c2b6b952d661230546c`. The correction is authored/read-back only; it has not been tested and must not inherit the failed run's evidence.
- Static audit also found material acceptance gaps that remain blockers: the workflow CLI supplies no registered input artifacts, uses a synthetic `/tmp` output path rather than the workflow's real output boundary, and does not reserve/finalize a durable run-ledger event. The runtime preflight does not itself perform the full JSON-Schema/cross-record validation used by the CI validator. Therefore the current CLI is only a lock gate and must not be treated as a complete research authorization mechanism, even if policy is later changed.
- Backup/restore code and manifest validation are authored, but no real copies, independent media/failure-domain evidence, physical offline verification or host restore drill exist. Synthetic tests are authored but not executed.
- Exact current branch-head workflow/status evidence must be re-read after this checkpoint; prior green checks do not transfer to the new commit. PR #74 remains Draft/open/unmerged; PR #82 remains held and untouched.
- **Status:** `IN_PROGRESS`; no acceptance claim. **Next permitted action:** continue repository-only hardening of the preflight/ledger integration and static review; do not run tests or workflows until the owner separately authorizes a bounded exact-head validation. Research remains locked.

---

## Repository-only hardening checkpoint — 2026-11-16

Work ID: `MS-20261116-CONTINUITY-001`

- Fixed the observed preflight test failure by making the scope lock take precedence over the action allowlist. The expected lock reason is now deterministic. Change: `infra/control_plane/safety_gate.py`.
- Added fail-closed requirements: research/analysis/backtest must provide at least one registered immutable input artifact; acquisition must provide a SHA-256 request fingerprint. Tests were authored for both conditions.
- Hardened `preflight_cli.py`: even if the policy is later opened, the legacy research workflows remain blocked until the CLI is upgraded to accept registered input manifests, validate the actual workflow output path, and persist durable RESERVED/FINALIZED run events. A test covers the unlocked-policy case.
- Hardened CI scope classification: reject absolute/traversal/backslash/control-character paths and parse `git diff --name-only -z` as NUL-delimited paths so embedded newlines cannot split a changed filename into allowlisted fragments. Regression tests were authored.
- All changes were written to the existing PR #74 branch with `[skip ci]` commits. They are authored and read back from GitHub; **no tests or workflows were run for these corrections**. The prior run #43794311916 remains a failure on its tested SHA; it is not evidence for the corrected code.
- Static review of backup helpers/schema found the required no-overwrite, hash/size verification, 3-location/2-media/2-failure-domain and offline-attestation metadata checks, plus at least one restore-drill record. Physical independence/offline isolation is not machine-proven and no real backup/restore has been performed.
- Remaining technical blockers: runtime preflight still does not invoke the full strict JSON-Schema/cross-record governance validator; legacy workflow CLI does not bind actual registered inputs/output destinations or durable run events; historical runs have not been reconstructed; and real host backup/restore remains unproven.
- Registry retains the three pre-existing candidate CSV identities/hashes as `PATH_UNRESOLVED`. Registry archive locations are empty; no local/registered archive scan, redownload, or reconstruction was performed under the research lock. RUN_LEDGER remains empty.
- No changes were made to PR #82. PR #74 remains Draft/open/unmerged. No merge, workflow dispatch/rerun, local Runner, provider/network request, dataset read, calculation, deploy, secret, spend or visibility change occurred.
- **Status:** `IN_PROGRESS`; Issue #49 remains open and 24/7 readiness is not proven. **Next permitted action:** continue repository-only integration of strict runtime governance validation and durable execution-ledger interfaces; exact-head validation and any real host backup drill remain owner-gated.

### Exact-head read-back after repository-only hardening

- Branch head immediately before this state refresh: 92aa26c09626a6d72ece86c330374b3d9a9ec922.
- Branch comparison against main: 176 commits ahead, 0 behind; merge base is the current main SHA 4c4b032196137af4658ea2c28e38a21605ee923b.
- Exact-head workflow-run query for 92aa26c: zero PR workflow runs. Combined status query: zero status entries. This is absence of validation, not a pass.
- Read-back confirmed the changed safety gate, CLI, tests, classifier, protocol, work item, registry and ledger. Registry still has exactly three unresolved candidate records; ledger is still empty.
- The known prior CI failure #43794311916 remains the only observed validation outcome for the affected earlier code: Test provider-neutral control plane failed at the CLI test; scope classification and CI helper tests passed. The corrective commits have no test evidence.


## Owner-authorized bounded validation — 2026-11-16

Work ID: `MS-20261116-CONTINUITY-001`

- The owner explicitly authorized one bounded exact-head hosted validation in this conversation after the prior untested hardening checkpoint.
- Scope remains `INFRA_ONLY`; `research_locked=true`. This authorization is limited to the existing infrastructure/synthetic-test acceptance suite. It does not authorize research reopening, provider requests, downloads, dataset reads, calculations, local Runner dispatch, workflow_dispatch/rerun, merge, deploy, secrets, spend or visibility changes.
- Reuse the existing PR #74 branch and work item. No new issue, PR, work ID, or duplicate test is created. The existing failed run #43794311916 remains attached to its original SHA and is not retried as-is; validation is for the new exact head after the recorded code changes.
- Acceptance: exact-head CI must run the infrastructure control-plane tests, preflight CLI tests, backup/restore tests and governance validation. Record the actual result and run ID; skipped jobs are not passes. If the exact-head run fails, do not repeat without a material correction and a recorded reason.


## Validation execution blocker — 2026-11-16

Work ID: `MS-20261116-CONTINUITY-001`

- The owner-authorized bounded validation was prepared against the existing PR #74 branch. Checkpoint commit: `addcb4be3821543ad5bf5aa41f17ddff636bedd1`.
- The GitHub Contents API write did not produce a push workflow run (no new run appeared for that commit). The connected GitHub integration exposes no workflow-dispatch or push-as-user operation. A local checkout is also unavailable in this execution environment; network clone was unavailable.
- Existing runs `43794311916` and `43794316955` both target the older SHA `5834b9d44504167148aa4ac09fcd2b3485a4666b`; both failed at the preflight CLI test. They are not valid evidence for the current branch HEAD and were not rerun.
- No tests were executed. No run event was fabricated; `RUN_LEDGER.jsonl` remains empty. No provider request, data download/read, research calculation, local Runner job, workflow dispatch/rerun, merge or deploy occurred. Research remains locked.
- Work item status is now `BLOCKED` solely on the missing exact-head execution path. Do not rerun the old SHA. **Next permitted action:** provide an authorized exact-head CI execution path (workflow dispatch capability or an approved local checkout/runner), then run the existing infrastructure suite once and record the exact result.
