"""Live telemetry collection from the durable coordinator for the health observer."""
from __future__ import annotations

import time
from typing import Optional

from .health_observer import (
    ObserverSnapshot,
    ProviderHealth,
    ProviderTelemetry,
    RunState,
    RunTelemetry,
    WorkerHeartbeat,
)
from .sqlite_coordinator import SQLiteCoordinator


_TASK_TO_RUN_STATE = {
    "queued": RunState.QUEUED,
    "recoverable": RunState.QUEUED,
    "submitted": RunState.QUEUED,
    "leased": RunState.LEASED,
    "running": RunState.LEASED,
    "succeeded": RunState.SUCCEEDED,
    "failed": RunState.FAILED,
    "cancelled": RunState.CANCELLED,
}


class CoordinatorHealthCollector:
    """Build a bounded observer snapshot from the persistent SQLite database.

    Backend health remains UNKNOWN until a separate provider probe records an
    explicit successful canary. Missing telemetry is never promoted to healthy.
    """

    def __init__(
        self,
        coordinator: SQLiteCoordinator,
        *,
        task_limit: int = 1000,
        worker_limit: int = 256,
    ) -> None:
        if not 1 <= task_limit <= 5000 or not 1 <= worker_limit <= 2048:
            raise ValueError("collector limits are outside supported bounds")
        self.coordinator = coordinator
        self.task_limit = task_limit
        self.worker_limit = worker_limit

    def collect(self, *, now: Optional[float] = None) -> ObserverSnapshot:
        collected_at = time.time() if now is None else float(now)
        tasks = self.coordinator.list_tasks(limit=self.task_limit)
        heartbeats = self.coordinator.list_worker_heartbeats(limit=self.worker_limit)

        runs = tuple(
            RunTelemetry(
                task_id=task.task_id,
                state=_TASK_TO_RUN_STATE[task.state],
                queued_at=task.created_at,
                lease_expires_at=task.lease_expires_at,
            )
            for task in tasks
        )
        workers = tuple(
            WorkerHeartbeat(
                worker_id=item.worker_id,
                last_heartbeat_at=item.heartbeat_at,
                status=item.status,
                failure_code=item.failure_code,
            )
            for item in heartbeats
        )
        provider_ids = sorted({
            task.provider_id for task in tasks if task.provider_id is not None
        })
        providers = tuple(
            ProviderTelemetry(provider_id=provider_id, health=ProviderHealth.UNKNOWN)
            for provider_id in provider_ids
        )
        return ObserverSnapshot(
            collected_at=collected_at,
            workers=workers,
            runs=runs,
            providers=providers,
            last_successful_canary_at=self.coordinator.latest_successful_canary_at(),
        )
