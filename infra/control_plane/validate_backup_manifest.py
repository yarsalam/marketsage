"""Validate a complete, versioned 3-2-1 backup and restore manifest."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .backup_restore import BackupSafetyError, _reject_symlink_components, sha256_file, verify_backup_copy
from jsonschema import Draft202012Validator, FormatChecker


class BackupManifestError(ValueError):
    """Backup manifest schema or cross-record invariant failed."""


def validate_backup_manifest(
    manifest: Mapping[str, Any], *, schema_path: str | Path,
) -> dict[str, int]:
    try:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupManifestError("backup_manifest_schema_missing_or_invalid") from exc
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(dict(manifest)))
    if errors:
        error = sorted(errors, key=lambda item: (tuple(str(x) for x in item.absolute_path), item.validator or ""))[0]
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        raise BackupManifestError(f"backup_manifest_schema_invalid:{location}:{error.validator or 'schema'}")

    copies = list(manifest["copies"])
    backup_id = manifest["backup_id"]
    artifact_id = manifest["artifact_id"]
    source_hash = manifest["source_sha256"]
    source_size = manifest["source_size_bytes"]
    for record in copies:
        if record["backup_id"] != backup_id or record["artifact_id"] != artifact_id:
            raise BackupManifestError("backup_copy_references_wrong_artifact_or_set")
        if record["sha256"] != source_hash or record["size_bytes"] != source_size:
            raise BackupManifestError("backup_copy_source_identity_mismatch")
        try:
            verify_backup_copy(record)
        except BackupSafetyError as exc:
            raise BackupManifestError("backup_copy_file_integrity_failed") from exc
    locations = {record["location_id"] for record in copies}
    media = {record["medium_id"] for record in copies}
    failure_domains = {record["failure_domain"] for record in copies}
    if len(locations) < 3:
        raise BackupManifestError("three_independent_locations_required")
    if len(media) < 2:
        raise BackupManifestError("two_independent_media_required")
    if len(failure_domains) < 2:
        raise BackupManifestError("two_failure_domains_required")
    if not any(record["offline_attested"] is True for record in copies):
        raise BackupManifestError("offline_copy_attestation_required")
    copy_paths = {record["copy_path"] for record in copies}
    if len(copy_paths) != len(copies):
        raise BackupManifestError("backup_copy_path_reused")

    restores = list(manifest["restore_drills"])
    for restore in restores:
        if restore["source_location_id"] not in locations:
            raise BackupManifestError("restore_source_not_in_backup_set")
        if restore["sha256"] != source_hash or restore["size_bytes"] != source_size:
            raise BackupManifestError("restore_hash_or_size_mismatch")
        if restore["restored_path"] in copy_paths:
            raise BackupManifestError("restore_overwrites_backup_copy")
        try:
            _reject_symlink_components(Path(restore["restored_path"]))
            restored_hash, restored_size = sha256_file(restore["restored_path"])
        except OSError as exc:
            raise BackupManifestError("restore_file_unavailable") from exc
        if restored_hash != source_hash or restored_size != source_size:
            raise BackupManifestError("restore_file_integrity_failed")
    return {
        "copies": len(copies),
        "locations": len(locations),
        "media": len(media),
        "failure_domains": len(failure_domains),
        "restore_drills": len(restores),
    }
