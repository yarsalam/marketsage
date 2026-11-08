from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from infra.control_plane.health_collector import CoordinatorHealthCollector
from infra.control_plane.health_observer import HealthLevel, ProviderHealth, assess_snapshot
from infra.control_plane.sqlite_coordinator import SQLiteCoordinator
from infra.control_plane.watchdog import CoordinatorWatchdog


class CoordinatorHealthCollectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.coordinator = SQLiteCoordinator(Path(self.temp.name) / "health.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_collector_reports_persisted_worker_and_task_telemetry(self) -> None:
        self.coordinator.enqueue(
            task_id="task-1", idempotency_key="key-1", input_digest="a" * 64
        )
        lease = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=20, now=100
        )
        self.coordinator.record_worker_heartbeat(
            worker_id="worker-a", task_id="task-1", status="healthy", now=101
        )
        snapshot = CoordinatorHealthCollector(self.coordinator).collect(now=102)
        self.assertEqual(snapshot.collected_at, 102)
        self.assertEqual(snapshot.workers[0].worker_id, "worker-a")
        self.assertEqual(snapshot.workers[0].status, "healthy")
        self.assertEqual(snapshot.runs[0].state.value, "leased")
        self.assertEqual(snapshot.runs[0].lease_expires_at, 120)
        self.assertEqual(snapshot.providers, ())
        self.assertIsNone(snapshot.last_successful_canary_at)
        assessment = assess_snapshot(snapshot, now=102)
        self.assertEqual(assessment.level, HealthLevel.DEGRADED)
        self.assertIn("provider_telemetry_missing", assessment.reason_codes)
        self.assertIn("canary_missing", assessment.reason_codes)

    def test_collector_never_promotes_unknown_provider_to_healthy(self) -> None:
        self.coordinator.enqueue(
            task_id="task-2", idempotency_key="key-2", input_digest="b" * 64
        )
        lease = self.coordinator.claim(task_id="task-2", owner="dispatcher", now=100)
        self.coordinator.mark_submitted(
            lease=lease, provider_id="backend-a", external_run_id="run-1", now=101
        )
        self.coordinator.record_worker_heartbeat(
            worker_id="worker-a", task_id="task-2", status="idle", now=102
        )
        snapshot = CoordinatorHealthCollector(self.coordinator).collect(now=103)
        self.assertEqual(snapshot.providers[0].health, ProviderHealth.UNKNOWN)


class CoordinatorWatchdogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.coordinator = SQLiteCoordinator(Path(self.temp.name) / "watchdog.sqlite3")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_watchdog_recovers_expired_lease_and_emits_its_own_heartbeat(self) -> None:
        self.coordinator.enqueue(
            task_id="task-1", idempotency_key="key-1", input_digest="a" * 64
        )
        self.coordinator.claim(
            task_id="task-1", owner="dead-worker", lease_seconds=2, now=100
        )
        report = CoordinatorWatchdog(
            self.coordinator, worker_id="watchdog-test"
        ).run_once(now=103)
        self.assertEqual(report.recovered_expired_leases, 1)
        self.assertEqual(report.task_count, 1)
        self.assertEqual(report.worker_count, 1)
        self.assertEqual(self.coordinator.get("task-1").state, "recoverable")
        self.assertEqual(
            self.coordinator.list_worker_heartbeats()[0].worker_id,
            "watchdog-test",
        )
        self.assertNotEqual(report.assessment.level, HealthLevel.HEALTHY)

    def test_stale_worker_heartbeat_is_reported_critical(self) -> None:
        self.coordinator.record_worker_heartbeat(
            worker_id="dead-worker", status="healthy", now=1
        )
        report = CoordinatorWatchdog(self.coordinator).run_once(now=200)
        self.assertEqual(report.assessment.level, HealthLevel.CRITICAL)
        self.assertIn("worker_heartbeat_stale", report.assessment.reason_codes)


if __name__ == "__main__":
    unittest.main()
