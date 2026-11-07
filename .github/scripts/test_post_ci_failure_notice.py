import json
import os
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from post_ci_failure_notice import (
    build_comment,
    failed_job_names,
    main,
    post_comment,
)


class FailureNoticeTests(unittest.TestCase):
    def test_only_failed_job_names_are_selected(self):
        needs = {
            "analysis": {"result": "failure", "outputs": {"private": "RAW-DATA"}},
            "user-backend": {"result": "success", "outputs": {"token": "SECRET"}},
            "admin-workspace": {"result": "failure"},
        }
        self.assertEqual(
            failed_job_names(needs),
            ["admin-workspace", "analysis"],
        )

    def test_comment_contains_only_sanitized_status(self):
        needs = {
            "analysis": {"result": "failure", "outputs": {"private": "RAW-DATA"}},
        }
        comment = build_comment(
            needs=needs,
            server_url="https://github.com",
            repository="yarsalam/marketsage",
            run_id="12345",
            run_number="67",
            run_attempt="1",
        )
        self.assertIn("analysis", comment)
        self.assertIn("https://github.com/yarsalam/marketsage/actions/runs/12345", comment)
        self.assertNotIn("RAW-DATA", comment)
        self.assertNotIn("SECRET", comment)
        self.assertNotIn("outputs", comment)

    def test_no_failure_produces_no_comment(self):
        self.assertIsNone(
            build_comment(
                needs={"analysis": {"result": "success"}},
                server_url="https://github.com",
                repository="yarsalam/marketsage",
                run_id="12345",
                run_number="67",
                run_attempt="1",
            )
        )

    def test_unsafe_job_name_is_not_included(self):
        self.assertEqual(failed_job_names({"<secret>": {"result": "failure"}}), [])

    def test_post_comment_uses_only_issue_comment_endpoint(self):
        class Response:
            status = 201

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with patch("post_ci_failure_notice.urllib.request.urlopen", return_value=Response()) as mocked:
            post_comment(
                api_url="https://api.github.com",
                token="test-token",
                repository="yarsalam/marketsage",
                body="sanitized only",
            )
        request = mocked.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertTrue(request.full_url.endswith("/repos/yarsalam/marketsage/issues/49/comments"))
        self.assertEqual(json.loads(request.data.decode())["body"], "sanitized only")
        self.assertNotIn("test-token", request.data.decode())

    def test_main_dry_run_validates_failure_path_without_network(self):
        env = {
            "NEEDS_JSON": json.dumps({"analysis": {"result": "failure"}}),
            "SERVER_URL": "https://github.com",
            "REPOSITORY": "yarsalam/marketsage",
            "RUN_ID": "12345",
            "RUN_NUMBER": "67",
            "RUN_ATTEMPT": "1",
            "DRY_RUN": "1",
        }
        with patch.dict(os.environ, env, clear=True):
            with patch("post_ci_failure_notice.post_comment") as mocked:
                self.assertEqual(main(), 0)
                mocked.assert_not_called()

    def test_workflow_supplies_repository_context_to_failure_reporter(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertRegex(
            workflow,
            r"(?m)^\s*REPOSITORY:\s+\$\{\{\s*github\.repository\s*\}\}\s*$",
        )

    def test_workflow_actions_are_pinned_to_full_commit_shas(self):
        root = Path(__file__).resolve().parents[2]
        workflow = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        refs = re.findall(r"^\s*(?:-\s*)?uses:\s+[^@\s]+@([0-9a-fA-F]+)", workflow, re.MULTILINE)
        self.assertTrue(refs, "expected at least one external action")
        self.assertTrue(
            all(re.fullmatch(r"[0-9a-fA-F]{40}", ref) for ref in refs),
            "all action references must be immutable 40-character SHAs",
        )

    def test_dependabot_has_bounded_weekly_actions_updates(self):
        root = Path(__file__).resolve().parents[2]
        config = (root / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        self.assertIn("package-ecosystem: github-actions", config)
        self.assertIn("interval: weekly", config)
        self.assertIn("open-pull-requests-limit: 5", config)


if __name__ == "__main__":
    unittest.main()
