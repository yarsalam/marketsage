from __future__ import annotations

import unittest

from infra.control_plane.task_registry import (
    TaskRecord,
    TaskRegistryError,
    TaskState,
    select_ready_tasks,
    topological_order,
    transition,
    validate_registry,
)


def task(
    task_id: str,
    *,
    dependencies: tuple[str, ...] = (),
    status: TaskState = TaskState.READY,
    priority: int = 100,
    attempt: int = 0,
    max_attempts: int = 2,
) -> TaskRecord:
    digest = (str(len(task_id))[-1] * 64)
    return TaskRecord(
        task_id=task_id,
        definition_id="infra." + task_id,
        definition_version=1,
        objective="bounded infrastructure test task",
        owner="automation",
        input_digest=digest,
        dependencies=dependencies,
        acceptance_criteria=("deterministic result",),
        expected_artifacts=("sanitized_summary",),
        timeout_seconds=60,
        max_attempts=max_attempts,
        status=status,
        attempt=attempt,
        priority=priority,
    )


class RegistryValidationTests(unittest.TestCase):
    def test_valid_graph_has_deterministic_topological_order(self) -> None:
        records = (
            task("task-c", dependencies=("task-a",)),
            task("task-b"),
            task("task-a"),
        )
        ordered = validate_registry(records)
        self.assertEqual(tuple(x.task_id for x in ordered), ("task-a", "task-b", "task-c"))

    def test_duplicate_task_ids_are_rejected(self) -> None:
        with self.assertRaises(TaskRegistryError):
            validate_registry((task("task-a"), task("task-a")))

    def test_missing_dependency_is_rejected(self) -> None:
        with self.assertRaises(TaskRegistryError):
            validate_registry((task("task-a", dependencies=("missing",)),))

    def test_cycles_are_rejected(self) -> None:
        with self.assertRaises(TaskRegistryError):
            validate_registry((
                task("task-a", dependencies=("task-b",)),
                task("task-b", dependencies=("task-a",)),
            ))

    def test_hard_safety_policy_rejects_cost_secret_or_privileged_actions(self) -> None:
        invalid = task("task-a")
        with self.assertRaises(TaskRegistryError):
            validate_registry((TaskRecord(**{**invalid.__dict__, "cost_ceiling_minor_units": 1}),))
        with self.assertRaises(TaskRegistryError):
            validate_registry((TaskRecord(**{**invalid.__dict__, "secrets_access": "read"}),))
        with self.assertRaises(TaskRegistryError):
            validate_registry((TaskRecord(**{**invalid.__dict__, "merge_allowed": True}),))


class SchedulerTests(unittest.TestCase):
    def test_independent_ready_tasks_can_run_in_parallel(self) -> None:
        records = (
            task("task-b", priority=20),
            task("task-a", priority=10),
            task("task-c", priority=30),
        )
        selected = select_ready_tasks(records, max_parallel=2)
        self.assertEqual(tuple(x.task_id for x in selected), ("task-a", "task-b"))

    def test_dependency_must_be_done_before_child_is_selected(self) -> None:
        records = (
            task("parent", status=TaskState.RUNNING),
            task("child", dependencies=("parent",)),
        )
        selected = select_ready_tasks(records, max_parallel=2)
        self.assertEqual(selected, ())

    def test_completed_dependency_unlocks_child(self) -> None:
        records = (
            task("parent", status=TaskState.DONE),
            task("child", dependencies=("parent",)),
        )
        selected = select_ready_tasks(records, max_parallel=2)
        self.assertEqual(tuple(x.task_id for x in selected), ("child",))

    def test_explicitly_blocked_task_is_not_selected(self) -> None:
        records = (task("task-a", status=TaskState.BLOCKED),)
        self.assertEqual(select_ready_tasks(records, max_parallel=1), ())

    def test_active_tasks_consume_parallel_slots(self) -> None:
        records = (task("task-a"), task("task-b"), task("task-c"))
        selected = select_ready_tasks(records, max_parallel=2, active_count=1)
        self.assertEqual(len(selected), 1)

    def test_retry_budget_is_bounded(self) -> None:
        record = task("task-a", attempt=1, max_attempts=2)
        started = transition(record, TaskState.RUNNING)
        self.assertEqual(started.attempt, 2)
        waiting = transition(started, TaskState.READY)
        self.assertEqual(waiting.attempt, 2)
        with self.assertRaises(TaskRegistryError):
            transition(waiting, TaskState.RUNNING)
        first_attempt = transition(task("task-b"), TaskState.RUNNING)
        with self.assertRaises(TaskRegistryError):
            transition(first_attempt, TaskState.RUNNING)

    def test_terminal_task_cannot_be_reopened(self) -> None:
        completed = task("task-a", status=TaskState.DONE)
        with self.assertRaises(TaskRegistryError):
            transition(completed, TaskState.READY)


if __name__ == "__main__":
    unittest.main()
