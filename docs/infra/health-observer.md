# Independent health observer: heartbeat and stuck-run semantics

**Status:** deterministic, read-only assessment primitives; not a running monitor or uptime claim.

## Observation boundary

The observer must run independently of the execution backend it monitors. It consumes a sanitized snapshot collected through separate read-only probes and does not enqueue work, renew leases, cancel runs, restart workers, or mutate coordinator state. This first increment implements deterministic snapshot assessment only; service deployment, external polling, alert delivery, observer HA, and backup/restore remain future work.

## Health rules

- A fresh heartbeat is healthy. A heartbeat older than the configured threshold is stale. A timestamp too far in the future is clock skew. A missing heartbeat is never green.
- A queued run beyond its queue-age threshold is delayed.
- A lease at or before the current time is expired.
- A non-terminal run past its deadline is overdue; terminal runs are not marked overdue.
- Provider unavailable is critical; degraded or unknown provider health is not treated as healthy.
- A missing or stale observer snapshot is UNKNOWN. No telemetry is not evidence of a healthy system.
- A stale/missing canary is surfaced as a reason code; clock skew is surfaced separately.

## Sanitized output

The assessment contains aggregate counts, a bounded set of reason codes, health levels, and ages. It does not include response bodies, raw provider payloads, secrets, environment variables, local paths, or market data.

## Acceptance covered

Tests cover recent/missed/delayed/future heartbeats, clock skew, stale observer snapshots, missing observations, expired leases, run deadlines, delayed queue, provider outage, stale canary, and terminal-run handling.

## Not yet proven

This module does not create heartbeats or poll GitHub/provider APIs. It does not prove observer independence in deployment, continuous coverage, alert delivery, or recovery after observer failure. Those require a separate service/process and operational drill.
