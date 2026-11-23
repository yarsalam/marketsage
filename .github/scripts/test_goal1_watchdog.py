from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from goal1_watchdog import assess_runs, build_comment, latest_state


NOW = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)


def run(event="schedule", status="completed", conclusion="success", age_minutes=10, branch="main"):
    created = (NOW - timedelta(minutes=age_minutes)).isoformat().replace("+00:00", "Z")
    return {
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "created_at": created,
        "run_started_at": created if status == "in_progress" else None,
        "head_branch": branch,
        "id": 987654321,
        "html_url": "https://github.com/private/run/987654321",
        "display_title": "RAW-PRIVATE-CONTENT",
    }


class WatchdogAssessmentTests(unittest.TestCase):
    def test_fresh_successful_schedule_is_healthy(self):
        result = assess_runs([run()], NOW)
        self.assertEqual(result["state"], "healthy")
        self.assertEqual(result["reasons"], [])

    def test_missing_schedule_fails_closed(self):
        result = assess_runs([run(event="push", branch="infra/goal1")], NOW)
        self.assertEqual(result["state"], "degraded")
        self.assertIn("schedule_not_observed", result["reasons"])

    def test_stale_schedule_is_detected(self):
        result = assess_runs([run(age_minutes=27 * 60)], NOW)
        self.assertIn("schedule_stale", result["reasons"])

    def test_old_queued_run_is_detected(self):
        result = assess_runs([
            run(status="queued", conclusion=None, age_minutes=25, event="push", branch="infra/goal1"),
            run(),
        ], NOW)
        self.assertIn("queued_run_overdue", result["reasons"])
        self.assertEqual(result["queued"], 1)

    def test_old_running_run_is_detected(self):
        result = assess_runs([
            run(status="in_progress", conclusion=None, age_minutes=40, event="push", branch="infra/goal1"),
            run(),
        ], NOW)
        self.assertIn("running_run_overdue", result["reasons"])
        self.assertEqual(result["running"], 1)

    def test_latest_trusted_failure_is_detected(self):
        result = assess_runs([
            run(event="push", branch="infra/goal1", conclusion="failure", age_minutes=5),
            run(),
        ], NOW)
        self.assertIn("latest_trusted_ci_failed", result["reasons"])

    def test_product_pr_failures_are_not_misclassified_as_infrastructure_failures(self):
        result = assess_runs([
            run(event="pull_request", branch="research/data", conclusion="failure", age_minutes=5),
            run(),
        ], NOW)
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_empty_history_is_degraded_not_healthy(self):
        result = assess_runs([], NOW)
        self.assertEqual(result["state"], "degraded")
        self.assertIn("no_ci_runs", result["reasons"])
        self.assertIn("schedule_not_observed", result["reasons"])


class SanitizedHandoffTests(unittest.TestCase):
    def test_comment_contains_aggregate_state_only(self):
        result = assess_runs([run()], NOW)
        body = build_comment(result, "yarsalam/marketsage")
        self.assertIn("State: healthy", body)
        self.assertIn("Queued runs: 0", body)
        self.assertNotIn("987654321", body)
        self.assertNotIn("RAW-PRIVATE-CONTENT", body)
        self.assertNotIn("private/run", body)
        self.assertNotIn("token", body.lower())

    def test_latest_state_reads_only_status_and_reason_codes(self):
        comments = [
            {"body": "<!-- marketsage-goal1-watchdog-state -->\nState: degraded\nReasons: queued_run_overdue, schedule_stale"}
        ]
        self.assertEqual(
            latest_state(comments),
            ("degraded", ("queued_run_overdue", "schedule_stale")),
        )


if __name__ == "__main__":
    unittest.main()
