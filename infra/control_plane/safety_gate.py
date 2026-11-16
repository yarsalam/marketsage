"""Fail-closed artifact/run preflight primitives (stdlib only).

This module is deliberately local-only: it performs no network requests, provider
calls, workflow dispatch, or data acquisition. JSONL ledgers are append-only.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

_SHA = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
_WORK = re.compile(r"^[A-Z0-9][A-Z0-9._-]{7,127}$")


class SafetyGateError(RuntimeError):
    """Sanitized fail-closed error."""


class RecoveryRequired(SafetyGateError):
    """A known artifact exists but its storage location cannot be resolved."""


class DuplicateAcquisition(SafetyGateError):
    """An equivalent acquisition is already recorded; reuse it."""


class DuplicateRun(SafetyGateError):
    """The exact code/input/parameter/environment run already exists."""


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: str | Path, *, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        raise SafetyGateError("canonical_ledger_missing")
    records: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SafetyGateError(f"ledger_invalid_jsonl_line:{line_number}") from exc
            if not isinstance(item, dict):
                raise SafetyGateError(f"ledger_record_not_object:{line_number}")
            records.append(item)
    return records


def append_jsonl(path: str | Path, record: Mapping[str, Any]) -> None:
    """Append one fsync'd record under an OS file lock; never replace the ledger."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n").encode()
    descriptor = os.open(target, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "ab", closefd=False) as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _read_locked_ledger(stream: Any) -> list[dict[str, Any]]:
    stream.seek(0)
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(stream, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SafetyGateError(f"ledger_invalid_jsonl_line:{line_number}") from exc
        if not isinstance(record, dict):
            raise SafetyGateError(f"ledger_record_not_object:{line_number}")
        records.append(record)
    return records


def _append_locked(stream: Any, record: Mapping[str, Any]) -> None:
    stream.seek(0, os.SEEK_END)
    stream.write(json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def reserve_run(
    ledger_path: str | Path, *, run_id: str, work_id: str, action: str,
    run_fingerprint: str, code_sha: str, input_hashes: Mapping[str, str],
    parameters: Mapping[str, Any], environment: Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically reserve a run; every prior fingerprint, including failures, blocks retry."""
    if not run_id or not _WORK.fullmatch(work_id) or not _GIT_SHA.fullmatch(code_sha):
        raise SafetyGateError("run_reservation_identity_invalid")
    if not _SHA.fullmatch(run_fingerprint) or any(not _SHA.fullmatch(v) for v in input_hashes.values()):
        raise SafetyGateError("run_reservation_hash_invalid")
    target = Path(ledger_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            records = _read_locked_ledger(stream)
            if any(item.get("run_fingerprint") == run_fingerprint for item in records):
                raise DuplicateRun("identical_run_already_reserved_or_recorded_no_retry")
            if any(item.get("run_id") == run_id for item in records):
                raise SafetyGateError("run_id_already_used")
            reservation = {
                "event_id": str(uuid.uuid4()),
                "event_type": "RESERVED",
                "run_id": run_id,
                "work_id": work_id,
                "action": action,
                "run_fingerprint": run_fingerprint,
                "code_sha": code_sha,
                "input_hashes": dict(sorted(input_hashes.items())),
                "parameters": dict(parameters),
                "environment": dict(environment),
                "started_at_utc": _utc_now(),
                "recorded_at_utc": _utc_now(),
                "status": "RUNNING",
                "exit_code": None,
                "result_artifact_ids": [],
                "reason": None,
            }
            _append_locked(stream, reservation)
            return reservation
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def finalize_run(
    ledger_path: str | Path, *, run_id: str, status: str,
    exit_code: int | None, result_artifact_ids: Iterable[str] = (),
    reason: str | None = None,
) -> dict[str, Any]:
    """Append one terminal event for a previously reserved run; never edits history."""
    if status not in {"SUCCESS", "FAILED", "BLOCKED", "REJECTED"}:
        raise SafetyGateError("run_terminal_status_invalid")
    target = Path(ledger_path)
    if not target.is_file():
        raise SafetyGateError("run_reservation_missing")
    with target.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            records = _read_locked_ledger(stream)
            reservations = [item for item in records if item.get("run_id") == run_id and item.get("event_type") == "RESERVED"]
            terminals = [item for item in records if item.get("run_id") == run_id and item.get("event_type") == "FINALIZED"]
            if len(reservations) != 1:
                raise SafetyGateError("run_reservation_missing_or_ambiguous")
            if terminals:
                raise SafetyGateError("run_already_finalized")
            reservation = reservations[0]
            terminal = {
                "event_id": str(uuid.uuid4()),
                "event_type": "FINALIZED",
                "run_id": run_id,
                "run_fingerprint": reservation["run_fingerprint"],
                "recorded_at_utc": _utc_now(),
                "status": status,
                "exit_code": exit_code,
                "result_artifact_ids": sorted(set(result_artifact_ids)),
                "reason": reason,
            }
            _append_locked(stream, terminal)
            return terminal
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def verify_immutable_artifact(record: Mapping[str, Any]) -> tuple[str, int]:
    """Re-hash one registered immutable artifact immediately before use."""
    if record.get("immutable") is not True or record.get("status") != "VERIFIED":
        raise SafetyGateError("immutable_artifact_not_verified")
    path = record.get("storage_path")
    if not isinstance(path, str) or not path:
        raise RecoveryRequired("immutable_artifact_path_unresolved")
    target = Path(path)
    absolute = Path(os.path.abspath(target))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise SafetyGateError("immutable_artifact_symlink_path")
    try:
        actual_hash, actual_size = file_sha256(target)
    except OSError as exc:
        raise RecoveryRequired("immutable_artifact_unavailable_for_recovery") from exc
    if actual_hash != record.get("sha256"):
        raise SafetyGateError("immutable_artifact_hash_mismatch")
    expected_size = record.get("size_bytes")
    if expected_size is not None and actual_size != expected_size:
        raise SafetyGateError("immutable_artifact_size_mismatch")
    return actual_hash, actual_size


def validate_artifact_registry(records: Iterable[Mapping[str, Any]]) -> None:
    ids: set[str] = set()
    hashes: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    for record in records:
        artifact_id = str(record.get("artifact_id", ""))
        if not artifact_id or artifact_id in ids:
            raise SafetyGateError("artifact_id_missing_or_duplicate")
        ids.add(artifact_id)
        digest = record.get("sha256")
        if digest is not None:
            if not isinstance(digest, str) or not _SHA.fullmatch(digest):
                raise SafetyGateError("artifact_sha256_invalid")
            previous = hashes.get(digest)
            if previous and previous != artifact_id:
                raise SafetyGateError("duplicate_artifact_hash")
            hashes[digest] = artifact_id
        fingerprint = record.get("request_fingerprint")
        if fingerprint:
            if fingerprint in fingerprints and fingerprints[fingerprint] != artifact_id:
                raise SafetyGateError("duplicate_request_fingerprint")
            fingerprints[fingerprint] = artifact_id


def find_existing_acquisition(
    records: Iterable[Mapping[str, Any]], *, artifact_identity: str, request_fingerprint: str
) -> Mapping[str, Any] | None:
    matches = [
        item for item in records
        if item.get("artifact_identity") == artifact_identity
        or (request_fingerprint and item.get("request_fingerprint") == request_fingerprint)
    ]
    if len(matches) > 1:
        raise SafetyGateError("ambiguous_existing_artifact_records")
    if not matches:
        return None
    found = matches[0]
    if found.get("status") in {"PATH_UNRESOLVED", "RECOVERY_REQUIRED"} or not found.get("storage_path"):
        raise RecoveryRequired("known_artifact_path_unresolved_search_archives_before_acquisition")
    raise DuplicateAcquisition("equivalent_artifact_exists_reuse_without_download")


def derive_run_fingerprint(
    *, code_sha: str, input_hashes: Mapping[str, str], parameters: Mapping[str, Any],
    environment: Mapping[str, Any],
) -> str:
    if not _GIT_SHA.fullmatch(code_sha):
        raise SafetyGateError("code_sha_invalid")
    if any(not _SHA.fullmatch(value) for value in input_hashes.values()):
        raise SafetyGateError("input_sha256_invalid")
    return canonical_digest({
        "code_sha": code_sha,
        "input_hashes": dict(sorted(input_hashes.items())),
        "parameters": parameters,
        "environment": environment,
    })


def reject_duplicate_run(records: Iterable[Mapping[str, Any]], fingerprint: str) -> None:
    matches = [item for item in records if item.get("run_fingerprint") == fingerprint]
    if matches:
        raise DuplicateRun("identical_run_already_recorded_no_automatic_retry")


def preflight(
    *, policy_path: str | Path, work_item_path: str | Path,
    artifact_registry_path: str | Path, run_ledger_path: str | Path,
    work_id: str, action: str, code_sha: str,
    input_artifacts: Mapping[str, str], parameters: Mapping[str, Any],
    environment: Mapping[str, Any], output_path: str | Path,
    request_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Validate authorization, scope, artifact hashes, idempotency and output safety."""
    if not _WORK.fullmatch(work_id):
        raise SafetyGateError("work_id_invalid")
    try:
        policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
        work = json.loads(Path(work_item_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SafetyGateError("canonical_policy_or_work_item_unavailable") from exc
    if (
        policy.get("schema_version") != 1
        or policy.get("project") != "MarketSage"
        or policy.get("scope_lock") not in {"INFRA_ONLY", "OPEN"}
        or not isinstance(policy.get("research_locked"), bool)
        or not isinstance(policy.get("allowed_actions"), list)
    ):
        raise SafetyGateError("execution_policy_invalid_or_incomplete")
    if action not in policy["allowed_actions"]:
        raise SafetyGateError("action_not_authorized_by_execution_policy")
    if policy.get("scope_lock") == "INFRA_ONLY" and action not in {"infrastructure", "governance", "synthetic_test"}:
        raise SafetyGateError("project_scope_locked")
    if policy.get("research_locked", True) and action in {"research", "acquisition", "analysis", "backtest"}:
        raise SafetyGateError("research_scope_locked")
    if work.get("work_id") != work_id or work.get("status") not in {"AUTHORIZED", "IN_PROGRESS"}:
        raise SafetyGateError("work_item_not_authorized")
    if action not in work.get("allowed_actions", []):
        raise SafetyGateError("action_not_authorized_for_work_item")
    if action != "infrastructure" and work_id not in policy.get("authorized_work_ids", []):
        raise SafetyGateError("owner_authorization_missing")

    artifacts = read_jsonl(artifact_registry_path)
    validate_artifact_registry(artifacts)
    verified: dict[str, str] = {}
    for artifact_id, expected_hash in input_artifacts.items():
        record = next((item for item in artifacts if item.get("artifact_id") == artifact_id), None)
        if record is None or record.get("status") != "VERIFIED":
            raise SafetyGateError("input_artifact_not_verified")
        path = record.get("storage_path")
        if not path:
            raise RecoveryRequired("input_artifact_path_unresolved")
        actual_hash, actual_size = verify_immutable_artifact(record)
        if actual_hash != expected_hash:
            raise SafetyGateError("input_artifact_hash_mismatch")
        verified[artifact_id] = actual_hash

    if request_fingerprint:
        existing = find_existing_acquisition(
            artifacts,
            artifact_identity=str(parameters.get("artifact_identity", "")),
            request_fingerprint=request_fingerprint,
        )
        if existing is not None:
            raise DuplicateAcquisition("request_already_satisfied")

    fingerprint = derive_run_fingerprint(
        code_sha=code_sha, input_hashes=verified, parameters=parameters, environment=environment
    )
    reject_duplicate_run(read_jsonl(run_ledger_path), fingerprint)

    destination = Path(output_path).resolve()
    if destination.exists():
        raise SafetyGateError("output_path_already_exists")
    for record in artifacts:
        if record.get("immutable") and record.get("storage_path"):
            protected = Path(record["storage_path"]).resolve()
            if destination == protected or protected in destination.parents or destination in protected.parents:
                raise SafetyGateError("output_path_overlaps_immutable_artifact")
    return {"work_id": work_id, "run_fingerprint": fingerprint,
            "verified_input_hashes": verified, "output_path": str(destination),
            "preflight": "PASS_NO_SIDE_EFFECTS"}
