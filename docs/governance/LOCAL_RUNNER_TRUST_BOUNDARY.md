# MarketSage local-data Runner — trust boundary and operating procedure

**Status:** Runner registered and online; first manual offline dataset-validator run passed (run 41906518123, attempt 2). The integrated TSETMC candidate pipeline is a separate, pending manual workflow.  
**Repository:** yarsalam/marketsage (private), repository-scoped Runner only.  
**Authority:** owner-approved manual-only compensating-control model in Issue #25. This is not equivalent to GitHub branch protection or rulesets.

## 1. Allowed workload

The laptop Runner is limited to reviewed, owner-dispatched research workflows. Ordinary CI and all pull-request validation continue on GitHub-hosted ubuntu-latest runners. No general CI job may target self-hosted.

Allowed local workloads:
1. the manual staged-dataset checksum/inventory validator on main;
2. a separately reviewed manual workflow that checks out the pinned integration commit 819f8b4028469cb0d498098fec88545a18ebacc6 and runs the offline TSETMC candidate-acceptance pipeline.

Disallowed:
- fork/PR/issue/comment/schedule/push/workflow-run/repository-dispatch triggers;
- arbitrary branch or user-provided ref execution;
- secrets, PATs, SSH keys, browser profiles, personal files, password stores, broker accounts or trading credentials;
- provider probes, VPN changes, alternate network routes, data repair, forward-fill, source approval, scoring, backtest approval, production deployment, broker access or trading;
- raw dataset uploads, row-level output artifacts, raw price values or absolute local paths in GitHub logs.

## 2. Manual-only trust model and residual risk

The local workflows must have only workflow_dispatch, contents: read, immutable full-SHA-pinned third-party actions, owner/ref/input guards, a fixed code checkout, a dedicated concurrency group and the exact Runner labels below. Each dispatch requires owner review of the current workflow source and the pinned execution commit.

The repository's private-repository branch protection/rulesets are unavailable on the current plan; main is not protected. Manual dispatch and source review are compensating operational controls, not technical branch protection. An account with sufficient repository write/Actions permissions could alter workflow code before dispatch; the controls reduce, but do not eliminate, this residual risk.

The Runner is online only to receive the explicitly approved workflow. Its GitHub connectivity is not permission to send the local dataset to external providers. The current integrated pipeline and wrapper make no provider requests. The Runner host does not have an egress firewall policy that guarantees arbitrary workflow code cannot communicate over the network; therefore workflow review and the narrow execution boundary remain mandatory.

## 3. Runner identity and installation

- Name: marketsage-local-01
- Repository: yarsalam/marketsage only
- Labels: self-hosted, linux, x64, marketsage-local, marketsage-research
- Version: 2.338.2
- Installation: /opt/actions-runner/marketsage
- Work directory: /opt/actions-runner/marketsage/_work
- OS identity: marketsage-runner, UID 110, GID 119, shell nologin
- Supplementary groups: only its own marketsage-runner group; not in sudo, docker, lxd or adm
- User home: /var/lib/marketsage-runner; /home/nima is not traversable by the Runner
- Service: actions.runner.yarsalam-marketsage.marketsage-local-01.service, enabled at boot and observed active/running after setup.

The repository-level Runner was registered with a fresh local-only registration token. The token is short-lived and must never be pasted into chat, written to a file, placed in shell history or reused. A token previously displayed in an earlier terminal transcript is compromised/expired and must never be reused.

## 4. Effective host filesystem and service controls

The staged dataset is /srv/marketsage/data/tsetmc_history_20261022:
- 8,801 source files plus SHA256SUMS and STAGING_README.txt;
- every source-file digest was verified during staging and again by the first GitHub workflow;
- files are mode 0440; directories are mode 2750; group marketsage-runner;
- Runner can read/traverse but cannot write to the dataset.

The separate output directory is /srv/marketsage/output, owned by marketsage-runner. The integrated workflow creates /srv/marketsage/output/tsetmc-integrated-acceptance with mode 0700 and uses umask 077; candidate CSVs, detailed reports and absolute paths remain local.

Effective service controls observed after the successful tar compatibility correction:
- User=marketsage-runner, Group=marketsage-runner
- ProtectHome=true
- ProtectSystem=strict
- PrivateTmp=true
- NoNewPrivileges=true
- ProtectKernelTunables=true
- ProtectKernelModules=true
- ProtectControlGroups=true
- ReadOnlyPaths=/srv/marketsage/data/tsetmc_history_20261022
- ReadWritePaths=/opt/actions-runner/marketsage /srv/marketsage/output /var/lib/marketsage-runner

