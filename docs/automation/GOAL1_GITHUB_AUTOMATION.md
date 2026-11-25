# MarketSage Goal 1 — GitHub automation operations

**Status:** proposed in a Draft PR; not active on main until human review and merge.

## Scope and safety boundary

This change is limited to GitHub automation. Until Goal 1 is accepted, CI does not execute product analysis, data acquisition, backtests, scoring/ranking, probability calibration, production-image builds, deployments, broker/trading access, or capital allocation. The existing required status-check names are preserved so the active main-protection ruleset remains compatible.

The repository is currently reported by GitHub as **public**, despite the owner request describing it as private. Treat all committed content and history as public. No visibility change is included.

## Event-driven validation

The CI workflow is intended to run on every branch push, pull requests targeting main, and a daily scheduled run at **03:17 UTC**.

The workflow classifies changed paths using a strict exact-path allowlist. Only a PR from an infra/** branch containing Goal 1 automation files can take the infrastructure-only path. Unknown, empty, mixed, product, data, or unclassifiable changes fail closed.

The existing required contexts are retained: analysis, user-backend, user-frontend, admin-workspace, production-images, Test provider-neutral control plane, and Test CI automation helpers.

For an allowlisted Goal 1 change, the five product/build contexts are skipped (GitHub treats skipped jobs as successful); the two automation test contexts run. For every other scope, the five contexts fail immediately with fixed messages and do not run product commands.

All CI jobs have explicit timeouts. Actions are pinned to immutable commit SHAs. Default permissions are contents:read; only the trusted notification/provenance jobs receive job-scoped issues:write, and the CI failure-notice job is further restricted to main and infra/** refs. Checkout credentials are not persisted. No artifact upload/download is configured.

## Queue, cancellation, retry, and recovery

The CI concurrency group is per PR/ref and event type with cancel-in-progress enabled. A newer push supersedes an older push for the same ref, and a newer pull-request event supersedes the older run for that PR; a scheduled validation is isolated and cannot cancel event-driven validation. This is appropriate only because CI is read-only and replaceable. If scope classification fails or is cancelled, the required `Test provider-neutral control plane` context fails closed; product/build jobs do not run. Expected cancellation of a superseded classifier does not generate a failure notice.

The watchdog uses a separate concurrency group with queue:max and no cancellation. GitHub permits up to 100 pending runs in a queue:max group; additional runs are canceled when full. queue:max cannot be combined with cancel-in-progress. This is bounded queueing, not an unlimited durable FIFO job broker.

The watchdog retries a transient GitHub API GET once. It does not retry permission/validation errors, rerun workflows, cancel jobs, or restart workers. A stale queued/running job or a failed trusted CI run creates a sanitized issue handoff. Human review determines whether a rerun is safe.

## Health and stuck-run detection

The watchdog runs every 15 minutes and after a MarketSage CI run completes. It reads workflow-run metadata only and checks:
- Queued CI older than 20 minutes.
- In-progress CI older than 35 minutes.
- Missing/stale daily schedule (26-hour threshold).
- Latest trusted infrastructure/main CI failure.
- Latest completed scheduled CI run must conclude successfully; a failed/cancelled schedule is reported even if a newer push succeeds.
- Workflow-run history is read with a five-page (500-run) bound; if the API reports more history than the observer inspected, health is Degraded rather than silently treating a partial scan as complete.
- The latest watchdog state is selected from the newest issue comments.

The observer trusts only runs whose `head_repository.full_name` equals this repository and whose event/branch pair is explicitly allowed: scheduled runs on `main`, pushes to `main` or `infra/**`, and same-repository pull requests from `infra/**`. Fork-originated PR runs are excluded even if their source branch is named `main` or `infra/**`. The `workflow_run` observer job independently skips events whose source repository is not this repository.

The report contains only aggregate state, counts, and fixed reason codes. It excludes run IDs, commit identifiers, logs, artifacts, raw data, prices, private paths, credentials, and secret values. Issue #49 is updated only when the state or reason set changes.

**Important limitation:** the watchdog runs on the same GitHub Actions service/hosted-runner pool it observes. It cannot detect its own missed schedule or a GitHub-wide outage. It is not an independent 24/7 heartbeat. An external observer and alert channel remain required before claiming continuous availability.

## Runner architecture

- Cloud-native CI and watchdog jobs use standard GitHub-hosted ubuntu-latest runners.
- Existing local TSETMC workflows remain manual-only and use the marketsage-local / marketsage-research self-hosted labels. They are not part of this automation and must never be dispatched by the automation.
- The laptop runner is not assumed to be online or always-on.
- No independent server runner is currently confirmed or provisioned.
- If a dedicated server runner is later approved, prefer ephemeral one-job runners, a separate low-privilege OS account, isolated workspaces, restricted egress, no Docker socket unless essential, no access to unrelated secrets/data, automatic teardown, and external log/health monitoring. Do not attach a generic self-hosted label to research jobs.

## Costs and platform limitations

GitHub currently reports this repository as public. Standard GitHub-hosted runners for public repositories are free under GitHub's billing policy; self-hosted runner usage itself is not billed by GitHub, but the server, storage, network, maintenance, and monitoring still cost money. If the repository becomes private, standard hosted compute draws from the account's included Actions usage and additional use may be billed. No larger runner, spending-cap increase, server purchase, or paid external monitor is authorized here.

GitHub scheduled workflows run only from the default branch, can be delayed or dropped during high load, and may be automatically disabled after 60 days of inactivity in public repositories. A schedule is a recurring signal, not a real-time SLA.

References:
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners

## Acceptance still required

This PR does not by itself prove Goal 1. After human review/merge, acceptance still requires:
1. Exact-head push and PR checks pass on the final merged commit.
2. At least one real daily scheduled CI run succeeds.
3. The watchdog observes fresh schedule, queue, running, and failure states.
4. A controlled timeout/failure/recovery drill is completed without an unbounded retry or artifact.
5. At least 24 hours of observed operation is recorded.
6. An independent heartbeat/alert channel is deployed and tested.
7. The runner inventory and costs are verified from repository/account settings.
8. The main-protection ruleset remains active and the seven required contexts are verified.

No automatic merge, release, deployment, provider activation, secret creation, or local workflow dispatch is authorized.
