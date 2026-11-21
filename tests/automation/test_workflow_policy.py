import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


class WorkflowPolicyTests(unittest.TestCase):
    def read(self, name: str) -> str:
        return (WORKFLOWS / name).read_text(encoding="utf-8")

    def test_infrastructure_ci_is_bounded_and_read_only(self):
        content = self.read("infra-ci.yml")
        self.assertIn("runs-on: ubuntu-latest", content)
        self.assertIn("timeout-minutes: 10", content)
        self.assertIn("contents: read", content)
        self.assertIn("cancel-in-progress: true", content)
        self.assertNotIn("self-hosted", content)
        self.assertNotIn("upload-artifact", content)

    def test_watchdog_is_scheduled_and_read_only(self):
        content = self.read("infra-watchdog.yml")
        self.assertIn('cron: "23 */6 * * *"', content)
        self.assertIn("actions: read", content)
        self.assertIn("timeout-minutes: 8", content)
        self.assertIn("cancel-in-progress: false", content)
        self.assertIn("queue: max", content)
        self.assertNotIn("self-hosted", content)
        self.assertNotIn("upload-artifact", content)

    def test_recovery_is_one_retry_and_scoped(self):
        content = self.read("infra-recovery.yml")
        self.assertIn("actions: write", content)
        self.assertIn("run_attempt == 1", content)
        self.assertIn("rerun-failed-jobs", content)
        self.assertIn("head_repository.full_name == github.repository", content)
        self.assertNotIn("actions/checkout", content)
        self.assertNotIn("upload-artifact", content)

    def test_ci_check_runs_for_every_pull_request_to_main(self):
        content = self.read("infra-ci.yml")
        self.assertIn("pull_request:", content)
        self.assertNotIn("paths:", content)

    def test_workflow_interpolations_are_not_backslash_escaped(self):
        for path in WORKFLOWS.glob("infra-*.yml"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn(r"\${", content, path.name)

    def test_recovery_retries_are_serialized(self):
        content = self.read("infra-recovery.yml")
        self.assertIn("group: marketsage-infra-recovery", content)
        self.assertIn("queue: max", content)
        self.assertIn("cancel-in-progress: false", content)
    def test_no_workflow_can_merge_or_deploy(self):
        for path in WORKFLOWS.glob("infra-*.yml"):
            content = path.read_text(encoding="utf-8").lower()
            for forbidden in ("gh pr merge", "deploy", "production", "backtest", "broker", "trading"):
                self.assertNotIn(forbidden, content, f"forbidden operation in {path.name}")


if __name__ == "__main__":
    unittest.main()