RestrictSUIDSGID is intentionally not enabled on this host. With GNU tar 1.35, the earlier Runner service sandbox produced Function not implemented during actions/checkout extraction. After removing only this directive, a nested GNU tar extraction test passed inside a hardened systemd sandbox and the Runner checkout succeeded; the other principal restrictions above remained effective. Do not broaden ReadWritePaths, grant privileged groups, or relax dataset permissions as a workaround.

These are tested host boundaries, not a formal penetration test. They do not eliminate kernel, supply-chain, account-compromise or network-egress risks.

## 5. Verified workflow result

Workflow: .github/workflows/local-tsetmc-offline-acceptance.yml  
Run: [41906518123](https://github.com/yarsalam/marketsage/actions/runs/41906518123), attempt 2, completed successfully.

Verified results:
- checked out main commit 46d3a541b7fa176b5a8c5693a0c46feb8bb9b3fc;
- verified all 8,801 source SHA-256 entries and 1,268,527,673 source bytes;
- counted 2,493 instrument-universe rows;
- NETWORK_REQUESTS=0;
- DATASET_MODIFIED=false;
- SCORING_ENABLED=false;
- BACKTEST_APPROVED=false.

Attempt 1 failed during tar extraction. The service compatibility change and a sandboxed tar regression test were completed before re-running attempt 2. Attempt 2 is the accepted validator result. This validates staged corpus integrity only; it does not approve source rights, raw/adjusted semantics, corporate actions, independent reconciliation, point-in-time validity, research eligibility, backtest or scoring.

## 6. Integrated TSETMC candidate workflow — pending

The separate workflow under review is .github/workflows/local-tsetmc-integrated-acceptance.yml. Its intended behavior:
- manual-only on main, owner-gated, explicit boolean confirmation, same Runner labels and concurrency group;
- checks out the exact workflow commit plus immutable pipeline source commit 819f8b4028469cb0d498098fec88545a18ebacc6;
- reads only the staged raw subtree and the explicit v2 crosswalk reconciliation_v2/instrument_details.jsonl;
- enforces no symlinks, no input paths outside the staged dataset, no dataset writes, maximum 3,000 discovered items, maximum 3 GiB of selected inputs, at least 16 GiB available RAM and 8 GiB free output disk;
- runs the integration pipeline once in the same Python process after preflight;
- validates output hashes and all fail-closed flags;
- writes detailed candidate CSVs/reports locally under the private output directory;
- prints only aggregate counts and safety flags to GitHub logs;
- does not upload artifacts, install packages, probe providers, approve sources, approve backtests, enable ranking/scoring or trade.

Do not dispatch this workflow until the PR has passed all required CI jobs and the owner has reviewed the exact workflow source and pinned pipeline SHA on main. The workflow has not yet been run.

## 7. Emergency stop, disable and unregister

If any local job behaves unexpectedly:

1. In repository Settings → Actions → Runners, disable marketsage-local-01 so GitHub cannot schedule another job.
2. Confirm the job is no longer active. On the laptop, run sudo systemctl stop actions.runner.yarsalam-marketsage.marketsage-local-01.service.
3. Confirm the listener is stopped, then from /opt/actions-runner/marketsage run sudo ./svc.sh uninstall.
4. If detaching the Runner from GitHub, generate a fresh repository removal token and enter it locally through a hidden prompt to ./config.sh remove --token "$REMOVE_TOKEN" as the Runner account. Never paste the token in chat or save it.
5. Only after the service is stopped and no job is active, clear the dedicated Runner _work directory if necessary. Never delete or modify /srv/marketsage/data/tsetmc_history_20261022 or SHA256SUMS.
6. Preserve private diagnostic logs and sanitized summaries; do not restart until the workflow source, pinned commit and host boundary have been reviewed.

## 8. Operating rules

- Do not change ordinary CI from GitHub-hosted runners.
- Do not dispatch from an arbitrary ref; use main and review its current workflow.
- Do not use a personal access token for normal Runner operation. If a PAT was entered into config.sh --check, revoke it if it was a real personal token; Runner operation itself uses its configured registration credentials.
- Never publish raw input rows, detailed candidate CSVs, absolute local paths, hostnames, usernames, secrets or local diagnostics.
- A green workflow, clean checksum audit or successful TSETMC parser does not equal source approval or strategy validation.
- No workflow may enable scoring, ranking, production release, broker access or trading.

## Related records

- [Issue #25 — local Runner activation](https://github.com/yarsalam/marketsage/issues/25)
- [Project state](PROJECT_STATE.md)
- [Decision log](DECISION_LOG.md)
- [Project execution constitution](PROJECT_EXECUTION_CONSTITUTION.md)
