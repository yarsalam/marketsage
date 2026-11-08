"""Docker-backed worker with fail-closed container isolation and fenced result publication.

Only immutable image IDs and reviewed, allowlisted task handlers are executable.
The Docker daemon is treated as part of the trusted computing base; deployments
must enable user-namespace remapping and the built-in seccomp profile.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from .lifecycle import RunState
from .providers import ProviderReceipt
from .sqlite_coordinator import SQLiteCoordinator
from .worker_runtime import (
    LaunchPlan,
    RuntimePolicyError,
    RuntimeProfile,
    SandboxCapabilities,
    TaskTrustAttestation,
    build_launch_plan,
    validate_sandbox_capabilities,
)

_IMAGE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class SandboxExecutionResult:
    status: str
    exit_code: Optional[int]
    timed_out: bool
    output_limit_exceeded: bool
    output_bytes: int
    output_sha256: str
    failure_code: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return (
            self.status == "completed"
            and self.exit_code == 0
            and not self.timed_out
            and not self.output_limit_exceeded
        )


@dataclass(frozen=True)
class WorkerRunResult:
    claimed: bool
    published: bool
    task_state: str
    execution: Optional[SandboxExecutionResult]
    reason_code: Optional[str] = None


class DockerSandboxExecutor:
    """Execute fixed task handlers in a digest-pinned, restricted Docker container."""

    TASK_COMMANDS: Mapping[str, tuple[str, ...]] = {
        "infra.sandbox.smoke": (
            "python",
            "-c",
            "\n".join((
                "import errno, os",
                "from pathlib import Path",
                "status = {}",
                "for line in Path('/proc/self/status').read_text().splitlines():",
                "    if ':' in line:",
                "        key, value = line.split(':', 1)",
                "        status[key] = value.strip()",
                "if os.getuid() != 65532: raise SystemExit('SMOKE:uid')",
                "if status.get('NoNewPrivs') != '1': raise SystemExit('SMOKE:no_new_privileges')",
                "if int(status.get('CapEff', '1'), 16) != 0: raise SystemExit('SMOKE:capabilities')",
                "probe = Path('/workspace/.marketsage-write-probe')",
                "try:",
                "    probe.write_text('must-not-write')",
                "except OSError as exc:",
                "    if exc.errno not in (errno.EACCES, errno.EPERM, errno.EROFS):",
                "        raise SystemExit('SMOKE:checkout_probe_error')",
                "else:",
                "    raise SystemExit('SMOKE:checkout_writable')",
                "try:",
                "    Path('/tmp/worker-smoke').write_text('isolated')",
                "except OSError:",
                "    raise SystemExit('SMOKE:tmp_not_writable')",
                "print('marketsage-worker-smoke-ok')",
            )),
        )
    }

    def __init__(self, *, image_id: str, docker_binary: str = "docker") -> None:
        if not _IMAGE_ID.fullmatch(image_id):
            raise ValueError("worker image must be an immutable local sha256 image ID")
        self.image_id = image_id
        self.docker_binary = docker_binary
        self._host_userns_enabled: Optional[bool] = None
        self._seccomp_enabled: Optional[bool] = None

    def _run(self, args: list[str], *, timeout: int = 20) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                [self.docker_binary, *args],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"},
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
            raise RuntimePolicyError("docker_control_plane_unavailable") from exc

    def _verify_image(self) -> None:
        result = self._run(["image", "inspect", "--format", "{{.Id}}", self.image_id])
        if result.stdout.strip() != self.image_id:
            raise RuntimePolicyError("worker_image_digest_mismatch")

    def _docker_security_options(self) -> tuple[bool, bool]:
        result = self._run(["info", "--format", "{{json .SecurityOptions}}"])
        try:
            values = json.loads(result.stdout)
        except (TypeError, ValueError) as exc:
            raise RuntimePolicyError("docker_security_attestation_unavailable") from exc
        options = " ".join(str(item).lower() for item in values)
        seccomp = "seccomp" in options and "unconfined" not in options
        userns = "userns" in options
        self._seccomp_enabled = seccomp
        self._host_userns_enabled = userns
        return seccomp, userns

    def attest(self, profile: RuntimeProfile) -> SandboxCapabilities:
        """Inspect daemon-level prerequisites; execute() verifies each container."""
        profile.validate()
        self._verify_image()
        seccomp, userns = self._docker_security_options()
        if not seccomp or not userns:
            raise RuntimePolicyError("docker_requires_seccomp_and_userns_remap")
        return SandboxCapabilities(
            runtime_image_digest=profile.image_digest,
            read_only_root=True,
            read_only_checkout=True,
            no_network=True,
            no_new_privileges=True,
            non_root_user=True,
            capabilities_dropped=True,
            seccomp_enforced=seccomp,
            user_namespace=userns,
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

    @staticmethod
    def _verify_container_config(
        details: dict[str, object],
        *,
        plan: LaunchPlan,
        workspace: Path,
        output_dir: Path,
    ) -> None:
        config = details.get("Config")
        host = details.get("HostConfig")
        mounts = details.get("Mounts")
        if not isinstance(config, dict) or not isinstance(host, dict) or not isinstance(mounts, list):
            raise RuntimePolicyError("container_inspection_invalid")
        if config.get("User") != f"{plan.uid}:{plan.uid}":
            raise RuntimePolicyError("container_user_mismatch")
        if host.get("NetworkMode") != "none" or not host.get("ReadonlyRootfs"):
            raise RuntimePolicyError("container_network_or_rootfs_policy_mismatch")
        if "ALL" not in [str(item).upper() for item in host.get("CapDrop", [])]:
            raise RuntimePolicyError("container_capability_drop_missing")
        security = " ".join(str(item).lower() for item in host.get("SecurityOpt", []))
        if "no-new-privileges" not in security or "unconfined" in security:
            raise RuntimePolicyError("container_security_options_mismatch")
        if host.get("PidMode") == "host" or host.get("IpcMode") == "host":
            raise RuntimePolicyError("container_host_namespace_blocked")
        if host.get("Privileged"):
            raise RuntimePolicyError("privileged_container_blocked")
        if int(host.get("Memory") or 0) != plan.memory_limit_bytes:
            raise RuntimePolicyError("container_memory_limit_mismatch")
        if int(host.get("NanoCpus") or 0) > plan.cpu_quota_millis * 1_000_000:
            raise RuntimePolicyError("container_cpu_limit_mismatch")
        if int(host.get("PidsLimit") or 0) != plan.pids_limit:
            raise RuntimePolicyError("container_pids_limit_mismatch")
        tmpfs = host.get("Tmpfs") or {}
        if "/tmp" not in tmpfs or f"size={plan.tmpfs_limit_bytes}" not in str(tmpfs["/tmp"]):
            raise RuntimePolicyError("container_tmpfs_limit_mismatch")

        by_destination = {str(item.get("Destination")): item for item in mounts if isinstance(item, dict)}
        required_mounts = {"/workspace", "/out"}
        unexpected_mounts = set(by_destination) - required_mounts - {"/dev/shm"}
        if not required_mounts.issubset(by_destination) or unexpected_mounts:
            destinations = ",".join(sorted(by_destination))
            raise RuntimePolicyError("container_mount_set_mismatch:" + destinations)
        checkout = by_destination["/workspace"]
        output = by_destination["/out"]
        shared_memory = by_destination.get("/dev/shm")
        if (
            Path(str(checkout.get("Source"))).resolve() != workspace
            or bool(checkout.get("RW"))
            or Path(str(output.get("Source"))).resolve() != output_dir
            or not bool(output.get("RW"))
            or (
                shared_memory is not None
                and str(shared_memory.get("Type")) != "tmpfs"
            )
        ):
            raise RuntimePolicyError("container_mount_policy_mismatch")

        limits = host.get("Ulimits") or []
        fsize = next((item for item in limits if item.get("Name") == "fsize"), None)
        if fsize is None or int(fsize.get("Hard") or 0) > plan.output_limit_bytes:
            raise RuntimePolicyError("container_output_ulimit_missing")

    @staticmethod
    def _directory_size(root: Path, *, maximum: int) -> tuple[int, bool]:
        total = 0
        for base, dirs, files in os.walk(root, followlinks=False):
            base_path = Path(base)
            for name in dirs:
                if (base_path / name).is_symlink():
                    return total, True
            for name in files:
                path = base_path / name
                if path.is_symlink() or not path.is_file():
                    return total, True
                total += path.stat().st_size
                if total > maximum:
                    return total, True
        return total, False

    @staticmethod
    def _hash_outputs(stdout_path: Path, stderr_path: Path, output_dir: Path, maximum: int) -> tuple[str, int, bool]:
        digest = hashlib.sha256()
        total = 0
        overflow = False
        for path in (stdout_path, stderr_path):
            size = path.stat().st_size
            total += size
            if total > maximum:
                return digest.hexdigest(), total, True
            digest.update(path.name.encode("utf-8") + b"\\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(64 * 1024), b""):
                    digest.update(chunk)
        size, unsafe = DockerSandboxExecutor._directory_size(output_dir, maximum=maximum - total)
        total += size
        if unsafe or total > maximum:
            return digest.hexdigest(), total, True
        for path in sorted(item for item in output_dir.rglob("*") if item.is_file()):
            digest.update(path.relative_to(output_dir).as_posix().encode("utf-8") + b"\\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(64 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest(), total, False

    def execute(
        self,
        *,
        plan: LaunchPlan,
        profile: RuntimeProfile,
        workspace: str | Path,
        command_id: str,
        abort_event: Optional[threading.Event] = None,
    ) -> SandboxExecutionResult:
        if command_id not in self.TASK_COMMANDS:
            raise RuntimePolicyError("task_handler_not_allowlisted")
        if plan.runtime_image_digest != profile.image_digest or self.image_id != f"sha256:{profile.image_digest}":
            raise RuntimePolicyError("runtime_plan_image_mismatch")
        if plan.network_enabled or plan.secrets_enabled or plan.writable_checkout:
            raise RuntimePolicyError("unsafe_launch_plan")
        validate_sandbox_capabilities(profile, self.attest(profile))

        root = Path(workspace)
        if root.is_symlink():
            raise RuntimePolicyError("workspace_root_is_symlink")
        try:
            workspace_path = root.resolve(strict=True)
        except OSError as exc:
            raise RuntimePolicyError("workspace_unavailable") from exc
        if not workspace_path.is_dir():
            raise RuntimePolicyError("workspace_not_directory")

        with tempfile.TemporaryDirectory(prefix="marketsage-worker-") as temp_name:
            temp_root = Path(temp_name)
            output_dir = temp_root / "out"
            output_dir.mkdir(mode=0o700)
            os.chmod(output_dir, 0o777)
            stdout_path = temp_root / "stdout.bin"
            stderr_path = temp_root / "stderr.bin"
            container_name = "marketsage-worker-" + uuid.uuid4().hex
            quota = f"{profile.cpu_quota_millis / 1000:.3f}"
            argv = [
                "create", "--name", container_name,
                "--network", "none", "--read-only",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges:true",
                "--pids-limit", str(profile.pids_limit),
                "--memory", str(profile.memory_limit_bytes),
                "--cpus", quota,
                "--user", f"{profile.uid}:{profile.uid}",
                "--tmpfs", f"/tmp:rw,noexec,nosuid,nodev,size={profile.tmpfs_limit_bytes}",
                "--mount", f"type=bind,source={workspace_path},target=/workspace,readonly",
                "--mount", f"type=bind,source={output_dir},target=/out",
                "--workdir", "/workspace",
                "--ulimit", f"fsize={profile.output_limit_bytes}:{profile.output_limit_bytes}",
                "--ulimit", "core=0",
                "--env", "LANG=C.UTF-8",
                "--env", "TZ=UTC",
                "--env", "PYTHONHASHSEED=0",
                "--env", "PYTHONDONTWRITEBYTECODE=1",
                "--env", "PYTHONUNBUFFERED=1",
                self.image_id,
                *self.TASK_COMMANDS[command_id],
            ]
            created = self._run(argv, timeout=30)
            container_id = created.stdout.strip()
            if not container_id:
                raise RuntimePolicyError("container_create_returned_no_id")
            timed_out = False
            exceeded = False
            status = "completed"
            failure_code: Optional[str] = None
            exit_code: Optional[int] = None
            try:
                inspect = self._run(["inspect", container_id], timeout=20)
                try:
                    details = json.loads(inspect.stdout)[0]
                except (TypeError, ValueError, IndexError) as exc:
                    raise RuntimePolicyError("container_inspection_invalid") from exc
                self._verify_container_config(
                    details,
                    plan=plan,
                    workspace=workspace_path,
                    output_dir=output_dir.resolve(),
                )

                with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
                    process = subprocess.Popen(
                        [self.docker_binary, "start", "--attach", container_id],
                        stdout=stdout_file,
                        stderr=stderr_file,
                        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"},
                    )
                    deadline = time.monotonic() + plan.wall_timeout_seconds
                    while process.poll() is None:
                        if abort_event is not None and abort_event.is_set():
                            status = "lease_lost"
                            self._run(["kill", container_id], timeout=10)
                            break
                        if time.monotonic() >= deadline:
                            timed_out = True
                            status = "timed_out"
                            self._run(["kill", container_id], timeout=10)
                            break
                        stdout_size = stdout_path.stat().st_size
                        stderr_size = stderr_path.stat().st_size
                        output_size, unsafe = self._directory_size(
                            output_dir, maximum=plan.output_limit_bytes
                        )
                        if (
                            stdout_size + stderr_size + output_size > plan.output_limit_bytes
                            or unsafe
                        ):
                            exceeded = True
                            status = "output_limit_exceeded"
                            self._run(["kill", container_id], timeout=10)
                            break
                        time.sleep(0.05)
                    try:
                        exit_code = process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                        status = "docker_client_terminated"
                    if exit_code != 0 and command_id == "infra.sandbox.smoke":
                        diagnostic = stderr_path.read_text(
                            encoding="utf-8", errors="replace"
                        )[:4096]
                        match = re.search(r"SMOKE:([a-z0-9_]+)", diagnostic)
                        if match:
                            failure_code = "sandbox_" + match.group(1)
                        elif "SyntaxError" in diagnostic:
                            failure_code = "sandbox_python_syntax"
                        elif "AssertionError" in diagnostic:
                            failure_code = "sandbox_assertion"
                        else:
                            failure_code = "sandbox_smoke_nonzero_exit"
            finally:
                try:
                    self._run(["rm", "--force", container_id], timeout=10)
                except RuntimePolicyError:
                    pass

            digest, total, unsafe = self._hash_outputs(
                stdout_path, stderr_path, output_dir, plan.output_limit_bytes
            )
            if unsafe:
                exceeded = True
                status = "output_limit_exceeded"
            return SandboxExecutionResult(
                status=status,
                exit_code=exit_code,
                timed_out=timed_out,
                output_limit_exceeded=exceeded,
                output_bytes=total,
                output_sha256=digest,
                failure_code=failure_code,
            )


class CoordinatedDockerWorker:
    """Claim a submitted task, renew its lease, run the sandbox, and publish once."""

    def __init__(
        self,
        *,
        coordinator: SQLiteCoordinator,
        outbox: object,
        executor: DockerSandboxExecutor,
        worker_id: str,
        lease_seconds: int = 60,
    ) -> None:
        if not worker_id or lease_seconds < 3:
            raise ValueError("worker_id and lease_seconds >= 3 are required")
        self.coordinator = coordinator
        self.outbox = outbox
        self.executor = executor
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds

    def run_submitted_task(
        self,
        *,
        manifest: Mapping[str, object],
        profile: RuntimeProfile,
        trust: TaskTrustAttestation,
        workspace: str | Path,
        command_id: str,
        no_side_effects_on_failure: bool = False,
    ) -> WorkerRunResult:
        from .manifest import validate_manifest

        validate_manifest(manifest)
        task_id = str(manifest["task_id"])
        key = str(manifest["idempotency_key"])
        task = self.coordinator.get(task_id)
        if (
            task.idempotency_key != key
            or task.input_digest != str(manifest["inputs_digest"])
            or task.provider_id is None
            or task.external_run_id is None
            or task.state not in {"submitted", "recoverable"}
        ):
            return WorkerRunResult(False, False, task.state, None, "task_not_submitted")

        capabilities = self.executor.attest(profile)
        plan = build_launch_plan(
            manifest=manifest,
            profile=profile,
            capabilities=capabilities,
            trust=trust,
        )
        lease = self.coordinator.claim(
            task_id=task_id,
            owner=self.worker_id,
            lease_seconds=self.lease_seconds,
        )
        if lease is None:
            current = self.coordinator.get(task_id)
            return WorkerRunResult(False, False, current.state, None, "worker_claim_unavailable")

        self.coordinator.record_worker_heartbeat(
            worker_id=self.worker_id,
            task_id=task_id,
            status="starting",
        )
        stop = threading.Event()
        lease_lost = threading.Event()

        def renew() -> None:
            interval = max(1.0, self.lease_seconds / 3)
            while not stop.wait(interval):
                if not self.coordinator.renew_lease(
                    lease=lease, lease_seconds=self.lease_seconds
                ):
                    self.coordinator.record_worker_heartbeat(
                        worker_id=self.worker_id,
                        task_id=task_id,
                        status="failed",
                        failure_code="lease_lost",
                    )
                    lease_lost.set()
                    return
                self.coordinator.record_worker_heartbeat(
                    worker_id=self.worker_id,
                    task_id=task_id,
                    status="healthy",
                )

        heartbeat = threading.Thread(target=renew, name=f"heartbeat-{self.worker_id}", daemon=True)
        heartbeat.start()
        runtime_reason: Optional[str] = None
        try:
            result = self.executor.execute(
                plan=plan,
                profile=profile,
                workspace=workspace,
                command_id=command_id,
                abort_event=lease_lost,
            )
        except RuntimePolicyError as exc:
            runtime_reason = str(exc)
            result = SandboxExecutionResult(
                "runtime_rejected", None, False, False, 0, hashlib.sha256(b"").hexdigest()
            )
        finally:
            stop.set()
            heartbeat.join(timeout=5)

        if lease_lost.is_set():
            current = self.coordinator.get(task_id)
            return WorkerRunResult(True, False, current.state, result, "worker_lease_lost")

        receipt_state = RunState.SUCCEEDED if result.succeeded else RunState.FAILED
        heartbeat_failure = (
            None if result.succeeded else (
                "worker_timeout" if result.timed_out
                else ("output_limit_exceeded" if result.output_limit_exceeded else
                      ("runtime_rejected" if result.status == "runtime_rejected" else
                       "worker_process_failed"))
            )
        )
        self.coordinator.record_worker_heartbeat(
            worker_id=self.worker_id,
            task_id=task_id,
            status="idle" if result.succeeded else "failed",
            failure_code=heartbeat_failure,
        )
        receipt = ProviderReceipt(
            provider_id=task.provider_id,
            external_run_id=task.external_run_id,
            idempotency_key=task.idempotency_key,
            input_digest=task.input_digest,
            state=receipt_state,
        )
        self.outbox.mark_terminal(
            receipt=receipt,
            no_side_effects_on_failure=(
                receipt_state == RunState.FAILED and no_side_effects_on_failure
            ),
        )
        summary = json.dumps(
            {
                "status": result.status,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "output_limit_exceeded": result.output_limit_exceeded,
                "output_bytes": result.output_bytes,
                "output_sha256": result.output_sha256,
                "failure_code": result.failure_code,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        if result.succeeded:
            published = self.coordinator.publish_result(lease=lease, result=summary)
        else:
            failure_class = (
                "worker_timeout" if result.timed_out
                else ("worker_runtime_failure" if result.status == "runtime_rejected" else "code_failure")
            )
            published = self.coordinator.mark_failed(
                lease=lease,
                failure_class=failure_class,
            )
        current = self.coordinator.get(task_id)
        return WorkerRunResult(
            claimed=True,
            published=published,
            task_state=current.state,
            execution=result,
            reason_code=(
                runtime_reason if runtime_reason is not None
                else (
                    result.failure_code if result.failure_code is not None
                    else (None if published else "coordinator_rejected_stale_result")
                )
            ),
        )
