"""Provider adapter contract and conservative failover over deterministic fakes.

This module is an infrastructure test seam only. It contains no live provider
clients and cannot launch external work. CapacityUnavailable means the provider
definitively rejected before accepting a run. SubmissionUncertain means an
acceptance may have occurred and must be reconciled before another provider is
considered.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence, runtime_checkable

from .lifecycle import IdempotencyConflict, RunState, TERMINAL_STATES


class ProviderError(RuntimeError):
    """Base class for sanitized provider adapter outcomes."""


class CapacityUnavailable(ProviderError):
    """Definite pre-acceptance capacity rejection; safe to try another adapter."""


class SubmissionUncertain(ProviderError):
    """Submission may have been accepted; reconcile before any failover."""


@dataclass(frozen=True)
class ProviderCapabilities:
    provider_id: str
    architectures: tuple[str, ...] = ("any",)
    network_policy: str = "none"
    secrets_required: bool = False
    cost_minor_units: int = 0
    supports_idempotency: bool = True
    supports_reconcile_by_key: bool = True
    terminal_failure_guarantees_no_side_effects: bool = False

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("provider_id is required")
        if not self.architectures or any(not item for item in self.architectures):
            raise ValueError("at least one non-empty architecture is required")
        if self.cost_minor_units < 0:
            raise ValueError("cost_minor_units cannot be negative")
        if self.network_policy not in {"none", "allowlist", "internet"}:
            raise ValueError("unsupported network policy")


@dataclass(frozen=True)
class ProviderReceipt:
    provider_id: str
    external_run_id: str
    idempotency_key: str
    input_digest: str
    state: RunState


@dataclass(frozen=True)
class DispatchDecision:
    receipt: Optional[ProviderReceipt]
    attempted_provider_ids: tuple[str, ...]
    blocked_reason: Optional[str] = None

    @property
    def accepted(self) -> bool:
        return self.receipt is not None

    @property
    def state(self) -> RunState:
        return self.receipt.state if self.receipt is not None else RunState.UNKNOWN


@runtime_checkable
class ProviderAdapter(Protocol):
    """Minimum provider-neutral contract used by the router."""

    capabilities: ProviderCapabilities

    def submit(self, *, idempotency_key: str, input_digest: str) -> ProviderReceipt:
        ...

    def inspect(self, external_run_id: str) -> Optional[ProviderReceipt]:
        ...

    def reconcile(self, idempotency_key: str) -> Optional[ProviderReceipt]:
        ...

    def request_cancel(self, external_run_id: str) -> Optional[ProviderReceipt]:
        ...


class IdempotentEffectLedger:
    """Shared fake side-effect sink used only to test cross-backend deduplication."""

    def __init__(self) -> None:
        self._effects: dict[str, tuple[str, str]] = {}

    def execute_once(self, *, idempotency_key: str, input_digest: str) -> bool:
        if not idempotency_key or not input_digest:
            raise ValueError("effect identity is required")
        existing = self._effects.get(idempotency_key)
        if existing is not None:
            if existing[0] != input_digest:
                raise IdempotencyConflict("idempotency key/input mismatch")
            return False
        self._effects[idempotency_key] = (input_digest, "committed")
        return True

    @property
    def effect_count(self) -> int:
        return len(self._effects)


class DeterministicFakeAdapter:
    """A local fake backend with explicit capacity and ambiguous-submit controls."""

    def __init__(
        self,
        provider_id: str,
        *,
        capacity_available: bool = True,
        uncertain_after_accept: bool = False,
        hide_reconciliation: bool = False,
        effects: Optional[IdempotentEffectLedger] = None,
    ) -> None:
        self.capabilities = ProviderCapabilities(
            provider_id=provider_id,
            terminal_failure_guarantees_no_side_effects=True,
        )
        self.capacity_available = capacity_available
        self.uncertain_after_accept = uncertain_after_accept
        self.hide_reconciliation = hide_reconciliation
        self.effects = effects or IdempotentEffectLedger()
        self.submit_calls = 0
        self.accepted_count = 0
        self._sequence = 0
        self._by_key: dict[str, ProviderReceipt] = {}
        self._by_id: dict[str, ProviderReceipt] = {}

    def submit(self, *, idempotency_key: str, input_digest: str) -> ProviderReceipt:
        self.submit_calls += 1
        if not idempotency_key or not input_digest:
            raise ValueError("idempotency_key and input_digest are required")
        existing = self._by_key.get(idempotency_key)
        if existing is not None:
            if existing.input_digest != input_digest:
                raise IdempotencyConflict("idempotency key/input mismatch")
            return existing
        if not self.capacity_available:
            raise CapacityUnavailable("provider capacity unavailable before acceptance")
        self._sequence += 1
        receipt = ProviderReceipt(
            provider_id=self.capabilities.provider_id,
            external_run_id=f"{self.capabilities.provider_id}-{self._sequence}",
            idempotency_key=idempotency_key,
            input_digest=input_digest,
            state=RunState.QUEUED,
        )
        self._by_key[idempotency_key] = receipt
        self._by_id[receipt.external_run_id] = receipt
        self.accepted_count += 1
        if self.uncertain_after_accept:
            self.uncertain_after_accept = False
            raise SubmissionUncertain("provider acceptance is uncertain")
        return receipt

    def inspect(self, external_run_id: str) -> Optional[ProviderReceipt]:
        return self._by_id.get(external_run_id)

    def reconcile(self, idempotency_key: str) -> Optional[ProviderReceipt]:
        if self.hide_reconciliation:
            return None
        return self._by_key.get(idempotency_key)

    def request_cancel(self, external_run_id: str) -> Optional[ProviderReceipt]:
        current = self._by_id.get(external_run_id)
        if current is None:
            return None
        if current.state in TERMINAL_STATES:
            return current
        # A queued fake can be cancelled immediately. A running fake remains
        # running until the provider confirms a terminal state.
        if current.state == RunState.QUEUED:
            return self._set_state(current, RunState.CANCELLED)
        return current

    def mark_running(self, external_run_id: str) -> ProviderReceipt:
        current = self._require(external_run_id)
        if current.state != RunState.QUEUED:
            raise ValueError("only queued runs can become running")
        return self._set_state(current, RunState.RUNNING)

    def mark_terminal(self, external_run_id: str, state: RunState) -> ProviderReceipt:
        if state not in TERMINAL_STATES:
            raise ValueError("a terminal provider state is required")
        current = self._require(external_run_id)
        if current.state in TERMINAL_STATES:
            raise ValueError("terminal provider run cannot transition")
        if state == RunState.SUCCEEDED:
            self.effects.execute_once(
                idempotency_key=current.idempotency_key,
                input_digest=current.input_digest,
            )
        return self._set_state(current, state)

    def _require(self, external_run_id: str) -> ProviderReceipt:
        current = self.inspect(external_run_id)
        if current is None:
            raise KeyError(external_run_id)
        return current

    def _set_state(self, current: ProviderReceipt, state: RunState) -> ProviderReceipt:
        updated = ProviderReceipt(
            provider_id=current.provider_id,
            external_run_id=current.external_run_id,
            idempotency_key=current.idempotency_key,
            input_digest=current.input_digest,
            state=state,
        )
        self._by_id[updated.external_run_id] = updated
        self._by_key[updated.idempotency_key] = updated
        return updated


class SafeFailoverRouter:
    """Fail over only after definite rejection or verified no-effect terminal failure."""

    def __init__(self, adapters: Sequence[ProviderAdapter]) -> None:
        if not adapters:
            raise ValueError("at least one provider adapter is required")
        ids = [adapter.capabilities.provider_id for adapter in adapters]
        if len(ids) != len(set(ids)):
            raise ValueError("provider_id values must be unique")
        self.adapters = tuple(adapters)
        self._by_id = {adapter.capabilities.provider_id: adapter for adapter in adapters}

    def submit(self, *, idempotency_key: str, input_digest: str) -> DispatchDecision:
        return self._submit_from(0, idempotency_key, input_digest, ())

    def retry_after_terminal_failure(self, previous: ProviderReceipt) -> DispatchDecision:
        adapter = self._by_id.get(previous.provider_id)
        if adapter is None:
            return DispatchDecision(None, (), "unknown_previous_provider")
        current = adapter.inspect(previous.external_run_id)
        if current is None:
            return DispatchDecision(None, (previous.provider_id,), "previous_run_unobservable")
        if current.state == RunState.SUCCEEDED:
            return DispatchDecision(current, (previous.provider_id,))
        if current.state not in TERMINAL_STATES:
            return DispatchDecision(None, (previous.provider_id,), "previous_run_not_terminal")
        if current.state != RunState.FAILED:
            return DispatchDecision(None, (previous.provider_id,), "terminal_state_not_retryable")
        if not adapter.capabilities.terminal_failure_guarantees_no_side_effects:
            return DispatchDecision(None, (previous.provider_id,), "terminal_failure_effects_unproven")
        index = next(
            i for i, candidate in enumerate(self.adapters)
            if candidate.capabilities.provider_id == previous.provider_id
        )
        return self._submit_from(
            index + 1,
            current.idempotency_key,
            current.input_digest,
            (previous.provider_id,),
        )

    def _submit_from(
        self,
        start: int,
        idempotency_key: str,
        input_digest: str,
        attempted: tuple[str, ...],
    ) -> DispatchDecision:
        visited = list(attempted)
        for adapter in self.adapters[start:]:
            provider_id = adapter.capabilities.provider_id
            visited.append(provider_id)
            try:
                receipt = adapter.submit(
                    idempotency_key=idempotency_key,
                    input_digest=input_digest,
                )
            except CapacityUnavailable:
                # The adapter contract guarantees that this error means no run
                # was accepted; advancing to another backend is therefore safe.
                continue
            except SubmissionUncertain:
                # Never send the same task to another backend while acceptance
                # may have happened. Reconcile once by the immutable task key.
                receipt = adapter.reconcile(idempotency_key)
                if receipt is None:
                    return DispatchDecision(None, tuple(visited), "submission_unknown")
                return DispatchDecision(receipt, tuple(visited))
            return DispatchDecision(receipt, tuple(visited))
        return DispatchDecision(None, tuple(visited), "no_provider_capacity")
