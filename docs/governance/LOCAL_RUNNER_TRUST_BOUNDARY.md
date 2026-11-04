# MarketSage local-data Runner — trust boundary and activation gate

**Status:** Owner-approved manual-only compensating-control design; host dataset preparation complete; Runner remains unregistered and offline until workflow review and final activation checks pass.  
**Scope:** Local TSETMC corpus acceptance and bounded offline Stage 4 data evaluation.  
**Authority:** The owner selected Option 2 in Issue #25 on 2026-11-04. This accepts residual risk caused by the lack of private-repository branch protection on the current GitHub plan.  
**Important:** This model is not equivalent to protected branches or rulesets.

## 1. Why the normal CI workflow must never use the local Runner

Ordinary pull-request validation must remain on GitHub-hosted runners. Never add a self-hosted job to the general CI workflow. Never execute arbitrary PR heads, fork code, issue/comment content, or other untrusted contributions on the laptop Runner.

The exact current workflow filenames and triggers must be inventoried from the repository before activation. Earlier documentation referred to `.github/workflows/ci.yml`; this filename and its current trigger set are not treated as verified until inspected against the current repository revision.

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

Create and review a separate workflow dedicated to the local TSETMC research workload. It must satisfy all of the following:

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
- Assign a unique label such as `marketsage-research` and require it in the dedicated job's `runs-on`.
- Do not grant an organization-wide Runner group or access to other repositories.
- Do not change any existing workflow to `runs-on: self-hosted`.
- Never reuse the previously chat-exposed registration token. Generate a fresh short-lived registration token from the repository settings and enter it only in the local terminal. Never paste it into chat, a file, shell history, workflow logs or a commit.
- Prefer one-job/ephemeral execution where operationally feasible. If a persistent Runner is used, document service identity, workspace cleanup, update procedure, offline/online controls, and a fast disable/unregister procedure.
- A Runner process being online does not grant approval for any job. The only permitted job is the reviewed manual workflow above.

## 5. Host identity and filesystem boundary — latest owner-reported audit

The following results were supplied by the owner from the Ubuntu laptop on 2026-11-04:

### OS identity and installed Runner package

- Account: `marketsage-runner`, UID 110, GID 119, home `/var/lib/marketsage-runner`, shell `/usr/sbin/nologin`.
- Supplementary groups: only `marketsage-runner`; confirmed absent from `sudo`, `docker`, `lxd` and `adm`.
- Home directory: `/var/lib/marketsage-runner`, mode `0750`, owned by `marketsage-runner:marketsage-runner`. The general user home `/home/nima` is not traversable by this account.
- Runner installation: `/opt/actions-runner/marketsage`, files owned by `marketsage-runner:marketsage-runner`; `config.sh` and `run.sh` are executable. Parent directories are root-owned and not writable by the Runner.
- Runner version: 2.338.2; archive checksum was verified before extraction.
- No `.runner`, `.credentials`, or `.credentials_rsaparams` files were present in the installation directory.
- No installed/loaded Runner service and no active `Runner.Listener`, `Runner.Worker` or `runsvc.sh` process were found.
- Runner is not registered, online or running as a service.

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

First permitted workload after workflow review and activation:
- verify the staged dataset checksum manifest;
- run the offline TSETMC integrated acceptance/reconciliation inspection without network access and without modifying inputs;
- produce a unique output directory with sanitized summaries only;
- report quarantine/unknown states without automatically repairing or approving instruments.

Do not inspect a holdout set, tune strategy parameters, calculate/enable investment scores, or infer source/legal approval from a successful parser or runner job.

## 7. Network and VPN

The first workload is offline and must not require provider access. The job must not change VPN settings, inspect browser profiles, read VPN credentials, modify system routes, or probe alternative network routes. Any later provider-specific network work requires a separate bounded design and network policy. Local Runner connectivity to GitHub is distinct from permission to send research data elsewhere.

## 8. Activation checklist

Runner registration and workflow activation remain gated until all of these checks are completed:

- [x] Owner selected the documented manual-only model and accepted its residual risk (Issue #25, 2026-11-04).
- [x] Dedicated unprivileged OS identity and group restrictions verified.
- [x] Staged dataset copied, SHA-256 verified and made read-only to Runner.
- [x] Runner read access and denied data writes tested; separate output write tested.
- [ ] Exact current CI and workflow files inventoried; every trigger, permission, action reference, checkout ref and runner target reviewed.
- [ ] Separate manual-only workflow added on an implementation branch and reviewed; no existing CI workflow changed to self-hosted.
- [ ] Workflow token permissions, absence of secrets, immutable action SHAs, ref/event guard, sanitization and concurrency validated.
- [ ] Runner service/workspace isolation and cleanup/disable procedure documented.
- [ ] Final pre-registration audit confirms no stale credentials or active Runner process/service.
- [ ] Fresh registration token generated and entered locally only; repository-level Runner registered with the dedicated label.
- [ ] Before the first dispatch, owner reviews the exact workflow source/commit and records the run approval.

Until the remaining unchecked items are complete, the Runner must remain unregistered and offline. Registration itself does not authorize unreviewed code or broader workloads.

## 9. Related records

- [Issue #25 — local Runner trust boundary](https://github.com/yarsalam/marketsage/issues/25)
- [Decision log](DECISION_LOG.md)
- [Project execution constitution](PROJECT_EXECUTION_CONSTITUTION.md)
