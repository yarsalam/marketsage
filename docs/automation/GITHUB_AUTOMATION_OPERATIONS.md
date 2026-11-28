# MarketSage GitHub automation — Goal 1 operations

This document defines the infrastructure-only automation boundary. It does not authorize automatic merges, releases, deployments, product development, market-data acquisition, investment scoring/ranking, probability calibration, backtests, broker access, trading, or capital allocation.

## Verified repository state — 2026-11-28

- GitHub reports the repository visibility as **public**, although the current owner instruction describes it as private. No visibility change was made. Treat all committed content, issues, PRs, and workflow summaries as public until the owner explicitly resolves this mismatch.
- The latest observed main commit is dated 2026-11-26. The previous report that main had not changed since 2026-11-07 was stale.
- PR #85 is **closed and unmerged**. Its proposed automation is not active on main. Do not treat its earlier successful checks as current infrastructure evidence.
- PR #6 is **closed and unmerged**. It was not changed or merged.
- The currently open PRs, verified 2026-11-27, are #88 (this Goal 1 infrastructure PR; open, ready for review, mergeable, with no submitted reviews), #87 (Draft, mergeable), #86 (Draft, mergeable), and #81 (Draft, not mergeable). PRs #87, #86, and #81 are outside the current execution scope and must not be advanced while Goal 1 is active.
- The active main ruleset exposes only branch-deletion and non-fast-forward protections, with no bypass actors. The classic branch-protection endpoint is not readable through the current GitHub connection. Required approvals and required status checks therefore remain unverified.
- Recent Actions history was inspected across the visible run pages. The latest three main-branch runs were: a successful scheduled run on 2026-11-27, a successful main push, and an older cancelled main push. No main-branch failure appeared in that visible history.
- The latest main scheduled run on 2026-11-27 completed successfully but executed the legacy analysis/research-backtest job, backend/frontend/admin build-and-test jobs, and production-image build. This is direct evidence that the prohibited legacy path remains active; it is not Goal 1 health evidence.
- No Goal 1 Watchdog scheduled run is present on main because the replacement Watchdog workflow exists only in PR #88.
- Workflow YAML was inspected. No repository secret values were read. The current connection does not expose runner inventory or account billing/quota details.

### Mainline freeze is not yet active — hard blocker

The current `main` version of `.github/workflows/ci.yml` still defines a daily scheduled trigger (`17 3 * * *`) and `workflow_dispatch`. It also contains an analysis test job that runs the analysis-engine test suite, application/backend/frontend/admin build jobs, and a production-image build job. The exact current file was inspected on 2026-11-28.

PR #88 replaces that workflow on its branch; it is now open and ready for review, but remains unmerged. Therefore the Goal 1-only freeze is **not active on main**. The existing mainline schedule/manual trigger and its analysis/production jobs remain configured until an owner-reviewed change reaches main. Do not dispatch the existing workflow manually. The 2026-11-27 scheduled run proves that the legacy analysis/backtest and production-image jobs have executed recently; no new legacy run was dispatched during this audit.

The three local TSETMC workflows were separately inspected on main: each is manual-only (`workflow_dispatch`) and targets the dedicated self-hosted runner labels. They were not dispatched.

### Current exact-head evidence boundary

The current exact PR #88 head has both push-triggered and pull-request-triggered runs, and both completed successfully. Each run executed one infrastructure contract-test job: 22 watchdog unit tests and 4 workflow contract tests passed; neither run uploaded artifacts. Two earlier exact-head iterations failed on test assertions while the watchdog recovery and billing documentation were being corrected; the current exact head is green on both events. No PR reviews have been submitted.

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
- Checks only main, infra, and ci branches; fork-originated completion events are rejected, and fork-originated runs are excluded again when evaluating API history.
- Reads at most five pages of workflow history (100 runs per page) created within the last 24 hours, retries each read-only GitHub API page at most three times with bounded request timeouts and short backoff, and marks truncated history as degraded instead of silently trusting a partial result. This rolling filter prevents old repository history from permanently exhausting the five-page safety limit.
- Detects queued runs older than 15 minutes, running jobs older than 30 minutes, the latest unrecovered failed/timed-out result per workflow and branch within 24 hours, and a missing or stale successful scheduled heartbeat older than 75 minutes.
- A later successful completion on the same workflow and branch clears an earlier failure; a cancellation does not count as recovery and is reported separately. A missing successful scheduled heartbeat is a degraded state, not an implicit healthy initialization.
- Records aggregate status in the GitHub Actions run summary. It emits no raw logs, artifacts, commit hashes, branch names, run identifiers, market data, prices, private paths, credentials, or tokens.
- Does not automatically rerun failed jobs. A human inspects the failed step and decides whether a single bounded retry is justified.

