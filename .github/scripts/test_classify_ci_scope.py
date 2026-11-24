from __future__ import annotations

import re
import unittest
from pathlib import Path

from classify_ci_scope import is_allowed_path, is_infrastructure_only

ROOT = Path(__file__).resolve().parents[2]
CI = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
WATCHDOG = (ROOT / ".github/workflows/goal1-watchdog.yml").read_text(encoding="utf-8")


class ScopeClassifierTests(unittest.TestCase):
    def test_only_explicit_goal1_paths_are_allowed(self):
        self.assertTrue(is_allowed_path(".github/workflows/ci.yml"))
        self.assertTrue(is_allowed_path(".github/workflows/goal1-watchdog.yml"))
        self.assertTrue(is_allowed_path(".github/scripts/goal1_watchdog.py"))
        self.assertTrue(is_allowed_path("docs/automation/GOAL1_GITHUB_AUTOMATION.md"))
        self.assertFalse(is_allowed_path("user/analysis-engine/model.py"))
        self.assertFalse(is_allowed_path("infra/control_plane/providers.py"))
        self.assertFalse(is_allowed_path("docs/governance/DECISION_LOG.md"))

    def test_traversal_absolute_and_confused_paths_fail_closed(self):
        for path in (
            "/.github/workflows/ci.yml",
            ".github/scripts/../private.py",
            r".github\\scripts\\goal1_watchdog.py",
            ".github/scripts/a\nuser/analysis.py",
        ):
            self.assertFalse(is_allowed_path(path))

    def test_infra_branch_with_allowlisted_paths_is_allowed(self):
        self.assertTrue(is_infrastructure_only(
            "pull_request",
            "infra/goal1-github-automation-2026-11-23",
            [".github/workflows/ci.yml", ".github/scripts/classify_ci_scope.py"],
        ))

    def test_mixed_or_product_changes_are_blocked(self):
        self.assertFalse(is_infrastructure_only(
            "pull_request",
            "infra/attempt",
            [".github/workflows/ci.yml", "user/analysis-engine/model.py"],
        ))
        self.assertFalse(is_infrastructure_only(
            "pull_request",
            "research/data-work",
            [".github/workflows/ci.yml"],
        ))

    def test_main_push_requires_every_changed_path_to_be_allowlisted(self):
        self.assertTrue(is_infrastructure_only("push", "main", [".github/workflows/ci.yml"]))
        self.assertFalse(is_infrastructure_only(
            "push", "main", [".github/workflows/ci.yml", "user/user-backend/src/app.ts"]
        ))

    def test_schedule_is_infrastructure_only(self):
        self.assertTrue(is_infrastructure_only("schedule", "main", []))

    def test_empty_or_unknown_scope_is_not_authorized(self):
        self.assertFalse(is_infrastructure_only("pull_request", "infra/empty", []))
        self.assertFalse(is_infrastructure_only("workflow_dispatch", "infra/manual", []))


class WorkflowPolicyTests(unittest.TestCase):
    def test_push_schedule_and_pr_runs_do_not_cancel_across_event_types(self):
        self.assertIn(
            "group: marketsage-goal1-ci-${{ github.event.pull_request.number || github.ref }}-${{ github.event_name }}",
            CI,
        )

    def test_event_driven_and_daily_schedule_are_present(self):
        self.assertRegex(CI, r"(?m)^  push:\s*$")
        self.assertRegex(CI, r"(?m)^  pull_request:\s*$")
        self.assertRegex(CI, r"(?m)^  schedule:\s*$")
        self.assertIn('    - cron: "17 3 * * *"', CI)
        self.assertNotIn("workflow_dispatch:", CI)

    def test_required_main_ruleset_contexts_are_preserved(self):
        for name in (
            "  analysis:",
            "  user-backend:",
            "  user-frontend:",
            "  admin-workspace:",
            "  production-images:",
            "    name: Test provider-neutral control plane",
            "    name: Test CI automation helpers",
        ):
            self.assertIn(name, CI)

    def test_product_and_production_jobs_are_fail_closed_without_commands(self):
        for job_id in ("analysis", "user-backend", "user-frontend", "admin-workspace", "production-images"):
            match = re.search(
                rf"(?ms)^  {re.escape(job_id)}:\n(.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
                CI,
            )
            self.assertIsNotNone(match)
            job = match.group(1)
            self.assertIn("needs: [classify-change-scope]", job)
            self.assertIn("needs.classify-change-scope.outputs.infra_only != 'true'", job)
            self.assertIn("exit 1", job)
            for forbidden in ("pytest ", "pnpm ", "docker compose", "upload-artifact"):
                self.assertNotIn(forbidden, job)

    def test_no_self_hosted_runner_artifact_or_secret_reference_in_ci(self):
        self.assertNotIn("runs-on: self-hosted", CI)
        self.assertNotIn("upload-artifact", CI)
        self.assertNotIn("download-artifact", CI)
        self.assertNotIn("secrets.", CI)

    def test_external_actions_are_pinned_to_full_commit_shas(self):
        refs = re.findall(r"(?m)^\s*-\s*uses:\s+[^@\s]+@([0-9a-fA-F]+)", CI + "\n" + WATCHDOG)
        self.assertTrue(refs)
        self.assertTrue(all(re.fullmatch(r"[0-9a-fA-F]{40}", ref) for ref in refs))

    def test_watchdog_is_scheduled_queued_and_bounded(self):
        self.assertRegex(WATCHDOG, r"(?m)^  schedule:\s*$")
        self.assertIn('    - cron: "*/15 * * * *"', WATCHDOG)
        self.assertRegex(WATCHDOG, r"(?m)^  workflow_run:\s*$")
        self.assertIn("queue: max", WATCHDOG)
        self.assertIn("timeout-minutes: 5", WATCHDOG)
        self.assertNotRegex(WATCHDOG, r"(?m)^\s*cancel-in-progress:")
        self.assertNotIn("workflow_dispatch:", WATCHDOG)

    def test_issue_write_failure_notice_is_restricted_to_trusted_refs(self):
        self.assertIn(
            "if: ${{ always() && (github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/heads/infra/')) && contains(needs.*.result, 'failure') }}",
            CI,
        )

    def test_watchdog_uses_only_read_actions_and_issue_handoff(self):
        self.assertIn("actions: read", WATCHDOG)
        self.assertIn("contents: read", WATCHDOG)
        self.assertIn("issues: write", WATCHDOG)
        self.assertNotIn("contents: write", WATCHDOG)
        self.assertNotIn("upload-artifact", WATCHDOG)


if __name__ == "__main__":
    unittest.main()
