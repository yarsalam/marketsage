from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from infra.control_plane.dispatch_outbox import DispatchState, SQLiteDispatchOutbox
from infra.control_plane.lifecycle import RunState
from infra.control_plane.manifest import derive_idempotency_key
from infra.control_plane.orchestrator import DurableOrchestrator
from infra.control_plane.providers import (
    DeterministicFakeAdapter, ProviderCapabilities, SafeFailoverRouter,
)
from infra.control_plane.sqlite_coordinator import SQLiteCoordinator


class DurableOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = Path(self.temp.name) / "control-plane.sqlite3"
        self.coordinator = SQLiteCoordinator(database)
        self.outbox = SQLiteDispatchOutbox(database)
        self.backend_a = DeterministicFakeAdapter("backend-a")
        self.backend_b = DeterministicFakeAdapter("backend-b")
        self.router = SafeFailoverRouter([self.backend_a, self.backend_b])
        self.orchestrator = DurableOrchestrator(
            coordinator=self.coordinator,
            outbox=self.outbox,
            router=self.router,
        )
        requested = datetime.now(timezone.utc).replace(microsecond=0)
        repository = {
            "provider": "github",
            "full_name": "yarsalam/marketsage",
            "ref": "refs/heads/infra/durable-provider-dispatch-outbox-2026-11",
            "commit_sha": "b" * 40,
        }
        definition = {"id": "infra.orchestrator-acceptance", "version": 1}
        digest = "a" * 64
        self.manifest = {
            "schema_version": 1,
            "task_id": "7d7e0e1c-9df4-4c87-b20b-4f57d4a3d4b7",
            "idempotency_key": derive_idempotency_key(
                provider=repository["provider"],
                repository=repository["full_name"],
                commit_sha=repository["commit_sha"],
                task_definition_id=definition["id"],
                task_definition_version=definition["version"],
                inputs_digest=digest,
            ),
            "inputs_digest": digest,
            "queue": "infra",
            "repository": repository,
            "task_definition": definition,
            "requested_at": requested.isoformat(),
            "deadline": (requested + timedelta(minutes=30)).isoformat(),
            "policy": {
                "cost_ceiling_minor_units": 0,
                "repository_access": "read-only",
                "secrets_access": "none",
                "network_policy": "none",
                "production_access": False,
                "merge_allowed": False,
                "deploy_allowed": False,
                "investment_actions_allowed": False,
                "raw_market_data_allowed": False,
            },
            "retry_policy": {
                "max_attempts": 2,
                "retry_on": ["provider_unavailable", "worker_lost"],
            },
            "result_policy": {
                "allowed_artifacts": ["sanitized_summary", "test_report"],
                "raw_logs_allowed": False,
                "secret_values_allowed": False,
                "local_paths_allowed": False,
            },
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_manifest_coordinator_outbox_and_router_are_connected(self) -> None:
        result = self.orchestrator.submit(self.manifest)
        self.assertEqual(result.task.state, "queued")
        self.assertTrue(result.dispatch.accepted)
        self.assertEqual(result.dispatch.receipt.provider_id, "backend-a")
        self.assertEqual(result.outbox.state, DispatchState.ACCEPTED)
        self.assertEqual(len(self.outbox.attempts(self.manifest["idempotency_key"])), 1)

    def test_duplicate_delivery_does_not_submit_twice(self) -> None:
        first = self.orchestrator.submit(self.manifest)
        second = self.orchestrator.submit(self.manifest)
        self.assertEqual(first.task.task_id, second.task.task_id)
        self.assertTrue(second.dispatch.accepted)
        self.assertEqual(self.backend_a.submit_calls, 1)
        self.assertEqual(self.backend_a.accepted_count, 1)
        self.assertEqual(self.backend_b.submit_calls, 0)

    def test_definite_capacity_rejection_fails_over_and_is_recorded(self) -> None:
        self.backend_a.capacity_available = False
        result = self.orchestrator.submit(self.manifest)
        self.assertTrue(result.dispatch.accepted)
        self.assertEqual(result.dispatch.receipt.provider_id, "backend-b")
        attempts = self.outbox.attempts(self.manifest["idempotency_key"])
        self.assertEqual([item.provider_id for item in attempts], ["backend-a", "backend-b"])
        self.assertEqual([item.state for item in attempts], [DispatchState.REJECTED, DispatchState.ACCEPTED])

    def test_lost_response_reconciles_same_backend_without_failover(self) -> None:
        self.backend_a.uncertain_after_accept = True
        result = self.orchestrator.submit(self.manifest)
        self.assertTrue(result.dispatch.accepted)
        self.assertEqual(result.outbox.state, DispatchState.ACCEPTED)
        self.assertEqual(self.backend_a.submit_calls, 1)
        self.assertEqual(self.backend_a.accepted_count, 1)
        self.assertEqual(self.backend_b.submit_calls, 0)

    def test_unresolved_submission_stays_unknown_across_reconciliation(self) -> None:
        self.backend_a.uncertain_after_accept = True
        self.backend_a.hide_reconciliation = True
        first = self.orchestrator.submit(self.manifest)
        second = self.orchestrator.reconcile(self.manifest)
        self.assertFalse(first.dispatch.accepted)
        self.assertFalse(second.dispatch.accepted)
        self.assertEqual(second.outbox.state, DispatchState.UNKNOWN)
        self.assertEqual(self.backend_a.submit_calls, 1)
        self.assertEqual(self.backend_b.submit_calls, 0)

    def test_restart_after_provider_acceptance_reconciles_without_resubmit(self) -> None:
        key = self.manifest["idempotency_key"]
        digest = self.manifest["inputs_digest"]
        # Simulate a provider accepting after the durable reservation, then the
        # process dying before it records the receipt in SQLite.
        self.outbox.prepare(idempotency_key=key, input_digest=digest)
        self.outbox.begin_attempt(idempotency_key=key, provider_id="backend-a")
        self.backend_a.submit(idempotency_key=key, input_digest=digest)
        result = self.orchestrator.reconcile(self.manifest)
        self.assertTrue(result.dispatch.accepted)
        self.assertEqual(result.outbox.state, DispatchState.ACCEPTED)
        self.assertEqual(self.backend_a.submit_calls, 1)
        self.assertEqual(self.backend_b.submit_calls, 0)

    def test_terminal_no_effect_failure_can_advance_to_next_backend(self) -> None:
        first = self.orchestrator.submit(self.manifest)
        self.backend_a.mark_terminal(first.dispatch.receipt.external_run_id, RunState.FAILED)
        result = self.orchestrator.reconcile(self.manifest)
        self.assertTrue(result.dispatch.accepted)
        self.assertEqual(result.dispatch.receipt.provider_id, "backend-b")
        attempts = self.outbox.attempts(self.manifest["idempotency_key"])
        self.assertEqual([item.state for item in attempts], [DispatchState.FAILED, DispatchState.ACCEPTED])

    def test_adapter_outside_zero_cost_offline_policy_is_never_called(self) -> None:
        unsafe = DeterministicFakeAdapter("unsafe-backend")
        unsafe.capabilities = ProviderCapabilities(
            provider_id="unsafe-backend",
            network_policy="internet",
            secrets_required=True,
            cost_minor_units=1,
        )
        guarded_router = SafeFailoverRouter([unsafe])
        guarded = DurableOrchestrator(
            coordinator=self.coordinator,
            outbox=self.outbox,
            router=guarded_router,
        )
        result = guarded.submit(self.manifest)
        self.assertFalse(result.dispatch.accepted)
        self.assertEqual(result.dispatch.blocked_reason, "no_eligible_provider")
        self.assertEqual(unsafe.submit_calls, 0)
        self.assertEqual(result.outbox.state, DispatchState.PREPARED)

    def test_invalid_manifest_is_rejected_before_any_durable_registration(self) -> None:
        invalid = {
            **self.manifest,
            "policy": {**self.manifest["policy"], "network_policy": "internet"},
        }
        with self.assertRaises(ValueError):
            self.orchestrator.submit(invalid)
        with self.assertRaises(KeyError):
            self.coordinator.get(self.manifest["task_id"])
        with self.assertRaises(KeyError):
            self.outbox.get(self.manifest["idempotency_key"])


if __name__ == "__main__":
    unittest.main()
