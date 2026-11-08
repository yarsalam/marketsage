"""Independent process watchdog for the persistent MarketSage coordinator."""
from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from dataclasses import dataclass
from typing import Optional

from .health_collector import CoordinatorHealthCollector
from .health_observer import HealthAssessment, HealthLevel, assess_snapshot
from .sqlite_coordinator import SQLiteCoordinator


@dataclass(frozen=True)
class WatchdogReport:
    recovered_expired_leases: int
    task_count: int
    worker_count: int
    provider_count: int
    assessment: HealthAssessment

    def sanitized_dict(self) -> dict[str, object]:
        return {
            "health": self.assessment.level.value,
            "recovered_expired_leases": self.recovered_expired_leases,
            "task_count": self.task_count,
            "worker_count": self.worker_count,
            "provider_count": self.provider_count,
            "worker_healthy_count": self.assessment.worker_healthy_count,
            "worker_stale_count": self.assessment.worker_stale_count,
            "worker_missing_count": self.assessment.worker_missing_count,
            "worker_failed_count": self.assessment.worker_failed_count,
            "queued_delayed_count": self.assessment.queued_delayed_count,
            "expired_lease_count": self.assessment.expired_lease_count,
            "provider_unavailable_count": self.assessment.provider_unavailable_count,
            "provider_unknown_count": self.assessment.provider_unknown_count,
            "reason_codes": list(self.assessment.reason_codes),
        }


class CoordinatorWatchdog:
    """Collect, assess and safely recover expired leases without redispatching."""

    def __init__(
        self,
        coordinator: SQLiteCoordinator,
        *,
        worker_id: str = "marketsage-watchdog",
        heartbeat_stale_after_seconds: float = 90.0,
        queue_stall_after_seconds: float = 300.0,
    ) -> None:
        if not worker_id or len(worker_id) > 128:
            raise ValueError("watchdog worker_id is invalid")
        self.coordinator = coordinator
        self.worker_id = worker_id
        self.collector = CoordinatorHealthCollector(coordinator)
        self.heartbeat_stale_after_seconds = heartbeat_stale_after_seconds
        self.queue_stall_after_seconds = queue_stall_after_seconds

    def run_once(self, *, now: Optional[float] = None) -> WatchdogReport:
        current = time.time() if now is None else float(now)
        recovered = self.coordinator.recover_expired(now=current)
        self.coordinator.record_worker_heartbeat(
            worker_id=self.worker_id,
            status="healthy",
            now=current,
        )
        snapshot = self.collector.collect(now=current)
        assessment = assess_snapshot(
            snapshot,
            now=current,
            heartbeat_stale_after_seconds=self.heartbeat_stale_after_seconds,
            queue_stall_after_seconds=self.queue_stall_after_seconds,
        )
        return WatchdogReport(
            recovered_expired_leases=recovered,
            task_count=len(snapshot.runs),
            worker_count=len(snapshot.workers),
            provider_count=len(snapshot.providers),
            assessment=assessment,
        )

    def run_forever(self, *, interval_seconds: int = 30) -> None:
        if not 5 <= interval_seconds <= 3600:
            raise ValueError("watchdog interval must be between 5 and 3600 seconds")
        while True:
            report = self.run_once()
            print(json.dumps(report.sanitized_dict(), sort_keys=True), flush=True)
            time.sleep(interval_seconds)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MarketSage coordinator health watchdog")
    parser.add_argument("--database", required=True, help="persistent local SQLite database path")
    parser.add_argument("--loop", action="store_true", help="run continuously as a service")
    parser.add_argument("--interval-seconds", type=int, default=30)
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args(argv)

    coordinator = SQLiteCoordinator(args.database)
    watchdog = CoordinatorWatchdog(
        coordinator,
        worker_id="marketsage-watchdog-" + socket.gethostname()[:48],
    )
    if args.loop:
        watchdog.run_forever(interval_seconds=args.interval_seconds)
        return 0

    report = watchdog.run_once()
    print(json.dumps(report.sanitized_dict(), sort_keys=True))
    if args.fail_on_critical and report.assessment.level in {
        HealthLevel.CRITICAL, HealthLevel.UNKNOWN,
    }:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
