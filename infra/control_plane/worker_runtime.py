"""Fail-closed policy gate for a portable, least-privilege worker sandbox.

This module deliberately does not execute tasks or claim to provide a sandbox.
It validates an immutable runtime profile and an external sandbox capability
attestation before producing a launch plan. A concrete executor must enforce
these controls at the OS/container boundary and pass independent conformance
tests before it can implement the execution protocol.
"""
from __future__ import annotations

import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Mapping, Optional

from .manifest import ManifestValidationError, validate_manifest

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_ALLOWED_ENV = frozenset({"LANG", "LC_ALL", "TZ", "PYTHONHASHSEED"})
_ALLOWED_ARTIFACTS = frozenset({"sanitized_summary", "test_report"})


class RuntimePolicyError(ValueError):
    """Sanitized worker policy rejection; never echoes supplied values."""


@dataclass(frozen=True)
class RuntimeProfile:
    runtime_id: str
    image_digest: str
    platform: str
    architecture: str
    uid: int
    memory_limit_bytes: int
    cpu_quota_millis: int
    wall_timeout_seconds: int
    pids_limit: int
    tmpfs_limit_bytes: int
    output_limit_bytes: int

    def validate(self) -> None:
        if not self.runtime_id or len(self.runtime_id) > 128:
            raise RuntimePolicyError("runtime_id_invalid")
        if not _SHA256.fullmatch(self.image_digest):
            raise RuntimePolicyError("runtime_digest_invalid")
        if self.platform != "linux" or self.architecture not in {"x86_64", "aarch64"}:
            raise RuntimePolicyError("runtime_platform_unsupported")
        if self.uid <= 0:
            raise RuntimePolicyError("worker_must_be_non_root")
        if not 16 * 1024 * 1024 <= self.memory_limit_bytes <= 8 * 1024 * 1024 * 1024:
            raise RuntimePolicyError("memory_limit_out_of_bounds")
        if not 10 <= self.cpu_quota_millis <= 8000:
            raise RuntimePolicyError("cpu_quota_out_of_bounds")
        if not 1 <= self.wall_timeout_seconds <= 3600:
            raise RuntimePolicyError("wall_timeout_out_of_bounds")
        if not 1 <= self.pids_limit <= 256:
            raise RuntimePolicyError("pids_limit_out_of_bounds")
        if not 1024 * 1024 <= self.tmpfs_limit_bytes <= 2 * 1024 * 1024 * 1024:
            raise RuntimePolicyError("tmpfs_limit_out_of_bounds")
        if not 1024 <= self.output_limit_bytes <= 16 * 1024 * 1024:
            raise RuntimePolicyError("output_limit_out_of_bounds")


@dataclass(frozen=True)
class SandboxCapabilities:
    """Observed/verified controls of a concrete OS-level sandbox implementation."""

    runtime_image_digest: str
    read_only_root: bool
    read_only_checkout: bool
    no_network: bool
    no_new_privileges: bool
    non_root_user: bool
    capabilities_dropped: bool
    seccomp_enforced: bool
    user_namespace: bool
    mount_namespace: bool
    pid_namespace: bool
    no_host_pid: bool
    no_host_network: bool
    no_host_mounts: bool
    isolated_tmp: bool
    memory_limit_bytes: int
    cpu_quota_millis: int
    wall_timeout_seconds: int
    pids_limit: int
    tmpfs_limit_bytes: int
    output_limit_bytes: int


@dataclass(frozen=True)
class TaskTrustAttestation:
    """Explicit owner/controller attestations for a reviewed immutable task commit."""

    reviewed_on_default_branch: bool
    owner_confirmed: bool
    commit_sha_verified: bool


@dataclass(frozen=True)
class LaunchPlan:
    task_id: str
    task_definition_id: str
    commit_sha: str
    runtime_id: str
    runtime_image_digest: str
    uid: int
    memory_limit_bytes: int
    cpu_quota_millis: int
    wall_timeout_seconds: int
    pids_limit: int
    tmpfs_limit_bytes: int
    output_limit_bytes: int
    network_enabled: bool
    secrets_enabled: bool
    writable_checkout: bool
    allowed_artifacts: tuple[str, ...]


