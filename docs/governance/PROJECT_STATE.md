# MarketSage — Current Project State

**Snapshot date:** 2026-11-05  
**Repository:** yarsalam/marketsage (Private)  
**Main HEAD at last inspection:** 07e641670ceab22496ef976a584934464570fd9a (after PR #38 merged)  
**Integration PR:** #6, feat/tindex-free-data-connector  
**Pinned integration code commit (updated by this PR):** 1dc6894c0823f6ffe77d27fd866576f5115a042c  
**Release posture:** research-only. No data source has passed the complete investment-source gate; no representative strategy has passed empirical validation; production ranking/scoring, broker access and trading remain disabled.

## Executive state

- PR #6 remains open and **must not be merged to main without explicit owner approval**. Its current integration code is used by the new local workflow only through the immutable commit SHA above.
- PR #8 remains parked after the GitHub-hosted TSETMC connection timeout. Do not repeat the same request from the same environment.
- PR #27 (manual-only staged-dataset validator), PR #31 (governance adoption), PR #32 (manual integrated TSETMC workflow), PR #34 (memory-bounded local analysis), PR #35 (governance sync), PR #36 (candidate-run record), PR #37 (TSETMC remediation plan) and PR #38 (sanitized local input diagnostics) are merged to main. PR #38 merged at `07e641670ceab22496ef976a584934464570fd9a` after all five required CI job types passed in run `42031417400`. PR #15 was closed as superseded; its divergent branch was not merged.
- PRs #7, #9, #13, #14, #16–#24, and #28–#30 are integrated into PR #6 in dependency order. Their CI results do not approve data sources or the strategy.
- PR #6's integration branch is 414 commits ahead and 10 behind main at the latest comparison; it is diverged and remains unmerged. PR #39 merged the pipeline classification correction at `1dc6894c0823f6ffe77d27fd866576f5115a042c` after all five required job types passed in run `42050542208`; this is the v1.1.1 execution pin and does not resolve any candidate identity. PR #43's World Bank Pink Sheet refresh is merged after all five required jobs passed in run `42051901501`. PR #45's TSETMC official REST candidate screen is merged into the integration branch at `cbe585efe26ee129370b39e6bd983e709aecf55c` after all five required job types passed in run `42055449340`. PR #44 was closed as stale-base/superseded. PR #46's FIPIRAN/IFB/Investats candidate screen is merged into integration at `0857a48ad9db6c5dab13ae0eca95354639d47324` after all five required jobs passed in run `42056363087`. PR #48 adds exact code/worktree provenance and a report/input hash sidecar for Stage 4. Its first exact-head run `42058606524` failed only because a test expected different wording from the validator's existing integer-zero check; test-only correction commit `3235284d51371ec3c56b9f48d2d0f831fae88187` passed all five required job types in exact-head run `42060466294`. The integration merge has not yet been confirmed; no data or source approval is included. PR #41 (this governance/pin update) remains open; PR #38 is merged. Do not merge PR #6 to main.
- Owner evidence blocker: [Issue #40](https://github.com/yarsalam/marketsage/issues/40) tracks review of the newly announced official TSETMC REST service, rights, seven identity conflicts, units/semantics and independent reconciliation evidence.
- This PR updates the main manual workflow's pinned implementation commit from the historical v1.1.0 commit `819f8b4028469cb0d498098fec88545a18ebacc6` to v1.1.1 commit `1dc6894c0823f6ffe77d27fd866576f5115a042c`. No workflow is dispatched by this change; the owner must review the exact merged workflow and pinned source before any future manual dispatch.
- The governance constitution is adopted on main via PR #31. Main branch protection is not enabled; the local Runner uses the owner-approved manual-only compensating-control model. This is not equivalent to branch protection/rulesets.

## Local Runner and first dataset gate

**Runner:** marketsage-local-01, repository-scoped to yarsalam/marketsage, version 2.338.2, labels marketsage-local and marketsage-research plus GitHub's standard labels.

**Service:** actions.runner.yarsalam-marketsage.marketsage-local-01.service, running as the unprivileged marketsage-runner account and enabled at boot. The account is not in sudo, docker, lxd or adm; it cannot traverse the owner's home directory. Issue [#25](https://github.com/yarsalam/marketsage/issues/25) was closed as completed on 2026-11-05 after Runner registration/activation and the first checksum-validator acceptance; this does not approve TSETMC data.

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

## Integrated TSETMC candidate run and next data task

PR #32 is merged to main at `11f9de85c13f3ee8bd61e6eb7aea64992a7271d4`. PR #34's memory-bounded correction is merged at `554fe2200ccb3a523442b0e241e81a748becfa44`. The first integrated local run used the original pipeline implementation commit `819f8b4028469cb0d498098fec88545a18ebacc6` (v1.1.0). PR #39 has since merged the classification correction into the integration branch at `1dc6894c0823f6ffe77d27fd866576f5115a042c` (v1.1.1). This PR updates the main workflow's immutable pin to that corrected commit; no workflow is dispatched here.

**Latest local candidate run:** [41914919555](https://github.com/yarsalam/marketsage/actions/runs/41914919555), manually dispatched on main on 2026-11-05. It completed successfully in two bounded batches (32 and 15 candidates), with 95 unique input files and 7,554 history rows. It made zero provider/network requests, did not overwrite the staged inputs, verified 32 local output-manifest files, uploaded no artifacts and kept row-level outputs private.

Sanitized result:
- 47 candidates discovered; 47 quarantined; 0 research-eligible.
- 0 research-feature rows; 0 six-month forward-label rows; no backtest run or approval.
- 0 input-file read errors.
- 7 discovery identity conflicts between history-row `insCode`/ISIN values and sibling search/crosswalk metadata.
- 47 candidates still lack verified usage rights, identity evidence, price/volume semantics, independent reconciliation and corporate-action completeness.
- 47 lack an adjusted-chart candidate; 35 also fall below the six-month history threshold.
- All scoring, ranking, backtest and capital-risk flags remain false.

**Classification correction:** pipeline v1.1.0 reported `INPUT_OR_PARSER_ERROR: 7`, but the same run's preflight reported `identity_conflict_count=7` and `input_file_read_errors=0`. [PR #39](https://github.com/yarsalam/marketsage/pull/39) merged a regression-tested correction into the integration branch at `1dc6894c0823f6ffe77d27fd866576f5115a042c`: discovery identity conflicts and ambiguous history selection now have separate reason codes and remediation stages, and identity acceptance is explicitly blocked on conflicts. The historical run remains a v1.1.0 result; no raw data was reprocessed by the code change.

**Independent source-screen updates**
- [PR #43](https://github.com/yarsalam/marketsage/pull/43) is merged into the integration branch; it records the November 3, 2026 Pink Sheet PDF, monthly averages through October, selected units and rights caveats. The XLSX workbook remains unparsed and third-party rights remain unresolved.
- [PR #44](https://github.com/yarsalam/marketsage/pull/44) was closed as a stale-base duplicate. [PR #45](https://github.com/yarsalam/marketsage/pull/45) is merged at `cbe585efe26ee129370b39e6bd983e709aecf55c` after all five required jobs passed in run `42055449340`; the catalog retains the November Pink Sheet evidence and keeps the TSETMC REST service separate from reverse-engineered CDN endpoints. The official REST docs host remains inaccessible, so authentication, subscription, history, semantics and rights remain unknown.
- [PR #46](https://github.com/yarsalam/marketsage/pull/46) merged at `0857a48ad9db6c5dab13ae0eca95354639d47324` after all five required jobs passed in run `42056363087`. The candidate-only screen records FIPIRAN fund NAV (up to 60 evenly spaced history points reported), IFB secondary fixed-income daily price/YTM (coverage depth unknown), and commercial Investats data (paid; quote/terms unknown). None is approved or wired into the engine.

**Next actions**
1. Verify the PR #48 integration merge and its post-merge CI; its corrected exact-head five-job CI passed in run `42060466294`. Complete owner evidence actions in [Issue #40](https://github.com/yarsalam/marketsage/issues/40) and [Issue #47](https://github.com/yarsalam/marketsage/issues/47). Keep TSETMC, FIPIRAN, IFB, Investats and other candidates unapproved until rights, units, per-series history, independent reconciliation and point-in-time evidence are verified.
2. This PR updates the main local workflow pin to corrected implementation commit `1dc6894c0823f6ffe77d27fd866576f5115a042c`. It does not dispatch the workflow. The owner must review the exact merged workflow and pin before any future manual dispatch.
3. Resolve the external evidence blockers in [Issue #40](https://github.com/yarsalam/marketsage/issues/40): review the official REST documentation from the intended Iran network; locally review the seven identity conflicts against an authoritative instrument master; provide applicable TSETMC rights/retention terms; identify a lawful independent price/volume reference; attest units, raw/adjusted semantics and corporate-action completeness.
4. Do not rerun the unchanged corpus. Reprocess only after a separately versioned, evidence-backed input correction or new immutable dataset version, with hashes preserved.
5. Obtain a permissioned and representative history before any locked walk-forward strategy evaluation. Attribute the Stage 4 extreme fold only from the exact original monthly CSV/hash/config; do not tune on the final holdout.
6. Keep source scoring, investment ranking, calibrated probabilities, production release, broker access and trading disabled until all data and empirical gates pass. Any real-money allocation or trade still requires separate explicit owner approval.

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

## Stage 4 exact-dataset attribution blocker

The 2023-10-31 through 2024-03-31 fold remains unexplained at approximately +240.89%. The exact monthly-price CSV used by the report is a local artifact and is not present in GitHub. The repository's `analyze_stage4_fold.py` diagnostic must be run against that exact file and its SHA-256 must match `1e71d898b18b4a6db74aba4826c86a4982efad934ee30aa82ff354883f01d878` before interpreting attribution. The owner action, exact command and acceptance criteria are recorded in [Issue #47](https://github.com/yarsalam/marketsage/issues/47). Do not substitute a different dataset, upload raw prices, or tune against the locked holdout. Stage 4 remains exploratory until the extreme fold is attributed and the source/point-in-time/cost gates are resolved.

## Current decision and next actions

1. Owner manually dispatches the updated `.github/workflows/local-tsetmc-integrated-acceptance.yml` on `main` with `confirm_integrated_acceptance=true` and reviews the sanitized counts, decision statuses, quarantine reasons and reprocessing queue.
2. Resolve TSETMC evidence gaps (rights, identity, semantics/units, corporate actions, independent reference, calendars and point-in-time availability) against the local-only outputs; do not upload raw rows or candidate CSVs.
3. Obtain an immutable, permissioned and representative historical dataset before any locked walk-forward strategy evaluation.
4. Attribute the Stage 4 extreme fold only when the exact original monthly CSV/hash/config is available; do not tune on the final holdout.
5. Compare the six-month decision horizon against predeclared baselines using net returns, costs, liquidity, drawdown, uncertainty and point-in-time replay.
6. Keep source scoring, investment ranking, calibrated probabilities, production release, broker access and trading disabled until all relevant data and empirical gates pass. Any real-money allocation or trade still requires the owner's separate explicit approval.

**Investment-stage status: NOT READY.** A successful Runner job, parser, dataset hash audit, or integration CI run is not an investment approval.
