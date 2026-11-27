# MarketSage GitHub automation — Goal 1 operations

This document defines the infrastructure-only automation boundary. It does not authorize automatic merges, releases, deployments, product development, market-data acquisition, investment scoring/ranking, probability calibration, backtests, broker access, trading, or capital allocation.

## Verified repository state — 2026-11-27

- GitHub reports the repository visibility as **public**, although the current owner instruction describes it as private. No visibility change was made. Treat all committed content, issues, PRs, and workflow summaries as public until the owner explicitly resolves this mismatch.
- The latest observed main commit is dated 2026-11-26. The previous report that main had not changed since 2026-11-07 was stale.
- PR #85 is **closed and unmerged**. Its proposed automation is not active on main. Do not treat its earlier successful checks as current infrastructure evidence.
- PR #6 is **closed and unmerged**. It was not changed or merged.
- The currently open PRs, verified 2026-11-27, are #88 (this Goal 1 infrastructure draft; open, Draft, mergeable, with no submitted reviews), #87 (Draft, mergeable), #86 (Draft, mergeable), and #81 (Draft, not mergeable). PRs #87, #86, and #81 are outside the current execution scope and must not be advanced while Goal 1 is active.
- The active main ruleset exposes only branch-deletion and non-fast-forward protections, with no bypass actors. The classic branch-protection endpoint is not readable through the current GitHub connection. Required approvals and required status checks therefore remain unverified.
- The current GitHub connection exposes PR-triggered runs for a supplied commit, but not a complete repository-wide Actions run listing. Therefore actual scheduled-run completion and the latest global failure totals are **not independently verified** in this audit. The default-branch CI file does define a daily schedule; that configuration is not proof that the schedule executed.
- Workflow YAML was inspected. No repository secret values were read. The current connection does not expose runner inventory or account billing/quota details.

### Mainline freeze is not yet active — hard blocker

The current `main` version of `.github/workflows/ci.yml` still defines a daily scheduled trigger (`17 3 * * *`) and `workflow_dispatch`. It also contains an analysis test job that runs the analysis-engine test suite, application/backend/frontend/admin build jobs, and a production-image build job. The exact current file was inspected on 2026-11-27.

PR #88 replaces that workflow on its branch, but PR #88 is still Draft and unmerged. Therefore the Goal 1-only freeze is **not active on main**. The existing mainline schedule/manual trigger and its analysis/production jobs remain configured until an owner-reviewed change reaches main. Do not dispatch the existing workflow manually. No claim is made that the legacy scheduled workflow has or has not executed in the latest interval because the connected run-history action does not provide a complete repository-wide run list.

The three local TSETMC workflows were separately inspected on main: each is manual-only (`workflow_dispatch`) and targets the dedicated self-hosted runner labels. They were not dispatched.

### Current exact-head evidence boundary

The connected run-history action returned one successful PR-triggered run for the current PR #88 head. Its only job completed successfully and the run has no artifacts. The PR description reports both push and pull-request success, but this audit interface filters commit workflow runs to PR-triggered events; the push-triggered run is therefore not independently confirmed here. No PR reviews have been submitted.

## Proposed cloud-native execution model in this branch

### Event-driven CI

The replacement MarketSage CI workflow is intentionally limited to Goal 1 infrastructure contract tests.

- Events: push to main/infra/ci branches and pull requests targeting main.
- Runner: GitHub-hosted ubuntu-latest.
- Permissions: contents: read only.
- Concurrency: one group per PR/ref; a newer commit cancels the superseded run.
- Timeout: 10 minutes.
- External actions: immutable full commit SHAs.
- No manual dispatch, no scheduled product workflow, no secrets, no artifacts, no application builds, no analysis/backtest job, and no production image job.

### Scheduled health check

The separate Goal 1 Watchdog workflow:

- Runs every 30 minutes from the default branch and after completion of the infrastructure CI workflow.
- Uses GitHub-hosted ubuntu-latest, with a 3-minute timeout.
- Uses actions: read and contents: read only.
- Checks only main, infra, and ci branches; fork-originated workflow runs are excluded.
- Reads at most five pages of workflow history (100 runs per page), retries each read-only GitHub API page at most three times with bounded request timeouts and short backoff, and marks truncated history as degraded instead of silently trusting a partial result.
- Detects queued runs older than 15 minutes, running jobs older than 30 minutes, recent failed/timed-out runs, and a missing successful scheduled heartbeat older than 75 minutes.
- Records aggregate status in the GitHub Actions run summary. It emits no raw logs, artifacts, commit hashes, branch names, run identifiers, market data, prices, private paths, credentials, or tokens.
- Does not automatically rerun failed jobs. A human inspects the failed step and decides whether a single bounded retry is justified.

