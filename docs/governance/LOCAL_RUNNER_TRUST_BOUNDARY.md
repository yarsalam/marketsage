# MarketSage local-data Runner — trust boundary and activation gate

**Status:** Owner-approved manual-only compensating-control design; PR #27 workflow is merged to `main` and CI passed; designated Runner installation is incomplete and Runner remains unregistered/offline pending final host checks.  
**Scope:** Local TSETMC corpus acceptance and bounded offline Stage 4 data evaluation.  
**Authority:** The owner selected Option 2 in Issue #25 on 2026-11-04. This accepts residual risk caused by the lack of private-repository branch protection on the current GitHub plan.  
**Important:** This model is not equivalent to protected branches or rulesets.

## 1. Why the normal CI workflow must never use the local Runner

Ordinary pull-request validation must remain on GitHub-hosted runners. Never add a self-hosted job to the general CI workflow. Never execute arbitrary PR heads, fork code, issue/comment content, or other untrusted contributions on the laptop Runner.

Verified on 2026-11-04: `main` contains `.github/workflows/ci.yml`, whose jobs use `ubuntu-latest`; no general CI job targets self-hosted. PR #27 added the only local workflow, `.github/workflows/local-tsetmc-offline-acceptance.yml`, with `workflow_dispatch` as its only trigger. The parked PR #8 TSETMC smoke workflow on the integration branch also uses `ubuntu-latest` and must not be repeated from the same GitHub-hosted environment.

A malicious or compromised workflow can execute arbitrary commands as `marketsage-runner`, read everything that account can read, write to its permitted output/workspace, and attempt network communication. Host filesystem permissions reduce local exposure but do not make workflow code safe.

## 2. Approved trust model and residual risk

The owner selected the manual-only compensating-control path rather than purchasing a paid plan or making the repository public.

GitHub does not enforce private-repository branch protection/rulesets for this repository on the current plan. Consequently:
- no claim may be made that the source branch is protected;
- manual dispatch and a code-review checklist are operational controls, not technical equivalents of branch protection;
- every local-data run requires an owner-side review of the exact workflow content and exact source commit before dispatch;
- the run must record the triggering SHA, actor, workflow path and run ID;
- unexpected refs, SHAs and event types must fail closed.

Residual risk accepted: anyone able to change the workflow/default-branch content and dispatch it, or an attacker controlling an authorized account, may change what executes on the Runner. The controls in this document reduce but cannot eliminate this risk. This exception applies only to the limited research dataset and workflow; it does not authorize secrets, personal data, trading access or broad host access.

## 3. Workflow requirements before registration/activation

PR #27's separate workflow is now merged to `main` at `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`. Static review and all five required CI job types passed on exact PR head `c60edd0f16244ab12e6602b9247e4174567f6081` in run `41833221157`. It has only `workflow_dispatch`, owner/default-branch/explicit-confirmation guards, `contents: read`, a full-SHA-pinned checkout, no secrets, no provider/network probes and no artifact upload. It targets the exact custom labels `marketsage-local` and `marketsage-research`. The owner must still review the exact current `main` SHA and workflow immediately before dispatch. The first workflow validates the staged dataset manifest and hashes; it does not yet execute the full PR #14 integrated pipeline.

The local workflow must continue to satisfy all of the following:

1. `on:` contains only `workflow_dispatch`. No `push`, `pull_request`, `pull_request_target`, fork, issue, issue-comment, schedule, workflow-run or repository-dispatch trigger.
2. The job has an explicit event/ref guard and rejects every event except `workflow_dispatch`. Dispatch must use the agreed trusted ref (initially the reviewed default-branch revision); record and verify the exact `github.sha` for every run.
3. The owner reviews the exact workflow source and triggering commit immediately before each dispatch. If either changes, repeat the review. A user-supplied arbitrary ref must not be accepted as executable code.
4. The job runs only on the exact labels assigned to the repository-scoped research Runner. Do not use a broad `self-hosted` target without the dedicated label.
5. Set workflow/job token permissions to `contents: read` only. Do not define or reference repository, organization, or environment secrets in this job.
6. Pin each third-party action to an immutable, reviewed full commit SHA. Do not use floating tags, remote scripts, unpinned container images or arbitrary downloaded executables.
7. Use a dedicated workspace and a concurrency group so local data jobs cannot overlap.
8. Run only the approved offline pipeline against the staged snapshot. No network probes, provider retries, VPN changes, data repair, source approval, scoring, deployment, broker access or trading.
9. Keep raw rows and source files local. Before publishing any artifact, allow only sanitized manifests, row counts, date ranges, reason codes, file hashes and reviewed aggregate metrics. Do not upload raw data or raw row samples. Never publish secrets, local absolute paths, usernames, hostnames or environment details.
10. A job must fail closed on missing data, checksum mismatch, unexpected file, unexpected ref/event, invalid manifest, write attempt to the source dataset, or output validation failure.

