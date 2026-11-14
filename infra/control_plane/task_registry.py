"""Deterministic dependency-aware task registry and safe ready-task selector.

The registry is metadata and a scheduler decision function only. It does not
dispatch processes, call providers, write GitHub, or authorize spending/merges.
"""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Sequence


_TASK_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TaskState(str, Enum):
    BLOCKED = "blocked"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    REJECTED = "rejected"


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    definition_id: str
    definition_version: int
    objective: str
    owner: str
    input_digest: str
    dependencies: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    expected_artifacts: tuple[str, ...]
    timeout_seconds: int
    max_attempts: int
    status: TaskState = TaskState.READY
    attempt: int = 0
    priority: int = 100
    cost_ceiling_minor_units: int = 0
    network_policy: str = "none"
    secrets_access: str = "none"
    merge_allowed: bool = False
    deploy_allowed: bool = False
    investment_actions_allowed: bool = False


class TaskRegistryError(ValueError):
    """Sanitized registry validation error containing identifiers/rule names only."""


def validate_registry(records: Sequence[TaskRecord]) -> tuple[TaskRecord, ...]:
    """Validate unique IDs, complete dependencies, hard safety policy and DAG order."""
    by_id: dict[str, TaskRecord] = {}
    for record in records:
        if not _TASK_ID.fullmatch(record.task_id):
            raise TaskRegistryError("task_id: invalid")
        if not _TASK_ID.fullmatch(record.definition_id):
            raise TaskRegistryError(f"{record.task_id}: definition_id_invalid")
        if record.task_id in by_id:
            raise TaskRegistryError(f"{record.task_id}: duplicate_task_id")
        if record.definition_version < 1:
            raise TaskRegistryError(f"{record.task_id}: definition_version_invalid")
        if not record.objective.strip() or not record.owner.strip():
            raise TaskRegistryError(f"{record.task_id}: objective_or_owner_missing")
        if not _SHA256.fullmatch(record.input_digest):
            raise TaskRegistryError(f"{record.task_id}: input_digest_invalid")
        if len(set(record.dependencies)) != len(record.dependencies):
            raise TaskRegistryError(f"{record.task_id}: duplicate_dependency")
        if record.task_id in record.dependencies:
            raise TaskRegistryError(f"{record.task_id}: self_dependency")
        if not record.acceptance_criteria or any(not item.strip() for item in record.acceptance_criteria):
            raise TaskRegistryError(f"{record.task_id}: acceptance_criteria_missing")
        if not record.expected_artifacts or any(not item.strip() for item in record.expected_artifacts):
            raise TaskRegistryError(f"{record.task_id}: expected_artifacts_missing")
        if not 1 <= record.timeout_seconds <= 3600:
            raise TaskRegistryError(f"{record.task_id}: timeout_out_of_bounds")
        if not isinstance(record.status, TaskState):
            raise TaskRegistryError(f"{record.task_id}: status_invalid")
        if not 1 <= record.max_attempts <= 3:
            raise TaskRegistryError(f"{record.task_id}: retry_budget_out_of_bounds")
        if not 0 <= record.attempt <= record.max_attempts:
            raise TaskRegistryError(f"{record.task_id}: attempt_out_of_bounds")
        if record.priority < 0:
            raise TaskRegistryError(f"{record.task_id}: priority_invalid")
        if record.cost_ceiling_minor_units != 0:
            raise TaskRegistryError(f"{record.task_id}: nonzero_cost_not_allowed")
        if record.network_policy != "none":
            raise TaskRegistryError(f"{record.task_id}: network_not_allowed")
        if record.secrets_access != "none":
            raise TaskRegistryError(f"{record.task_id}: secrets_not_allowed")
        if record.merge_allowed or record.deploy_allowed or record.investment_actions_allowed:
            raise TaskRegistryError(f"{record.task_id}: privileged_action_not_allowed")
        by_id[record.task_id] = record

    for record in records:
        for dependency in record.dependencies:
            if dependency not in by_id:
                raise TaskRegistryError(f"{record.task_id}: dependency_missing")

    return topological_order(tuple(by_id.values()))


def topological_order(records: Sequence[TaskRecord]) -> tuple[TaskRecord, ...]:
    """Return deterministic dependency order, raising when the graph contains a cycle."""
    by_id = {record.task_id: record for record in records}
    indegree = {task_id: 0 for task_id in by_id}
    dependents: dict[str, list[str]] = {task_id: [] for task_id in by_id}
    for record in records:
        for dependency in record.dependencies:
            if dependency not in by_id:
                raise TaskRegistryError(f"{record.task_id}: dependency_missing")
            indegree[record.task_id] += 1
            dependents[dependency].append(record.task_id)

    ready = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    ordered: list[TaskRecord] = []
    while ready:
        task_id = ready.popleft()
        ordered.append(by_id[task_id])
        for child in sorted(dependents[task_id]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if len(ordered) != len(records):
        raise TaskRegistryError("dependency_graph: cycle_detected")
    return tuple(ordered)


def select_ready_tasks(
    records: Sequence[TaskRecord],
    *,
    max_parallel: int,
    active_count: int = 0,
) -> tuple[TaskRecord, ...]:
    """Select only explicitly READY tasks whose dependencies are DONE.

    Selection is deterministic by (priority, task_id). This function reserves no
    leases and performs no dispatch; a durable coordinator must claim tasks before
    any worker is started.
    """
    ordered = validate_registry(records)
    if max_parallel < 1 or active_count < 0:
        raise ValueError("parallelism bounds are invalid")
    slots = max(0, max_parallel - active_count)
    if slots == 0:
        return ()
    by_id = {record.task_id: record for record in ordered}
    candidates = [
        record for record in ordered
        if record.status == TaskState.READY
        and all(by_id[dependency].status == TaskState.DONE for dependency in record.dependencies)
    ]
    candidates.sort(key=lambda record: (record.priority, record.task_id))
    return tuple(candidates[:slots])


def transition(record: TaskRecord, new_status: TaskState) -> TaskRecord:
    """Apply a bounded task-state transition without mutating the original record."""
    allowed = {
        TaskState.BLOCKED: {TaskState.READY, TaskState.REJECTED},
        TaskState.READY: {TaskState.RUNNING, TaskState.BLOCKED, TaskState.REJECTED},
        TaskState.RUNNING: {TaskState.DONE, TaskState.READY, TaskState.BLOCKED, TaskState.REJECTED},
        TaskState.DONE: set(),
        TaskState.REJECTED: set(),
    }
    if new_status not in allowed[record.status]:
        raise TaskRegistryError(f"{record.task_id}: invalid_state_transition")
    attempt = record.attempt
    if new_status == TaskState.RUNNING:
        if attempt >= record.max_attempts:
            raise TaskRegistryError(f"{record.task_id}: retry_budget_exhausted")
        attempt += 1
    return replace(record, status=new_status, attempt=attempt)
