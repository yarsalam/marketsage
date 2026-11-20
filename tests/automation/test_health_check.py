import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.automation.health_check import assess_health


NOW = datetime(2026, 11, 20, 7, 0, tzinfo=timezone.utc)


def stamp(delta: timedelta) -> str:
    return (NOW - delta).isoformat().replace("+00:00", "Z")


def make_run(
    run_id: int,
    name: str = "MarketSage Infrastructure CI",
    event: str = "push",
    status: str = "completed",
    conclusion: str = "success",
    age: timedelta = timedelta(minutes=2),
) -> dict:
    return {
        "id": run_id,
        "name": name,
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "created_at": stamp(age),
        "run_started_at": stamp(age),
    }


class HealthAssessmentTests(unittest.TestCase):
    def test_first_schedule_is_bootstrap_not_failure(self):
        result = assess_health([], {}, "100", NOW)
        self.assertEqual(result["status"], "bootstrap_pending")
        self.assertEqual(result["schedule_freshness"], "bootstrap_pending")

    def test_recent_successful_schedule_is_healthy(self):
        run = make_run(
            10,
            name="MarketSage Infrastructure Watchdog",
            event="schedule",
            age=timedelta(hours=6),
        )
        result = assess_health([run], {}, "100", NOW)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["schedule_freshness"], "fresh")

    def test_old_successful_schedule_is_degraded(self):
        run = make_run(
            10,
            name="MarketSage Infrastructure Watchdog",
            event="schedule",
            age=timedelta(hours=9),
        )
        result = assess_health([run], {}, "100", NOW)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["schedule_freshness"], "stale")

    def test_old_queued_infrastructure_run_is_detected(self):
        run = make_run(
            11,
            status="queued",
            conclusion="",
            age=timedelta(minutes=25),
        )
        result = assess_health([run], {}, "100", NOW)
        self.assertEqual(result["stale_queued_runs"], 1)
        self.assertEqual(result["status"], "degraded")

    def test_old_running_job_is_detected(self):
        run = make_run(
            12,
            status="in_progress",
            conclusion="",
            age=timedelta(minutes=5),
        )
        jobs = {
            "12": [{
                "status": "in_progress",
                "started_at": stamp(timedelta(minutes=13)),
            }]
        }
        result = assess_health([run], jobs, "100", NOW)
        self.assertEqual(result["stale_running_jobs"], 1)
        self.assertEqual(result["status"], "degraded")

    def test_current_watchdog_run_is_excluded(self):
        run = make_run(
            100,
            name="MarketSage Infrastructure Watchdog",
            event="schedule",
            status="in_progress",
            conclusion="",
            age=timedelta(hours=30),
        )
        result = assess_health([run], {}, "100", NOW)
        self.assertEqual(result["status"], "bootstrap_pending")
        self.assertEqual(result["inspected_infrastructure_runs"], 0)

    def test_unrelated_workflows_are_ignored(self):
        run = make_run(
            13,
            name="Unrelated Workflow",
            status="queued",
            conclusion="",
            age=timedelta(days=2),
        )
        result = assess_health([run], {}, "100", NOW)
        self.assertEqual(result["status"], "bootstrap_pending")
        self.assertEqual(result["stale_queued_runs"], 0)


if __name__ == "__main__":
    unittest.main()
