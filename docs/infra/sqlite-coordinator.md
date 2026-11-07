# SQLite coordinator: first persistence boundary

**Status:** experimental infrastructure component; not a 24/7 or multi-host readiness claim.

## Scope

`infra/control_plane/sqlite_coordinator.py` provides a durable, single-host implementation of the coordinator contract using Python's standard-library `sqlite3` module. It is intended to replace process-local in-memory state for a worker/controller pair that shares one local persistent filesystem.

It provides:

- Persistent task identity and idempotency-key uniqueness.
- Atomic task claims using SQLite write transactions.
- Monotonically increasing fencing tokens.
- Lease expiry and recovery to a claimable state.
- Rejection of stale worker results after lease expiry or reassignment.
- Persistent terminal success/failure state.
- WAL mode and full synchronous commits.

## Explicit limits

This is **not** a distributed database and must not be treated as a multi-host queue. Do not put the SQLite database on an arbitrary network filesystem or allow independent hosts to write it. SQLite locking/WAL semantics and filesystem behavior must be validated for the actual host/storage combination.

It does not submit provider jobs, execute untrusted code, manage secrets, or dispatch GitHub Actions. It does not prove runner uptime, health monitoring, hung-job detection, or failover across machines.

A future multi-host coordinator requires a separately reviewed transactional service/API and an explicit zero-cost deployment decision. Do not silently replace this component with a paid managed database.

## Required acceptance

Run the new tests from a clean checkout:

```bash
python3 -m unittest -v infra.control_plane.test_sqlite_coordinator
```

The tests cover restart persistence, idempotent enqueue across coordinator instances, identity conflicts, concurrent claim exclusion, lease expiry/reclaim, fencing against stale results, and terminal failure behavior.

Before operational use, still validate:
- Process-level contention under the intended filesystem and OS.
- Crash/restart behavior with abrupt process termination.
- Database backup/restore and corruption handling.
- Disk-full and locked-database behavior.
- Bounded queue growth and retention policy.
- File ownership/permissions and service-account isolation.

No market data, private datasets, secrets, paid services, merge, deployment, or investment actions are in scope.
