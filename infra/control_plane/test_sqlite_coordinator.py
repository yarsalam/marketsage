from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from infra.control_plane.sqlite_coordinator import (
    IdempotencyConflict,
    SQLiteCoordinator,
)


class SQLiteCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "coordinator.sqlite3"
        self.coordinator = SQLiteCoordinator(self.db)
        self.coordinator.enqueue(
            task_id="task-1", idempotency_key="key-1", input_digest="a" * 64
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_task_survives_coordinator_restart(self) -> None:
        reopened = SQLiteCoordinator(self.db)
        self.assertEqual(reopened.get("task-1").state, "queued")

    def test_duplicate_delivery_is_idempotent_across_instances(self) -> None:
        second = SQLiteCoordinator(self.db)
        result = second.enqueue(
            task_id="task-other", idempotency_key="key-1", input_digest="a" * 64
        )
        self.assertEqual(result.task_id, "task-1")

    def test_key_reuse_with_different_input_is_rejected(self) -> None:
        with self.assertRaises(IdempotencyConflict):
            self.coordinator.enqueue(
                task_id="task-2", idempotency_key="key-1", input_digest="b" * 64
            )

    def test_task_id_collision_is_rejected(self) -> None:
        with self.assertRaises(IdempotencyConflict):
            self.coordinator.enqueue(
                task_id="task-1", idempotency_key="key-2", input_digest="b" * 64
            )

    def test_only_one_concurrent_owner_can_claim(self) -> None:
        second = SQLiteCoordinator(self.db)
        barrier = threading.Barrier(2)
        results = []

        def run(coordinator: SQLiteCoordinator, owner: str) -> None:
            barrier.wait()
            results.append(coordinator.claim(task_id="task-1", owner=owner))

        first_thread = threading.Thread(target=run, args=(self.coordinator, "worker-a"))
        second_thread = threading.Thread(target=run, args=(second, "worker-b"))
        first_thread.start()
        second_thread.start()
        first_thread.join()
        second_thread.join()
        self.assertEqual(sum(item is not None for item in results), 1)

    def test_expired_lease_is_reclaimed_with_new_fence(self) -> None:
        old = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=10, now=100
        )
        self.assertEqual(self.coordinator.recover_expired(now=109), 0)
        self.assertEqual(self.coordinator.recover_expired(now=110), 1)
        new = self.coordinator.claim(
            task_id="task-1", owner="worker-b", lease_seconds=10, now=110
        )
        self.assertGreater(new.fencing_token, old.fencing_token)
        self.assertFalse(
            self.coordinator.publish_result(lease=old, result="stale", now=111)
        )
        self.assertTrue(
            self.coordinator.publish_result(lease=new, result="fresh", now=111)
        )
        reopened = SQLiteCoordinator(self.db)
        self.assertEqual(reopened.get("task-1").result, "fresh")

    def test_expired_worker_cannot_publish_before_recovery_sweep(self) -> None:
        lease = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=2, now=100
        )
        self.assertFalse(
            self.coordinator.publish_result(lease=lease, result="late", now=102)
        )
        self.assertEqual(self.coordinator.get("task-1").state, "leased")

    def test_terminal_failure_is_persisted_and_not_claimable(self) -> None:
        lease = self.coordinator.claim(
            task_id="task-1", owner="worker-a", now=100
        )
        self.assertTrue(
            self.coordinator.mark_failed(
                lease=lease, failure_class="test_failure", now=101
            )
        )
        self.assertEqual(self.coordinator.get("task-1").state, "failed")
        self.assertIsNone(
            self.coordinator.claim(task_id="task-1", owner="worker-b", now=102)
        )

    def test_unknown_failure_class_is_rejected(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="worker-a")
        with self.assertRaises(ValueError):
            self.coordinator.mark_failed(
                lease=lease, failure_class="retry-anything"
            )


if __name__ == "__main__":
    unittest.main()
