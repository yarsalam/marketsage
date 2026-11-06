# Provider-neutral task contract v1

**Status:** draft interface for implementation; not yet wired to a scheduler or worker. **No CI execution is triggered by this file.**

## Purpose

Every provider must receive the same logical task definition. Provider adapters translate the task into CircleCI, Buildkite, Gitee Go, GitFlic, Woodpecker, Forgejo Actions, or a local worker request. Provider-specific YAML must not become the source of truth for task intent or safety policy.

Machine-readable schema: `schemas/infra-task-v1.schema.json`.

## Required identity

- `task_id`: unique logical task ID (UUID).
- `idempotency_key`: stable key for the logical work, derived from repository, immutable commit SHA, task definition version and normalized inputs. A duplicate webhook must resolve to the same logical task.
- `repository.commit_sha`: immutable 40-character Git commit SHA. Never dispatch against a moving branch name alone.
- `task_definition.id` and `version`: allowlisted task profile, not an arbitrary command supplied by a webhook or untrusted PR.
- `requested_at` and `deadline`: timestamps used for expiry and bounded execution.

## Policy invariants for the current infrastructure-only phase

- `cost_ceiling_minor_units` must be `0`; no provider may activate paid usage, pay-as-you-go, trial overage or automatic top-up.
- `secrets_access` must be `none`.
- `production_access`, `merge_allowed`, `deploy_allowed` and `investment_actions_allowed` must be `false`.
- `repository_access` is read-only at most.
- `network_policy` is `none` by default; any future allowlist requires explicit policy review.
- Artifacts may be only sanitized summaries and test reports. Raw market data, secrets, private local paths and unredacted error payloads are forbidden.
- Task definitions are allowlisted and versioned. The coordinator must reject unknown task IDs, policy escalation, extra properties and expired deadlines.

## State and concurrency are coordinator-owned

The manifest is immutable input, not a mutable run status. The coordinator stores lifecycle state and attempts separately:

`queued -> leased -> dispatch_pending -> dispatched -> running -> succeeded | failed | cancelled | timed_out`.

- Persist dispatch intent before calling a provider (transactional outbox).
- A lease has an owner, expiry, heartbeat and monotonically increasing fencing token.
- Reconcile an uncertain provider response before failover; do not dispatch a second copy merely because the first response timed out.
- A worker may publish results only while its fencing token is current.
- Retry only capacity/provider/worker-loss failures. A code or test failure remains failed and is never hidden by provider shopping.
- Keep attempt history and sanitized failure classification for audit.

## Provider adapter contract

An adapter must implement: `capabilities()`, `health()`, `submit(task, idempotency_key)`, `inspect(external_run_id)`, `cancel(external_run_id)`, and `normalize_result(external_run_id)`. The adapter must return a definitive state or `unknown`; `unknown` requires reconciliation, not immediate failover.

Provider-specific features are optional. The coordinator must not assume a vendor's YAML, webhook, cache, secret store, runner, or artifact format is portable.

## Acceptance before implementation is considered complete

1. Validate manifests against the JSON Schema and reject unknown fields.
2. Duplicate delivery creates one logical task.
3. Concurrent workers cannot claim the same active lease.
4. Expired lease recovery increments fencing token and rejects stale result publication.
5. Simulated dispatch timeout is reconciled before a second submit.
6. Provider quota/account block is classified separately from test failure.
7. Test failure remains failed and is not retried on a different provider.
8. Cost guard rejects every provider requiring billing activation or paid overage.
9. Redaction test proves secrets, raw market data and local paths cannot enter result artifacts.
10. No merge, deploy, production access, ranking/scoring or investment action is reachable through this contract.

## Implementation order

1. Schema validation and deterministic idempotency key tests.
2. Coordinator persistence model and transactional outbox.
3. Lease/heartbeat/fencing implementation and recovery tests.
4. Local fake provider adapter for deterministic contract tests.
5. Only then implement real provider adapters, starting with a local isolated runner.
6. External providers remain disabled until account, jurisdiction, quota and zero-billing eligibility are verified.
## Initial implementation status

- `schemas/infra-task-v1.schema.json`: strict Draft 2020-12 schema; unknown fields are rejected. Current policy fixes cost at zero, secrets and network access off, and production/merge/deploy/investment actions off.
- `infra/control_plane/manifest.py`: validates the schema, requires timezone-aware timestamps and a deadline after request time, derives a stable SHA-256 idempotency key from provider/repository/commit/task-version/input digest, and reports only sanitized validation paths/rule names.
- `infra/control_plane/test_manifest.py`: tests valid manifests, commit-bound idempotency, cost/network/secret denial, unknown fields, invalid commit SHA, deadline ordering, identity mismatch and safe multi-error reporting.
- `requirements-infra.txt`: isolates the JSON Schema validation dependency from the MarketSage analysis-engine dependencies.

A temporary isolated harness using the same schema and validator logic passed 10 checks. This was not a run from a repository checkout and was not a GitHub Actions run. The repository tests still need to be executed from a clean checkout when an authorized non-billed execution environment is available.

Not implemented yet: persistent task storage, transactional outbox, provider adapters, leases/heartbeats/fencing, dispatch reconciliation, fake-provider lifecycle tests, monitoring or recovery. This contract and validator do not establish 24/7 readiness.
