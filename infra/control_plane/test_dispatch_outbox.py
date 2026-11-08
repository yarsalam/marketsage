from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from infra.control_plane.dispatch_outbox import DispatchState, SQLiteDispatchOutbox
from infra.control_plane.lifecycle import IdempotencyConflict, RunState
from infra.control_plane.providers import ProviderReceipt


DIGEST = "a" * 64


def receipt(provider: str, run_id: str, state: RunState = RunState.QUEUED) -> ProviderReceipt:
    return ProviderReceipt(provider, run_id, "task-key", DIGEST, state)


class DispatchOutboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "dispatch.sqlite3"
        self.outbox = SQLiteDispatchOutbox(self.db)
        self.outbox.prepare(idempotency_key="task-key", input_digest=DIGEST, now=1)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_prepared_state_and_idempotent_registration_survive_restart(self) -> None:
        first = self.outbox.get("task-key")
        second = SQLiteDispatchOutbox(self.db).prepare(
            idempotency_key="task-key", input_digest=DIGEST, now=2
        )
        self.assertEqual(first, second)
        self.assertEqual(second.state, DispatchState.PREPARED)

    def test_key_reuse_with_different_input_is_rejected(self) -> None:
        with self.assertRaises(IdempotencyConflict):
            self.outbox.prepare(idempotency_key="task-key", input_digest="b" * 64)

    def test_submission_is_persisted_before_provider_call(self) -> None:
        attempt = self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.assertEqual(attempt.state, DispatchState.SUBMITTING)
        reopened = SQLiteDispatchOutbox(self.db)
        self.assertEqual(reopened.get("task-key").state, DispatchState.SUBMITTING)
        self.assertIsNone(reopened.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=11))
        self.assertIsNone(reopened.begin_attempt(idempotency_key="task-key", provider_id="backend-b", now=11))

    def test_unknown_submission_blocks_failover_even_after_restart(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.assertTrue(self.outbox.mark_unknown(
            idempotency_key="task-key", provider_id="backend-a", reason_code="transport_timeout", now=11
        ))
        reopened = SQLiteDispatchOutbox(self.db)
        self.assertEqual(reopened.get("task-key").state, DispatchState.UNKNOWN)
        self.assertIsNone(reopened.begin_attempt(idempotency_key="task-key", provider_id="backend-b", now=12))

    def test_reconciliation_of_unknown_submission_records_existing_run(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.outbox.mark_unknown(idempotency_key="task-key", provider_id="backend-a", now=11)
        accepted = self.outbox.mark_accepted(receipt=receipt("backend-a", "run-1"), now=12)
        self.assertEqual(accepted.state, DispatchState.ACCEPTED)
        self.assertEqual(accepted.external_run_id, "run-1")
        self.assertIsNone(self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-b", now=13))

    def test_definite_capacity_rejection_allows_second_backend(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.assertTrue(self.outbox.mark_rejected(
            idempotency_key="task-key", provider_id="backend-a", now=11
        ))
        next_attempt = self.outbox.begin_attempt(
            idempotency_key="task-key", provider_id="backend-b", now=12
        )
        self.assertEqual(next_attempt.attempt_no, 2)
        self.assertEqual(next_attempt.provider_id, "backend-b")

    def test_terminal_failure_requires_explicit_no_effect_guarantee_for_failover(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.outbox.mark_accepted(receipt=receipt("backend-a", "run-1"), now=11)
        failed = self.outbox.mark_terminal(
            receipt=receipt("backend-a", "run-1", RunState.FAILED),
            no_side_effects_on_failure=False, now=12,
        )
        self.assertEqual(failed.state, DispatchState.FAILED)
        self.assertIsNone(self.outbox.begin_attempt(
            idempotency_key="task-key", provider_id="backend-b", now=13
        ))

    def test_verified_no_effect_terminal_failure_allows_next_backend(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.outbox.mark_accepted(receipt=receipt("backend-a", "run-1"), now=11)
        self.outbox.mark_terminal(
            receipt=receipt("backend-a", "run-1", RunState.FAILED),
            no_side_effects_on_failure=True, now=12,
        )
        next_attempt = self.outbox.begin_attempt(
            idempotency_key="task-key", provider_id="backend-b", now=13
        )
        self.assertEqual(next_attempt.attempt_no, 2)

    def test_success_is_terminal_and_cannot_be_retried(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.outbox.mark_accepted(receipt=receipt("backend-a", "run-1"), now=11)
        result = self.outbox.mark_terminal(
            receipt=receipt("backend-a", "run-1", RunState.SUCCEEDED), now=12
        )
        self.assertEqual(result.state, DispatchState.SUCCEEDED)
        self.assertIsNone(self.outbox.begin_attempt(
            idempotency_key="task-key", provider_id="backend-b", now=13
        ))

    def test_receipt_cannot_change_immutable_task_input(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        mismatched = ProviderReceipt("backend-a", "run-1", "task-key", "b" * 64, RunState.QUEUED)
        with self.assertRaises(IdempotencyConflict):
            self.outbox.mark_accepted(receipt=mismatched, now=11)

    def test_attempt_history_is_durable_and_ordered(self) -> None:
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-a", now=10)
        self.outbox.mark_rejected(idempotency_key="task-key", provider_id="backend-a", now=11)
        self.outbox.begin_attempt(idempotency_key="task-key", provider_id="backend-b", now=12)
        reopened = SQLiteDispatchOutbox(self.db)
        attempts = reopened.attempts("task-key")
        self.assertEqual([x.provider_id for x in attempts], ["backend-a", "backend-b"])
        self.assertEqual([x.state for x in attempts], [DispatchState.REJECTED, DispatchState.SUBMITTING])

    def test_only_one_concurrent_provider_attempt_is_reserved(self) -> None:
        barrier = threading.Barrier(2)
        results = []
        lock = threading.Lock()

        def reserve(provider: str) -> None:
            barrier.wait()
            result = SQLiteDispatchOutbox(self.db).begin_attempt(
                idempotency_key="task-key", provider_id=provider, now=20
            )
            with lock:
                results.append(result)

        threads = [
            threading.Thread(target=reserve, args=("backend-a",)),
            threading.Thread(target=reserve, args=("backend-b",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(sum(item is not None for item in results), 1)

    def test_provider_attempt_budget_is_bounded(self) -> None:
        for index, provider in enumerate(("backend-a", "backend-b", "backend-c"), start=1):
            attempt = self.outbox.begin_attempt(
                idempotency_key="task-key", provider_id=provider, now=index * 10
            )
            self.assertEqual(attempt.attempt_no, index)
            self.outbox.mark_rejected(
                idempotency_key="task-key", provider_id=provider, now=index * 10 + 1
            )
        self.assertIsNone(self.outbox.begin_attempt(
            idempotency_key="task-key", provider_id="backend-d", now=50
        ))


if __name__ == "__main__":
    unittest.main()