The scheduled workflow is a best-effort monitor, not an SLA. GitHub scheduled events run from the default branch and may be delayed or dropped during service load. A GitHub-hosted workflow cannot independently alert if GitHub Actions itself is disabled, unavailable, or no longer schedules the workflow. The daily ChatGPT audit is an additional observer, not a 24/7 external heartbeat.

## Failure handling and operator recovery

1. Open the GitHub Actions overview and inspect the newest relevant run.
2. Check whether a queued run exceeded 15 minutes or a running job exceeded 30 minutes.
3. For a failed run, inspect only the failing step needed to identify the cause. Never copy raw logs into an issue or chat without sanitization.
4. Do not automatically rerun the entire workflow. Retry only after confirming a transient cause, and prefer the failed job only.
5. A cancelled run may have been superseded by a newer commit. Check the newest run for the same PR/ref before treating cancellation as failure.
6. If the Watchdog API read fails after three attempts, its run is marked failed with a sanitized summary. Verify Actions API permissions and GitHub service status.
7. No artifact is uploaded. GitHub Actions run records and step summaries are the status ledger.

ChatGPT's scheduled audit reports the latest main commit, open PRs, mergeability, recent workflow runs, and blockers in this conversation. Mobile push delivery is not guaranteed.

## Runner strategy

- Use GitHub-hosted runners for cloud-native, read-only CI and health checks.
- The three TSETMC workflows on main remain manual-only and require dedicated self-hosted labels. They were not dispatched. The laptop runner is not an always-on service and must never be assumed available.
- Runner inventory could not be verified through the current connection; no always-on server runner is proven to exist.
- Do not provision a persistent runner until a separate server, budget, ownership, and security boundary are approved.
- If a dedicated server runner is later necessary, prefer one-job ephemeral runners or disposable VMs/containers, a dedicated unprivileged OS account, no repository secrets, no fork PR execution, restricted outbound network, isolated workspaces, bounded concurrency, patching, heartbeat, and a documented kill/recovery procedure.

## Cost and account limits

The repository is currently public. Standard GitHub-hosted runners for public repositories are generally free, but this must not be generalized to a future private repository or non-standard runner.

The 30-minute schedule creates at most 48 watchdog runs per day. Each run has a 3-minute hard timeout; actual billed usage depends on runner billing rules and execution duration. Event-driven CI adds usage per push/PR. The account plan, remaining minutes, spending cap, and billing are not visible through this connection. Do not increase spending limits or provision paid infrastructure. If the repository becomes private, verify the plan quota and billing controls before relying on this cadence.

## Security and release boundary

- No automatic merge, auto-merge, release, deployment, or production operation.
- No repository secrets are read or required by these workflows.
- The Watchdog uses only the ephemeral GitHub Actions token with read-only Actions/Contents permissions; the token is not printed or stored in artifacts.
- No workflow uploads artifacts.
- Fork-originated runs are excluded from the privileged monitoring path; the Watchdog checks out main only.
- Keep PR #6 closed/unmerged unless the owner explicitly authorizes a separate action. Do not merge any sensitive PR automatically.
- Do not change repository visibility, branch protection, secrets, or spending limits from this branch.

## Goal 1 acceptance evidence still required

- [ ] Exact-head push and pull-request CI pass on this infrastructure PR.
- [ ] The replacement workflows are reviewed and merged by the owner; no automated merge.
- [ ] At least two successful scheduled Watchdog runs are observed on main.
- [ ] At least 24 hours of post-merge scheduled observation is recorded.
- [ ] A controlled test demonstrates stale-queue/stuck-run detection and bounded API retry without exposing raw output.
- [ ] Concurrency cancellation and timeout behavior are practically verified on GitHub-hosted runners.
- [ ] A failed check is observed and the documented human recovery path is exercised once.
- [ ] Required reviews/checks and native branch protection are verified in repository settings.
- [ ] Runner inventory, account plan, usage quota, and spending limits are confirmed.
- [ ] An independent external heartbeat is evaluated if detection must continue when GitHub Actions itself is unavailable.

Do not declare Goal 1 ready until the practical evidence above is complete. Goal 2 remains blocked.
