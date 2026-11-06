# Provider-neutral execution architecture

**Status:** design proposal; implementation not yet validated  
**Priority:** infrastructure-first; no ordinary MarketSage product/data/research feature work until the unattended execution system is proven.

## 1. Decision

MarketSage must not depend on GitHub Actions, a single CI vendor, a single VPS provider, or the owner's laptop. GitHub remains the canonical source of truth initially, but task orchestration, execution, result storage, health monitoring, and recovery must be separable and replaceable.

Oracle Cloud is currently unavailable for this project: signup returned an export/compliance denial. Do not bypass it with location spoofing, false identity/address, VPN workarounds, or another person's account. Oracle may only be reconsidered after an official compliance review clears the signup.

A free VPS is not a prerequisite for progress. First make tasks portable and provider-neutral; then attach execution capacity that is actually available and authorized.

## 2. Logical architecture

- **Event intake:** GitHub webhooks (push, pull_request, issue/comment, workflow completion), provider webhooks, and a bounded polling fallback.
- **Control plane:** durable task registry, queue, scheduler, provider selection, leases, retry policy, budget guard, cancellation and operator handoff.
- **Execution adapters:** GitHub Actions, CircleCI, Buildkite, GitLab CI, Woodpecker, Forgejo Actions, and later local/on-demand or rented workers.
- **Portable task runtime:** versioned task manifests and containerized commands; evaluate Dagger for portable execution, but do not require it until a small proof-of-concept demonstrates value.
- **Result plane:** provider-neutral run records, sanitized summaries, test reports and immutable references to artifacts. Keep raw market data and secrets out of CI artifacts.
- **Source resilience:** GitHub remains canonical initially; add a verified read-only mirror to an independent Forge (Forgejo or GitLab) with one-way replication and documented restore. Do not permit split-brain writes.
- **Observability:** heartbeat, worker health, queue age, stuck-task detection, provider availability, budget consumption, failure classification and owner notifications.

## 3. Start small: durable coordinator without premature Temporal/Jenkins

Initial coordinator should be a small, auditable service backed by PostgreSQL. Use PostgreSQL transactions and SKIP LOCKED row claiming to acquire tasks; use leases and heartbeats for worker ownership. Avoid making Redis or a complex workflow engine a mandatory dependency in the first version.

Evaluate Temporal only if real workflows demonstrate a need for durable multi-step orchestration, compensation, long waits, or complex fan-out/fan-in. Jenkins is not the default: it adds a separately operated control plane and plugin/update surface without a demonstrated need. Woodpecker is a candidate self-hosted CI engine, not the coordinator itself.

Suggested core entities:

- task: immutable task id, type, repository, commit SHA, inputs digest, priority, deadline, policy class, idempotency key and status.
- attempt: task id, provider, external run id, worker id, attempt number, start/end, exit classification and sanitized result.
- lease: task id, owner, issued/expiry timestamps, heartbeat timestamp and fencing token.
- provider: enabled state, capabilities, last health check, known quota/budget state, concurrency cap and circuit-breaker state.
- artifact: content digest, storage reference, retention deadline and classification.
- event: append-only lifecycle/audit events with secrets and sensitive payloads excluded.

Task states: queued -> leased -> dispatched -> running -> succeeded | failed | cancelled | timed_out. Provider-capacity failures may return a task to queued after a bounded delay. Code/test failures remain failures and must not be hidden by trying another provider.

## 4. Safe failover protocol

1. Create one durable task and idempotency key for the exact commit and task definition.
2. Select a provider only if its capability, account status, budget guard, concurrency and health checks pass.
3. Acquire a lease with a monotonically increasing fencing token before dispatch.
4. Record the provider dispatch intent before the external API call (transactional outbox pattern); reconcile uncertain dispatch outcomes before trying another provider.
5. A task may fail over only when the first provider confirms it never started, or the coordinator can prove the prior worker has stopped and its lease has expired. Never launch a duplicate just because a run is slow or a quota dashboard is stale.
6. Each worker validates the fencing token before publishing results. Stale workers cannot overwrite a newer attempt.
7. Retry only transient provider/infrastructure failures, with bounded attempts, exponential backoff, jitter and a deadline.
8. Classify failures separately: account/billing/quota, provider outage, queue/concurrency, runner allocation, network, worker loss, policy denial, configuration, code/test failure.
9. A failed test remains failed across providers. Fallback is for execution capacity, not for shopping for a passing result.
10. Cancel or quarantine orphaned external runs before reassigning work.

## 5. Provider evaluation matrix

