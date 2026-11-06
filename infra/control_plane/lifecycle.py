"""Deterministic in-memory provider and coordinator fixtures.

These classes are contract-test fixtures only. They are not durable, distributed,
or suitable for production scheduling.
"""
from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RunState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


TERMINAL_STATES = {RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED}


@dataclass(frozen=True)
class ProviderRun:
    external_run_id: str
    idempotency_key: str
    input_digest: str
    state: RunState


class IdempotencyConflict(ValueError):
    """An idempotency key was reused for different immutable input."""


class FakeProvider:
    """A deterministic provider that can simulate an ambiguous submit response."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runs_by_key: dict[str, ProviderRun] = {}
        self._runs_by_id: dict[str, ProviderRun] = {}

    def submit(
        self, *, idempotency_key: str, input_digest: str, lose_response: bool = False
    ) -> ProviderRun:
        if not idempotency_key or not input_digest:
            raise ValueError("idempotency_key and input_digest are required")
        with self._lock:
            existing = self._runs_by_key.get(idempotency_key)
            if existing is not None:
                if existing.input_digest != input_digest:
                    raise IdempotencyConflict("idempotency key/input mismatch")
                run = existing
            else:
                external_id = "fake-" + hashlib.sha256(
                    idempotency_key.encode("utf-8")
                ).hexdigest()[:20]
                run = ProviderRun(
                    external_run_id=external_id,
                    idempotency_key=idempotency_key,
                    input_digest=input_digest,
                    state=RunState.QUEUED,
                )
                self._runs_by_key[idempotency_key] = run
                self._runs_by_id[external_id] = run
        if lose_response:
            raise TimeoutError("simulated response loss; submission may have succeeded")
        return run

    def inspect(self, external_run_id: str) -> Optional[ProviderRun]:
        with self._lock:
            return self._runs_by_id.get(external_run_id)

    def reconcile(self, idempotency_key: str) -> Optional[ProviderRun]:
        """Look up an uncertain submission without creating another run."""
        with self._lock:
            return self._runs_by_key.get(idempotency_key)

    def set_state(self, external_run_id: str, state: RunState) -> ProviderRun:
        with self._lock:
            current = self._runs_by_id[external_run_id]
            if current.state in TERMINAL_STATES:
                raise ValueError("terminal provider run cannot transition")
            updated = ProviderRun(
                current.external_run_id, current.idempotency_key,
                current.input_digest, state,
            )
            self._runs_by_id[external_run_id] = updated
            self._runs_by_key[current.idempotency_key] = updated
            return updated


@dataclass(frozen=True)
class Lease:
    task_id: str
    owner: str
    fencing_token: int


@dataclass
class _Task:
    task_id: str
    idempotency_key: str
    input_digest: str
    state: str = "queued"
    owner: Optional[str] = None
    fencing_token: int = 0
    result: Optional[str] = None


class InMemoryCoordinator:
    """Single-process test fixture for dedupe, lease fencing and result publication."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tasks_by_key: dict[str, _Task] = {}
        self._tasks_by_id: dict[str, _Task] = {}

    def enqueue(self, *, task_id: str, idempotency_key: str, input_digest: str) -> _Task:
        with self._lock:
            existing = self._tasks_by_key.get(idempotency_key)
            if existing:
                if existing.input_digest != input_digest:
                    raise IdempotencyConflict("idempotency key/input mismatch")
                return existing
            task_id_owner = self._tasks_by_id.get(task_id)
            if task_id_owner is not None:
                if (
                    task_id_owner.idempotency_key != idempotency_key
                    or task_id_owner.input_digest != input_digest
                ):
                    raise IdempotencyConflict("task id reused for different identity")
                return task_id_owner
            task = _Task(task_id, idempotency_key, input_digest)
            self._tasks_by_key[idempotency_key] = task
            self._tasks_by_id[task_id] = task
            return task

    def claim(self, *, task_id: str, owner: str) -> Optional[Lease]:
        with self._lock:
            task = self._tasks_by_id[task_id]
            if task.state not in {"queued", "recoverable"}:
                return None
            task.fencing_token += 1
            task.owner = owner
            task.state = "leased"
            return Lease(task_id, owner, task.fencing_token)

    def recover_expired(self, *, task_id: str, current_owner: str) -> None:
        """Test hook representing a lease expiry confirmed by the coordinator."""
        with self._lock:
            task = self._tasks_by_id[task_id]
            if task.state != "leased" or task.owner != current_owner:
                raise ValueError("no matching active lease")
            task.state = "recoverable"
            task.owner = None

    def publish_result(self, *, lease: Lease, result: str) -> bool:
        with self._lock:
            task = self._tasks_by_id[lease.task_id]
            if (
                task.state != "leased"
                or task.owner != lease.owner
                or task.fencing_token != lease.fencing_token
            ):
                return False
            task.result = result
            task.state = "succeeded"
            return True

    def mark_failed(self, *, lease: Lease, failure_class: str) -> bool:
        """Publish a terminal failure only while the worker's fencing token is current."""
        if failure_class not in {"test_failure", "code_failure"}:
            raise ValueError("only terminal task failures are accepted here")
        with self._lock:
            task = self._tasks_by_id[lease.task_id]
            if (
                task.state != "leased"
                or task.owner != lease.owner
                or task.fencing_token != lease.fencing_token
            ):
                return False
            task.state = "failed"
            task.owner = None
            return True

    def get(self, task_id: str) -> _Task:
        with self._lock:
            return self._tasks_by_id[task_id]
