# Dependency-aware task registry and scheduler

**Status:** deterministic planning/selection primitives; no task dispatch is connected.

## Task record

Each immutable task record contains a stable task ID, versioned definition, objective, owner, input digest, dependency IDs, explicit acceptance criteria, expected artifacts, timeout, retry budget, priority, state, and zero-cost/no-secret/no-network/privileged-action policy fields.

The registry rejects duplicate IDs, unknown/self/duplicate dependencies, cycles, missing acceptance/evidence fields, invalid digests, unbounded retry/time budgets, nonzero cost, network/secret access, and merge/deploy/investment permissions.

## Scheduler behavior

The selector validates the full graph, then returns only tasks whose stored state is explicitly READY and whose dependencies are all DONE. It selects deterministically by priority and task ID and respects the number of already-running tasks. BLOCKED, RUNNING, DONE, and REJECTED tasks are never dispatched by this selector.

Selection does not reserve a lease and is not an execution authorization. A durable coordinator must atomically claim a selected task before a worker is started. A later integration will use the SQLite coordinator and immutable task manifest.

## Acceptance covered

- Stable IDs and task definitions.
- Missing dependencies, duplicate identifiers, self-dependencies, and cycles rejected.
- Deterministic topological order.
- Dependency-aware scheduling and independent parallel selection.
- Active task capacity and explicit BLOCKED state respected.
- Bounded state transitions and retry budget.
- Zero cost, no network, no secrets, and no privileged actions enforced.

## Not yet covered

This increment does not yet materialize every live GitHub issue/PR as a versioned registry record, persist selections, reserve a lease, start a worker, or report execution through a status endpoint. Those integration steps remain required before this becomes an operational scheduler.
