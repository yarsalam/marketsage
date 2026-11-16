"""Synthetic-friendly 3-2-1 backup copy verification and non-overwriting restore helpers.

This module never chooses host paths or claims physical/offline independence.
The operator supplies location/media/failure-domain metadata and attests offline
isolation; hashes and byte-for-byte restores are verified by the code.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping


class BackupSafetyError(RuntimeError):
    """Backup or restore rejected without exposing file contents."""


def sha256_file(path: str | Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _safe_relative(value: str) -> Path:
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or not parsed.parts or any(part in {"", ".", ".."} for part in parsed.parts):
        raise BackupSafetyError("backup_relative_path_invalid")
    if "\\" in value:
        raise BackupSafetyError("backup_relative_path_invalid")
    return Path(*parsed.parts)


def _reject_symlink_components(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise BackupSafetyError("backup_symlink_path_rejected")


def create_backup_copy(
    source: str | Path, *, target_root: str | Path, relative_path: str,
    backup_id: str, artifact_id: str, location_id: str, medium_id: str,
    failure_domain: str, offline_attested: bool,
) -> dict[str, Any]:
    """Create one immutable copy without replacing any existing destination."""
    source_path = Path(source)
    target_base = Path(target_root)
    relative = _safe_relative(relative_path)
    _reject_symlink_components(source_path)
    _reject_symlink_components(target_base)
    if not source_path.is_file() or not target_base.is_dir():
        raise BackupSafetyError("backup_source_or_target_unavailable")
    before_hash, before_size = sha256_file(source_path)
    destination = target_base / backup_id / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(destination)
    try:
        with source_path.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
    except FileExistsError as exc:
        raise BackupSafetyError("backup_destination_exists_no_overwrite") from exc
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    after_hash, after_size = sha256_file(source_path)
    copy_hash, copy_size = sha256_file(destination)
    if (before_hash, before_size) != (after_hash, after_size):
        destination.unlink(missing_ok=True)
        raise BackupSafetyError("source_changed_during_backup")
    if (copy_hash, copy_size) != (before_hash, before_size):
        destination.unlink(missing_ok=True)
        raise BackupSafetyError("backup_copy_hash_mismatch")
    return {
        "backup_id": backup_id,
        "artifact_id": artifact_id,
        "relative_path": relative.as_posix(),
        "sha256": before_hash,
        "size_bytes": before_size,
        "location_id": location_id,
        "medium_id": medium_id,
        "failure_domain": failure_domain,
        "offline_attested": bool(offline_attested),
        "copy_path": str(destination),
        "verified": True,
    }


def validate_321_copies(records: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Validate recorded 3-2-1 topology; offline isolation remains an owner attestation."""
    copies = list(records)
    if any(record.get("verified") is not True for record in copies):
        raise BackupSafetyError("backup_copy_not_verified")
    if len({record.get("location_id") for record in copies}) < 3:
        raise BackupSafetyError("three_independent_locations_required")
    if len({record.get("medium_id") for record in copies}) < 2:
        raise BackupSafetyError("two_independent_media_required")
    if len({record.get("failure_domain") for record in copies}) < 2:
        raise BackupSafetyError("two_failure_domains_required")
    if not any(record.get("offline_attested") is True for record in copies):
        raise BackupSafetyError("offline_copy_attestation_required")
    hashes = {record.get("sha256") for record in copies}
    sizes = {record.get("size_bytes") for record in copies}
    if len(hashes) != 1 or len(sizes) != 1:
        raise BackupSafetyError("backup_copy_identity_mismatch")
    return {
        "copies": len(copies),
        "locations": len({record.get("location_id") for record in copies}),
        "media": len({record.get("medium_id") for record in copies}),
        "failure_domains": len({record.get("failure_domain") for record in copies}),
    }


def verify_backup_copy(record: Mapping[str, Any]) -> tuple[str, int]:
    path = record.get("copy_path")
    if not isinstance(path, str) or not path:
        raise BackupSafetyError("backup_copy_path_missing")
    _reject_symlink_components(Path(path))
    try:
        digest, size = sha256_file(path)
    except OSError as exc:
        raise BackupSafetyError("backup_copy_unavailable") from exc
    if digest != record.get("sha256") or size != record.get("size_bytes"):
        raise BackupSafetyError("backup_copy_integrity_mismatch")
    return digest, size


def restore_backup_copy(record: Mapping[str, Any], destination: str | Path) -> dict[str, Any]:
    """Restore to a new path only; verify the exact hash after copying."""
    verify_backup_copy(record)
    target = Path(destination)
    _reject_symlink_components(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Path(record["copy_path"]).open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
            dst.flush()
            os.fsync(dst.fileno())
    except FileExistsError as exc:
        raise BackupSafetyError("restore_destination_exists_no_overwrite") from exc
    except Exception:
        if target.exists():
            target.unlink()
        raise
    digest, size = sha256_file(target)
    if digest != record["sha256"] or size != record["size_bytes"]:
        target.unlink(missing_ok=True)
        raise BackupSafetyError("restored_file_integrity_mismatch")
    return {"restored_path": str(target), "sha256": digest, "size_bytes": size, "verified": True}
