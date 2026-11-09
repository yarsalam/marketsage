#!/usr/bin/env python3
"""Validate MarketSage strategy/work/evidence records without third-party dependencies."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
VALID_STATUSES = {
    "PROPOSED", "READY", "IN_PROGRESS", "VALIDATION", "ACCEPTED",
    "BLOCKED", "REWORK", "REJECTED", "STOPPED", "ARCHIVED",
}
PROJECT_DECISIONS = {"CONTINUE", "PIVOT", "HOLD", "STOP", "ARCHIVE"}
REQUIRED_TASK_FIELDS = {
    "id", "title", "track", "owner", "status", "timebox_hours",
    "objective", "user_problem", "deliverables", "acceptance_criteria",
    "stop_conditions", "depends_on", "evidence_refs", "requires_user_flow_proof",
}
REQUIRED_RECORDS = {
    "work": "docs/governance/WORK_REGISTER.json",
    "policy": "docs/governance/DECISION_POLICY.json",
    "gates": "docs/governance/RELEASE_GATES.json",
    "evidence": "docs/governance/EVIDENCE_LEDGER.json",
    "state": "docs/governance/PROJECT_STATE.json",
}


def _load(root: Path, key: str) -> dict[str, Any]:
    path = root / REQUIRED_RECORDS[key]
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{key} record must be a JSON object")
    return value


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    for key in REQUIRED_RECORDS:
        try:
            records[key] = _load(root, key)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{key}: cannot load valid JSON ({type(exc).__name__})")
    if errors:
        return errors

    work = records["work"]
    policy = records["policy"]
    evidence = records["evidence"]
    state = records["state"]
    gates = records["gates"]

    if set(work.get("allowed_statuses", [])) != VALID_STATUSES:
        errors.append("work: allowed_statuses does not match the lifecycle vocabulary")
    if set(policy.get("project_decisions", [])) != PROJECT_DECISIONS:
        errors.append("policy: project_decisions does not match the decision vocabulary")
    if state.get("project_decision") not in PROJECT_DECISIONS:
        errors.append("state: project_decision is invalid")
    if state.get("product_release_status") not in {"NOT_READY", "READY_FOR_REVIEW", "RELEASED", "BLOCKED"}:
        errors.append("state: product_release_status is invalid")
    if state.get("first_user_value_flow") not in {"NOT_YET_PROVEN", "PROVEN"}:
        errors.append("state: first_user_value_flow is invalid")

    tasks = work.get("items")
    if not isinstance(tasks, list) or not tasks:
        errors.append("work: items must be a non-empty array")
        tasks = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"work: item[{index}] must be an object")
            continue
        missing = REQUIRED_TASK_FIELDS - set(task)
        if missing:
            errors.append(f"work: item[{index}] missing fields {','.join(sorted(missing))}")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id.strip():
            errors.append(f"work: item[{index}] has invalid id")
            continue
        if task_id in by_id:
            errors.append(f"work: duplicate task id {task_id}")
        by_id[task_id] = task
        if task.get("status") not in VALID_STATUSES:
            errors.append(f"work: {task_id} has invalid status")
        if not isinstance(task.get("timebox_hours"), (int, float)) or task["timebox_hours"] <= 0:
            errors.append(f"work: {task_id} must have a positive timebox")
        for field in ("deliverables", "acceptance_criteria", "stop_conditions", "depends_on", "evidence_refs"):
            if not isinstance(task.get(field), list):
                errors.append(f"work: {task_id}.{field} must be an array")
            elif field in {"deliverables", "acceptance_criteria", "stop_conditions"} and not task[field]:
                errors.append(f"work: {task_id}.{field} must not be empty")
        for field in ("objective", "user_problem", "owner", "track", "title"):
            if not isinstance(task.get(field), str) or not task[field].strip():
                errors.append(f"work: {task_id}.{field} must be non-empty text")
        if not isinstance(task.get("requires_user_flow_proof"), bool):
            errors.append(f"work: {task_id}.requires_user_flow_proof must be boolean")

    for task_id, task in by_id.items():
        for dependency in task.get("depends_on", []):
            if dependency not in by_id:
                errors.append(f"work: {task_id} references unknown dependency {dependency}")

    # Dependency-cycle check (DFS).
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            errors.append(f"work: dependency cycle includes {node}")
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in by_id.get(node, {}).get("depends_on", []):
            if dep in by_id:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for task_id in by_id:
        visit(task_id)

    evidence_items = evidence.get("evidence")
    if not isinstance(evidence_items, list):
        errors.append("evidence: evidence must be an array")
        evidence_items = []
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for entry in evidence_items:
        if not isinstance(entry, dict) or not entry.get("id"):
            errors.append("evidence: every evidence entry needs an id")
            continue
        if entry["id"] in evidence_by_id:
            errors.append(f"evidence: duplicate evidence id {entry['id']}")
        evidence_by_id[entry["id"]] = entry
        if entry.get("outcome") not in {"PASS", "FAIL", "PENDING", "LIMITED"}:
            errors.append(f"evidence: {entry['id']} has invalid outcome")
        if not entry.get("commit") or not entry.get("reference") or not entry.get("limitations"):
            errors.append(f"evidence: {entry['id']} must include commit, reference and limitations")

    for task_id, task in by_id.items():
        for evidence_id in task.get("evidence_refs", []):
            entry = evidence_by_id.get(evidence_id)
            if entry is None:
                errors.append(f"work: {task_id} references missing evidence {evidence_id}")
            elif entry.get("task_id") != task_id:
                errors.append(f"evidence: {evidence_id} is linked to the wrong task")
        if task.get("status") == "ACCEPTED":
            linked = [evidence_by_id.get(ref) for ref in task.get("evidence_refs", [])]
            linked = [item for item in linked if item]
            if task.get("requires_user_flow_proof") and not any(
                item.get("type") == "USER_FLOW" and item.get("outcome") == "PASS"
                for item in linked
            ):
                errors.append(f"work: {task_id} cannot be ACCEPTED without passing USER_FLOW evidence")
            elif not task.get("requires_user_flow_proof") and not any(
                item.get("outcome") == "PASS" for item in linked
            ):
                errors.append(f"work: {task_id} cannot be ACCEPTED without passing evidence")

    gate_items = gates.get("gates")
    if not isinstance(gate_items, list) or not gate_items:
        errors.append("gates: gates must be a non-empty array")
    else:
        gate_ids = [item.get("id") for item in gate_items if isinstance(item, dict)]
        if len(gate_ids) != len(set(gate_ids)):
            errors.append("gates: duplicate gate ids")

    if state.get("investment_outputs") != "DISABLED_BY_POLICY":
        errors.append("state: investment_outputs must remain DISABLED_BY_POLICY")
    if state.get("source_approval") != "NONE":
        errors.append("state: source_approval must remain NONE until evidence is recorded")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: project operating-system records are structurally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
