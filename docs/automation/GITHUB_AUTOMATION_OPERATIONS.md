# MarketSage GitHub automation operations

This document describes the repository automation boundary. It does not authorize automatic merges, releases, deployments, provider registration, private-data collection, investment scoring, backtesting approval, broker access, trading, or capital allocation.

## 1. Triggers and execution boundary

The `.github/workflows/ci.yml` workflow runs on:

- Pushes to `main`, `deploy/**`, `research/**`, `ci/**`, and `infra/**`.
- Pull requests targeting `main`, `deploy/**`, and `infra/**`.
- Daily scheduled full validation at **03:17 UTC**.
- Manual `workflow_dispatch`.

Scheduled workflows run from the default branch. A schedule added on a feature branch is not operational until the workflow reaches `main`. GitHub can delay scheduled events; a daily schedule is a recurring health signal, not a real-time SLA or an always-on worker.

Cloud CI uses standard GitHub-hosted `ubuntu-latest` runners. It does not use the owner's laptop Runner. The repository is public by the recorded owner decision; no paid/larger runner or increase to the additional-spend limit is authorized by this workflow.

## 2. CI jobs and bounded runtime

| Job | Timeout | Purpose |
| --- | ---: | --- |
| `analysis` | 25 min | Python analysis and research-engine tests |
| `user-backend` | 30 min | Backend build and tests |
| `user-frontend` | 30 min | Frontend build |
| `admin-workspace` | 30 min | Admin web/API build and tests |
| `production-images` | 40 min | Compose validation and local image build only; no push |
| `infra-control-plane-tests` | 15 min | Discover and run every `test_*.py` module under `infra/control_plane` |
| `ci-infra-tests` | 5 min | Offline regression tests for failure notice and direct-main provenance helpers |
| `detect-direct-main-update` | 5 min | Main-push-only provenance detection |
| `notify-failure` | 5 min | Failure-only sanitized Issue #49 handoff |

All external Actions are pinned to immutable 40-character commit SHAs. Dependabot checks GitHub Actions weekly in one grouped PR; its updates must pass review and CI before acceptance.

Workflow-level permissions default to `contents: read`. The two narrow jobs with issue-comment duties receive job-scoped `issues: write`: the direct-main provenance detector and the failure notifier. The detector also receives `pull-requests: read`. The control-plane/application validation jobs do not need repository secrets or contents-write access.

## 3. Concurrency, cancellation, and retries

The CI concurrency group is keyed by pull-request number when available, otherwise by Git ref. A newer validation for the same PR/ref cancels the superseded CI run; separate PRs remain independent. A cancellation caused by a newer commit is not a test failure—inspect the newest exact-head run.

This cancellation policy is for replaceable CI validation only. Stateful task execution must use the durable coordinator/lease/outbox controls and must not be treated as interchangeable with CI concurrency. A cancel request is not proof that an external execution has stopped; the provider must confirm a terminal state before a retry/failover is considered safe.

Retries must remain bounded and limited to classified transient, idempotent operations. Do not retry permanent 4xx/permission/data-validation failures or rerun whole workflows repeatedly without identifying a transient cause. No unbounded polling or automatic retry loop is authorized.

## 4. Main-branch provenance and protection

The separate **Detect direct main updates** job runs only on a push to `main`. It compares the before/after SHAs and verifies that each pushed commit is associated with a merged PR targeting `main`. A forced/non-fast-forward update, unassociated commit, oversized range, or unverifiable API response produces a sanitized warning on Issue #49 and a failed check.

This is **detection, not prevention**. It does not block or revert a push and is not a replacement for a native ruleset/branch-protection rule. It is intentionally not a required PR check because it is skipped for pull-request events.

The live main ruleset is `main-protection` (ID `26789479`), targeting `refs/heads/main`. It requires PRs and seven status checks: `analysis`, `user-backend`, `user-frontend`, `admin-workspace`, `production-images`, `Test provider-neutral control plane`, and `Test CI automation helpers`; it blocks branch deletion and non-fast-forward updates. The current ruleset asks for **10 approving reviews**, which is likely impractical for the current single-owner operating model. The owner must set an achievable human approval count without weakening the seven required checks. The ruleset payload has no bypass actors; administrator bypass behavior must still be understood from the repository settings.

## 5. Failure reporting and its blind spots

After a failed dependency job, `notify-failure` attempts to add a sanitized comment to Issue #49. It reports the run link and safe job identifiers only. It does not upload logs/artifacts, serialize exception details, or expose credentials, raw market data, prices, private paths, or environment values.

The **failure notifier shares the same GitHub-hosted runner pool as the CI jobs**. It cannot independently report a pool-wide allocation outage if that runner pool itself is unavailable. A missing Issue comment may indicate notification failure; the Actions run remains the source of truth. GitHub Mobile push delivery depends on the owner's notification settings and is not guaranteed by this workflow.

