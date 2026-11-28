from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


class Goal1WorkflowContractTests(unittest.TestCase):
    def test_ci_is_event_driven_and_infrastructure_only(self) -> None:
        content = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("  push:", content)
        self.assertIn("  pull_request:", content)
        self.assertIn("branches: [main]", content)
        self.assertIn("cancel-in-progress: true", content)
        self.assertIn("timeout-minutes: 10", content)
        self.assertIn('python-version: "3.12"', content)
        self.assertIn("ci-infra-tests:", content)
        self.assertIn("contents: read", content)
        self.assertNotIn("schedule:", content)
        self.assertNotIn("workflow_dispatch:", content)
        self.assertNotIn("issues: write", content)
        self.assertNotIn("secrets.", content)
        for forbidden in (
            "analysis:",
            "production-images:",
            "backtest",
            "broker",
            "trading",
            "ranking",
            "probability calibration",
            "capital allocation",
            "upload-artifact",
        ):
            self.assertNotIn(forbidden, content)

    def test_watchdog_is_scheduled_and_read_only(self) -> None:
        content = (WORKFLOWS / "goal1-watchdog.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "*/30 * * * *"', content)
        self.assertIn("workflow_run:", content)
        self.assertIn('workflows: ["MarketSage CI"]', content)
        self.assertIn("types: [completed]", content)
        self.assertIn("actions: read", content)
        self.assertIn("contents: read", content)
        self.assertIn("cancel-in-progress: false", content)
        self.assertIn("timeout-minutes: 3", content)
        self.assertIn("ref: main", content)
        self.assertIn("head_repository.full_name == github.repository", content)
        self.assertIn("persist-credentials: false", content)
        self.assertNotIn("workflow_dispatch:", content)
        self.assertNotIn("issues: write", content)
        self.assertNotIn("contents: write", content)
        self.assertNotIn("secrets.", content)
        self.assertNotIn("upload-artifact", content)

    def test_runbook_discloses_mainline_freeze_is_not_yet_active(self) -> None:
        content = (ROOT / "docs" / "automation" / "GITHUB_AUTOMATION_OPERATIONS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Mainline freeze is not yet active", content)
        self.assertIn("workflow_dispatch", content)
        self.assertIn("analysis/production jobs remain configured", content)
        self.assertIn("not independently verified", content)
        self.assertIn("PR #88", content)
        self.assertIn("no supported callback", content)
        self.assertIn("per-30-minute delivery", content)
        self.assertIn("independent 24/7 heartbeat", content)
        self.assertIn("4,320 runner-minutes", content)
        self.assertIn("1,440 runner-minutes", content)
        self.assertIn("$25.92", content)
        self.assertIn("$8.64", content)
        self.assertIn("$12 per month", content)
        self.assertIn("created within the last 24 hours", content)
        self.assertIn("same workflow and branch", content)
        self.assertIn("A missing successful scheduled heartbeat is a degraded state", content)

    def test_external_actions_are_pinned_to_full_commit_shas(self) -> None:
        for path in (WORKFLOWS / "ci.yml", WORKFLOWS / "goal1-watchdog.yml"):
            content = path.read_text(encoding="utf-8")
            refs = re.findall(
                r"(?m)^\s*(?:-\s*)?uses:\s+[^@\s]+@([0-9a-fA-F]+)",
                content,
            )
            self.assertTrue(refs, f"expected a pinned action in {path.name}")
            self.assertTrue(
                all(re.fullmatch(r"[0-9a-fA-F]{40}", ref) for ref in refs),
                f"all action references in {path.name} must be immutable full SHAs",
            )


if __name__ == "__main__":
    unittest.main()