def validate_sandbox_capabilities(
    profile: RuntimeProfile,
    capabilities: SandboxCapabilities,
) -> None:
    """Reject executors that cannot prove every mandatory isolation boundary."""
    profile.validate()
    if capabilities.runtime_image_digest != profile.image_digest:
        raise RuntimePolicyError("runtime_digest_mismatch")
    required = {
        "read_only_root": capabilities.read_only_root,
        "read_only_checkout": capabilities.read_only_checkout,
        "no_network": capabilities.no_network,
        "no_new_privileges": capabilities.no_new_privileges,
        "non_root_user": capabilities.non_root_user,
        "capabilities_dropped": capabilities.capabilities_dropped,
        "seccomp_enforced": capabilities.seccomp_enforced,
        "user_namespace": capabilities.user_namespace,
        "mount_namespace": capabilities.mount_namespace,
        "pid_namespace": capabilities.pid_namespace,
        "no_host_pid": capabilities.no_host_pid,
        "no_host_network": capabilities.no_host_network,
        "no_host_mounts": capabilities.no_host_mounts,
        "isolated_tmp": capabilities.isolated_tmp,
    }
    missing = sorted(name for name, enabled in required.items() if not enabled)
    if missing:
        raise RuntimePolicyError("sandbox_control_missing:" + ",".join(missing))

    limits = {
        "memory_limit": (capabilities.memory_limit_bytes, profile.memory_limit_bytes),
        "cpu_quota": (capabilities.cpu_quota_millis, profile.cpu_quota_millis),
        "wall_timeout": (capabilities.wall_timeout_seconds, profile.wall_timeout_seconds),
        "pids_limit": (capabilities.pids_limit, profile.pids_limit),
        "tmpfs_limit": (capabilities.tmpfs_limit_bytes, profile.tmpfs_limit_bytes),
        "output_limit": (capabilities.output_limit_bytes, profile.output_limit_bytes),
    }
    for name, (actual, maximum) in limits.items():
        if actual <= 0 or actual > maximum:
            raise RuntimePolicyError(name + "_not_enforced_within_profile")


def validate_relative_path(value: str) -> PurePosixPath:
    """Accept a normalized relative POSIX path; reject traversal and host paths."""
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise RuntimePolicyError("path_invalid")
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        raise RuntimePolicyError("path_must_be_normalized_relative")
    candidate = PurePosixPath(value)
    if candidate.is_absolute():
        raise RuntimePolicyError("path_must_be_normalized_relative")
    if ":" in candidate.parts[0]:
        raise RuntimePolicyError("path_drive_or_scheme_blocked")
    return candidate