The direct-main detector also posts only fixed reason codes and commit identifiers when it detects an unexpected main update. Neither job is an independent 24/7 observer of the persistent worker/control plane.

## 6. Manual-only local workflows and persistent workers

The TSETMC integrated acceptance, offline dataset validation, and sanitized local diagnostics workflows are deliberately **manual-only**. They require the dedicated self-hosted Runner labels and explicit owner confirmation. They must not be put on a schedule or triggered by ordinary pushes/PRs. Do not dispatch them automatically.

The laptop Runner `marketsage-local-01` is an owner-operated resource, not an always-on host. Its service and local proxy may be healthy while the laptop is running, but this does not establish continuous availability. Do not run untrusted PR code or general coding-agent tasks on it. Private staged datasets remain local, read-only to the Runner, and must not be uploaded to GitHub artifacts or logs.

Any persistent Worker required for unattended task execution must run on a separately managed host or equivalent independently available environment. It needs a dedicated least-privilege account, restricted egress, isolated workspaces, no untrusted-PR execution, immutable worker image, bounded CPU/memory/PIDs/time/output, process supervision, heartbeat, watchdog, disk/backup/restore checks, safe patching, and an independently observable recovery path. No new paid server or service is provisioned by this document.

## 7. Daily operations and recovery

1. Open Actions and select **MarketSage CI**.
2. For each PR, inspect the newest run for its exact head commit; older green runs do not validate a newer SHA.
3. For queued/in-progress jobs, inspect the job list and queue age. For cancelled runs, check whether a newer run superseded them.
4. For a failed job, inspect only the failing step needed to identify the cause. Redact credentials, environment values, host paths, raw market values, and private source payloads before sharing diagnostics.
5. Rerun only after identifying a transient, retry-safe failure. Never use unbounded retries.
6. Check the latest successful scheduled run timestamp and confirm the workflow remains enabled. A missing schedule run is not a healthy signal.
7. After any workflow change, validate the exact PR head and inspect all required checks; skipped, cancelled, queued, and stale checks are not successes.
8. For a local-only workflow, review the immutable source SHA and workflow file first, then dispatch manually with the required owner confirmation. Automation must not do this on the owner's behalf.

## 8. Coding-agent boundary

CI validates code; it does not autonomously plan, author, review, and deliver engineering changes. A coding agent must be explicitly enabled and tested before claiming an unattended issue-to-PR loop.

Any permitted agent must be issue-scoped and branch/PR-only, with no merge, auto-merge, release, deployment, production, secrets, billing, or local-only dispatch permission. Human review and exact-head CI remain mandatory. While Issue #49 is open, do not assign ordinary MarketSage product, data-source, or investment-research issues to an agent.

If a cloud coding agent is unavailable or requires a paid plan, do not substitute a broad personal token or unbounded API key in Actions. Evaluate a separately approved and budget-bounded option instead.

## 9. Cost and account controls

Standard GitHub-hosted runners are free for public repositories; private-repository included-minute and billing rules differ by plan. This workflow does not read the owner's billing configuration. Before changing repository visibility, increasing schedule frequency, adding agent execution, or enabling extra runners, verify the current account usage and cost boundary in GitHub settings. Do not increase the USD 0 additional-spending limit or activate paid resources without separate owner approval.

Prefer event-driven push/PR validation plus the bounded daily schedule. Minute-level polling and unbounded job fan-out are prohibited.

## 10. Acceptance status and completion boundary

The following facts are established:

- Main has a real successful daily `schedule` run: [run #42471588681](https://github.com/yarsalam/marketsage/actions/runs/42471588681).
- The direct-main detector has unit coverage and a post-merge main-push execution record.
- The current provider-neutral PR #71 head has green exact-head push/PR CI, including **164/164** control-plane tests, and a successful hosted Docker worker canary.
- The two-backend fake-adapter/outbox tests cover duplicate delivery, lost/ambiguous response reconciliation, crash boundaries, safe failover, and one simulated shared side effect.

The full infrastructure acceptance is **not complete**. Remaining evidence includes controlled concurrency/timeout/cancellation drills, operational task-registry-to-dispatch integration, a process-level independent observer/recovery drill, persistent Worker operation independent of the laptop, a clean end-to-end worker acceptance on the intended host, backup/restore and resource-exhaustion recovery, an issue-to-PR agent test if permitted, owner confirmation of the practical main approval count, and a full 24-hour observation window. The schedule is not an uptime SLA.

A successful CI run validates code in its runner environment only. It does not prove provider availability, local Runner availability, a legal/eligible data source, an investment strategy, or 24/7 service. Do not claim readiness until the remaining acceptance items have exact evidence.

## 11. Non-authorized actions

No automatic merge, auto-merge, release, publish, deployment, production change, secret creation/rotation/access, billing change, provider account activation, raw market data collection, investment scoring/ranking/probability calibration, backtest approval, broker access, trading, or capital allocation is authorized.
