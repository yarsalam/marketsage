"""Unattended, persistent polling daemon for the MarketSage sandbox worker."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional

from .dispatch_outbox import SQLiteDispatchOutbox
from .docker_worker import CoordinatedDockerWorker, DockerSandboxExecutor
from .orchestrator import DurableOrchestrator
from .sqlite_coordinator import SQLiteCoordinator
from .watchdog import CoordinatorWatchdog
from .worker_runtime import RuntimeProfile, RuntimePolicyError, TaskTrustAttestation


TrustResolver = Callable[[Mapping[str, object]], TaskTrustAttestation]


@dataclass(frozen=True)
class WorkerDaemonReport:
    inspected: int
    executed: int
    succeeded: int
    failed: int
    skipped: int
    recovered_expired_leases: int
    reason_codes: tuple[str, ...]

    def sanitized_dict(self) -> dict[str, object]:
        return {
            "inspected": self.inspected,
            "executed": self.executed,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "recovered_expired_leases": self.recovered_expired_leases,
            "reason_codes": list(sorted(set(self.reason_codes))),
        }


def verify_local_main_checkout(
    manifest: Mapping[str, object],
    *,
    workspace: str | Path,
    owner_confirmed: bool,
) -> TaskTrustAttestation:
    """Require a clean local main checkout whose HEAD exactly matches the manifest."""
    repository = manifest.get("repository")
    if not isinstance(repository, Mapping):
        return TaskTrustAttestation(False, owner_confirmed, False)
    expected_sha = repository.get("commit_sha")
    expected_ref = repository.get("ref")
    root = Path(workspace)
    try:
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=root, check=True, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root, check=True, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root, check=True, capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return TaskTrustAttestation(False, owner_confirmed, False)
    reviewed = branch == "main" and expected_ref in {"refs/heads/main", "main"} and not dirty
    verified = isinstance(expected_sha, str) and head == expected_sha
    return TaskTrustAttestation(
        reviewed_on_default_branch=reviewed,
        owner_confirmed=owner_confirmed,
        commit_sha_verified=verified,
    )


class DurableWorkerDaemon:
    """Poll persisted manifests and execute only reviewed, allowlisted tasks."""

    def __init__(
        self,
        *,
        coordinator: SQLiteCoordinator,
        outbox: SQLiteDispatchOutbox,
        worker: CoordinatedDockerWorker,
        executor: DockerSandboxExecutor,
        workspace: str | Path,
        profile: RuntimeProfile,
        owner_confirmed: bool,
        worker_id: str,
        trust_resolver: TrustResolver = verify_local_main_checkout,
        max_tasks_per_poll: int = 1,
    ) -> None:
        if not worker_id or len(worker_id) > 96:
            raise ValueError("worker_id is invalid")
        if not 1 <= max_tasks_per_poll <= 10:
            raise ValueError("max_tasks_per_poll must be between 1 and 10")
        self.coordinator = coordinator
        self.outbox = outbox
        self.worker = worker
        self.executor = executor
        self.workspace = str(Path(workspace).resolve())
        self.profile = profile
        self.owner_confirmed = owner_confirmed
        self.worker_id = worker_id
        self.trust_resolver = trust_resolver
        self.max_tasks_per_poll = max_tasks_per_poll
        # Router is intentionally absent: the daemon executes only already
        # submitted tasks and can never initiate or retry provider dispatch.
        self.orchestrator = DurableOrchestrator(
            coordinator=coordinator,
            outbox=outbox,
            router=None,
            owner=worker_id,
            lease_seconds=worker.lease_seconds,
        )
        self.watchdog = CoordinatorWatchdog(
            coordinator,
            worker_id=(worker_id + "-watchdog")[:128],
        )

    @classmethod
    def from_docker_image(
        cls,
        *,
        coordinator: SQLiteCoordinator,
        outbox: SQLiteDispatchOutbox,
        image_id: str,
        workspace: str | Path,
        owner_confirmed: bool,
        worker_id: str,
        memory_limit_bytes: int = 128 * 1024 * 1024,
        cpu_quota_millis: int = 500,
        wall_timeout_seconds: int = 300,
        pids_limit: int = 64,
        tmpfs_limit_bytes: int = 16 * 1024 * 1024,
        output_limit_bytes: int = 4 * 1024 * 1024,
        lease_seconds: int = 60,
    ) -> "DurableWorkerDaemon":
        import re

        if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
            raise ValueError("worker image ID must be immutable")
        architecture = platform.machine()
        if architecture not in {"x86_64", "aarch64"}:
            raise ValueError("worker architecture is unsupported")
        profile = RuntimeProfile(
            runtime_id="marketsage-digest-pinned-worker",
            image_digest=image_id.removeprefix("sha256:"),
            platform="linux",
            architecture=architecture,
            uid=65532,
            memory_limit_bytes=memory_limit_bytes,
            cpu_quota_millis=cpu_quota_millis,
            wall_timeout_seconds=wall_timeout_seconds,
            pids_limit=pids_limit,
            tmpfs_limit_bytes=tmpfs_limit_bytes,
            output_limit_bytes=output_limit_bytes,
        )
        executor = DockerSandboxExecutor(image_id=image_id)
        worker = CoordinatedDockerWorker(
            coordinator=coordinator,
            outbox=outbox,
            executor=executor,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
        )
        return cls(
            coordinator=coordinator,
            outbox=outbox,
            worker=worker,
            executor=executor,
            workspace=workspace,
            profile=profile,
            owner_confirmed=owner_confirmed,
            worker_id=worker_id,
        )

    def run_once(self) -> WorkerDaemonReport:
        recovered = self.coordinator.recover_expired()
        self.coordinator.record_worker_heartbeat(
            worker_id=self.worker_id,
            status="idle",
        )
        inspected = executed = succeeded = failed = skipped = 0
        reasons: list[str] = []

        candidates = sorted(
            (
                task for task in self.coordinator.list_tasks(limit=5000)
                if task.state in {"submitted", "recoverable"}
                and task.provider_id is not None
                and task.external_run_id is not None
            ),
            key=lambda task: (task.created_at, task.task_id),
        )
        for task in candidates[: self.max_tasks_per_poll]:
            inspected += 1
            try:
                manifest = self.coordinator.get_manifest(task.task_id)
            except KeyError:
                skipped += 1
                reasons.append("persisted_manifest_missing")
                continue

            definition = manifest.get("task_definition")
            command_id = definition.get("id") if isinstance(definition, Mapping) else None
            if not isinstance(command_id, str) or command_id not in self.executor.TASK_COMMANDS:
                skipped += 1
                reasons.append("task_definition_not_allowlisted")
                continue

            trust = self.trust_resolver(
                manifest,
                workspace=self.workspace,
                owner_confirmed=self.owner_confirmed,
            )
            if not (
                trust.reviewed_on_default_branch
                and trust.owner_confirmed
                and trust.commit_sha_verified
            ):
                skipped += 1
                reasons.append("task_trust_attestation_incomplete")
                continue

            try:
                result = self.orchestrator.execute_with_worker(
                    worker=self.worker,
                    manifest=manifest,
                    profile=self.profile,
                    trust=trust,
                    workspace=self.workspace,
                    command_id=command_id,
                )
            except RuntimePolicyError:
                skipped += 1
                reasons.append("worker_runtime_policy_rejected")
                continue
            except (OSError, ValueError):
                skipped += 1
                reasons.append("worker_request_rejected")
                continue

            if not result.claimed:
                skipped += 1
                if result.reason_code:
                    reasons.append(result.reason_code)
                continue
            executed += 1
            if result.published and result.task_state == "succeeded":
                succeeded += 1
            else:
                failed += 1
                reasons.append(result.reason_code or "worker_result_not_published")

        # Keep the watchdog process alive and publish its own heartbeat. It does
        # not send new tasks and cannot override the provider Outbox retry gate.
        self.watchdog.run_once()
        return WorkerDaemonReport(
            inspected=inspected,
            executed=executed,
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            recovered_expired_leases=recovered,
            reason_codes=tuple(sorted(set(reasons))),
        )

    def run_forever(self, *, poll_interval_seconds: int = 10) -> None:
        if not 2 <= poll_interval_seconds <= 300:
            raise ValueError("poll interval must be between 2 and 300 seconds")
        while True:
            report = self.run_once()
            print(json.dumps(report.sanitized_dict(), sort_keys=True), flush=True)
            time.sleep(poll_interval_seconds)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="MarketSage unattended Docker worker daemon")
    parser.add_argument("--database", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--worker-id", default="marketsage-docker-worker")
    parser.add_argument("--owner-confirmed", action="store_true")
    parser.add_argument("--poll-interval-seconds", type=int, default=10)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)

    coordinator = SQLiteCoordinator(args.database)
    outbox = SQLiteDispatchOutbox(args.database)
    daemon = DurableWorkerDaemon.from_docker_image(
        coordinator=coordinator,
        outbox=outbox,
        image_id=args.image_id,
        workspace=args.workspace,
        owner_confirmed=args.owner_confirmed,
        worker_id=args.worker_id,
    )
    if args.once:
        print(json.dumps(daemon.run_once().sanitized_dict(), sort_keys=True))
        return 0
    daemon.run_forever(poll_interval_seconds=args.poll_interval_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
