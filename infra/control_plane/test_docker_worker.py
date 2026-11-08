from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from infra.control_plane.dispatch_outbox import DispatchState, SQLiteDispatchOutbox
from infra.control_plane.docker_worker import (
    CoordinatedDockerWorker,
    SandboxExecutionResult,
)
from infra.control_plane.lifecycle import RunState
from infra.control_plane.manifest import derive_idempotency_key
from infra.control_plane.orchestrator import DurableOrchestrator
from infra.control_plane.providers import DeterministicFakeAdapter, SafeFailoverRouter
from infra.control_plane.sqlite_coordinator import SQLiteCoordinator
from infra.control_plane.worker_runtime import (
    RuntimeProfile,
    SandboxCapabilities,
    TaskTrustAttestation,
)


class FakeSandboxExecutor:
    def __init__(self, result: SandboxExecutionResult) -> None:
        self.result = result
        self.calls = 0

    def attest(self, profile: RuntimeProfile) -> SandboxCapabilities:
        return SandboxCapabilities(
            runtime_image_digest=profile.image_digest,
            read_only_root=True,
            read_only_checkout=True,
            no_network=True,
            no_new_privileges=True,
            non_root_user=True,
            capabilities_dropped=True,
            seccomp_enforced=True,
            user_namespace=True,
            mount_namespace=True,
            pid_namespace=True,
            no_host_pid=True,
            no_host_network=True,
            no_host_mounts=True,
            isolated_tmp=True,
            memory_limit_bytes=profile.memory_limit_bytes,
            cpu_quota_millis=profile.cpu_quota_millis,
            wall_timeout_seconds=profile.wall_timeout_seconds,
            pids_limit=profile.pids_limit,
            tmpfs_limit_bytes=profile.tmpfs_limit_bytes,
            output_limit_bytes=profile.output_limit_bytes,
        )

    def execute(self, **kwargs) -> SandboxExecutionResult:
        self.calls += 1
        return self.result


class CoordinatedDockerWorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = Path(self.temp.name) / "worker.sqlite3"
        self.coordinator = SQLiteCoordinator(database)
        self.outbox = SQLiteDispatchOutbox(database)
        adapter = DeterministicFakeAdapter("dispatch-backend")
        self.orchestrator = DurableOrchestrator(
            coordinator=self.coordinator,
            outbox=self.outbox,
            router=SafeFailoverRouter([adapter]),
        )
        requested = datetime.now(timezone.utc).replace(microsecond=0)
        repository = {
            "provider": "github",
            "full_name": "yarsalam/marketsage",
            "ref": "refs/heads/main",
            "commit_sha": "b" * 40,
        }
        definition = {"id": "infra.sandbox.smoke", "version": 1}
        digest = "a" * 64
        self.manifest = {
            "schema_version": 1,
            "task_id": "7d7e0e1c-9df4-4c87-b20b-4f57d4a3d4b7",
            "idempotency_key": derive_idempotency_key(
                provider=repository["provider"],
                repository=repository["full_name"],
                commit_sha=repository["commit_sha"],
                task_definition_id=definition["id"],
                task_definition_version=definition["version"],
                inputs_digest=digest,
            ),
            "inputs_digest": digest,
            "queue": "infra",
            "repository": repository,
            "task_definition": definition,
            "requested_at": requested.isoformat(),
            "deadline": (requested + timedelta(minutes=30)).isoformat(),
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
        self.profile = RuntimeProfile(
            runtime_id="python312-slim",
            image_digest="c" * 64,
            platform="linux",
            architecture="x86_64",
            uid=65532,
            memory_limit_bytes=64 * 1024 * 1024,
            cpu_quota_millis=500,
            wall_timeout_seconds=30,
            pids_limit=64,
            tmpfs_limit_bytes=8 * 1024 * 1024,
            output_limit_bytes=1024 * 1024,
        )
        self.trust = TaskTrustAttestation(
            reviewed_on_default_branch=True,
            owner_confirmed=True,
            commit_sha_verified=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _worker(self, executor: FakeSandboxExecutor) -> CoordinatedDockerWorker:
        return CoordinatedDockerWorker(
            coordinator=self.coordinator,
            outbox=self.outbox,
            executor=executor,  # deterministic test double; real executor is DockerSandboxExecutor
            worker_id="worker-test-01",
            lease_seconds=6,
        )

    def test_orchestrator_dispatch_then_worker_claims_and_publishes_result(self) -> None:
        submitted = self.orchestrator.submit(self.manifest)
        self.assertEqual(submitted.task.state, "submitted")
        executor = FakeSandboxExecutor(
            SandboxExecutionResult(
                status="completed",
                exit_code=0,
                timed_out=False,
                output_limit_exceeded=False,
                output_bytes=17,
                output_sha256="d" * 64,
            )
        )
        worker = self._worker(executor)
        result = self.orchestrator.execute_with_worker(
            worker=worker,
            manifest=self.manifest,
            profile=self.profile,
            trust=self.trust,
            workspace=self.temp.name,
            command_id="infra.sandbox.smoke",
        )
        self.assertTrue(result.claimed)
        self.assertTrue(result.published)
        self.assertEqual(result.task_state, "succeeded")
        self.assertEqual(executor.calls, 1)
        self.assertEqual(self.outbox.get(self.manifest["idempotency_key"]).state, DispatchState.SUCCEEDED)
        self.assertIn('"output_sha256":"dddddddd', self.coordinator.get(self.manifest["task_id"]).result)

    def test_failed_worker_is_terminal_and_does_not_unlock_failover(self) -> None:
        self.orchestrator.submit(self.manifest)
        executor = FakeSandboxExecutor(
            SandboxExecutionResult(
                status="completed",
                exit_code=3,
                timed_out=False,
                output_limit_exceeded=False,
                output_bytes=5,
                output_sha256="e" * 64,
            )
        )
        result = self._worker(executor).run_submitted_task(
            manifest=self.manifest,
            profile=self.profile,
            trust=self.trust,
            workspace=self.temp.name,
            command_id="infra.sandbox.smoke",
        )
        self.assertTrue(result.published)
        self.assertEqual(result.task_state, "failed")
        dispatch = self.outbox.get(self.manifest["idempotency_key"])
        self.assertEqual(dispatch.state, DispatchState.FAILED)
        self.assertFalse(dispatch.no_side_effects)
        self.assertIsNone(self.outbox.begin_attempt(
            idempotency_key=self.manifest["idempotency_key"],
            provider_id="second-backend",
        ))

    def test_worker_refuses_unsubmitted_task_without_invoking_executor(self) -> None:
        task_id, key, digest = (
            self.manifest["task_id"],
            self.manifest["idempotency_key"],
            self.manifest["inputs_digest"],
        )
        self.coordinator.enqueue(task_id=task_id, idempotency_key=key, input_digest=digest)
        executor = FakeSandboxExecutor(
            SandboxExecutionResult("completed", 0, False, False, 0, "f" * 64)
        )
        result = self._worker(executor).run_submitted_task(
            manifest=self.manifest,
            profile=self.profile,
            trust=self.trust,
            workspace=self.temp.name,
            command_id="infra.sandbox.smoke",
        )
        self.assertFalse(result.claimed)
        self.assertEqual(result.reason_code, "task_not_submitted")
        self.assertEqual(executor.calls, 0)


if __name__ == "__main__":
    unittest.main()
