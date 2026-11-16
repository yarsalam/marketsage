import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from infra.control_plane.backup_restore import (
    BackupSafetyError,
    create_backup_copy,
    restore_backup_copy,
    validate_321_copies,
    verify_backup_copy,
)
from infra.control_plane.validate_backup_manifest import BackupManifestError, validate_backup_manifest



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
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            manifest = {
                "manifest_version": 1, "backup_id": "backup-1",
                "artifact_id": "fixture-1", "source_sha256": records[0]["sha256"],
                "source_size_bytes": records[0]["size_bytes"], "created_at_utc": now,
                "copies": records,
                "restore_drills": [{
                    "restore_id": "restore-1", "source_location_id": "loc-c",
                    "restored_path": restored["restored_path"],
                    "sha256": restored["sha256"], "size_bytes": restored["size_bytes"],
                    "restored_at_utc": now, "verified": True,
                }],
            }
            schema_path = Path(__file__).resolve().parents[2] / "schemas" / "backup-manifest-v1.schema.json"
            self.assertEqual(validate_backup_manifest(manifest, schema_path=schema_path)["copies"], 3)

    def test_manifest_rejects_copy_hash_mismatch_and_incomplete_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "raw.bin"
            source.write_bytes(b"backup fixture")
            records = []
            for index, (location, medium, failure, offline) in enumerate([
                ("a", "disk", "rack-a", False),
                ("b", "disk", "rack-b", False),
                ("c", "removable", "vault", True),
            ]):
                target = root / f"target-{index}"
                target.mkdir()
                records.append(create_backup_copy(
                    source, target_root=target, relative_path="raw.bin",
                    backup_id="backup-2", artifact_id="fixture-2",
                    location_id=location, medium_id=medium,
                    failure_domain=failure, offline_attested=offline,
                ))
            now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            manifest = {
                "manifest_version": 1, "backup_id": "backup-2",
                "artifact_id": "fixture-2", "source_sha256": records[0]["sha256"],
                "source_size_bytes": records[0]["size_bytes"], "created_at_utc": now,
                "copies": records,
                "restore_drills": [{
                    "restore_id": "restore-2", "source_location_id": "c",
                    "restored_path": str(root / "restored.bin"),
                    "sha256": records[0]["sha256"], "size_bytes": records[0]["size_bytes"],
                    "restored_at_utc": now, "verified": True,
                }],
            }
            schema_path = Path(__file__).resolve().parents[2] / "schemas" / "backup-manifest-v1.schema.json"
            manifest["copies"][1]["sha256"] = "f" * 64
            with self.assertRaisesRegex(BackupManifestError, "backup_copy_source_identity_mismatch"):
                validate_backup_manifest(manifest, schema_path=schema_path)

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
