import unittest
import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from infra.control_plane.validate_governance import (
    GovernanceValidationError,
    validate_artifact_records,
    validate_run_records,
)


def artifact(artifact_id="a", digest="a" * 64, identity="symbol-a", request=None,
             status="VERIFIED", storage_path="/archive/a", backup="NOT_VERIFIED"):
    return {
        "artifact_id": artifact_id,
        "artifact_identity": identity,
        "sha256": digest,
        "request_fingerprint": request,
        "status": status,
        "storage_path": storage_path,
        "backup_restore_status": backup,
    }


class GovernanceValidationTests(unittest.TestCase):
    def test_duplicate_artifact_id_is_rejected(self):
        with self.assertRaisesRegex(GovernanceValidationError, "duplicate_artifact_id"):
            validate_artifact_records([artifact(), artifact(digest="b" * 64, identity="symbol-b")])

    def test_duplicate_hash_is_rejected(self):
        with self.assertRaisesRegex(GovernanceValidationError, "duplicate_artifact_sha256"):
            validate_artifact_records([
                artifact(),
                artifact(artifact_id="b", identity="symbol-b"),
            ])

    def test_duplicate_acquisition_fingerprint_is_rejected(self):
        with self.assertRaisesRegex(GovernanceValidationError, "duplicate_acquisition_fingerprint"):
            validate_artifact_records([
                artifact(request="c" * 64),
                artifact(artifact_id="b", digest="b" * 64, identity="symbol-b", request="c" * 64),
            ])

    def test_unresolved_artifact_must_not_claim_a_path_or_verified_restore(self):
        with self.assertRaisesRegex(GovernanceValidationError, "unresolved_artifact_has_storage_path"):
            validate_artifact_records([
                artifact(status="PATH_UNRESOLVED", storage_path="/unknown")
            ])

    def test_duplicate_run_fingerprint_is_rejected_even_after_failure(self):
        policy = {"research_locked": True, "allowed_actions": ["synthetic_test"]}
        work = {"work_id": "MS-20261116-CONTINUITY-001", "allowed_actions": ["synthetic_test"]}
        reservation = {
            "event_id": "event-1", "event_type": "RESERVED",
            "run_id": "run-1", "work_id": work["work_id"],
            "action": "synthetic_test", "run_fingerprint": "d" * 64,
        }
        failed = {
            "event_id": "event-2", "event_type": "FINALIZED",
            "run_id": "run-1", "run_fingerprint": "d" * 64,
        }
        duplicate = {
            **reservation, "event_id": "event-3", "run_id": "run-2",
        }
        with self.assertRaisesRegex(GovernanceValidationError, "duplicate_run_fingerprint"):
            validate_run_records([reservation, failed, duplicate], policy, work)

    def test_running_reservation_without_terminal_event_is_valid(self):
        policy = {"research_locked": True, "allowed_actions": ["synthetic_test"]}
        work = {"work_id": "MS-20261116-CONTINUITY-001", "allowed_actions": ["synthetic_test"]}
        reservation = {
            "event_id": "event-1", "event_type": "RESERVED",
            "run_id": "run-1", "work_id": work["work_id"],
            "action": "synthetic_test", "run_fingerprint": "d" * 64,
        }
        validate_run_records([reservation], policy, work)


    def test_run_reservation_and_finalization_match_append_only_schema(self):
        root = Path(__file__).resolve().parents[2]
        schema = json.loads((root / "schemas/governance-records-v1.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        reservation = {
            "event_id": "event-1", "event_type": "RESERVED",
            "run_id": "run-1", "work_id": "MS-20261116-CONTINUITY-001",
            "action": "synthetic_test", "run_fingerprint": "d" * 64,
            "code_sha": "a" * 40, "input_hashes": {"fixture": "b" * 64},
            "parameters": {}, "environment": {"python": "3.12"},
            "started_at_utc": now, "recorded_at_utc": now,
            "status": "RUNNING", "exit_code": None,
            "result_artifact_ids": [], "reason": None,
        }
        finalization = {
            "event_id": "event-2", "event_type": "FINALIZED",
            "run_id": "run-1", "run_fingerprint": "d" * 64,
            "recorded_at_utc": now, "status": "FAILED",
            "exit_code": 1, "result_artifact_ids": [], "reason": "synthetic failure",
        }
        self.assertTrue(validator.is_valid(reservation))
        self.assertTrue(validator.is_valid(finalization))

    def test_research_run_is_rejected_while_scope_is_locked(self):
        policy = {"research_locked": True, "allowed_actions": ["research"]}
        work = {"work_id": "MS-20261116-CONTINUITY-001", "allowed_actions": ["research"]}
        record = {
            "event_id": "event-1",
            "event_type": "RESERVED",
            "run_id": "run-1",
            "run_fingerprint": "d" * 64,
            "work_id": work["work_id"],
            "action": "research",
        }
        with self.assertRaisesRegex(GovernanceValidationError, "research_run_recorded_while_locked"):
            validate_run_records([record], policy, work)


if __name__ == "__main__":
    unittest.main()
