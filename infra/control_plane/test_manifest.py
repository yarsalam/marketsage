from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from infra.control_plane.manifest import (
    ManifestValidationError,
    derive_idempotency_key,
    validate_manifest,
)


class TaskManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        requested_at = datetime.now(timezone.utc).replace(microsecond=0)
        deadline = requested_at + timedelta(minutes=30)
        self.manifest = {
            "schema_version": 1,
            "task_id": "7d7e0e1c-9df4-4c87-b20b-4f57d4a3d4b7",
            "idempotency_key": "0" * 64,
            "inputs_digest": "a" * 64,
            "queue": "infra",
            "repository": {
                "provider": "github",
                "full_name": "yarsalam/marketsage",
                "ref": "refs/heads/infra/provider-neutral-control-plane-2026-11",
                "commit_sha": "b" * 40,
            },
            "task_definition": {"id": "infra.schema-validation", "version": 1},
            "requested_at": requested_at.isoformat(),
            "deadline": deadline.isoformat(),
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
        repo = self.manifest["repository"]
        task = self.manifest["task_definition"]
        self.manifest["idempotency_key"] = derive_idempotency_key(
            provider=repo["provider"],
            repository=repo["full_name"],
            commit_sha=repo["commit_sha"],
            task_definition_id=task["id"],
            task_definition_version=task["version"],
            inputs_digest=self.manifest["inputs_digest"],
        )

    def test_accepts_valid_infrastructure_manifest(self) -> None:
        validate_manifest(self.manifest)

    def test_idempotency_key_is_stable_and_commit_bound(self) -> None:
        args = {
            "provider": "github",
            "repository": "yarsalam/marketsage",
            "commit_sha": "b" * 40,
            "task_definition_id": "infra.schema-validation",
            "task_definition_version": 1,
            "inputs_digest": "a" * 64,
        }
        self.assertEqual(derive_idempotency_key(**args), derive_idempotency_key(**args))
        changed = dict(args, commit_sha="c" * 40)
        self.assertNotEqual(derive_idempotency_key(**args), derive_idempotency_key(**changed))

    def test_rejects_nonzero_cost_ceiling(self) -> None:
        invalid = {**self.manifest, "policy": {**self.manifest["policy"], "cost_ceiling_minor_units": 1}}
        with self.assertRaises(ManifestValidationError):
            validate_manifest(invalid)

    def test_rejects_secret_access_and_does_not_echo_secret(self) -> None:
        secret = "sensitive-token-value"
        invalid = {**self.manifest, "policy": {**self.manifest["policy"], "secrets_access": secret}}
        with self.assertRaises(ManifestValidationError) as caught:
            validate_manifest(invalid)
        self.assertNotIn(secret, str(caught.exception))

    def test_rejects_extra_properties(self) -> None:
        invalid = {**self.manifest, "shell_command": "echo unsafe"}
        with self.assertRaises(ManifestValidationError):
            validate_manifest(invalid)

    def test_rejects_network_access(self) -> None:
        invalid = {**self.manifest, "policy": {**self.manifest["policy"], "network_policy": "explicit_allowlist"}}
        with self.assertRaises(ManifestValidationError):
            validate_manifest(invalid)

    def test_rejects_deadline_before_request(self) -> None:
        invalid = {**self.manifest, "deadline": self.manifest["requested_at"]}
        with self.assertRaises(ManifestValidationError):
            validate_manifest(invalid)

    def test_rejects_idempotency_key_not_bound_to_task_identity(self) -> None:
        invalid = {**self.manifest, "idempotency_key": "f" * 64}
        with self.assertRaises(ManifestValidationError):
            validate_manifest(invalid)

    def test_rejects_non_sha_commit_reference(self) -> None:
        invalid = {**self.manifest, "repository": {**self.manifest["repository"], "commit_sha": "main"}}
        with self.assertRaises(ManifestValidationError):
            validate_manifest(invalid)


if __name__ == "__main__":
    unittest.main()