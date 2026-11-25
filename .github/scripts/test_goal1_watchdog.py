from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from goal1_watchdog import assess_runs, build_comment, fetch_workflow_runs, latest_state


NOW = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)


def run(
    event="schedule",
    status="completed",
    conclusion="success",
    age_minutes=10,
    branch="main",
    head_repository="owner/repo",
):
    created = (NOW - timedelta(minutes=age_minutes)).isoformat().replace("+00:00", "Z")
    return {
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "created_at": created,
        "run_started_at": created if status == "in_progress" else None,
        "head_branch": branch,
        "head_repository": {"full_name": head_repository},
        "id": 987654321,
        "html_url": "https://github.com/private/run/987654321",
        "display_title": "RAW-PRIVATE-CONTENT",
    }


class WatchdogAssessmentTests(unittest.TestCase):
    def test_fresh_successful_schedule_is_healthy(self):
        result = assess_runs([run()], NOW, repository="owner/repo")
        self.assertEqual(result["state"], "healthy")
        self.assertEqual(result["reasons"], [])

    def test_missing_schedule_fails_closed(self):
        result = assess_runs([run(event="push", branch="infra/goal1")], NOW, repository="owner/repo")
        self.assertEqual(result["state"], "degraded")
        self.assertIn("schedule_not_observed", result["reasons"])

    def test_stale_schedule_is_detected(self):
        result = assess_runs([run(age_minutes=27 * 60)], NOW, repository="owner/repo")
        self.assertIn("schedule_stale", result["reasons"])

    def test_failed_latest_schedule_is_detected_even_after_newer_successful_push(self):
        result = assess_runs([
            run(event="push", branch="infra/goal1", age_minutes=1),
            run(event="schedule", conclusion="failure", age_minutes=5),
        ], NOW, repository="owner/repo")
        self.assertIn("latest_schedule_not_successful", result["reasons"])
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_truncated_workflow_history_fails_closed(self):
        result = assess_runs([run()], NOW, repository="owner/repo", history_complete=False)
        self.assertIn("workflow_history_truncated", result["reasons"])

    def test_old_queued_run_is_detected(self):
        result = assess_runs([
            run(status="queued", conclusion=None, age_minutes=25, event="push", branch="infra/goal1"),
            run(),
        ], NOW, repository="owner/repo")
        self.assertIn("queued_run_overdue", result["reasons"])
        self.assertEqual(result["queued"], 1)

    def test_old_running_run_is_detected(self):
        result = assess_runs([
            run(status="in_progress", conclusion=None, age_minutes=40, event="push", branch="infra/goal1"),
            run(),
        ], NOW, repository="owner/repo")
        self.assertIn("running_run_overdue", result["reasons"])
        self.assertEqual(result["running"], 1)

    def test_latest_trusted_failure_is_detected(self):
        result = assess_runs([
            run(event="push", branch="infra/goal1", conclusion="failure", age_minutes=5),
            run(),
        ], NOW, repository="owner/repo")
        self.assertIn("latest_trusted_ci_failed", result["reasons"])

    def test_product_pr_failures_are_not_misclassified_as_infrastructure_failures(self):
        result = assess_runs([
            run(event="pull_request", branch="research/data", conclusion="failure", age_minutes=5),
            run(),
        ], NOW, repository="owner/repo")
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_fork_pull_request_on_infrastructure_branch_is_not_trusted(self):
        result = assess_runs([
            run(
                event="pull_request",
                branch="infra/untrusted",
                conclusion="failure",
                age_minutes=1,
                head_repository="attacker/marketsage",
            ),
            run(),
        ], NOW, repository="owner/repo")
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_fork_pull_request_named_main_is_not_trusted(self):
        result = assess_runs([
            run(
                event="pull_request",
                branch="main",
                conclusion="failure",
                age_minutes=1,
                head_repository="attacker/marketsage",
            ),
            run(),
        ], NOW, repository="owner/repo")
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_unsupported_event_on_main_is_not_trusted(self):
        result = assess_runs([
            run(event="workflow_dispatch", branch="main", conclusion="failure", age_minutes=1),
            run(),
        ], NOW, repository="owner/repo")
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_missing_head_repository_fails_closed(self):
        item = run(event="push", branch="infra/goal1", conclusion="failure", age_minutes=1)
        item.pop("head_repository")
        result = assess_runs([item, run()], NOW, repository="owner/repo")
        self.assertNotIn("latest_trusted_ci_failed", result["reasons"])

    def test_empty_history_is_degraded_not_healthy(self):
        result = assess_runs([], NOW, repository="owner/repo")
        self.assertEqual(result["state"], "degraded")
        self.assertIn("no_ci_runs", result["reasons"])
        self.assertIn("schedule_not_observed", result["reasons"])


class WorkflowPaginationTests(unittest.TestCase):
    def test_workflow_run_observer_is_gated_to_same_repository(self):
        workflow = (
            Path(__file__).resolve().parents[1]
            / "workflows"
            / "goal1-watchdog.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "if: ${{ github.event_name == 'schedule' || github.event.workflow_run.head_repository.full_name == github.repository }}",
            workflow,
        )


    @patch("goal1_watchdog.request_json")
    def test_fetches_all_pages_needed_for_reported_total(self, request_json):
        request_json.side_effect = [
            {"total_count": 101, "workflow_runs": [{} for _ in range(100)]},
            {"total_count": 101, "workflow_runs": [{}]},
        ]
        runs, complete = fetch_workflow_runs(
            "https://api.github.com", "owner/repo", "not-a-real-token"
        )
        self.assertEqual(len(runs), 101)
        self.assertTrue(complete)
        self.assertEqual(request_json.call_count, 2)

    @patch("goal1_watchdog.request_json")
    def test_history_over_page_limit_is_reported_incomplete(self, request_json):
        request_json.return_value = {
            "total_count": 501,
            "workflow_runs": [{} for _ in range(100)],
        }
        runs, complete = fetch_workflow_runs(
            "https://api.github.com", "owner/repo", "not-a-real-token", max_pages=5
        )
        self.assertEqual(len(runs), 500)
        self.assertFalse(complete)
        self.assertEqual(request_json.call_count, 5)


class SanitizedHandoffTests(unittest.TestCase):
    def test_comment_contains_aggregate_state_only(self):
        result = assess_runs([run()], NOW, repository="owner/repo")
        body = build_comment(result, "yarsalam/marketsage")
        self.assertIn("State: healthy", body)
        self.assertIn("Queued runs: 0", body)
        self.assertNotIn("987654321", body)
        self.assertNotIn("RAW-PRIVATE-CONTENT", body)
        self.assertNotIn("private/run", body)
        self.assertNotIn("token", body.lower())

    def test_latest_state_prefers_newest_first_comment_page(self):
        comments = [
            {
                "created_at": "2026-11-23T10:00:00Z",
                "body": """<!-- marketsage-goal1-watchdog-state -->
State: healthy
Reasons: none""",
            },
            {
                "created_at": "2026-11-23T09:45:00Z",
                "body": """<!-- marketsage-goal1-watchdog-state -->
State: degraded
Reasons: schedule_stale""",
            },
        ]
        self.assertEqual(latest_state(comments), ("healthy", ()))

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
