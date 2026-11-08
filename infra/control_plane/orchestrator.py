"""Durable intake-to-provider orchestration over SQLite and the safe router.

This is a dispatch orchestrator, not a worker executor. It validates an immutable
manifest, records the logical task in the durable coordinator, prepares the
provider outbox, and delegates provider selection/submission to the outbox-aware
router. Ambiguous submissions remain blocked for reconciliation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .dispatch_outbox import DispatchSnapshot, SQLiteDispatchOutbox
from .manifest import validate_manifest
from .providers import DispatchDecision, SafeFailoverRouter
from .sqlite_coordinator import SQLiteCoordinator, TaskSnapshot


@dataclass(frozen=True)
class OrchestrationResult:
    """A consistent read of the three durable dispatch components."""

    task: TaskSnapshot
    dispatch: DispatchDecision
    outbox: DispatchSnapshot


class DurableOrchestrator:
    """Connect manifest validation, durable task intake, outbox, and provider router.

    The coordinator and outbox may share one local SQLite database file. They
    intentionally remain separate transactional components: registration is
    idempotent, so a restart between their commits can safely resume submission.
    SQLite is single-host only. This class never starts a worker or performs
    investment, production, merge, deployment, or network operations itself.
    """

    def __init__(
        self,
        *,
        coordinator: SQLiteCoordinator,
        outbox: SQLiteDispatchOutbox,
        router: SafeFailoverRouter,
    ) -> None:
        self.coordinator = coordinator
        self.outbox = outbox
        self.router = router

    @staticmethod
    def _identity(manifest: Mapping[str, Any]) -> tuple[str, str, str]:
        return (
            str(manifest["task_id"]),
            str(manifest["idempotency_key"]),
            str(manifest["inputs_digest"]),
        )

    def submit(self, manifest: Mapping[str, Any]) -> OrchestrationResult:
        """Validate and durably register once, then attempt safe provider dispatch."""
        validate_manifest(manifest)
        task_id, idempotency_key, input_digest = self._identity(manifest)

        # Order is deliberate: a task is durable before any provider side effect.
        task = self.coordinator.enqueue(
            task_id=task_id,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
        self.outbox.prepare(
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
        decision = self.router.submit_durable(
            outbox=self.outbox,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
        return OrchestrationResult(
            task=task,
            dispatch=decision,
            outbox=self.outbox.get(idempotency_key),
        )

    def reconcile(self, manifest: Mapping[str, Any]) -> OrchestrationResult:
        """Reconcile an existing task without creating a new logical task or run."""
        validate_manifest(manifest)
        task_id, idempotency_key, input_digest = self._identity(manifest)
        task = self.coordinator.get(task_id)
        if task.idempotency_key != idempotency_key or task.input_digest != input_digest:
            raise ValueError("manifest does not match the persisted task identity")
        dispatch_state = self.outbox.get(idempotency_key)
        if dispatch_state.input_digest != input_digest:
            raise ValueError("manifest does not match the persisted dispatch identity")
        decision = self.router.submit_durable(
            outbox=self.outbox,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
        return OrchestrationResult(
            task=task,
            dispatch=decision,
            outbox=self.outbox.get(idempotency_key),
        )
