from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from infra.control_plane.worker_runtime import (
    RuntimePolicyError,
    RuntimeProfile,
    SandboxCapabilities,
    TaskTrustAttestation,
    assert_no_symlink_components,
    bounded_output,
    build_launch_plan,
    build_minimal_environment,
    validate_relative_path,
    validate_sandbox_capabilities,
)

DIGEST = "a" * 64
COMMIT = "b" * 40


def profile() -> RuntimeProfile:
    return RuntimeProfile(
        runtime_id="python312-infra-v1",
        image_digest=DIGEST,
        platform="linux",
        architecture="x86_64",
        uid=10001,
        memory_limit_bytes=512 * 1024 * 1024,
        cpu_quota_millis=1000,
        wall_timeout_seconds=120,
        pids_limit=32,
        tmpfs_limit_bytes=64 * 1024 * 1024,
        output_limit_bytes=1024 * 1024,
    )


def capabilities(**overrides) -> SandboxCapabilities:
    values = {
        "runtime_image_digest": DIGEST,
        "read_only_root": True,
        "read_only_checkout": True,
        "no_network": True,
        "no_new_privileges": True,
        "non_root_user": True,
        "capabilities_dropped": True,
        "seccomp_enforced": True,
        "user_namespace": True,
        "mount_namespace": True,
        "pid_namespace": True,
        "no_host_pid": True,
        "no_host_network": True,
        "no_host_mounts": True,
        "isolated_tmp": True,
        "memory_limit_bytes": 256 * 1024 * 1024,
        "cpu_quota_millis": 500,
        "wall_timeout_seconds": 60,
        "pids_limit": 16,
        "tmpfs_limit_bytes": 32 * 1024 * 1024,
        "output_limit_bytes": 512 * 1024,
    }
    values.update(overrides)
    return SandboxCapabilities(**values)


def manifest() -> dict:
    from datetime import datetime, timedelta, timezone
    from infra.control_plane.manifest import derive_idempotency_key

    now = datetime.now(timezone.utc).replace(microsecond=0)
    repo = {
        "provider": "github",
        "full_name": "yarsalam/marketsage",
        "ref": "refs/heads/main",
        "commit_sha": COMMIT,
    }
    task = {"id": "infra.harmless-check", "version": 1}
    inputs_digest = "c" * 64
    return {
        "schema_version": 1,
        "task_id": "2cb3e01c-2dd7-4ca2-8f8f-01c2a3442c54",
        "idempotency_key": derive_idempotency_key(
            provider=repo["provider"],
            repository=repo["full_name"],
            commit_sha=repo["commit_sha"],
            task_definition_id=task["id"],
            task_definition_version=task["version"],
            inputs_digest=inputs_digest,
        ),
        "inputs_digest": inputs_digest,
        "queue": "infra",
        "repository": repo,
        "task_definition": task,
        "requested_at": now.isoformat(),
        "deadline": (now + timedelta(minutes=5)).isoformat(),
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
        "retry_policy": {"max_attempts": 1, "retry_on": []},
        "result_policy": {
            "allowed_artifacts": ["sanitized_summary", "test_report"],
            "raw_logs_allowed": False,
            "secret_values_allowed": False,
            "local_paths_allowed": False,
        },
    }


class RuntimeProfileTests(unittest.TestCase):
    def test_valid_profile_passes(self) -> None:
        profile().validate()

    def test_root_uid_is_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            RuntimeProfile(**{**profile().__dict__, "uid": 0}).validate()

    def test_mutable_or_unpinned_runtime_is_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            RuntimeProfile(**{**profile().__dict__, "image_digest": "latest"}).validate()

    def test_out_of_bounds_limits_are_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            RuntimeProfile(**{**profile().__dict__, "pids_limit": 10000}).validate()


class SandboxCapabilityTests(unittest.TestCase):
    def test_complete_sandbox_attestation_passes(self) -> None:
        validate_sandbox_capabilities(profile(), capabilities())

    def test_missing_security_control_fails_closed(self) -> None:
        with self.assertRaisesRegex(RuntimePolicyError, "sandbox_control_missing"):
            validate_sandbox_capabilities(profile(), capabilities(no_network=False))

    def test_resource_limit_above_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimePolicyError, "not_enforced_within_profile"):
            validate_sandbox_capabilities(
                profile(), capabilities(memory_limit_bytes=profile().memory_limit_bytes + 1)
            )

    def test_runtime_digest_mismatch_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimePolicyError, "runtime_digest_mismatch"):
            validate_sandbox_capabilities(profile(), capabilities(runtime_image_digest="d" * 64))