The workflow file must be reviewed before Runner registration. Do not register first and assume the workflow can be repaired later.

## 4. Repository-scoped Runner

- Register a repository-level Runner for `yarsalam/marketsage` only.
- Assign the custom labels `marketsage-local` and `marketsage-research` and require both in the dedicated job's `runs-on`; GitHub also supplies the standard `self-hosted`, `linux` and `x64` labels.
- Do not grant an organization-wide Runner group or access to other repositories.
- Do not change any existing workflow to `runs-on: self-hosted`.
- Never reuse the previously chat-exposed registration token. Generate a fresh short-lived registration token from the repository settings and enter it only in the local terminal. Never paste it into chat, a file, shell history, workflow logs or a commit.
- Prefer one-job/ephemeral execution where operationally feasible. If a persistent Runner is used, document service identity, workspace cleanup, update procedure, offline/online controls, and a fast disable/unregister procedure.
- A Runner process being online does not grant approval for any job. The only permitted job is the reviewed manual workflow above.

## 5. Host identity and filesystem boundary — latest owner-reported audit

The following results were supplied by the owner from the Ubuntu laptop on 2026-11-04:

### OS identity and Runner package location — corrected by latest owner terminal output

- Account: `marketsage-runner`, UID 110, GID 119, home `/var/lib/marketsage-runner`, shell `/usr/sbin/nologin`.
- Supplementary groups: only `marketsage-runner`; confirmed absent from `sudo`, `docker`, `lxd` and `adm`.
- Home directory: `/var/lib/marketsage-runner`, mode `0750`, owned by `marketsage-runner:marketsage-runner`. The general user home `/home/nima` is not traversable by this account.
- Latest terminal output shows the complete 228,071,396-byte `actions-runner-linux-x64-2.338.2.tar.gz` in `/home/nima/actions-runner`. Extracted `config.sh`, `run.sh`, `bin` and `externals` are also present there, but their timestamps are 2026-10-26; their version/correspondence to the newer archive has not been verified.
- `/opt/actions-runner/marketsage` contains only a 9,719,808-byte partial archive; extracted `config.sh` and `run.sh` are absent. The designated installation is incomplete. Do not copy the personal directory's `.env`, `.path` or `_diag` files into the dedicated Runner directory.
- No Runner service or active `Runner.Listener`/`Runner.Worker`/`runsvc.sh` process was found in the latest terminal output. No registration marker was visible in the displayed directory listings. Runner is not registered or online.
- The archive checksum has not yet been re-verified against the full archive now in the personal directory. Verify the published SHA-256 and extract a fresh copy directly into the designated path; do not rely on the older extracted files.
- Any registration token previously pasted into chat is compromised and must never be reused. A fresh token must be entered locally only.

### Dataset and output

- Dataset path: `/srv/marketsage/data/tsetmc_history_20261022`.
- 8,801 original source files plus `SHA256SUMS` and `STAGING_README.txt`; 8,803 files total.
- Every one of the 8,801 source-file hashes was verified against the source during staging, then re-verified from the staged checksum manifest before publication.
- Source files were not modified. The adjusted research-only candidates were deliberately excluded.
- Dataset files are mode `0440`; directories are mode `2750`; group is `marketsage-runner`. The Runner can read/traverse but cannot write to the dataset.
- Separate output path: `/srv/marketsage/output`, owned by `marketsage-runner:marketsage-runner`, mode `0750`.
- As `marketsage-runner`, representative files from raw, normalized, reports, pipeline metadata, discovery, reconciliation and acceptance were read and SHA-256 checked. Pipeline JSON parsing and discovery CSV reading passed.
- Write attempts to dataset root, normalized directory and a source file were denied; a deliberate create attempt at the dataset root returned `PermissionError`.
- The Runner successfully created and deleted a temporary test file in its output directory.
- The user account home and unrelated project directories remain inaccessible to the Runner.

These are owner-reported terminal results, not an independent penetration test. They verify the tested OS permission boundary, not the safety of arbitrary workflow code, kernel exploits, supply-chain compromise or network exfiltration.

## 6. Data handling and first workload

The staged directory contains raw provider responses, normalized histories, reports, discovery metadata, v2 reconciliation evidence and acceptance reports.

