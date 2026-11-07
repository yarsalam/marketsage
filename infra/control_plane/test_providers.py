from __future__ import annotations

import unittest

from infra.control_plane.lifecycle import RunState
from infra.control_plane.providers import (
    CapacityUnavailable,
    DeterministicFakeAdapter,
    IdempotentEffectLedger,
    ProviderCapabilities,
    SafeFailoverRouter,
    SubmissionUncertain,
)


class ProviderAdapterTests(unittest.TestCase):
    def test_two_fake_backends_implement_the_same_contract(self) -> None:
        for provider_id in ("fake-a", "fake-b"):
            adapter = DeterministicFakeAdapter(provider_id)
            first = adapter.submit(idempotency_key="key-1", input_digest="a" * 64)
            duplicate = adapter.submit(idempotency_key="key-1", input_digest="a" * 64)
            self.assertEqual(first, duplicate)
            self.assertEqual(adapter.inspect(first.external_run_id), first)
            self.assertEqual(adapter.reconcile("key-1"), first)
            self.assertEqual(adapter.accepted_count, 1)

    def test_capability_contract_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            ProviderCapabilities(provider_id="", cost_minor_units=0)
        with self.assertRaises(ValueError):
            ProviderCapabilities(provider_id="fake", cost_minor_units=-1)
        with self.assertRaises(ValueError):
            ProviderCapabilities(provider_id="fake", network_policy="unrestricted-secret")

    def test_definite_capacity_rejection_fails_over_to_second_backend(self) -> None:
        effects = IdempotentEffectLedger()
        first = DeterministicFakeAdapter("fake-a", capacity_available=False, effects=effects)
        second = DeterministicFakeAdapter("fake-b", effects=effects)
        decision = SafeFailoverRouter((first, second)).submit(
            idempotency_key="task-1", input_digest="a" * 64
        )
        self.assertEqual(decision.receipt.provider_id, "fake-b")
        self.assertEqual(decision.attempted_provider_ids, ("fake-a", "fake-b"))
        self.assertEqual(first.accepted_count, 0)
        self.assertEqual(second.accepted_count, 1)
        second.mark_terminal(decision.receipt.external_run_id, RunState.SUCCEEDED)
        self.assertEqual(effects.effect_count, 1)

    def test_ambiguous_submit_is_reconciled_without_secondary_submit(self) -> None:
        effects = IdempotentEffectLedger()
        first = DeterministicFakeAdapter(
            "fake-a", uncertain_after_accept=True, effects=effects
        )
        second = DeterministicFakeAdapter("fake-b", effects=effects)
        decision = SafeFailoverRouter((first, second)).submit(
            idempotency_key="task-2", input_digest="b" * 64
        )
        self.assertEqual(decision.receipt.provider_id, "fake-a")
        self.assertEqual(decision.state, RunState.QUEUED)
        self.assertEqual(second.submit_calls, 0)
        self.assertEqual(first.accepted_count, 1)

    def test_unobservable_ambiguous_submit_blocks_failover(self) -> None:
        first = DeterministicFakeAdapter(
            "fake-a", uncertain_after_accept=True, hide_reconciliation=True
        )
        second = DeterministicFakeAdapter("fake-b")
        decision = SafeFailoverRouter((first, second)).submit(
            idempotency_key="task-3", input_digest="c" * 64
        )
        self.assertIsNone(decision.receipt)
        self.assertEqual(decision.blocked_reason, "submission_unknown")
        self.assertEqual(second.submit_calls, 0)

    def test_running_provider_run_cannot_be_failed_over(self) -> None:
        first = DeterministicFakeAdapter("fake-a")
        second = DeterministicFakeAdapter("fake-b")
        first_receipt = first.submit(idempotency_key="task-4", input_digest="d" * 64)
        running = first.mark_running(first_receipt.external_run_id)
        decision = SafeFailoverRouter((first, second)).retry_after_terminal_failure(running)
        self.assertEqual(decision.blocked_reason, "previous_run_not_terminal")
        self.assertEqual(second.submit_calls, 0)

    def test_verified_terminal_failure_allows_safe_failover_once(self) -> None:
        effects = IdempotentEffectLedger()
        first = DeterministicFakeAdapter("fake-a", effects=effects)
        second = DeterministicFakeAdapter("fake-b", effects=effects)
        initial = first.submit(idempotency_key="task-5", input_digest="e" * 64)
        failed = first.mark_terminal(initial.external_run_id, RunState.FAILED)
        decision = SafeFailoverRouter((first, second)).retry_after_terminal_failure(failed)
        self.assertEqual(decision.receipt.provider_id, "fake-b")
        self.assertEqual(second.accepted_count, 1)
        second.mark_terminal(decision.receipt.external_run_id, RunState.SUCCEEDED)
        self.assertEqual(effects.effect_count, 1)

    def test_terminal_success_is_returned_without_retry(self) -> None:
        first = DeterministicFakeAdapter("fake-a")
        second = DeterministicFakeAdapter("fake-b")
        initial = first.submit(idempotency_key="task-6", input_digest="f" * 64)
        succeeded = first.mark_terminal(initial.external_run_id, RunState.SUCCEEDED)
        decision = SafeFailoverRouter((first, second)).retry_after_terminal_failure(succeeded)
        self.assertEqual(decision.receipt, succeeded)
        self.assertEqual(second.submit_calls, 0)

    def test_cancel_request_is_not_treated_as_terminal_for_running_work(self) -> None:
        first = DeterministicFakeAdapter("fake-a")
        second = DeterministicFakeAdapter("fake-b")
        initial = first.submit(idempotency_key="task-7", input_digest="1" * 64)
        first.mark_running(initial.external_run_id)
        cancellation = first.request_cancel(initial.external_run_id)
        self.assertEqual(cancellation.state, RunState.RUNNING)
        decision = SafeFailoverRouter((first, second)).retry_after_terminal_failure(cancellation)
        self.assertEqual(decision.blocked_reason, "previous_run_not_terminal")
        self.assertEqual(second.submit_calls, 0)

    def test_idempotency_key_cannot_be_reused_with_different_input(self) -> None:
        adapter = DeterministicFakeAdapter("fake-a")
        adapter.submit(idempotency_key="same-key", input_digest="a" * 64)
        with self.assertRaises(ValueError):
            adapter.submit(idempotency_key="same-key", input_digest="b" * 64)


if __name__ == "__main__":
    unittest.main()
