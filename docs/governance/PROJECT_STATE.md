# MarketSage — Current Project State

**Current snapshot date:** 2026-11-09  
**Repository:** yarsalam/marketsage (**Public**, verified from GitHub repository metadata)  
**Main HEAD:** 4c4b032196137af4658ea2c28e38a21605ee923b  
**Active product issue:** [#72 — Product Phase 1: evidence-first Market Coverage Workspace](https://github.com/yarsalam/marketsage/issues/72)  
**Active product branch:** `research/market-coverage-workspace-2026-11`  
**Product PR:** [#73 — evidence-first Market Coverage workspace](https://github.com/yarsalam/marketsage/pull/73), Draft and open; latest exact head `4e50e908d68c058113c960647276833058fc5cea`; feature implementation, refresh/retry fix and documentation progress are on this branch  
**Infrastructure PR:** [#71](https://github.com/yarsalam/marketsage/pull/71), Draft, open and unmerged  
**Release posture:** research-only. No source is approved for production investment scoring; no validated probability model or strategy is approved; production allocation, broker access and trading remain disabled.

## Owner execution priority update — 2026-11-09

- Product, data-quality, source-contract and research-system engineering continue independently of the infrastructure backlog.
- Ordinary CI, build and test jobs use GitHub-hosted runners. No project task may wait for the owner's laptop Runner unless the exact task requires local-only data or host access.
- If local execution is essential, provide one bounded owner command and continue unrelated product work.
- PR #73 latest exact head `4e50e908d68c058113c960647276833058fc5cea`; push run #42615545257 and PR run #42615554518 both passed.
- The local dataset acceptance run #42482678959 passed once; this is not evidence of 24/7 Runner availability. Issue #57 is closed as non-blocking; PRs #71 and #74 are parked. PR #74 must not be merged unchanged because its CI intentionally suppresses product tests.
- Main remains protected. PR #6 remains explicitly unmerged. No source approval, production investment scoring/ranking, calibrated probabilities, backtest approval, production deployment, broker access, trading or capital allocation is authorized.

## Current product state — 2026-11-09

- The owner explicitly resumed MarketSage product development. Product work proceeds independently of the remaining infrastructure evidence gap; that gap must not silently be labelled accepted or complete.
- Phase 1 is an evidence-first Market Coverage Workspace. It exposes the existing Python source registry, data-quality report and Iranian provider-readiness catalog via NestJS and a Persian RTL Next.js page.
- In this branch, read-only NestJS endpoints were added: `GET /api/markets/sources`, `GET /api/markets/data-quality`, and `GET /api/markets/iran-providers`. Controller forwarding tests were added.
- The Persian coverage page reads those APIs and presents source status, market scope, asset family, research wiring, production approval state, timestamp quality, data-capture/freshness status, source gates and Iranian provider readiness. The page is the default landing tab for this increment.
- NestJS unit tests cover forwarding of the new API routes and bounded service-unavailable behavior when the analysis engine is unreachable.
- PR #73 is Draft and open at exact head `4e50e908d68c058113c960647276833058fc5cea`. The coverage page now supports manual refresh and retry after fetch failure; its loading state is abort-safe. Exact-head push run [42615545257](https://github.com/yarsalam/marketsage/actions/runs/42615545257) and PR run [42615554518](https://github.com/yarsalam/marketsage/actions/runs/42615554518) both passed all substantive jobs, including analysis, backend, frontend, admin workspace and production image build. No local Runner was used.
- The page reports actual registry and runtime values only. It does not create synthetic quotes, infer provider availability, approve data, or change scoring.
- Product plan: [docs/PRODUCT_RESTART_PLAN_2026-11.md](../PRODUCT_RESTART_PLAN_2026-11.md). Current acceptance checklist: Issue #72.
- The integration PR #6 remains open and must not be merged to main without separate explicit owner approval. PR #8 remains parked. PRs #71 and #74 are infrastructure-only, Draft and unmerged; #74's temporary product-CI freeze is superseded and that PR must not be merged unchanged.

## Current data and investment posture

- Main's source registry contains ten source definitions; none is production-approved. Yahoo Finance via yfinance is the only source wired into the current research baseline, and remains research-only.
- FRED/ALFRED adapter exists but is not scheduled or connected to the scoring path.
- TSETMC and CODAL are candidate-only. Iranian gold/FX sources are not selected; fixed-income/fund and local crypto sources remain unapproved.
- The existing decision/momentum path uses a small global-proxy/crypto universe. Its nominal horizon parameter does not make the calculation a six-month-specific forecast. It is a research baseline, not a validated investment decision engine for Iran.
- Publication-time-aware macro, news, political/geopolitical events, social sentiment, validated regime detection and calibrated probabilities are not available as production decision inputs.
- Captured-as-of replay must not be confused with publisher-source-vintage replay. Historical Yahoo prices have retrieval time but no verified original publication timestamp.
- No source approval, investment scoring/ranking, probability calibration, backtest approval, production deployment, broker connection, trade or capital allocation is authorized by this restart. The six-month product objective stays binding.

## Infrastructure status — separately tracked

- The owner supplied host output showing the dedicated UID-110 Rootless Docker daemon active, socket owned by UID 110, `rootless` and `seccomp` security options present, only `host` and `none` networks, and the system-wide Docker daemon preserved.
- The latest recorded self-hosted dataset-acceptance dispatch [#42482678959](https://github.com/yarsalam/marketsage/actions/runs/42482678959) completed successfully on 2026-11-08. This is one manual run only; it does not prove live availability, 24/7 operation, independent failure-domain recovery or general worker acceptance. Product work must not depend on this Runner.
- GitHub-hosted Docker acceptance [#42465921830](https://github.com/yarsalam/marketsage/actions/runs/42465921830) and PR CI [#42465926206](https://github.com/yarsalam/marketsage/actions/runs/42465926206) passed for the corresponding infrastructure commit.
- PR #71 remains Draft and unmerged. No merge to main was made. Live independently operated backend failover and a complete 24-hour observation window are not evidenced in the repository at this snapshot.
- Product Phase 1 does not dispatch local-runner jobs and does not depend on this infrastructure acceptance record.

## Next product sequence

1. Complete Phase 1 coverage workspace and pass exact-commit CI for PR #73.
2. Add a verified instrument/universe registry with separate Iran/global identities, venue, symbol lifecycle, quote currency and units.
3. Close source-rights, connectivity, timestamp, historical-coverage, unit, corporate-action and independent-reconciliation gates provider by provider; keep unknowns quarantined.
4. Stabilize point-in-time storage and FRED/ALFRED vintages; preserve raw response references, hashes, parser versions and revisions.
5. Build verified Iranian price/FX/gold/fixed-income/crypto series as separate families; do not merge official/free-market rates or local/global crypto pairs.
6. Add news and macro/event context only after original-source and publication/update timestamps are audited.
7. Revisit the six-month research baseline and existing Stage 4 anomaly using the exact original dataset/hash; keep the final holdout unopened.
8. Only after the owner-approved source and empirical gates pass may any investment-facing calculation be proposed for separate review.

The prior 2026-11-05 operational snapshot is preserved below as historical evidence; its pending actions and state descriptions are not a statement of current status.

## Historical snapshot — 2026-11-05


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
