from __future__ import annotations

import json
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from goal1_watchdog import (
    ApiReadError,
    _request_runs,
    build_summary,
    evaluate_runs,
)


NOW = datetime(2026, 11, 27, 7, 0, tzinfo=timezone.utc)


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def make_run(
    *,
    run_id: int = 1,
    name: str = "MarketSage CI",
    event: str = "push",
    branch: str = "infra/test",
    status: str = "completed",
    conclusion: str = "success",
    created_minutes_ago: int = 5,
    updated_minutes_ago: int = 4,
    started_minutes_ago: int | None = None,
    head_repository_full_name: str = "yarsalam/marketsage",
) -> dict:
    created = NOW - timedelta(minutes=created_minutes_ago)
    updated = NOW - timedelta(minutes=updated_minutes_ago)
    started = (
        NOW - timedelta(minutes=started_minutes_ago)
        if started_minutes_ago is not None
        else None
    )
    return {
        "id": run_id,
        "name": name,
        "event": event,
        "head_branch": branch,
        "status": status,
        "conclusion": conclusion,
        "created_at": iso(created),
        "updated_at": iso(updated),
        "run_started_at": iso(started) if started else None,
        "head_repository": {"full_name": head_repository_full_name},
    }


class WatchdogEvaluationTests(unittest.TestCase):
    def test_recent_successful_heartbeat_is_healthy(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(
                    run_id=10,
                    name="MarketSage Goal 1 Watchdog",
                    event="schedule",
                    branch="main",
                    updated_minutes_ago=20,
                ),
                make_run(run_id=11, updated_minutes_ago=5),
            ],
            now=NOW,
            current_run_id=99,
            repository="yarsalam/marketsage",
        )
        self.assertEqual(metrics["status"], "HEALTHY")
        self.assertEqual(metrics["recent_failures"], 0)
        self.assertEqual(metrics["heartbeat_state"], "within_window")

    def test_missing_heartbeat_is_initializing_not_false_success(self) -> None:
        metrics = evaluate_runs([make_run()], now=NOW)
        self.assertEqual(metrics["status"], "INITIALIZING")
        self.assertEqual(metrics["heartbeat_state"], "not_yet_observed")

    def test_stale_successful_heartbeat_degrades_health(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(
                    name="MarketSage Goal 1 Watchdog",
                    event="schedule",
                    branch="main",
                    updated_minutes_ago=90,
                )
            ],
            now=NOW,
        )
        self.assertEqual(metrics["status"], "DEGRADED")
        self.assertEqual(metrics["heartbeat_state"], "stale")

    def test_queued_run_over_limit_is_detected(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(status="queued", conclusion=None, created_minutes_ago=20)
            ],
            now=NOW,
        )
        self.assertEqual(metrics["stale_queued"], 1)
        self.assertEqual(metrics["status"], "DEGRADED")

    def test_long_running_job_is_detected(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(
                    status="in_progress",
                    conclusion=None,
                    created_minutes_ago=40,
                    started_minutes_ago=35,
                )
            ],
            now=NOW,
        )
        self.assertEqual(metrics["stale_running"], 1)
        self.assertEqual(metrics["status"], "DEGRADED")

    def test_recent_failure_is_detected(self) -> None:
        metrics = evaluate_runs(
            [make_run(conclusion="failure", updated_minutes_ago=30)],
            now=NOW,
        )
        self.assertEqual(metrics["recent_failures"], 1)
        self.assertEqual(metrics["status"], "DEGRADED")

    def test_old_failure_is_outside_the_alert_window(self) -> None:
        metrics = evaluate_runs(
            [make_run(conclusion="failure", updated_minutes_ago=25 * 60)],
            now=NOW,
        )
        self.assertEqual(metrics["recent_failures"], 0)

    def test_cancelled_run_is_not_counted_as_failure(self) -> None:
        metrics = evaluate_runs(
            [make_run(conclusion="cancelled", updated_minutes_ago=10)],
            now=NOW,
        )
        self.assertEqual(metrics["recent_failures"], 0)
        self.assertEqual(metrics["recent_cancelled"], 1)

    def test_unrelated_branches_are_excluded_from_goal1_health(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(
                    branch="research/data-work",
                    conclusion="failure",
                    updated_minutes_ago=5,
                )
            ],
            now=NOW,
        )
        self.assertEqual(metrics["inspected_runs"], 0)
        self.assertEqual(metrics["recent_failures"], 0)

    def test_fork_runs_are_excluded_from_repository_health_history(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(
                    conclusion="failure",
                    updated_minutes_ago=5,
                    head_repository_full_name="attacker/fork",
                ),
                make_run(
                    name="MarketSage Goal 1 Watchdog",
                    event="schedule",
                    branch="main",
                    head_repository_full_name="attacker/fork",
                ),
            ],
            now=NOW,
            repository="yarsalam/marketsage",
        )
        self.assertEqual(metrics["inspected_runs"], 0)
        self.assertEqual(metrics["recent_failures"], 0)
        self.assertEqual(metrics["status"], "INITIALIZING")

    def test_current_watchdog_run_is_excluded(self) -> None:
        metrics = evaluate_runs(
            [
                make_run(
                    run_id=77,
                    name="MarketSage Goal 1 Watchdog",
                    event="schedule",
                    branch="main",
                    status="in_progress",
                    conclusion=None,
                    created_minutes_ago=90,
                    started_minutes_ago=90,
                )
            ],
            now=NOW,
            current_run_id="77",
        )
        self.assertEqual(metrics["inspected_runs"], 0)
        self.assertEqual(metrics["status"], "INITIALIZING")

    def test_truncated_history_fails_closed(self) -> None:
        metrics = evaluate_runs([], now=NOW, history_truncated=True)
        self.assertEqual(metrics["status"], "DEGRADED")
        self.assertTrue(metrics["history_truncated"])
        self.assertIn("truncated at the safety limit: yes", build_summary(metrics))

    def test_summary_contains_aggregate_only(self) -> None:
        metrics = evaluate_runs(
            [make_run(conclusion="failure", updated_minutes_ago=10)],
            now=NOW,
        )
        summary = build_summary(metrics)
        for forbidden in ("SECRET_TOKEN", "private/path", "deadbeef", "research/data-work", "123456"):
            self.assertNotIn(forbidden, summary)
        self.assertIn("Recent failed or timed-out runs", summary)
        self.assertIn("Human handoff", summary)

    def test_api_retry_is_limited_and_error_is_sanitized(self) -> None:
        with patch(
            "goal1_watchdog.urllib.request.urlopen",
            side_effect=urllib.error.URLError("PRIVATE_RESPONSE_DETAIL"),
        ) as mocked:
            with patch("goal1_watchdog.time.sleep") as sleep:
                with self.assertRaises(ApiReadError) as raised:
                    _request_runs(
                        "https://api.github.com",
                        "yarsalam/marketsage",
                        "not-a-real-credential",
                    )
        self.assertEqual(mocked.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertNotIn("PRIVATE_RESPONSE_DETAIL", str(raised.exception))
        self.assertNotIn("not-a-real-credential", str(raised.exception))

    def test_permission_error_is_not_retried(self) -> None:
        denied = urllib.error.HTTPError(
            "https://api.github.com", 403, "forbidden", None, None
        )
        with patch(
            "goal1_watchdog.urllib.request.urlopen",
            side_effect=denied,
        ) as mocked:
            with self.assertRaises(ApiReadError) as raised:
                _request_runs(
                    "https://api.github.com",
                    "yarsalam/marketsage",
                    "not-a-real-credential",
                )
        self.assertEqual(mocked.call_count, 1)
        self.assertNotIn("not-a-real-credential", str(raised.exception))

    def test_api_success_returns_workflow_runs(self) -> None:
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, limit: int) -> bytes:
                return json.dumps(
                    {"total_count": 2, "workflow_runs": [{"id": 1}, {"id": 2}]}
                ).encode()

        with patch("goal1_watchdog.urllib.request.urlopen", return_value=Response()):
            runs, truncated = _request_runs(
                "https://api.github.com",
                "yarsalam/marketsage",
                "not-a-real-credential",
            )
        self.assertEqual(runs, [{"id": 1}, {"id": 2}])
        self.assertFalse(truncated)

    def test_history_pagination_is_bounded_and_truncation_is_reported(self) -> None:
        pages = [
            {"total_count": 600, "workflow_runs": [{"id": index} for index in range(100)]}
            for _ in range(5)
        ]
        with patch("goal1_watchdog._request_runs_page", side_effect=pages) as mocked:
            runs, truncated = _request_runs(
                "https://api.github.com",
                "yarsalam/marketsage",
                "not-a-real-credential",
            )
        self.assertEqual(mocked.call_count, 5)
        self.assertEqual(len(runs), 500)
        self.assertTrue(truncated)


if __name__ == "__main__":
    unittest.main()
