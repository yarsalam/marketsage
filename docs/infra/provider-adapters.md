# Provider adapters and safe failover

**Status:** fake-backend conformance layer only; no live provider integration.

## Adapter contract

Each adapter exposes immutable capabilities and four operations: submit, inspect, reconcile by idempotency key, and request cancellation. The router distinguishes two materially different errors:

- A definite capacity rejection means the adapter guarantees no run was accepted. The router may move to the next adapter.
- An uncertain submit means acceptance may have happened. The router reconciles once by the immutable task key and must stop if the run remains unknown. It never guesses that a timeout means no execution.

A cancellation request is not a terminal result. Running work remains non-terminal until the adapter reports a terminal state.

## Failover rules

The router only retries an already accepted run on another backend after inspecting the original provider and confirming a terminal failure whose adapter capability explicitly guarantees that the failure produced no side effect. Success is returned as success; queued, running, cancelled, missing, or ambiguous runs block failover.

The deterministic tests share a fake idempotent effect ledger across backends. This proves deduplication inside the simulation only. It is not a claim of exactly-once behavior for arbitrary real providers. Real adapters must document their idempotency scope, lookup guarantees, cancellation semantics, capacity-rejection semantics, and failure side-effect guarantees before they can be eligible for routing.

## Capabilities and policy

The current fake adapters have zero cost, no network requirement, no secrets, and an unrestricted architecture label for test purposes. Those fields are descriptive fixture values; they do not authorize any real provider or execution. Real provider capability records must be reviewed against the task manifest's cost, network, secret, and architecture policy.

## Acceptance covered

- Two independent fake adapters implement the same protocol.
- Duplicate submissions with the same key and digest return one fake run.
- Key reuse with a different digest is rejected.
- Definite capacity rejection safely tries the next backend.
- Ambiguous submission reconciles or fails closed without submitting elsewhere.
- A running task and an unconfirmed cancellation cannot fail over.
- Only a verified no-effect terminal failure can retry on the next backend.
- Shared fake idempotency sink records one side effect.

## Not covered

No real cloud provider, account, credential, secret, external network, live job, billing, service deployment, production dataset, market-data fetch, investment scoring, backtest approval, broker access, or trading is enabled. Lease-expiry and durable cross-process coordination remain separate integration work with the SQLite coordinator.
