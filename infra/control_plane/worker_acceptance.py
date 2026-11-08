"""Owner-controlled smoke harness for the concrete Docker worker sandbox.

Run only from an owner-controlled branch/default branch. The worker receives a
fixed allowlisted no-network task; no user payloads, secrets or market data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .dispatch_outbox import SQLiteDispatchOutbox
from .docker_worker import CoordinatedDockerWorker, DockerSandboxExecutor
from .lifecycle import RunState
from .manifest import derive_idempotency_key
from .orchestrator import DurableOrchestrator
from .providers import DeterministicFakeAdapter, SafeFailoverRouter
from .sqlite_coordinator import SQLiteCoordinator
from .worker_runtime import RuntimeProfile, TaskTrustAttestation


def _manifest(commit_sha: str) -> dict[str, object]:
    requested = datetime.now(timezone.utc).replace(microsecond=0)
    repository = {
        "provider": "github",
        "full_name": "yarsalam/marketsage",
        "ref": "refs/heads/main",
        "commit_sha": commit_sha,
    }
    definition = {"id": "infra.sandbox.smoke", "version": 1}
    digest = hashlib.sha256(b"marketsage-fixed-sandbox-smoke-v1").hexdigest()
    task_id = str(uuid.uuid4())
    key = derive_idempotency_key(
        provider=repository["provider"],
        repository=repository["full_name"],
        commit_sha=repository["commit_sha"],
        task_definition_id=definition["id"],
        task_definition_version=definition["version"],
        inputs_digest=digest,
    )
    return {
        "schema_version": 1,
        "task_id": task_id,
        "idempotency_key": key,
        "inputs_digest": digest,
        "queue": "infra",
        "repository": repository,
        "task_definition": definition,
        "requested_at": requested.isoformat(),
        "deadline": (requested + timedelta(minutes=5)).isoformat(),
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--workspace", default=".")
    args = parser.parse_args()

    if platform.machine() not in {"x86_64", "AMD64"}:
        raise SystemExit("worker smoke currently requires linux/amd64")
    if len(args.commit_sha) != 40 or any(c not in "0123456789abcdef" for c in args.commit_sha):
        raise SystemExit("commit SHA must be a full lowercase Git SHA")

    image_digest = args.image_id.removeprefix("sha256:")
    profile = RuntimeProfile(
        runtime_id="marketsage-python312-slim",
        image_digest=image_digest,
        platform="linux",
        architecture="x86_64",
        uid=65532,
        memory_limit_bytes=128 * 1024 * 1024,
        cpu_quota_millis=500,
        wall_timeout_seconds=30,
        pids_limit=64,
        tmpfs_limit_bytes=16 * 1024 * 1024,
        output_limit_bytes=1024 * 1024,
    )
    trust = TaskTrustAttestation(
        reviewed_on_default_branch=True,
        owner_confirmed=True,
        commit_sha_verified=True,
    )

    with tempfile.TemporaryDirectory(prefix="marketsage-worker-acceptance-") as temp:
        database = Path(temp) / "worker.sqlite3"
        coordinator = SQLiteCoordinator(database)
        outbox = SQLiteDispatchOutbox(database)
        router = SafeFailoverRouter([DeterministicFakeAdapter("dispatch-fixture")])
        orchestrator = DurableOrchestrator(
            coordinator=coordinator,
            outbox=outbox,
            router=router,
        )
        manifest = _manifest(args.commit_sha)
        accepted = orchestrator.submit(manifest)
        if not accepted.dispatch.accepted:
            raise SystemExit("fixture dispatch was not accepted")

        executor = DockerSandboxExecutor(image_id=args.image_id)
        worker = CoordinatedDockerWorker(
            coordinator=coordinator,
            outbox=outbox,
            executor=executor,
            worker_id="docker-worker-acceptance",
            lease_seconds=12,
        )
        result = orchestrator.execute_with_worker(
            worker=worker,
            manifest=manifest,
            profile=profile,
            trust=trust,
            workspace=str(Path(args.workspace).resolve()),
            command_id="infra.sandbox.smoke",
        )
        summary = {
            "claimed": result.claimed,
            "published": result.published,
            "task_state": result.task_state,
            "reason_code": result.reason_code,
            "worker_status": result.execution.status if result.execution else None,
            "exit_code": result.execution.exit_code if result.execution else None,
            "timed_out": result.execution.timed_out if result.execution else None,
            "output_limit_exceeded": result.execution.output_limit_exceeded if result.execution else None,
            "output_bytes": result.execution.output_bytes if result.execution else None,
            "output_sha256": result.execution.output_sha256 if result.execution else None,
        }
        print(json.dumps({"worker": summary}, sort_keys=True))
        if not result.claimed or not result.published or result.task_state != "succeeded":
            raise SystemExit("sandbox worker did not publish a successful terminal result")
        if result.execution is None or not result.execution.succeeded:
            raise SystemExit("sandbox worker execution did not meet the smoke contract")
        if outbox.get(str(manifest["idempotency_key"])).state.value != "succeeded":
            raise SystemExit("dispatch outbox did not reach succeeded")

        print(json.dumps({
            "result": "success",
            "task_state": result.task_state,
            "worker_status": result.execution.status,
            "exit_code": result.execution.exit_code,
            "output_bytes": result.execution.output_bytes,
            "output_sha256": result.execution.output_sha256,
            "image_id": args.image_id,
            "network": "none",
            "checkout": "read-only",
            "secrets": "none",
            "uid": profile.uid,
            "cost_minor_units": 0,
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
