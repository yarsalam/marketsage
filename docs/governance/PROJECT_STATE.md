# MarketSage — Current Project State

**Snapshot date:** 2026-11-05  
**Repository:** yarsalam/marketsage (Private)  
**Main base commit for this update:** 46d3a541b7fa176b5a8c5693a0c46feb8bb9b3fc  
**Integration PR:** #6, feat/tindex-free-data-connector  
**Pinned integration code commit:** 819f8b4028469cb0d498098fec88545a18ebacc6  
**Release posture:** research-only. No data source has passed the complete investment-source gate; no representative strategy has passed empirical validation; production ranking/scoring, broker access and trading remain disabled.

## Executive state

- PR #6 remains open and **must not be merged to main without explicit owner approval**. Its current integration code is used by the new local workflow only through the immutable commit SHA above.
- PR #8 remains parked after the GitHub-hosted TSETMC connection timeout. Do not repeat the same request from the same environment.
- PR #27 (manual-only staged-dataset validator) and PR #31 (clean governance adoption) are merged to main. PR #15 was closed as superseded; its divergent branch was not merged.
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

A separate manual-only workflow is being added in this PR to run the PR #14 integrated offline TSETMC candidate-acceptance pipeline. It:
- checks out this workflow's exact manually selected main commit;
- checks out the integration implementation at the fixed SHA 819f8b4028469cb0d498098fec88545a18ebacc6;
- requires the owner confirmation input and the repository-scoped Runner labels;
- checks the staged dataset is readable and non-writable, checks the v2 identity crosswalk, bounds discovery size, requires at least 16 GiB available RAM and 8 GiB free output disk, and refuses symlinks/out-of-dataset inputs;
- makes no provider/network requests, changes no input file, and keeps row-level candidate outputs and local absolute paths on the laptop under the private output directory;
- prints only sanitized counts and fail-closed status flags to GitHub logs; no artifacts are uploaded.

This integrated workflow has not yet been dispatched. The owner must review the exact workflow on main and its pinned source SHA before manually running it. The local Runner connector currently cannot dispatch a new workflow on the owner's behalf.

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

1. Review the integrated offline pipeline's sanitized counts, decision statuses, quarantine and reprocessing queue after the owner dispatches it.
2. Resolve TSETMC evidence gaps (rights, identity, semantics/units, corporate actions, independent reference, calendars and point-in-time availability) against the local-only outputs; do not upload raw rows or candidate CSVs.
3. Obtain an immutable, permissioned and representative historical dataset before any locked walk-forward strategy evaluation.
4. Attribute the Stage 4 extreme fold only when the exact original monthly CSV/hash/config is available; do not tune on the final holdout.
5. Compare the six-month decision horizon against predeclared baselines using net returns, costs, liquidity, drawdown, uncertainty and point-in-time replay.
6. Keep source scoring, investment ranking, calibrated probabilities, production release, broker access and trading disabled until all relevant data and empirical gates pass. Any real-money allocation or trade still requires the owner's separate explicit approval.

**Investment-stage status: NOT READY.** A successful Runner job, parser, dataset hash audit, or integration CI run is not an investment approval.