def assert_no_symlink_components(root: str | Path, relative_path: str) -> Path:
    """Reject symlinks in every existing component beneath a trusted root.

    This is a preflight check only; an executor must still use directory file
    descriptors/openat-style no-follow operations to avoid TOCTOU races.
    """
    rel = validate_relative_path(relative_path)
    root_path = Path(root)
    if root_path.is_symlink():
        raise RuntimePolicyError("trusted_root_is_symlink")
    try:
        trusted_root = root_path.resolve(strict=True)
    except OSError as exc:
        raise RuntimePolicyError("trusted_root_unavailable") from exc
    if not trusted_root.is_dir():
        raise RuntimePolicyError("trusted_root_not_directory")

    current = trusted_root
    for index, part in enumerate(rel.parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            break
        except OSError as exc:
            raise RuntimePolicyError("path_component_unavailable") from exc
        if stat.S_ISLNK(mode):
            raise RuntimePolicyError("symlink_component_blocked")
        if index < len(rel.parts) - 1 and not stat.S_ISDIR(mode):
            raise RuntimePolicyError("non_directory_path_component")
    resolved = (trusted_root / Path(*rel.parts)).resolve(strict=False)
    try:
        resolved.relative_to(trusted_root)
    except ValueError as exc:
        raise RuntimePolicyError("path_escape_blocked") from exc
    return resolved


def build_minimal_environment(configured: Mapping[str, str]) -> dict[str, str]:
    """Build a fresh allowlisted environment; never inherit host environment."""
    result: dict[str, str] = {}
    for name, value in configured.items():
        if not isinstance(name, str) or not _ENV_NAME.fullmatch(name):
            raise RuntimePolicyError("environment_name_invalid")
        if name not in _ALLOWED_ENV:
            raise RuntimePolicyError("environment_variable_not_allowlisted")
        if not isinstance(value, str) or len(value) > 256 or "\x00" in value:
            raise RuntimePolicyError("environment_value_invalid")
        result[name] = value
    # PATH, HOME, credentials, cloud metadata, proxy settings and arbitrary
    # inherited variables must come from the fixed executor profile, not the host.
    return result


def bounded_output(value: bytes, *, maximum_bytes: int) -> bytes:
    """Return output only if it is within the declared byte ceiling."""
    if maximum_bytes < 1:
        raise RuntimePolicyError("output_limit_invalid")
    if len(value) > maximum_bytes:
        raise RuntimePolicyError("output_exceeds_limit")
    return value


def build_launch_plan(
    *,
    manifest: Mapping[str, object],
    profile: RuntimeProfile,
    capabilities: SandboxCapabilities,
    trust: TaskTrustAttestation,
) -> LaunchPlan:
    """Validate task, trust and sandbox policies; this function never launches."""
    try:
        validate_manifest(manifest)
    except ManifestValidationError as exc:
        raise RuntimePolicyError("task_manifest_rejected") from exc

    if not (
        trust.reviewed_on_default_branch
        and trust.owner_confirmed
        and trust.commit_sha_verified
    ):
        raise RuntimePolicyError("task_trust_attestation_incomplete")

    validate_sandbox_capabilities(profile, capabilities)
    repository = manifest["repository"]
    task_definition = manifest["task_definition"]
    result_policy = manifest["result_policy"]
    policy = manifest["policy"]

    if not isinstance(repository, Mapping) or not isinstance(task_definition, Mapping):
        raise RuntimePolicyError("task_identity_invalid")
    if not isinstance(result_policy, Mapping) or not isinstance(policy, Mapping):
        raise RuntimePolicyError("task_policy_invalid")
    if repository.get("ref") != "refs/heads/main":
        raise RuntimePolicyError("unreviewed_source_ref_blocked")
    if policy.get("network_policy") != "none" or policy.get("secrets_access") != "none":
        raise RuntimePolicyError("network_or_secret_policy_blocked")
    if policy.get("cost_ceiling_minor_units") != 0:
        raise RuntimePolicyError("nonzero_cost_blocked")
    if policy.get("production_access") or policy.get("merge_allowed") or policy.get("deploy_allowed"):
        raise RuntimePolicyError("privileged_task_blocked")
    if policy.get("investment_actions_allowed") or policy.get("raw_market_data_allowed"):
        raise RuntimePolicyError("investment_or_raw_data_task_blocked")
    artifacts = result_policy.get("allowed_artifacts")
    if not isinstance(artifacts, list) or not set(artifacts).issubset(_ALLOWED_ARTIFACTS):
        raise RuntimePolicyError("artifact_policy_blocked")
    if result_policy.get("raw_logs_allowed") or result_policy.get("secret_values_allowed") or result_policy.get("local_paths_allowed"):
        raise RuntimePolicyError("unsafe_result_policy_blocked")

    return LaunchPlan(
        task_id=str(manifest["task_id"]),
        task_definition_id=str(task_definition["id"]),
        commit_sha=str(repository["commit_sha"]),
        runtime_id=profile.runtime_id,
        runtime_image_digest=profile.image_digest,
        uid=profile.uid,
        memory_limit_bytes=capabilities.memory_limit_bytes,
        cpu_quota_millis=capabilities.cpu_quota_millis,
        wall_timeout_seconds=capabilities.wall_timeout_seconds,
        pids_limit=capabilities.pids_limit,
        tmpfs_limit_bytes=capabilities.tmpfs_limit_bytes,
        output_limit_bytes=capabilities.output_limit_bytes,
        network_enabled=False,
        secrets_enabled=False,
        writable_checkout=False,
        allowed_artifacts=tuple(sorted(artifacts)),
    )
