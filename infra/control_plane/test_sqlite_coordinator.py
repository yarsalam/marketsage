from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import threading
import time
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

    def test_active_lease_can_be_renewed_without_changing_fence(self) -> None:
        lease = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=10, now=100
        )
        self.assertTrue(
            self.coordinator.renew_lease(
                lease=lease, lease_seconds=20, now=105
            )
        )
        self.assertEqual(self.coordinator.get("task-1").fencing_token, lease.fencing_token)
        self.assertEqual(self.coordinator.recover_expired(now=110), 0)
        self.assertTrue(
            self.coordinator.publish_result(lease=lease, result="renewed", now=124)
        )

    def test_expired_lease_cannot_be_renewed_before_recovery_sweep(self) -> None:
        lease = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=2, now=100
        )
        self.assertFalse(
            self.coordinator.renew_lease(
                lease=lease, lease_seconds=30, now=102
            )
        )

    def test_stale_lease_cannot_be_renewed_after_reclaim(self) -> None:
        old = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=2, now=100
        )
        self.assertEqual(self.coordinator.recover_expired(now=102), 1)
        new = self.coordinator.claim(
            task_id="task-1", owner="worker-b", lease_seconds=30, now=102
        )
        self.assertFalse(
            self.coordinator.renew_lease(
                lease=old, lease_seconds=30, now=103
            )
        )
        self.assertTrue(
            self.coordinator.renew_lease(
                lease=new, lease_seconds=30, now=103
            )
        )

    def test_lease_renewal_requires_positive_duration(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="worker-a", now=100)
        with self.assertRaises(ValueError):
            self.coordinator.renew_lease(
                lease=lease, lease_seconds=0, now=101
            )

    def test_lease_renewal_never_shortens_existing_expiry(self) -> None:
        lease = self.coordinator.claim(
            task_id="task-1", owner="worker-a", lease_seconds=100, now=100
        )
        self.assertTrue(
            self.coordinator.renew_lease(
                lease=lease, lease_seconds=10, now=110
            )
        )
        self.assertEqual(self.coordinator.recover_expired(now=199), 0)

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

    def test_committed_task_survives_abrupt_process_exit(self) -> None:
        script = """
import os
import sys
from infra.control_plane.sqlite_coordinator import SQLiteCoordinator
coordinator = SQLiteCoordinator(sys.argv[1])
coordinator.enqueue(task_id="child-task", idempotency_key="child-key", input_digest="c" * 64)
os._exit(0)
"""
        completed = subprocess.run(
            [sys.executable, "-c", script, str(self.db)],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        reopened = SQLiteCoordinator(self.db)
        self.assertEqual(reopened.get("child-task").state, "queued")

    def test_only_one_separate_process_can_claim_task(self) -> None:
        ready_a = Path(self.temp.name) / "ready-a"
        ready_b = Path(self.temp.name) / "ready-b"
        go = Path(self.temp.name) / "go"
        script = """
import pathlib
import sys
import time
from infra.control_plane.sqlite_coordinator import SQLiteCoordinator
database, ready, gate, owner = sys.argv[1:]
pathlib.Path(ready).touch()
deadline = time.monotonic() + 10
while not pathlib.Path(gate).exists():
    if time.monotonic() >= deadline:
        raise SystemExit("claim gate timed out")
    time.sleep(0.01)
lease = SQLiteCoordinator(database).claim(task_id="task-1", owner=owner)
print("CLAIMED" if lease is not None else "NOT_CLAIMED")
"""
        processes = [
            subprocess.Popen(
                [sys.executable, "-c", script, str(self.db), str(ready_a), str(go), "process-a"],
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ),
            subprocess.Popen(
                [sys.executable, "-c", script, str(self.db), str(ready_b), str(go), "process-b"],
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            ),
        ]
        try:
            deadline = time.monotonic() + 10
            while not (ready_a.exists() and ready_b.exists()):
                if time.monotonic() >= deadline:
                    self.fail("worker processes did not reach the claim barrier")
                time.sleep(0.01)
            go.touch()
            outputs = [process.communicate(timeout=10) for process in processes]
            self.assertTrue(
                all(process.returncode == 0 for process in processes),
                [stderr for _, stderr in outputs],
            )
            outcomes = [stdout.strip() for stdout, _ in outputs]
            self.assertCountEqual(outcomes, ["CLAIMED", "NOT_CLAIMED"])
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)

    def test_provider_acceptance_is_attached_to_current_lease(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="dispatcher", now=100)
        self.assertTrue(self.coordinator.mark_submitted(
            lease=lease, provider_id="backend-a", external_run_id="run-1", now=101
        ))
        task = self.coordinator.get("task-1")
        self.assertEqual(task.state, "submitted")
        self.assertIsNone(task.owner)
        self.assertIsNone(task.lease_expires_at)
        self.assertEqual(task.provider_id, "backend-a")
        self.assertEqual(task.external_run_id, "run-1")

    def test_stale_lease_cannot_attach_provider_acceptance(self) -> None:
        lease = self.coordinator.claim(
            task_id="task-1", owner="dispatcher", lease_seconds=2, now=100
        )
        self.assertFalse(self.coordinator.mark_submitted(
            lease=lease, provider_id="backend-a", external_run_id="run-1", now=102
        ))
        self.assertEqual(self.coordinator.get("task-1").state, "leased")

    def test_provider_heartbeat_and_terminal_result_are_bound_to_run_identity(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="dispatcher", now=100)
        self.assertTrue(self.coordinator.mark_submitted(
            lease=lease, provider_id="backend-a", external_run_id="run-1", now=101
        ))
        self.assertFalse(self.coordinator.mark_provider_running(
            task_id="task-1", provider_id="backend-b",
            external_run_id="run-1", now=102,
        ))
        self.assertTrue(self.coordinator.mark_provider_running(
            task_id="task-1", provider_id="backend-a",
            external_run_id="run-1", now=102,
        ))
        running = self.coordinator.get("task-1")
        self.assertEqual(running.state, "running")
        self.assertEqual(running.heartbeat_at, 102)
        self.assertTrue(self.coordinator.publish_provider_result(
            task_id="task-1", provider_id="backend-a", external_run_id="run-1",
            state="succeeded", result="artifact:sha256:test", now=103,
        ))
        self.assertEqual(self.coordinator.get("task-1").state, "succeeded")
        self.assertTrue(self.coordinator.publish_provider_result(
            task_id="task-1", provider_id="backend-a", external_run_id="run-1",
            state="succeeded", result="artifact:sha256:test", now=104,
        ))
        self.assertFalse(self.coordinator.publish_provider_result(
            task_id="task-1", provider_id="backend-b", external_run_id="run-2",
            state="succeeded", result="artifact:sha256:test", now=105,
        ))

    def test_expired_dispatch_lease_is_released_and_reclaimed_with_new_fence(self) -> None:
        old = self.coordinator.claim(
            task_id="task-1", owner="dispatcher-a", lease_seconds=3, now=100
        )
        self.assertEqual(self.coordinator.recover_expired(now=103), 1)
        new = self.coordinator.claim(
            task_id="task-1", owner="dispatcher-b", lease_seconds=30, now=103
        )
        self.assertGreater(new.fencing_token, old.fencing_token)
        self.assertFalse(self.coordinator.mark_submitted(
            lease=old, provider_id="backend-a", external_run_id="stale", now=104
        ))

    def test_v1_database_migrates_without_losing_queued_tasks(self) -> None:
        legacy = Path(self.temp.name) / "legacy-v1.sqlite3"
        import sqlite3
        with sqlite3.connect(legacy) as connection:
            connection.executescript(
                """
                CREATE TABLE tasks (
                    task_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    input_digest TEXT NOT NULL,
                    state TEXT NOT NULL CHECK (state IN ('queued','leased','recoverable','succeeded','failed')),
                    owner TEXT,
                    fencing_token INTEGER NOT NULL DEFAULT 0 CHECK (fencing_token >= 0),
                    lease_expires_at REAL,
                    result TEXT,
                    failure_class TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    CHECK (
                        (state = 'leased' AND owner IS NOT NULL AND lease_expires_at IS NOT NULL)
                        OR
                        (state <> 'leased' AND owner IS NULL AND lease_expires_at IS NULL)
                    )
                );
                INSERT INTO tasks VALUES (
                    'legacy-task','legacy-key','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                    'queued',NULL,0,NULL,NULL,NULL,1,1
                );
                PRAGMA user_version=1;
                """
            )
        migrated = SQLiteCoordinator(legacy)
        task = migrated.get("legacy-task")
        self.assertEqual(task.state, "queued")
        self.assertIsNone(task.provider_id)
        self.assertIsNone(task.external_run_id)
        lease = migrated.claim(task_id="legacy-task", owner="post-migration")
        self.assertIsNotNone(lease)

    def test_unknown_failure_class_is_rejected(self) -> None:
        lease = self.coordinator.claim(task_id="task-1", owner="worker-a")
        with self.assertRaises(ValueError):
            self.coordinator.mark_failed(
                lease=lease, failure_class="retry-anything"
            )


if __name__ == "__main__":
    unittest.main()
