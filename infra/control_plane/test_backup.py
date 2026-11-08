from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from infra.control_plane.backup import create_backup, restore_backup
from infra.control_plane.dispatch_outbox import DispatchState, SQLiteDispatchOutbox
from infra.control_plane.sqlite_coordinator import SQLiteCoordinator


class SQLiteBackupRestoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "control-plane.sqlite3"
        self.coordinator = SQLiteCoordinator(self.database)
        self.outbox = SQLiteDispatchOutbox(self.database)
        self.task_id = "backup-test-task"
        self.key = "b" * 64
        self.digest = "a" * 64
        self.coordinator.enqueue(
            task_id=self.task_id,
            idempotency_key=self.key,
            input_digest=self.digest,
            manifest_json='{"schema_version":1,"task_id":"backup-test-task"}',
        )
        self.outbox.prepare(idempotency_key=self.key, input_digest=self.digest)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_backup_and_restore_preserve_coordinator_and_outbox_state(self) -> None:
        backup = self.root / "snapshot.sqlite3"
        restored = self.root / "restored.sqlite3"

        report = create_backup(self.database, backup)
        self.assertEqual(report.integrity, "ok")
        self.assertEqual(len(report.sha256), 64)
        self.assertGreater(report.size_bytes, 0)
        self.assertGreater(report.page_count, 0)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)

        restored_report = restore_backup(backup, restored)
        self.assertEqual(restored_report.integrity, "ok")
        self.assertTrue(restored.exists())

        recovered_coordinator = SQLiteCoordinator(restored)
        recovered_outbox = SQLiteDispatchOutbox(restored)
        task = recovered_coordinator.get(self.task_id)
        dispatch = recovered_outbox.get(self.key)
        self.assertEqual(task.state, "queued")
        self.assertEqual(task.input_digest, self.digest)
        self.assertEqual(
            recovered_coordinator.get_manifest(self.task_id),
            {"schema_version": 1, "task_id": self.task_id},
        )
        self.assertEqual(dispatch.state, DispatchState.PREPARED)
        self.assertEqual(dispatch.input_digest, self.digest)

    def test_backup_refuses_to_overwrite_existing_destination(self) -> None:
        destination = self.root / "existing.sqlite3"
        destination.write_bytes(b"do-not-replace")
        with self.assertRaises(FileExistsError):
            create_backup(self.database, destination)
        self.assertEqual(destination.read_bytes(), b"do-not-replace")

    def test_restore_refuses_to_overwrite_existing_destination(self) -> None:
        backup = self.root / "snapshot.sqlite3"
        destination = self.root / "existing-restore.sqlite3"
        create_backup(self.database, backup)
        destination.write_bytes(b"do-not-replace")
        with self.assertRaises(FileExistsError):
            restore_backup(backup, destination)
        self.assertEqual(destination.read_bytes(), b"do-not-replace")

    def test_corrupt_source_is_rejected_without_publishing_a_backup(self) -> None:
        corrupt = self.root / "corrupt.sqlite3"
        destination = self.root / "must-not-exist.sqlite3"
        corrupt.write_bytes(b"not-a-sqlite-database")
        with self.assertRaises(sqlite3.DatabaseError):
            create_backup(corrupt, destination)
        self.assertFalse(destination.exists())

    def test_corrupt_backup_is_rejected_before_restore(self) -> None:
        corrupt = self.root / "corrupt-backup.sqlite3"
        destination = self.root / "must-not-exist.sqlite3"
        corrupt.write_bytes(b"not-a-sqlite-database")
        with self.assertRaises(sqlite3.DatabaseError):
            restore_backup(corrupt, destination)
        self.assertFalse(destination.exists())

    def test_source_and_destination_must_differ(self) -> None:
        with self.assertRaises(ValueError):
            create_backup(self.database, self.database)
        with self.assertRaises(ValueError):
            restore_backup(self.database, self.database)


if __name__ == "__main__":
    unittest.main()
