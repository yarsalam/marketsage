# MarketSage — Current Project State

**Snapshot date:** 2026-11-06  
**Repository:** yarsalam/marketsage (Private)  
**Main HEAD:** 07e641670ceab22496ef976a584934464570fd9a  
**Integration PR:** #6, feat/tindex-free-data-connector  
**Current integration HEAD:** 1d90726c593b0818982407c309ff13301798f5b3  
**Pinned integration code commit:** 819f8b4028469cb0d498098fec88545a18ebacc6  
**Release posture:** research-only. No data source has passed the complete investment-source gate; no representative strategy has passed empirical validation; production ranking/scoring, broker access and trading remain disabled.

## Executive state

- PR #6 remains open and **must not be merged to main without explicit owner approval**. Its current integration code is used by the new local workflow only through the immutable commit SHA above.
- PR #8 remains parked after the GitHub-hosted TSETMC connection timeout. Do not repeat the same request from the same environment.
- PR #27 (manual-only staged-dataset validator), PR #31 (clean governance adoption), PR #32 (manual integrated TSETMC workflow) and PR #34 (memory-bounded local analysis) are merged to main. PR #15 was closed as superseded; its divergent branch was not merged.
- PRs #7, #9, #13, #14, #16–#24, and #28–#30 are integrated into PR #6 in dependency order. Their CI results do not approve data sources or the strategy.
- The governance constitution is adopted on main via PR #31. Main branch protection is not enabled; the local Runner uses the owner-approved manual-only compensating-control model. This is not equivalent to branch protection/rulesets.

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
- The latest owner-local validation attempt failed during dependency bootstrap before tests; the manifest and lifecycle test modules have not run from a clean checkout. The mirror probe is now HTTPS-downgrade-safe and has six offline regression tests; those passed only in an isolated temporary harness, not on the owner network or from a clean repository checkout.
- [Issue #52](https://github.com/yarsalam/marketsage/issues/52) is the owner-action handoff for running the bounded mirror probe on the actual worker network. Until that evidence exists, no mirror is selected and no dependency constraints are changed.
- Oracle signup returned an export/compliance denial. Do not bypass it by changing identity, address, location, VPN or using another person's account.
- The laptop Runner is registered and isolated for reviewed manual local workloads, but it is not an always-on control plane and does not establish 24/7 readiness. No local workflow is dispatched by this update.

**Current status:** infrastructure not ready; durable queue/outbox, real provider adapters, restart recovery, stale-run monitoring, independent backend failover and a clean end-to-end zero-cost canary remain unproven. Research scoring/ranking, backtest approval, production deployment and trading remain disabled.
