# MarketSage GitHub automation operations

This document describes the repository automation boundary. It does not authorize automatic merges, releases, deployments, data collection, investment scoring, backtesting approval, broker access, trading, or capital allocation.

## Current cloud CI design

The `.github/workflows/ci.yml` workflow is intended to run on:

- Pushes to `main`, `deploy/**`, `research/**`, and `ci/**`.
- Pull requests targeting `main` or `deploy/**`.
- A daily scheduled run at 03:17 UTC.
- Manual `workflow_dispatch`.

Scheduled workflows execute from the repository default branch. The daily schedule therefore becomes active only after this workflow change is merged into `main`. GitHub may delay scheduled events during periods of Actions load; this is a recurring health check, not a real-time uptime guarantee.

The workflow uses GitHub-hosted `ubuntu-latest` runners for cloud-native tests and builds. It does not use the owner's laptop runner. The job timeouts are:

| Job | Timeout |
| --- | ---: |
| analysis | 25 minutes |
| user-backend | 30 minutes |
| user-frontend | 30 minutes |
| admin-workspace | 30 minutes |
| production-images | 40 minutes |

The concurrency group is keyed by pull-request number when available, otherwise by Git ref. A newer run for the same PR/ref cancels its superseded run. Separate PRs remain independent. A cancelled run is not evidence of a test failure; inspect the newest run for that PR/ref.

The workflow currently requests only `contents: read`. It does not require repository secrets and must not print credentials, raw datasets, prices, private paths, or unfiltered exception payloads.

## Manual-only local workflows

The TSETMC integrated acceptance and sanitized diagnostics workflows are deliberately manual-only. They require the dedicated self-hosted runner labels and explicit confirmation inputs. They must not be placed on a schedule or triggered by ordinary pushes/PRs. The laptop runner is not an always-on service and must never be assumed available.

Do not use the local runner for untrusted PR code. Any future server runner must be a separately managed, least-privilege environment with restricted network access, isolated workspaces, bounded concurrency, health monitoring, safe patching, and a documented recovery path. Keep private input data off GitHub and out of artifacts.

## Daily operations and failure recovery

1. Open the Actions tab and select **MarketSage CI**.
2. For each PR, inspect the newest run for its exact head commit. Do not infer current success from an older run.
3. If a run is queued or in progress, inspect its job list. If it is cancelled, check whether a newer run superseded it.
4. For a failed job, inspect only the failing step needed to identify the cause. Redact credentials, paths, raw market values, and private source payloads before sharing any diagnostic output.
5. Rerun failed jobs only after identifying a transient failure. Do not create unbounded retries or rerun expensive workflows repeatedly.
6. A missing daily run is not proof of a healthy system. Check the latest successful run timestamp and the Actions workflow's enabled state.
7. After a workflow change, validate the exact PR head before considering the change complete.

GitHub's scheduled events can be delayed or dropped under heavy load. The schedule is intentionally not placed at the start of an hour; it is not an SLA or an always-on worker.

## Automation capabilities not yet enabled

CI validates code; by itself it does not autonomously plan and write new engineering changes. A coding agent must be explicitly enabled and assigned bounded issues before this repository can have an unattended code-authoring loop.

GitHub Copilot cloud agent is one possible option for a personal repository, subject to a paid Copilot plan and the account's cloud-agent feature being enabled. Before using it:

- Confirm the account is eligible and cloud agent is enabled for this repository.
- Keep its work issue-scoped and PR-based.
- Require human review and checks; do not grant merge, release, deployment, secrets, or production permissions.
- Do not assign data/research issues while the infrastructure-first priority is active.

If cloud agent is unavailable, evaluate a separately budgeted coding-agent integration rather than placing an unbounded API key or a broad personal token in CI.

## Cost and account controls

This repository is private. GitHub-hosted runner usage consumes the account's included Actions minutes and may be billed after the allowance is exhausted. The account plan, remaining quota, and billing budget are not visible to this workflow. Before increasing run frequency or adding agent jobs, inspect GitHub Actions usage and configure a hard spending limit that stops additional usage. Prefer bounded daily validation plus event-driven PR checks over minute-level polling.

## Protection and release boundary

The current `main` branch must be protected before enabling any bot or workflow that can write repository contents. Require PR-based changes and the relevant CI checks; disable force-push and branch deletion. Keep merge/release/deploy authority with the repository owner. PR #6 remains subject to separate explicit owner approval.

## Acceptance evidence still required

- Daily schedule is merged to the default branch and at least one scheduled run succeeds.
- Exact-head CI passes after the schedule/concurrency/timeout changes.
- Concurrency cancellation and timeout behavior have been verified with controlled runs.
- Failure notification and stuck-run detection are observable and tested.
- Branch protection and spending limits are verified in repository/account settings.
- A coding agent is enabled with least privilege and demonstrates a bounded issue-to-PR cycle.
- Any persistent server runner has a tested health/recovery process and is independent of the owner's laptop.

Do not claim 24/7 readiness until these checks have evidence.
