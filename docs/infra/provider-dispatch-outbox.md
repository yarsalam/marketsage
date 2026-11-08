# Durable provider dispatch outbox

**Status:** first durable submission-state component; not a complete orchestrator or 24/7 worker.

`infra/control_plane/dispatch_outbox.py` records provider submission intent before the external call. It uses SQLite transactions and persists a bounded attempt history keyed by the immutable task idempotency key and input digest.

## Safety behavior

- A new task starts in `prepared`.
- `begin_attempt` commits `submitting` before a caller contacts a provider. A second process cannot reserve a parallel attempt.
- A process interruption or lost response must be recorded as `unknown`. An unknown submission survives restart and blocks another provider.
- A reconciliation receipt can turn `unknown` into `accepted`; a missing reconciliation result leaves it unknown and blocked.
- Only a definitive pre-acceptance rejection permits another provider.
- A terminal failure permits another provider only when the caller supplies an explicit provider guarantee that the failed run produced no side effect.
- Success and cancellation are terminal. Provider attempts are bounded to three and each provider ID can be attempted only once for one task key.
- Reuse of an idempotency key with a different SHA-256 input digest is rejected.

## Important limits

This module does not call providers, execute workers, or itself provide exactly-once external effects. The orchestrator must place `begin_attempt` before every provider submission, persist all returned receipts/outcomes, reconcile every uncertain submission by key, and only pass `no_side_effects_on_failure=true` when backed by a provider contract and conformance evidence. A false provider guarantee can still create duplicate external effects.

SQLite is single-host only and must use a local persistent filesystem. It is not a multi-host distributed coordinator. No live provider, secrets, network calls, paid services, market data, merge, deploy, or investment activity is included.

## Tests

`python -m unittest -v infra.control_plane.test_dispatch_outbox` covers restart persistence, concurrent attempt reservation, ambiguity blocking, reconciliation, safe pre-acceptance failover, provider-guaranteed no-effect failover, terminal success, immutable input binding, and bounded provider attempts.

## Orchestration integration

`infra/control_plane/orchestrator.py` now wires the strict manifest validator,
`SQLiteCoordinator`, `SQLiteDispatchOutbox`, and `SafeFailoverRouter` into one
intake-to-dispatch path. `DurableOrchestrator.submit()` validates first, persists
the logical task, prepares the outbox, and then calls the router's
`submit_durable()` method. `reconcile()` resumes an existing task without
creating a new logical task.

The durable router reserves each provider attempt before calling the adapter.
It marks definite capacity rejection as rejected, records ambiguous submissions
as unknown, and reconciles by the same immutable key before considering any
other provider. Unexpected adapter errors are treated as ambiguous. The v1
manifest policy is enforced against adapter declarations: non-zero cost,
network access, or secret requirements are ineligible.

The integration tests use deterministic in-process fake adapters only. They
cover duplicate delivery, definitive capacity failover, lost-response
reconciliation, unknown-state blocking, simulated restart after provider
acceptance, terminal no-effect failover, invalid-manifest rejection, and
provider-policy rejection.

This still does not execute worker code, and does not turn fake provider
contracts into evidence about any real external provider. The coordinator task
record remains the durable intake record; a worker execution/result lifecycle
and concrete OS sandbox remain separate acceptance stages.
