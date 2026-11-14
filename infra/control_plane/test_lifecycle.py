from __future__ import annotations

import unittest

from infra.control_plane.lifecycle import (
    FakeProvider, IdempotencyConflict, InMemoryCoordinator, RunState,
)


class FakeProviderLifecycleTests(unittest.TestCase):
    def test_duplicate_submit_returns_one_external_run(self) -> None:
        provider = FakeProvider()
        first = provider.submit(idempotency_key="key-1", input_digest="a" * 64)
        second = provider.submit(idempotency_key="key-1", input_digest="a" * 64)
        self.assertEqual(first.external_run_id, second.external_run_id)

    def test_key_reuse_with_different_input_is_rejected(self) -> None:
        provider = FakeProvider()
        provider.submit(idempotency_key="key-1", input_digest="a" * 64)
        with self.assertRaises(IdempotencyConflict):
            provider.submit(idempotency_key="key-1", input_digest="b" * 64)

    def test_lost_submit_response_is_reconciled_without_resubmit(self) -> None:
        provider = FakeProvider()
        with self.assertRaises(TimeoutError):
            provider.submit(
                idempotency_key="key-1", input_digest="a" * 64, lose_response=True
            )
        reconciled = provider.reconcile("key-1")
        self.assertIsNotNone(reconciled)
        self.assertEqual(reconciled, provider.reconcile("key-1"))

    def test_unknown_submission_is_not_treated_as_absent(self) -> None:
        provider = FakeProvider()
        self.assertIsNone(provider.reconcile("not-submitted"))
        with self.assertRaises(TimeoutError):
            provider.submit(
                idempotency_key="ambiguous", input_digest="c" * 64, lose_response=True
            )
        self.assertIsNotNone(provider.reconcile("ambiguous"))

    def test_terminal_provider_run_cannot_be_reopened(self) -> None:
        provider = FakeProvider()
        run = provider.submit(idempotency_key="key-1", input_digest="a" * 64)
        provider.set_state(run.external_run_id, RunState.FAILED)
        with self.assertRaises(ValueError):
            provider.set_state(run.external_run_id, RunState.RUNNING)


class CoordinatorLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinator = InMemoryCoordinator()
        self.task = self.coordinator.enqueue(
            task_id="task-1", idempotency_key="key-1", input_digest="a" * 64
        )

    def test_duplicate_delivery_creates_one_logical_task(self) -> None:
        duplicate = self.coordinator.enqueue(
            task_id="task-2", idempotency_key="key-1", input_digest="a" * 64
        )
        self.assertIs(duplicate, self.task)

    def test_task_id_collision_does_not_overwrite_existing_task(self) -> None:
        with self.assertRaises(IdempotencyConflict):
            self.coordinator.enqueue(
                task_id="task-1", idempotency_key="key-2", input_digest="b" * 64
            )
        self.assertIs(self.coordinator.get("task-1"), self.task)
        duplicate = self.coordinator.enqueue(
            task_id="task-2", idempotency_key="key-1", input_digest="a" * 64
        )
        self.assertIs(duplicate, self.task)

    def test_only_one_owner_can_claim_active_task(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="worker-a")
        self.assertIsNotNone(lease)
        self.assertIsNone(self.coordinator.claim(task_id="task-1", owner="worker-b"))

    def test_expired_lease_increments_fence_and_rejects_stale_result(self) -> None:
        old = self.coordinator.claim(task_id="task-1", owner="worker-a")
        self.coordinator.recover_expired(task_id="task-1", current_owner="worker-a")
        new = self.coordinator.claim(task_id="task-1", owner="worker-b")
        self.assertGreater(new.fencing_token, old.fencing_token)
        self.assertFalse(self.coordinator.publish_result(lease=old, result="stale"))
        self.assertTrue(self.coordinator.publish_result(lease=new, result="fresh"))

    def test_test_failure_is_terminal_and_not_claimable_for_failover(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="worker-a")
        self.assertTrue(
            self.coordinator.mark_failed(lease=lease, failure_class="test_failure")
        )
        self.assertEqual(self.coordinator.get("task-1").state, "failed")
        self.assertIsNone(self.coordinator.claim(task_id="task-1", owner="other-provider"))

    def test_stale_worker_cannot_publish_failure_after_lease_recovery(self) -> None:
        old = self.coordinator.claim(task_id="task-1", owner="worker-a")
        self.coordinator.recover_expired(task_id="task-1", current_owner="worker-a")
        current = self.coordinator.claim(task_id="task-1", owner="worker-b")
        self.assertFalse(
            self.coordinator.mark_failed(lease=old, failure_class="test_failure")
        )
        self.assertEqual(self.coordinator.get("task-1").state, "leased")
        self.assertTrue(
            self.coordinator.mark_failed(lease=current, failure_class="test_failure")
        )
        self.assertEqual(self.coordinator.get("task-1").state, "failed")


if __name__ == "__main__":
    unittest.main()
