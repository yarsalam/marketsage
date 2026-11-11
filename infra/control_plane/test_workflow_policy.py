"""Static guardrails for unattended workflow cadence and local-runner isolation."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def read_workflow(name: str) -> str:
    return (REPOSITORY_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


class WorkflowPolicyTests(unittest.TestCase):
    def test_docker_canary_is_daily_and_only_pushes_on_main(self) -> None:
        workflow = read_workflow("docker-worker-acceptance.yml")
        schedules = re.findall(
            r"""(?m)^\s*-\s*cron:\s*["']([^"']+)["']\s*$""",
            workflow,
        )
        self.assertEqual(schedules, ["43 4 * * *"])

        push = re.search(
            r"(?ms)^  push:\s*\n(.*?)(?=^  [a-z_]+:|\Z)",
            workflow,
        )
        self.assertIsNotNone(push)
        branches = re.findall(r"(?m)^\s*-\s*([^\s#]+)\s*$", push.group(1))
        self.assertEqual(branches, ["main"])
        self.assertIn("timeout-minutes: 15", workflow)

    def test_self_hosted_worker_acceptance_is_manual_only(self) -> None:
        workflow = read_workflow("self-hosted-worker-acceptance.yml")
        triggers = re.search(
            r"(?ms)^on:\s*\n(.*?)(?=^permissions:)",
            workflow,
        )
        self.assertIsNotNone(triggers)
        self.assertRegex(triggers.group(1), r"(?m)^  workflow_dispatch:")
        self.assertNotRegex(triggers.group(1), r"(?m)^  (push|pull_request|schedule):")
        self.assertIn("confirm_local_worker_acceptance", workflow)
        self.assertRegex(
            workflow,
            r"(?m)^    runs-on: \[self-hosted, linux, x64, marketsage-server-worker\]$",
        )
        self.assertNotRegex(
            workflow,
            r"(?m)^    runs-on: \[self-hosted, linux, x64\]$",
        )
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertIn("timeout-minutes: 20", workflow)

    def test_self_hosted_diagnostics_do_not_echo_host_paths(self) -> None:
        workflow = read_workflow("self-hosted-worker-acceptance.yml")
        for diagnostic in (
            'echo "XDG_RUNTIME_DIR=',
            "ls -ld ",
            "namei -l ",
            "stat -Lc ",
            "getfacl -p ",
            "systemctl --user show",
            "systemctl --user status",
            "tee /tmp/",
        ):
            self.assertNotIn(diagnostic, workflow)
        self.assertIn('>> "$GITHUB_ENV"', workflow)
        self.assertIn('DOCKER_HOST="unix://${XDG_RUNTIME_DIR}/docker.sock"', workflow)

    def test_default_branch_ci_remains_event_driven_and_daily(self) -> None:
        workflow = read_workflow("ci.yml")
        self.assertRegex(workflow, r"(?m)^  push:")
        self.assertRegex(workflow, r"(?m)^  pull_request:")
        self.assertIn('cron: "17 3 * * *"', workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)


if __name__ == "__main__":
    unittest.main()