class PathSafetyTests(unittest.TestCase):
    def test_normalized_relative_path_is_accepted(self) -> None:
        self.assertEqual(str(validate_relative_path("work/output/report.json")), "work/output/report.json")

    def test_absolute_path_is_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            validate_relative_path("/etc/passwd")

    def test_parent_traversal_is_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            validate_relative_path("work/../../etc/passwd")

    def test_dot_and_repeated_separator_are_rejected(self) -> None:
        for value in ("work/./file", "work//file"):
            with self.subTest(value=value), self.assertRaises(RuntimePolicyError):
                validate_relative_path(value)

    def test_windows_path_is_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            validate_relative_path("C:\\Windows\\System32")

    def test_symlink_component_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            outside = root.parent / (root.name + "-outside")
            outside.mkdir()
            try:
                (root / "escape").symlink_to(outside, target_is_directory=True)
                with self.assertRaisesRegex(RuntimePolicyError, "symlink_component_blocked"):
                    assert_no_symlink_components(root, "escape/secret.txt")
            finally:
                outside.rmdir()

    def test_plain_descendant_is_resolved_beneath_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            resolved = assert_no_symlink_components(temp, "workspace/output.txt")
            self.assertTrue(resolved.is_relative_to(Path(temp).resolve()))


class EnvironmentAndOutputTests(unittest.TestCase):
    def test_only_minimal_environment_allowlist_is_returned(self) -> None:
        self.assertEqual(
            build_minimal_environment({"LANG": "C.UTF-8", "TZ": "UTC"}),
            {"LANG": "C.UTF-8", "TZ": "UTC"},
        )

    def test_path_and_secret_variables_are_not_allowlisted(self) -> None:
        for name in ("PATH", "HOME", "GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY", "HTTP_PROXY"):
            with self.subTest(name=name), self.assertRaises(RuntimePolicyError):
                build_minimal_environment({name: "must-not-pass"})

    def test_output_larger_than_budget_is_rejected(self) -> None:
        with self.assertRaises(RuntimePolicyError):
            bounded_output(b"12345", maximum_bytes=4)

    def test_output_within_budget_is_returned(self) -> None:
        self.assertEqual(bounded_output(b"ok", maximum_bytes=2), b"ok")


class LaunchPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.trust = TaskTrustAttestation(True, True, True)

    def test_valid_task_builds_non_executing_launch_plan(self) -> None:
        plan = build_launch_plan(
            manifest=manifest(),
            profile=profile(),
            capabilities=capabilities(),
            trust=self.trust,
        )
        self.assertEqual(plan.commit_sha, COMMIT)
        self.assertFalse(plan.network_enabled)
        self.assertFalse(plan.secrets_enabled)
        self.assertFalse(plan.writable_checkout)
        self.assertEqual(plan.uid, 10001)

    def test_untrusted_pr_task_is_rejected(self) -> None:
        trust = TaskTrustAttestation(False, True, True)
        with self.assertRaisesRegex(RuntimePolicyError, "task_trust_attestation_incomplete"):
            build_launch_plan(manifest=manifest(), profile=profile(), capabilities=capabilities(), trust=trust)

    def test_missing_owner_confirmation_is_rejected(self) -> None:
        trust = TaskTrustAttestation(True, False, True)
        with self.assertRaises(RuntimePolicyError):
            build_launch_plan(manifest=manifest(), profile=profile(), capabilities=capabilities(), trust=trust)

    def test_non_main_source_ref_is_rejected(self) -> None:
        invalid = manifest()
        invalid["repository"]["ref"] = "refs/heads/feature/untrusted"
        from infra.control_plane.manifest import derive_idempotency_key
        invalid["idempotency_key"] = derive_idempotency_key(
            provider=invalid["repository"]["provider"],
            repository=invalid["repository"]["full_name"],
            commit_sha=invalid["repository"]["commit_sha"],
            task_definition_id=invalid["task_definition"]["id"],
            task_definition_version=invalid["task_definition"]["version"],
            inputs_digest=invalid["inputs_digest"],
        )
        with self.assertRaisesRegex(RuntimePolicyError, "unreviewed_source_ref_blocked"):
            build_launch_plan(manifest=invalid, profile=profile(), capabilities=capabilities(), trust=self.trust)


if __name__ == "__main__":
    unittest.main()
