import json
import tempfile
import unittest
from pathlib import Path

from infra.control_plane.safety_gate import (
    DuplicateAcquisition, DuplicateRun, RecoveryRequired, SafetyGateError,
    derive_run_fingerprint, find_existing_acquisition, reject_duplicate_run,
    validate_artifact_registry, preflight,
)


class SafetyGateTests(unittest.TestCase):
    def test_duplicate_artifact_id_fails(self):
        with self.assertRaises(SafetyGateError):
            validate_artifact_registry([{"artifact_id": "a"}, {"artifact_id": "a"}])

    def test_duplicate_hash_fails(self):
        digest = "a" * 64
        with self.assertRaises(SafetyGateError):
            validate_artifact_registry([
                {"artifact_id": "a", "sha256": digest},
                {"artifact_id": "b", "sha256": digest},
            ])

    def test_known_unresolved_artifact_requires_recovery_not_download(self):
        with self.assertRaises(RecoveryRequired):
            find_existing_acquisition(
                [{"artifact_id": "a", "artifact_identity": "symbol-x",
                  "request_fingerprint": "f", "status": "PATH_UNRESOLVED"}],
                artifact_identity="symbol-x", request_fingerprint="f",
            )

    def test_existing_equivalent_artifact_blocks_duplicate_acquisition(self):
        with self.assertRaises(DuplicateAcquisition):
            find_existing_acquisition(
                [{"artifact_id": "a", "artifact_identity": "symbol-x",
                  "request_fingerprint": "f", "storage_path": "/archive/x",
                  "status": "VERIFIED"}],
                artifact_identity="symbol-x", request_fingerprint="f",
            )

    def test_run_fingerprint_is_deterministic(self):
        args = dict(code_sha="a" * 64, input_hashes={"x": "b" * 64},
                    parameters={"window": 5}, environment={"python": "3.12"})
        self.assertEqual(derive_run_fingerprint(**args), derive_run_fingerprint(**args))

    def test_identical_run_is_not_repeated(self):
        fingerprint = "c" * 64
        with self.assertRaises(DuplicateRun):
            reject_duplicate_run([{"run_fingerprint": fingerprint, "status": "FAILED"}], fingerprint)


    def test_preflight_rejects_research_while_infrastructure_scope_is_locked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = root / "policy.json"
            work = root / "work.json"
            artifacts = root / "artifacts.jsonl"
            ledger = root / "runs.jsonl"
            policy.write_text(json.dumps({"scope_lock": "INFRA_ONLY", "research_locked": True}), encoding="utf-8")
            work.write_text(json.dumps({"work_id": "MS-20261116-CONTINUITY-001",
                                        "status": "AUTHORIZED", "allowed_actions": ["research"]}), encoding="utf-8")
            artifacts.write_text("", encoding="utf-8")
            ledger.write_text("", encoding="utf-8")
            with self.assertRaisesRegex(SafetyGateError, "project_scope_locked"):
                preflight(policy_path=policy, work_item_path=work,
                          artifact_registry_path=artifacts, run_ledger_path=ledger,
                          work_id="MS-20261116-CONTINUITY-001", action="research",
                          code_sha="a" * 64, input_artifacts={}, parameters={},
                          environment={}, output_path=root / "new-output")

    def test_changed_parameter_changes_fingerprint(self):
        base = dict(code_sha="a" * 64, input_hashes={"x": "b" * 64},
                    environment={"python": "3.12"})
        self.assertNotEqual(
            derive_run_fingerprint(parameters={"window": 5}, **base),
            derive_run_fingerprint(parameters={"window": 6}, **base),
        )


if __name__ == "__main__":
    unittest.main()
