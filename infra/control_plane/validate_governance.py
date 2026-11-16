"""Strict, side-effect-free validation for canonical MarketSage governance records."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class GovernanceValidationError(ValueError):
    """Canonical governance records are missing, malformed or contradictory."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceValidationError(f"invalid_or_missing_json:{path.name}") from exc
    if not isinstance(value, dict):
        raise GovernanceValidationError(f"json_record_not_object:{path.name}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise GovernanceValidationError(f"missing_jsonl:{path.name}") from exc
    records: list[dict[str, Any]] = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GovernanceValidationError(f"invalid_jsonl:{path.name}:{number}") from exc
        if not isinstance(record, dict):
            raise GovernanceValidationError(f"jsonl_record_not_object:{path.name}:{number}")
        records.append(record)
    return records


def _validate_schema(instance: dict[str, Any], schema: dict[str, Any], label: str) -> None:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), error.validator or ""),
    )
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "$"
        raise GovernanceValidationError(f"schema_invalid:{label}:{location}:{first.validator or 'schema'}")


def validate_artifact_records(records: list[dict[str, Any]]) -> None:
    ids: set[str] = set()
    identities: set[str] = set()
    hashes: set[str] = set()
    requests: set[str] = set()
    for record in records:
        artifact_id = record["artifact_id"]
        identity = record["artifact_identity"]
        digest = record["sha256"]
        request = record.get("request_fingerprint")
        if artifact_id in ids:
            raise GovernanceValidationError("duplicate_artifact_id")
        if identity in identities:
            raise GovernanceValidationError("duplicate_artifact_identity")
        if digest in hashes:
            raise GovernanceValidationError("duplicate_artifact_sha256")
        if request and request in requests:
            raise GovernanceValidationError("duplicate_acquisition_fingerprint")
        ids.add(artifact_id)
        identities.add(identity)
        hashes.add(digest)
        if request:
            requests.add(request)
        if record["status"] in {"PATH_UNRESOLVED", "RECOVERY_REQUIRED"}:
            if record["storage_path"] is not None:
                raise GovernanceValidationError("unresolved_artifact_has_storage_path")
            if record["backup_restore_status"] == "VERIFIED":
                raise GovernanceValidationError("unresolved_artifact_cannot_have_verified_restore")
        if record["status"] == "VERIFIED" and not record["storage_path"]:
            raise GovernanceValidationError("verified_artifact_missing_storage_path")


def validate_run_records(records: list[dict[str, Any]], policy: dict[str, Any], work: dict[str, Any]) -> None:
    event_ids: set[str] = set()
    fingerprint_owners: dict[str, str] = {}
    runs: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        event_id = record["event_id"]
        run_id = record["run_id"]
        event_type = record["event_type"]
        fingerprint = record["run_fingerprint"]
        if event_id in event_ids:
            raise GovernanceValidationError("duplicate_run_event_id")
        event_ids.add(event_id)
        owner = fingerprint_owners.get(fingerprint)
        if owner is not None and owner != run_id:
            raise GovernanceValidationError("duplicate_run_fingerprint")
        fingerprint_owners[fingerprint] = run_id
        events = runs.setdefault(run_id, {})
        if event_type in events:
            raise GovernanceValidationError("duplicate_run_event_type")
        if event_type == "RESERVED":
            if record["work_id"] != work["work_id"]:
                raise GovernanceValidationError("run_references_unknown_work_item")
            if record["action"] not in work["allowed_actions"] or record["action"] not in policy["allowed_actions"]:
                raise GovernanceValidationError("run_action_not_authorized")
            if policy["research_locked"] and record["action"] in {"research", "acquisition", "analysis", "backtest"}:
                raise GovernanceValidationError("research_run_recorded_while_locked")
        elif event_type == "FINALIZED":
            reservation = events.get("RESERVED")
            if reservation is None:
                raise GovernanceValidationError("run_finalized_without_reservation")
            if reservation["run_fingerprint"] != fingerprint:
                raise GovernanceValidationError("run_finalization_fingerprint_mismatch")
        else:
            raise GovernanceValidationError("unknown_run_event_type")
        events[event_type] = record

    for events in runs.values():
        if "RESERVED" not in events:
            raise GovernanceValidationError("run_reservation_missing")
        reservation = events["RESERVED"]
        final = events.get("FINALIZED")
        if final is not None and final["recorded_at_utc"] < reservation["recorded_at_utc"]:
            raise GovernanceValidationError("run_finalization_precedes_reservation")


def validate_governance(root: Path) -> dict[str, int | str]:
    governance = root / "docs" / "governance"
    schema_path = root / "schemas" / "governance-records-v1.schema.json"
    schema = _read_json(schema_path)
    Draft202012Validator.check_schema(schema)

    policy = _read_json(governance / "execution_policy.json")
    _validate_schema(policy, schema, "execution_policy")
    work_files = sorted((governance / "work_items").glob("*.json"))
    if len(work_files) != 1:
        raise GovernanceValidationError("expected_exactly_one_active_work_item")
    work = _read_json(work_files[0])
    _validate_schema(work, schema, "work_item")

    if work["work_id"] not in policy["authorized_work_ids"]:
        raise GovernanceValidationError("work_item_not_authorized_by_policy")
    if not set(work["allowed_actions"]).issubset(set(policy["allowed_actions"])):
        raise GovernanceValidationError("work_item_actions_exceed_policy")
    if policy["scope_lock"] == "INFRA_ONLY" and not policy["research_locked"]:
        raise GovernanceValidationError("infra_only_requires_research_lock")
    if work["status"] == "AUTHORIZED" and policy["scope_lock"] != "INFRA_ONLY":
        raise GovernanceValidationError("authorized_infra_work_requires_infra_only_scope")

    artifacts = _read_jsonl(governance / "ARTIFACT_REGISTRY.jsonl")
    for record in artifacts:
        _validate_schema(record, schema, "artifact")
    validate_artifact_records(artifacts)

    runs = _read_jsonl(governance / "RUN_LEDGER.jsonl")
    for record in runs:
        _validate_schema(record, schema, "run_event")
    validate_run_records(runs, policy, work)

    return {"artifacts": len(artifacts), "runs": len(runs), "work_id": work["work_id"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        result = validate_governance(args.root.resolve())
    except (GovernanceValidationError, OSError, ValueError) as exc:
        print(f"GOVERNANCE_VALIDATION=FAIL reason={exc}", file=sys.stderr)
        return 1
    print(
        "GOVERNANCE_VALIDATION=PASS "
        f"artifacts={result['artifacts']} runs={result['runs']} work_id={result['work_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
