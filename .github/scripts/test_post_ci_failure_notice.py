import json
import unittest
from unittest.mock import patch

from post_ci_failure_notice import build_comment, failed_job_names, post_comment


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


if __name__ == "__main__":
    unittest.main()
