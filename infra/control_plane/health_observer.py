"""Pure, read-only health assessment primitives for an independent observer.

The observer consumes snapshots from a separate collector. This module does not
connect to a worker backend, write coordinator state, restart work, or dispatch
tasks. Missing or stale telemetry is reported as unknown/degraded, never healthy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence


class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class HeartbeatLevel(str, Enum):
    HEALTHY = "healthy"
    STALE = "stale"
    CLOCK_SKEW = "clock_skew"
    MISSING = "missing"
    FAILED = "failed"


class RunState(str, Enum):
    QUEUED = "queued"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProviderHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class WorkerHeartbeat:
    worker_id: str
    last_heartbeat_at: Optional[float]
    status: str = "healthy"
    failure_code: Optional[str] = None


@dataclass(frozen=True)
class RunTelemetry:
    task_id: str
    state: RunState
    queued_at: float
    lease_expires_at: Optional[float] = None
    deadline_at: Optional[float] = None


@dataclass(frozen=True)
class ProviderTelemetry:
    provider_id: str
    health: ProviderHealth


@dataclass(frozen=True)
class ObserverSnapshot:
    collected_at: Optional[float]
    workers: tuple[WorkerHeartbeat, ...] = ()
    runs: tuple[RunTelemetry, ...] = ()
    providers: tuple[ProviderTelemetry, ...] = ()
    last_successful_canary_at: Optional[float] = None


@dataclass(frozen=True)
class HeartbeatAssessment:
    worker_id: str
    level: HeartbeatLevel
    age_seconds: Optional[float]


@dataclass(frozen=True)
class HealthAssessment:
    level: HealthLevel
    observer_age_seconds: Optional[float]
    worker_healthy_count: int
    worker_stale_count: int
    worker_clock_skew_count: int
    worker_missing_count: int
    worker_failed_count: int
    queued_delayed_count: int
    expired_lease_count: int
    deadline_exceeded_count: int
    provider_unavailable_count: int
    provider_degraded_count: int
    provider_unknown_count: int
    canary_age_seconds: Optional[float]
    reason_codes: tuple[str, ...]


def assess_heartbeat(
    heartbeat: WorkerHeartbeat,
    *,
    now: float,
    stale_after_seconds: float = 90.0,
    clock_skew_tolerance_seconds: float = 30.0,
) -> HeartbeatAssessment:
    if not heartbeat.worker_id:
        raise ValueError("worker_id is required")
    if heartbeat.status not in {"starting", "healthy", "idle", "stopping", "failed"}:
        raise ValueError("worker status is invalid")
    if stale_after_seconds <= 0 or clock_skew_tolerance_seconds < 0:
        raise ValueError("heartbeat thresholds are invalid")
    if heartbeat.status == "failed":
        return HeartbeatAssessment(heartbeat.worker_id, HeartbeatLevel.FAILED, None)
    seen = heartbeat.last_heartbeat_at
    if seen is None:
        return HeartbeatAssessment(heartbeat.worker_id, HeartbeatLevel.MISSING, None)
    if seen < 0 or now < 0:
        raise ValueError("heartbeat timestamps cannot be negative")
    age = now - seen
    if age < -clock_skew_tolerance_seconds:
        return HeartbeatAssessment(heartbeat.worker_id, HeartbeatLevel.CLOCK_SKEW, age)
    normalized_age = max(0.0, age)
    if normalized_age > stale_after_seconds:
        return HeartbeatAssessment(heartbeat.worker_id, HeartbeatLevel.STALE, normalized_age)
    return HeartbeatAssessment(heartbeat.worker_id, HeartbeatLevel.HEALTHY, normalized_age)


def assess_snapshot(
    snapshot: ObserverSnapshot,
    *,
    now: float,
    heartbeat_stale_after_seconds: float = 90.0,
    queue_stall_after_seconds: float = 300.0,
    canary_stale_after_seconds: float = 900.0,
    observer_stale_after_seconds: float = 120.0,
    clock_skew_tolerance_seconds: float = 30.0,
) -> HealthAssessment:
    """Return sanitized aggregate counts from a point-in-time telemetry snapshot."""
    thresholds = (
        heartbeat_stale_after_seconds,
        queue_stall_after_seconds,
        canary_stale_after_seconds,
        observer_stale_after_seconds,
    )
    if any(value <= 0 for value in thresholds) or clock_skew_tolerance_seconds < 0:
        raise ValueError("observer thresholds are invalid")
    if now < 0:
        raise ValueError("now cannot be negative")

    if snapshot.collected_at is None:
        return _unknown("observer_snapshot_missing")
    if snapshot.collected_at < 0:
        raise ValueError("collected_at cannot be negative")
    observer_age = now - snapshot.collected_at
    if observer_age < -clock_skew_tolerance_seconds:
        return _unknown("observer_clock_skew", observer_age)
    observer_age = max(0.0, observer_age)
    if observer_age > observer_stale_after_seconds:
        return _unknown("observer_snapshot_stale", observer_age)

    heartbeat_results = [
        assess_heartbeat(
            item,
            now=now,
            stale_after_seconds=heartbeat_stale_after_seconds,
            clock_skew_tolerance_seconds=clock_skew_tolerance_seconds,
        )
        for item in snapshot.workers
    ]
    healthy_workers = sum(x.level == HeartbeatLevel.HEALTHY for x in heartbeat_results)
    stale_workers = sum(x.level == HeartbeatLevel.STALE for x in heartbeat_results)
    skewed_workers = sum(x.level == HeartbeatLevel.CLOCK_SKEW for x in heartbeat_results)
    missing_workers = sum(x.level == HeartbeatLevel.MISSING for x in heartbeat_results)
    failed_workers = sum(x.level == HeartbeatLevel.FAILED for x in heartbeat_results)

    delayed_queue = 0
    expired_leases = 0
    overdue_runs = 0
    for run in snapshot.runs:
        if not run.task_id or run.queued_at < 0:
            raise ValueError("run telemetry identity/timestamp is invalid")
        if run.state in {RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED}:
            continue
        if run.deadline_at is not None and run.deadline_at <= now:
            overdue_runs += 1
        if run.state == RunState.QUEUED and now - run.queued_at > queue_stall_after_seconds:
            delayed_queue += 1
        if run.state == RunState.LEASED:
            if run.lease_expires_at is None or run.lease_expires_at < 0:
                raise ValueError("leased work requires a valid lease expiry")
            if run.lease_expires_at <= now:
                expired_leases += 1

    provider_unavailable = sum(x.health == ProviderHealth.UNAVAILABLE for x in snapshot.providers)
    provider_degraded = sum(x.health == ProviderHealth.DEGRADED for x in snapshot.providers)
    provider_unknown = sum(x.health == ProviderHealth.UNKNOWN for x in snapshot.providers)

    canary_age: Optional[float] = None
    canary_missing = snapshot.last_successful_canary_at is None
    canary_clock_skew = False
    if snapshot.last_successful_canary_at is not None:
        if snapshot.last_successful_canary_at < 0:
            raise ValueError("canary timestamp cannot be negative")
        canary_age = now - snapshot.last_successful_canary_at
        if canary_age < -clock_skew_tolerance_seconds:
            canary_clock_skew = True
        else:
            canary_age = max(0.0, canary_age)

    reason_codes: list[str] = []
    if stale_workers:
        reason_codes.append("worker_heartbeat_stale")
    if skewed_workers:
        reason_codes.append("worker_clock_skew")
    if missing_workers:
        reason_codes.append("worker_heartbeat_missing")
    if failed_workers:
        reason_codes.append("worker_failed")
    if delayed_queue:
        reason_codes.append("queue_delay")
    if expired_leases:
        reason_codes.append("lease_expired")
    if overdue_runs:
        reason_codes.append("run_deadline_exceeded")
    if provider_unavailable:
        reason_codes.append("provider_unavailable")
    if provider_degraded:
        reason_codes.append("provider_degraded")
    if provider_unknown:
        reason_codes.append("provider_health_unknown")
    if not snapshot.providers:
        reason_codes.append("provider_telemetry_missing")
    if not snapshot.workers:
        reason_codes.append("worker_telemetry_missing")
    if canary_missing:
        reason_codes.append("canary_missing")
    elif canary_clock_skew:
        reason_codes.append("canary_clock_skew")
    elif canary_age is not None and canary_age > canary_stale_after_seconds:
        reason_codes.append("canary_stale")

    no_observations = not (
        snapshot.workers or snapshot.runs or snapshot.providers
        or snapshot.last_successful_canary_at is not None
    )
    if no_observations:
        level = HealthLevel.UNKNOWN
        reason_codes.append("no_observations")
    elif stale_workers or failed_workers or expired_leases or overdue_runs or provider_unavailable:
        level = HealthLevel.CRITICAL
    elif reason_codes:
        level = HealthLevel.DEGRADED
    else:
        level = HealthLevel.HEALTHY

    return HealthAssessment(
        level=level,
        observer_age_seconds=observer_age,
        worker_healthy_count=healthy_workers,
        worker_stale_count=stale_workers,
        worker_clock_skew_count=skewed_workers,
        worker_missing_count=missing_workers,
        worker_failed_count=failed_workers,
        queued_delayed_count=delayed_queue,
        expired_lease_count=expired_leases,
        deadline_exceeded_count=overdue_runs,
        provider_unavailable_count=provider_unavailable,
        provider_degraded_count=provider_degraded,
        provider_unknown_count=provider_unknown,
        canary_age_seconds=canary_age,
        reason_codes=tuple(sorted(set(reason_codes))),
    )


def _unknown(reason: str, observer_age: Optional[float] = None) -> HealthAssessment:
    return HealthAssessment(
        level=HealthLevel.UNKNOWN,
        observer_age_seconds=observer_age,
        worker_healthy_count=0,
        worker_stale_count=0,
        worker_clock_skew_count=0,
        worker_missing_count=0,
        worker_failed_count=0,
        queued_delayed_count=0,
        expired_lease_count=0,
        deadline_exceeded_count=0,
        provider_unavailable_count=0,
        provider_degraded_count=0,
        provider_unknown_count=0,
        canary_age_seconds=None,
        reason_codes=(reason,),
    )
