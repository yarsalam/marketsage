import tempfile
import unittest
from pathlib import Path

from infra.control_plane.backup_restore import (
    BackupSafetyError,
    create_backup_copy,
    restore_backup_copy,
    validate_321_copies,
    verify_backup_copy,
)


class BackupRestoreTests(unittest.TestCase):
    def test_three_two_one_copy_metadata_and_restore_are_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.bin"
            source.write_bytes(b"immutable synthetic fixture")
            specs = [
                ("loc-a", "disk", "rack-a", False),
                ("loc-b", "disk", "rack-b", False),
                ("loc-c", "removable", "offline-vault", True),
            ]
            records = []
            for index, (location, medium, failure, offline) in enumerate(specs):
                target = root / f"target-{index}"
                target.mkdir()
                records.append(create_backup_copy(
                    source, target_root=target, relative_path="raw/raw.bin",
                    backup_id="backup-1", artifact_id="fixture-1",
                    location_id=location, medium_id=medium,
                    failure_domain=failure, offline_attested=offline,
                ))
            topology = validate_321_copies(records)
            self.assertEqual(topology, {
                "copies": 3, "locations": 3, "media": 2, "failure_domains": 3,
            })
            self.assertTrue(all(verify_backup_copy(record)[0] == records[0]["sha256"] for record in records))
            restored = restore_backup_copy(records[2], root / "restore" / "raw.bin")
            self.assertTrue(restored["verified"])
            self.assertEqual((root / "restore" / "raw.bin").read_bytes(), source.read_bytes())

    def test_three_copies_without_offline_attestation_are_rejected(self):
        records = [
            {"location_id": "a", "medium_id": "disk", "failure_domain": "a",
             "offline_attested": False, "verified": True, "sha256": "a" * 64, "size_bytes": 1},
            {"location_id": "b", "medium_id": "disk", "failure_domain": "b",
             "offline_attested": False, "verified": True, "sha256": "a" * 64, "size_bytes": 1},
            {"location_id": "c", "medium_id": "removable", "failure_domain": "c",
             "offline_attested": False, "verified": True, "sha256": "a" * 64, "size_bytes": 1},
        ]
        with self.assertRaisesRegex(BackupSafetyError, "offline_copy_attestation_required"):
            validate_321_copies(records)

    def test_tampered_backup_copy_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.bin"
            source.write_bytes(b"source")
            target = root / "target"
            target.mkdir()
            record = create_backup_copy(
                source, target_root=target, relative_path="raw.bin",
                backup_id="backup-1", artifact_id="fixture-1",
                location_id="loc-a", medium_id="disk", failure_domain="rack-a",
                offline_attested=False,
            )
            Path(record["copy_path"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(BackupSafetyError, "backup_copy_integrity_mismatch"):
                verify_backup_copy(record)

    def test_backup_and_restore_never_overwrite_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.bin"
            source.write_bytes(b"source")
            target = root / "target"
            target.mkdir()
            record = create_backup_copy(
                source, target_root=target, relative_path="raw.bin",
                backup_id="backup-1", artifact_id="fixture-1",
                location_id="loc-a", medium_id="disk", failure_domain="rack-a",
                offline_attested=False,
            )
            with self.assertRaisesRegex(BackupSafetyError, "backup_destination_exists_no_overwrite"):
                create_backup_copy(
                    source, target_root=target, relative_path="raw.bin",
                    backup_id="backup-1", artifact_id="fixture-1",
                    location_id="loc-a", medium_id="disk", failure_domain="rack-a",
                    offline_attested=False,
                )
            existing = root / "existing.bin"
            existing.write_bytes(b"keep")
            with self.assertRaisesRegex(BackupSafetyError, "restore_destination_exists_no_overwrite"):
                restore_backup_copy(record, existing)
            self.assertEqual(existing.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