The dataset is not source-approved or approved for backtesting. Current acceptance evidence reports zero instruments automatically approved for backtesting; investment scoring remains disabled. The 79 adjusted research-only candidate outputs and the older reconciliation candidate outputs were excluded.

First permitted workload after host activation and owner review is only the PR #27 offline dataset validator:
- verify the staged dataset inventory and all 8,801 source-file hashes;
- write the sanitized validator report under `/srv/marketsage/output` without network access or input modification;
- keep `eligible_for_scoring=false` and `approved_for_backtest=false`.

This first workflow does not run the full PR #14 integrated TSETMC acceptance/reconciliation pipeline. That pipeline requires a separate, explicitly reviewed manual workflow after the validator report and host dependencies are checked.

Do not inspect a holdout set, tune strategy parameters, calculate/enable investment scores, or infer source/legal approval from a successful parser or runner job.

## 7. Network and VPN

The first workload is offline and must not require provider access. The job must not change VPN settings, inspect browser profiles, read VPN credentials, modify system routes, or probe alternative network routes. Any later provider-specific network work requires a separate bounded design and network policy. Local Runner connectivity to GitHub is distinct from permission to send research data elsewhere.

## 8. Activation checklist

- [x] Owner selected the manual-only model and accepted its residual risk (Issue #25, 2026-11-04).
- [x] Dedicated unprivileged OS identity and group restrictions verified.
- [x] Staged dataset copied, SHA-256 verified and made read-only to Runner (owner-reported).
- [x] Runner read access and denied data writes tested; separate output write tested (owner-reported).
- [x] Current workflow inventory reviewed: general CI remains on GitHub-hosted runners; PR #8 smoke also uses GitHub-hosted runners.
- [x] Separate manual-only local validator workflow added and merged to `main` in PR #27.
- [x] Workflow permissions, no-secrets boundary, immutable action SHA, owner/ref/confirmation guard, serialization and sanitized local output reviewed.
- [x] Emergency stop/unregister procedure documented below.
- [ ] Full v2.338.2 archive hash-verified and freshly extracted under `/opt/actions-runner/marketsage`; current designated path contains only a partial archive.
- [ ] Systemd service installed as `marketsage-runner` with workspace/service hardening and cleanup controls applied.
- [ ] Final pre-registration audit confirms no stale credentials, active Runner process or service.
- [ ] Fresh registration token generated and entered locally only; repository-level Runner registered with custom labels `marketsage-local,marketsage-research`.
- [ ] Before the first dispatch, owner reviews the exact current `main` workflow source/commit and records the run approval.

Until the remaining unchecked items are complete, the Runner must remain unregistered and offline. PR #27 being on `main` does not start or register it.

## 9. Emergency disable and unregister

If a local job behaves unexpectedly:

1. Disable the repository Runner in **Settings → Actions → Runners** so GitHub cannot schedule another job on it.
2. On the laptop, from `/opt/actions-runner/marketsage`, stop the installed service with `sudo ./svc.sh stop`. Confirm no Runner job/process remains before touching the workspace.
3. Remove the systemd service with `sudo ./svc.sh uninstall`.
4. If the Runner must be detached from GitHub, generate a fresh removal token in repository Runner settings and run `./config.sh remove --token "$REMOVE_TOKEN"` as the Runner account. Enter the token through a hidden local prompt; never paste it into chat, shell history, files or logs.
5. Only after the service is stopped and no job is active, clear contents of the dedicated Runner `_work` directory if needed. Do not delete or modify `/srv/marketsage/data/tsetmc_history_20261022` or its source hashes during emergency cleanup.
6. Preserve the sanitized report and diagnostic logs for review; do not restart until the workflow source, triggering SHA and host boundary have been re-reviewed.

For normal service operation, install with `sudo ./svc.sh install marketsage-runner` and start/stop through `sudo ./svc.sh start` / `sudo ./svc.sh stop`. The service must remain under the unprivileged account. A systemd drop-in should set `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectHome=true`, `ProtectSystem=full`, make the staged dataset read-only, and permit writes only to the Runner installation/workspace and `/srv/marketsage/output`. Verify the exact generated unit name and resulting effective properties locally before starting it. These controls do not restrict network egress; the accepted residual risk remains.

## 10. Related records

- [Issue #25 — local Runner trust boundary](https://github.com/yarsalam/marketsage/issues/25)
- [Decision log](DECISION_LOG.md)
- [Project execution constitution](PROJECT_EXECUTION_CONSTITUTION.md)