| Provider | Hosted capacity | Self-hosted capacity | Current role |
|---|---|---|---|
| GitHub Actions | Included quota exhausted on this private repo; account Actions budget currently blocks usage | Self-hosted runner supported | Keep configured; do not dispatch hosted jobs until quota reset or owner-approved budget change |
| CircleCI | Free plan currently advertises up to 6,000 build minutes on small Docker, 5 active users; credits depend on resource class | Supported; free plan advertises up to 5 concurrent self-hosted tasks | First hosted fallback candidate; verify private-repository eligibility and actual credit metering |
| Buildkite | Free plan currently advertises up to 2,000 Linux vCPU minutes/month | Up to 10 concurrent self-hosted agents on Free plan | Secondary candidate; validate account free-plan transition and limits |
| GitLab CI | Hosted shared-runner limits depend on current plan/namespace and must be verified in-account | Self-managed runners supported | Evaluate as alternate Forge and runner control plane |
| Woodpecker CI | Not a free hosted capacity source by itself | Requires compute we control | Preferred lightweight self-hosted CI candidate |
| Forgejo Actions | Not a free compute source by itself | Requires compute we control | Evaluate as independent Forge + Actions-compatible runner |
| Jenkins | Not a free compute source by itself | Requires compute we control | Defer unless a concrete plugin/job need justifies it |
| Dagger | Not a hosted scheduler or quota pool | Runs wherever a compatible worker exists | Evaluate as portable task execution layer, not a CI provider |

Provider pricing and quotas change. Treat public plan pages as leads, not proof of an account's actual entitlement. Recheck before activation and record the date, plan, resource class, concurrency and cost exposure. Never infer free capacity solely from account creation.

## 6. Compute strategy without Oracle

- **No-cost hosted CI first:** use only confirmed free capacity on CircleCI/Buildkite/GitLab after validating the actual account and private-repository conditions.
- **Self-hosted second:** evaluate a low-cost isolated VPS only after estimating monthly cost and obtaining explicit owner authorization. Do not install a CI worker on the yarsalam production VPS.
- **Free cloud trials:** may be used only as temporary experiments if eligibility and terms permit; credits/trials are not treated as durable always-on capacity.
- **Owner laptop:** may be an explicitly on-demand worker, never the always-on coordinator or sole execution path.
- **No free compute available:** continue repository-only design, documentation, static analysis that can be run in the current authorized environment, and local work when the owner is available. Report that 24/7 execution is not yet proven rather than pretending.

## 7. Security and cost boundaries

- Separate worker accounts and ephemeral workspaces; no production network route by default.
- PR code is untrusted. Do not expose secrets to fork/untrusted PR jobs. Use least-privilege, read-only repository tokens wherever possible.
- Do not store provider tokens in repository files, logs, artifacts, task payloads or issue comments.
- Restrict outbound network access where feasible; pin actions/images/dependencies and record provenance.
- Apply per-provider and global monthly ceilings, concurrency limits, job timeouts, storage/egress limits and artifact retention.
- Stop dispatch before a budget ceiling is crossed. No paid usage, plan upgrades, VPS purchase or billing change without explicit owner authorization.
- Sanitize all reports; never upload raw market data, local datasets, personal paths, secrets or sensitive error payloads.
- No automated merge, release, deploy, production access, scoring/ranking activation, probability calibration, backtest approval, broker/trading or capital allocation.
- PR #6 remains under separate explicit approval.

## 8. Work queues

Keep queues separate so independent tasks can run concurrently without editing the same files:

1. infra: coordinator, adapters, runner provisioning, health and recovery.
2. ci-quality: unit/integration/regression tests and portable task definitions.
3. security: dependency, secret, container and workflow permission checks.
4. docs: operator runbooks, architecture records and sanitized reports.
5. source-reliability: source reachability and alternative-source feasibility only; no ingestion or use of unverified data while infrastructure priority is active.
6. research-methods: literature and methodology review only; no scoring activation or backtest execution.
7. release-readiness: acceptance evidence and human approval handoff; no deployment.

Every task must name its owner/agent, exact file scope, base commit, acceptance command, time budget and forbidden actions. Parallel workers must use isolated branches/workspaces. Integration is serialized through a review queue.

## 9. Acceptance tests before calling this 24/7-ready

- Event-triggered task creation and scheduled task creation both work.
- At least two genuinely independent providers are configured and tested, or one provider plus an independently controlled worker pool.
- A quota/account-blocked provider is classified correctly and a safe failover succeeds.
- A real test failure does not trigger provider shopping and remains visible as failed.
- Simulated lost worker/expired lease recovers without duplicate publication.
- Uncertain dispatch is reconciled before fallback.
- Duplicate webhook delivery creates one logical task.
- Budget stop, concurrency cap, timeout, cancellation and bounded retry are demonstrated.
- Health check and stale queue/run detection produce a sanitized operator notification.
- Restore from the independent source mirror is demonstrated without split-brain writes.
- All workflows and worker permissions are reviewed; no secrets or sensitive datasets appear in logs/artifacts.
- Operator runbook documents account limitations, manual actions, incident recovery and shutdown.
- End-to-end evidence is recorded. Until then, do not claim unattended 24/7 readiness.

## 10. Immediate next steps

1. Audit the existing workflows and current PR #50 implementation against this architecture.
2. Prototype a provider-neutral task manifest and local coordinator interface; no hosted Actions dispatch required.
3. Verify CircleCI Free and Buildkite Free account-level eligibility before creating dependencies on them. Account creation and OAuth authorization require the owner.
4. Evaluate GitLab shared-runner allowance and self-managed runner terms for a private repository.
5. Build a small Dagger portability proof only if it simplifies running the existing test commands.
6. Select Woodpecker or Forgejo only after a suitable isolated compute host is available.
7. Run the failover/recovery drills before expanding to other project queues.