The scheduled workflow is a best-effort monitor, not an SLA. GitHub scheduled events run from the default branch and may be delayed or dropped during service load. A GitHub-hosted workflow cannot independently alert if GitHub Actions itself is disabled, unavailable, or no longer schedules the workflow. The daily ChatGPT audit is an additional observer, not a 24/7 external heartbeat. Because this repository is currently public, GitHub also automatically disables scheduled workflows after 60 days without repository activity. After any such deactivation, an owner must re-enable the workflow and verify a fresh scheduled success. This is an additional reason that a GitHub-only schedule cannot provide an independent 24/7 guarantee.

## Failure handling and operator recovery

1. Open the GitHub Actions overview and inspect the newest relevant run.
2. Check whether a queued run exceeded 15 minutes or a running job exceeded 30 minutes.
3. For a failed run, inspect only the failing step needed to identify the cause. Never copy raw logs into an issue or chat without sanitization.
4. Do not automatically rerun the entire workflow. Retry only after confirming a transient cause, and prefer the failed job only.
5. A cancelled run may have been superseded by a newer commit. Check the newest run for the same PR/ref before treating cancellation as failure.
6. If the Watchdog API read fails after three attempts, its run is marked failed with a sanitized summary. Verify Actions API permissions and GitHub service status.
7. No artifact is uploaded. GitHub Actions run records and step summaries are the status ledger.

ChatGPT's scheduled audit reports the latest main commit, open PRs, mergeability, recent workflow runs, and blockers in this conversation. The GitHub Watchdog itself writes only to the GitHub Actions step summary: the current integration has no supported callback that posts each 30-minute execution into this ChatGPT conversation. The separate ChatGPT audit is daily, so it cannot guarantee per-30-minute delivery or act as an independent 24/7 heartbeat. Mobile push and email delivery are not asserted as confirmed.

## Runner strategy

- Use GitHub-hosted runners for cloud-native, read-only CI and health checks.
- The three TSETMC workflows on main remain manual-only and require dedicated self-hosted labels. They were not dispatched. The laptop runner is not an always-on service and must never be assumed available.
- Runner inventory could not be verified through the current connection; no always-on server runner is proven to exist.
- Do not provision a persistent runner until a separate server, budget, ownership, and security boundary are approved.
- If a dedicated server runner is later necessary, prefer one-job ephemeral runners or disposable VMs/containers, a dedicated unprivileged OS account, no repository secrets, no fork PR execution, restricted outbound network, isolated workspaces, bounded concurrency, patching, heartbeat, and a documented kill/recovery procedure.

## Cost and account limits

The repository is currently public. Standard GitHub-hosted runners for public repositories are generally free, but this must not be generalized to a future private repository or non-standard runner.

The 30-minute schedule creates at most 48 scheduled watchdog runs per day. At the 3-minute hard timeout, the schedule-only theoretical ceiling is 144 runner-minutes per day, or 4,320 runner-minutes in a 30-day month ($25.92 at the standard Linux x64 rate of $0.006/minute). GitHub rounds each job's partial minute up to a whole billable minute, so if every scheduled job completes in under one minute, the 48 daily runs still represent about 1,440 runner-minutes per 30-day month ($8.64). These are schedule-only estimates; additional `workflow_run`-triggered watchdog executions and event-driven CI are excluded. The 3-minute timeout is a per-run bound, not a monthly spending cap.

GitHub currently reports this repository as public, where standard GitHub-hosted runners are free. If the repository is private on GitHub Free, the included Actions compute is $12 per month (about 2,000 standard Linux x64 minutes at $0.006/minute). At one billable minute per scheduled run, the schedule alone would use about $8.64 of that allowance and leave roughly 560 equivalent minutes for CI and `workflow_run` executions. If every scheduled run reached its 3-minute timeout, the schedule alone would exceed the included amount by about $13.92. Usage beyond the included amount is blocked when no valid payment method is configured; with a payment method, overage may be billed unless a budget stops it. The account plan, payment method, remaining quota, spending cap, and billing are not visible through this connection. Do not increase budgets or provision paid infrastructure. Re-check the plan and budget before relying on this cadence after any visibility change.

## Security and release boundary

- No automatic merge, auto-merge, release, deployment, or production operation.
- No repository secrets are read or required by these workflows.
- The Watchdog uses only the ephemeral GitHub Actions token with read-only Actions/Contents permissions; the token is not printed or stored in artifacts.
- No workflow uploads artifacts.
- Fork-originated runs are excluded from the privileged monitoring path; the Watchdog checks out main only.
- Keep PR #6 closed/unmerged unless the owner explicitly authorizes a separate action. Do not merge any sensitive PR automatically.
- Do not change repository visibility, branch protection, secrets, or spending limits from this branch.

## Goal 1 acceptance evidence still required

- [x] Exact-head push and pull-request CI pass on this infrastructure PR (one infrastructure job per event; 22 unit tests and 4 workflow contract tests; zero artifacts).
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
