from __future__ import annotations

import unittest

from infra.control_plane.health_observer import (
    HealthLevel,
    HeartbeatLevel,
    ObserverSnapshot,
    ProviderHealth,
    ProviderTelemetry,
    RunState,
    RunTelemetry,
    WorkerHeartbeat,
    assess_heartbeat,
    assess_snapshot,
)


class HeartbeatAssessmentTests(unittest.TestCase):
    def test_recent_heartbeat_is_healthy(self) -> None:
        result = assess_heartbeat(WorkerHeartbeat("worker-a", 95), now=100)
        self.assertEqual(result.level, HeartbeatLevel.HEALTHY)
        self.assertEqual(result.age_seconds, 5)

    def test_missed_heartbeat_is_stale(self) -> None:
        result = assess_heartbeat(WorkerHeartbeat("worker-a", 0), now=100)
        self.assertEqual(result.level, HeartbeatLevel.STALE)

    def test_future_heartbeat_outside_tolerance_is_clock_skew(self) -> None:
        result = assess_heartbeat(WorkerHeartbeat("worker-a", 200), now=100)
        self.assertEqual(result.level, HeartbeatLevel.CLOCK_SKEW)

    def test_missing_heartbeat_is_not_healthy(self) -> None:
        result = assess_heartbeat(WorkerHeartbeat("worker-a", None), now=100)
        self.assertEqual(result.level, HeartbeatLevel.MISSING)

    def test_invalid_threshold_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assess_heartbeat(WorkerHeartbeat("worker-a", 100), now=100, stale_after_seconds=0)


class SnapshotAssessmentTests(unittest.TestCase):
    def test_fresh_snapshot_with_all_green_signals_is_healthy(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=100,
            workers=(WorkerHeartbeat("worker-a", 95),),
            runs=(RunTelemetry("task-a", RunState.QUEUED, queued_at=99),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.HEALTHY),),
            last_successful_canary_at=98,
        )
        assessment = assess_snapshot(snapshot, now=100)
        self.assertEqual(assessment.level, HealthLevel.HEALTHY)
        self.assertEqual(assessment.reason_codes, ())

    def test_stale_observer_snapshot_is_unknown_not_healthy(self) -> None:
        snapshot = ObserverSnapshot(collected_at=0)
        assessment = assess_snapshot(snapshot, now=500)
        self.assertEqual(assessment.level, HealthLevel.UNKNOWN)
        self.assertIn("observer_snapshot_stale", assessment.reason_codes)

    def test_missing_observer_snapshot_is_unknown(self) -> None:
        assessment = assess_snapshot(ObserverSnapshot(collected_at=None), now=100)
        self.assertEqual(assessment.level, HealthLevel.UNKNOWN)
        self.assertEqual(assessment.reason_codes, ("observer_snapshot_missing",))

    def test_expired_lease_and_deadline_are_critical(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=100,
            runs=(RunTelemetry(
                "task-a", RunState.LEASED, queued_at=50,
                lease_expires_at=99, deadline_at=90,
            ),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.HEALTHY),),
        )
        assessment = assess_snapshot(snapshot, now=100)
        self.assertEqual(assessment.level, HealthLevel.CRITICAL)
        self.assertEqual(assessment.expired_lease_count, 1)
        self.assertEqual(assessment.deadline_exceeded_count, 1)

    def test_delayed_queue_and_stale_canary_are_degraded(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=1000,
            runs=(RunTelemetry("task-a", RunState.QUEUED, queued_at=1),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.HEALTHY),),
            last_successful_canary_at=1,
        )
        assessment = assess_snapshot(snapshot, now=1000)
        self.assertEqual(assessment.level, HealthLevel.DEGRADED)
        self.assertEqual(assessment.queued_delayed_count, 1)
        self.assertIn("canary_stale", assessment.reason_codes)

    def test_provider_outage_is_reported_from_external_snapshot(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=100,
            workers=(WorkerHeartbeat("worker-a", 99),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.UNAVAILABLE),),
            last_successful_canary_at=99,
        )
        assessment = assess_snapshot(snapshot, now=100)
        self.assertEqual(assessment.level, HealthLevel.CRITICAL)
        self.assertEqual(assessment.provider_unavailable_count, 1)

    def test_missing_telemetry_is_degraded_not_green(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=100,
            workers=(WorkerHeartbeat("worker-a", None),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.UNKNOWN),),
        )
        assessment = assess_snapshot(snapshot, now=100)
        self.assertEqual(assessment.level, HealthLevel.DEGRADED)
        self.assertIn("worker_heartbeat_missing", assessment.reason_codes)
        self.assertIn("provider_health_unknown", assessment.reason_codes)

    def test_terminal_runs_are_not_counted_as_overdue(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=100,
            runs=(RunTelemetry(
                "task-a", RunState.SUCCEEDED, queued_at=1,
                lease_expires_at=2, deadline_at=3,
            ),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.HEALTHY),),
            last_successful_canary_at=99,
        )
        assessment = assess_snapshot(snapshot, now=100)
        self.assertEqual(assessment.level, HealthLevel.HEALTHY)
        self.assertEqual(assessment.deadline_exceeded_count, 0)

    def test_no_observations_is_unknown(self) -> None:
        assessment = assess_snapshot(ObserverSnapshot(collected_at=100), now=100)
        self.assertEqual(assessment.level, HealthLevel.UNKNOWN)
        self.assertIn("no_observations", assessment.reason_codes)

    def test_worker_clock_skew_is_degraded(self) -> None:
        snapshot = ObserverSnapshot(
            collected_at=100,
            workers=(WorkerHeartbeat("worker-a", 200),),
            providers=(ProviderTelemetry("provider-a", ProviderHealth.HEALTHY),),
            last_successful_canary_at=99,
        )
        assessment = assess_snapshot(snapshot, now=100)
        self.assertEqual(assessment.level, HealthLevel.DEGRADED)
        self.assertEqual(assessment.worker_clock_skew_count, 1)


if __name__ == "__main__":
    unittest.main()
