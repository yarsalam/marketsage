from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker


class ManifestValidationError(ValueError):
    """Validation failure with sanitized paths and rule names only."""

    def __init__(self, issues: list[str]) -> None:
        self.issues = tuple(issues)
        super().__init__("Invalid task manifest: " + "; ".join(issues))


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "schemas" / "infra-task-v1.schema.json"


def load_schema() -> dict[str, Any]:
    with _schema_path().open("r", encoding="utf-8") as stream:
        schema = json.load(stream)
    Draft202012Validator.check_schema(schema)
    return schema


def derive_idempotency_key(
    *,
    provider: str,
    repository: str,
    commit_sha: str,
    task_definition_id: str,
    task_definition_version: int,
    inputs_digest: str,
) -> str:
    """Return a stable key for one exact task definition and immutable input set."""
    identity = {
        "provider": provider,
        "repository": repository,
        "commit_sha": commit_sha,
        "task_definition_id": task_definition_id,
        "task_definition_version": task_definition_version,
        "inputs_digest": inputs_digest,
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    """Validate a manifest against the strict v1 schema and identity invariants.

    Error messages deliberately omit invalid values so secrets or private payloads
    cannot be echoed into logs by a caller.
    """
    if not isinstance(manifest, Mapping):
        raise ManifestValidationError(["$: expected object"])

    validator = Draft202012Validator(load_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(dict(manifest)), key=lambda error: (tuple(str(part) for part in error.absolute_path), error.validator or ""))
    if errors:
        issues: list[str] = []
        for error in errors:
            path = ".".join(str(part) for part in error.absolute_path) or "$"
            issues.append(f"{path}: {error.validator or 'schema'}")
        raise ManifestValidationError(issues)

    try:
        requested_at = datetime.fromisoformat(str(manifest["requested_at"]).replace("Z", "+00:00"))
        deadline = datetime.fromisoformat(str(manifest["deadline"]).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ManifestValidationError(["requested_at/deadline: date-time"]) from exc
    if requested_at.utcoffset() is None or deadline.utcoffset() is None:
        raise ManifestValidationError(["requested_at/deadline: timezone-required"])
    if deadline <= requested_at:
        raise ManifestValidationError(["deadline: must-be-after-requested_at"])

    repository = manifest["repository"]
    task_definition = manifest["task_definition"]
    expected_key = derive_idempotency_key(
        provider=repository["provider"],
        repository=repository["full_name"],
        commit_sha=repository["commit_sha"],
        task_definition_id=task_definition["id"],
        task_definition_version=task_definition["version"],
        inputs_digest=manifest["inputs_digest"],
    )
    if manifest["idempotency_key"] != expected_key:
        raise ManifestValidationError(["idempotency_key: identity-mismatch"])
