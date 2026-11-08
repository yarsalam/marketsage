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
from infra.control_plane.worker_daemon import DurableWorkerDaemon
from infra.control_plane.worker_runtime import (
    RuntimeProfile,
    SandboxCapabilities,
    TaskTrustAttestation,
)


class FakeExecutor:
    TASK_COMMANDS = {"infra.sandbox.smoke": ("python", "-c", "safe-fixed-smoke")}

    def __init__(self) -> None:
        self.calls = 0
        self.result = SandboxExecutionResult(
            status="completed",
            exit_code=0,
            timed_out=False,
            output_limit_exceeded=False,
            output_bytes=20,
            output_sha256="d" * 64,
        )

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


class DurableWorkerDaemonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        database = Path(self.temp.name) / "daemon.sqlite3"
        self.coordinator = SQLiteCoordinator(database)
        self.outbox = SQLiteDispatchOutbox(database)
        self.adapter = DeterministicFakeAdapter("dispatch-backend")
        self.orchestrator = DurableOrchestrator(
            coordinator=self.coordinator,
            outbox=self.outbox,
            router=SafeFailoverRouter([self.adapter]),
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
            "deadline": (requested + timedelta(minutes=20)).isoformat(),
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
                "max_attempts": 1,
                "retry_on": [],
            },
            "result_policy": {
                "allowed_artifacts": ["sanitized_summary", "test_report"],
                "raw_logs_allowed": False,
                "secret_values_allowed": False,
                "local_paths_allowed": False,
            },
        }
        self.profile = RuntimeProfile(
            runtime_id="worker-daemon-test",
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
        self.trust = TaskTrustAttestation(True, True, True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _daemon(self, *, owner_confirmed: bool = True):
        executor = FakeExecutor()
        worker = CoordinatedDockerWorker(
            coordinator=self.coordinator,
            outbox=self.outbox,
            executor=executor,
            worker_id="daemon-worker",
            lease_seconds=6,
        )
        daemon = DurableWorkerDaemon(
            coordinator=self.coordinator,
            outbox=self.outbox,
            worker=worker,
            executor=executor,
            workspace=self.temp.name,
            profile=self.profile,
            owner_confirmed=owner_confirmed,
            worker_id="daemon",
            trust_resolver=lambda manifest, **kwargs: self.trust,
        )
        return daemon, executor

    def test_daemon_picks_up_persisted_manifest_and_executes_once(self) -> None:
        self.orchestrator.submit(self.manifest)
        self.assertIsNotNone(self.coordinator.get_manifest(self.manifest["task_id"]))
        daemon, executor = self._daemon()
        report = daemon.run_once()
        self.assertEqual(report.inspected, 1)
        self.assertEqual(report.executed, 1)
        self.assertEqual(report.succeeded, 1)
        self.assertEqual(executor.calls, 1)
        self.assertEqual(self.coordinator.get(self.manifest["task_id"]).state, "succeeded")
        self.assertEqual(self.outbox.get(self.manifest["idempotency_key"]).state, DispatchState.SUCCEEDED)

        repeated = daemon.run_once()
        self.assertEqual(repeated.executed, 0)
        self.assertEqual(executor.calls, 1)

    def test_unallowlisted_task_is_skipped_without_claiming_or_execution(self) -> None:
        self.manifest["task_definition"] = {"id": "shell.arbitrary", "version": 1}
        self.manifest["idempotency_key"] = derive_idempotency_key(
            provider="github",
            repository="yarsalam/marketsage",
            commit_sha="b" * 40,
            task_definition_id="shell.arbitrary",
            task_definition_version=1,
            inputs_digest="a" * 64,
        )
        self.orchestrator.submit(self.manifest)
        daemon, executor = self._daemon()
        report = daemon.run_once()
        self.assertEqual(report.skipped, 1)
        self.assertIn("task_definition_not_allowlisted", report.reason_codes)
        self.assertEqual(executor.calls, 0)
        self.assertEqual(self.coordinator.get(self.manifest["task_id"]).state, "submitted")

    def test_unconfirmed_owner_policy_skips_task_without_claiming(self) -> None:
        self.orchestrator.submit(self.manifest)
        executor = FakeExecutor()
        worker = CoordinatedDockerWorker(
            coordinator=self.coordinator,
            outbox=self.outbox,
            executor=executor,
            worker_id="daemon-worker",
            lease_seconds=6,
        )
        daemon = DurableWorkerDaemon(
            coordinator=self.coordinator,
            outbox=self.outbox,
            worker=worker,
            executor=executor,
            workspace=self.temp.name,
            profile=self.profile,
            owner_confirmed=False,
            worker_id="daemon",
            trust_resolver=lambda manifest, **kwargs: TaskTrustAttestation(True, False, True),
        )
        report = daemon.run_once()
        self.assertEqual(report.skipped, 1)
        self.assertIn("task_trust_attestation_incomplete", report.reason_codes)
        self.assertEqual(executor.calls, 0)
        self.assertEqual(self.coordinator.get(self.manifest["task_id"]).state, "submitted")


if __name__ == "__main__":
    unittest.main()
