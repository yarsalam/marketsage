"""Durable task intake, dispatch-lease and provider-run orchestration.

This coordinates submission and records provider execution state. It does not
claim to execute worker code; a concrete sandbox worker remains a separate layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .dispatch_outbox import DispatchSnapshot, DispatchState, SQLiteDispatchOutbox
from .lifecycle import RunState
from .manifest import validate_manifest
from .providers import DispatchDecision, ProviderReceipt, SafeFailoverRouter
from .sqlite_coordinator import Lease, SQLiteCoordinator, TaskSnapshot


@dataclass(frozen=True)
class OrchestrationResult:
    task: TaskSnapshot
    dispatch: DispatchDecision
    outbox: DispatchSnapshot


class DurableOrchestrator:
    """Connect Manifest -> Coordinator lease -> Outbox -> Router -> result ledger."""

    def __init__(
        self, *, coordinator: SQLiteCoordinator, outbox: SQLiteDispatchOutbox,
        router: SafeFailoverRouter, owner: str = "orchestrator",
        lease_seconds: int = 300,
    ) -> None:
        if not owner or lease_seconds < 1:
            raise ValueError("owner and positive lease_seconds are required")
        self.coordinator = coordinator
        self.outbox = outbox
        self.router = router
        self.owner = owner
        self.lease_seconds = lease_seconds

    @staticmethod
    def _identity(manifest: Mapping[str, Any]) -> tuple[str, str, str]:
        return (
            str(manifest["task_id"]),
            str(manifest["idempotency_key"]),
            str(manifest["inputs_digest"]),
        )

    @staticmethod
    def _terminal_decision(task: TaskSnapshot) -> DispatchDecision:
        mapping = {
            "succeeded": RunState.SUCCEEDED,
            "failed": RunState.FAILED,
            "cancelled": RunState.CANCELLED,
        }
        state = mapping.get(task.state)
        if state is None or not task.provider_id or not task.external_run_id:
            return DispatchDecision(None, (), "task_terminal")
        return DispatchDecision(
            ProviderReceipt(
                provider_id=task.provider_id,
                external_run_id=task.external_run_id,
                idempotency_key=task.idempotency_key,
                input_digest=task.input_digest,
                state=state,
            ),
            (task.provider_id,),
            "task_terminal",
        )

    def _result(
        self, task_id: str, decision: DispatchDecision, idempotency_key: str,
    ) -> OrchestrationResult:
        return OrchestrationResult(
            task=self.coordinator.get(task_id),
            dispatch=decision,
            outbox=self.outbox.get(idempotency_key),
        )

    def _record_receipt(
        self, *, task_id: str, receipt: ProviderReceipt, lease: Optional[Lease],
    ) -> bool:
        if lease is not None:
            attached = self.coordinator.mark_submitted(
                lease=lease,
                provider_id=receipt.provider_id,
                external_run_id=receipt.external_run_id,
            )
            if not attached:
                return False

        if receipt.state == RunState.RUNNING:
            return self.coordinator.mark_provider_running(
                task_id=task_id,
                provider_id=receipt.provider_id,
                external_run_id=receipt.external_run_id,
            )
        if receipt.state in {RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED}:
            return self.coordinator.publish_provider_result(
                task_id=task_id,
                provider_id=receipt.provider_id,
                external_run_id=receipt.external_run_id,
                state=receipt.state.value,
                result=None,
                failure_class="provider_failure" if receipt.state == RunState.FAILED else None,
            )
        # QUEUED is an accepted run; mark_submitted has already persisted its ID.
        return True

    def _dispatch(
        self, *, task_id: str, idempotency_key: str, input_digest: str,
    ) -> OrchestrationResult:
        self.coordinator.recover_expired()
        task = self.coordinator.get(task_id)
        if task.idempotency_key != idempotency_key or task.input_digest != input_digest:
            raise ValueError("manifest does not match the persisted task identity")
        if task.state in {"succeeded", "failed", "cancelled"}:
            return self._result(task_id, self._terminal_decision(task), idempotency_key)

        lease: Optional[Lease] = None
        if task.state in {"queued", "recoverable"}:
            lease = self.coordinator.claim(
                task_id=task_id,
                owner=self.owner,
                lease_seconds=self.lease_seconds,
            )
            if lease is None:
                blocked = DispatchDecision(None, (), "coordinator_claim_unavailable")
                return self._result(task_id, blocked, idempotency_key)
        elif task.state == "leased":
            blocked = DispatchDecision(None, (), "coordinator_lease_active")
            return self._result(task_id, blocked, idempotency_key)
        elif task.state not in {"submitted", "running"}:
            blocked = DispatchDecision(None, (), "coordinator_state_unhandled")
            return self._result(task_id, blocked, idempotency_key)

        decision = self.router.submit_durable(
            outbox=self.outbox,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )

        if decision.receipt is not None:
            if not self._record_receipt(task_id=task_id, receipt=decision.receipt, lease=lease):
                blocked = DispatchDecision(
                    None, decision.attempted_provider_ids, "coordinator_lease_lost"
                )
                return self._result(task_id, blocked, idempotency_key)
        elif lease is not None:
            # UNKNOWN and exhausted capacity both return the task to a claimable
            # state; the outbox itself decides whether a new submission is safe.
            self.coordinator.release_for_reconciliation(lease=lease)

        return self._result(task_id, decision, idempotency_key)

    def submit(self, manifest: Mapping[str, Any]) -> OrchestrationResult:
        """Validate, persist, claim and dispatch one immutable task."""
        validate_manifest(manifest)
        task_id, idempotency_key, input_digest = self._identity(manifest)
        self.coordinator.enqueue(
            task_id=task_id,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
        self.outbox.prepare(
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
        return self._dispatch(
            task_id=task_id,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )

    def reconcile(self, manifest: Mapping[str, Any]) -> OrchestrationResult:
        """Resume a prior intake/dispatch and publish an observed provider state."""
        validate_manifest(manifest)
        task_id, idempotency_key, input_digest = self._identity(manifest)
        task = self.coordinator.get(task_id)
        if task.idempotency_key != idempotency_key or task.input_digest != input_digest:
            raise ValueError("manifest does not match the persisted task identity")
        dispatch = self.outbox.get(idempotency_key)
        if dispatch.input_digest != input_digest:
            raise ValueError("manifest does not match the persisted dispatch identity")
        return self._dispatch(
            task_id=task_id,
            idempotency_key=idempotency_key,
            input_digest=input_digest,
        )
