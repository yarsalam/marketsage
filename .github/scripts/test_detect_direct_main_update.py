from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from detect_direct_main_update import (
    classify_main_update,
    post_sanitized_notice,
    verify_push,
)


SHA_A = "a" * 40
SHA_B = "b" * 40
SHA_C = "c" * 40


class ClassifyMainUpdateTests(unittest.TestCase):
    def test_all_commits_with_merged_main_pr_are_accepted(self) -> None:
        compare = {"status": "ahead", "commits": [{"sha": SHA_B}, {"sha": SHA_C}]}
        pulls = {
            SHA_B: [{"merged_at": "2026-11-07T00:00:00Z", "base": {"ref": "main"}}],
            SHA_C: [{"merged_at": "2026-11-07T00:01:00Z", "base": {"ref": "main"}}],
        }
        self.assertEqual(
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_C, forced=False,
                compare=compare, pulls_by_sha=pulls,
            ),
            [],
        )

    def test_commit_without_merged_main_pr_is_reported(self) -> None:
        compare = {"status": "ahead", "commits": [{"sha": SHA_B}]}
        self.assertEqual(
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_B, forced=False,
                compare=compare, pulls_by_sha={SHA_B: []},
            ),
            ["commit_without_merged_main_pr"],
        )

    def test_open_pr_or_pr_targeting_other_branch_is_not_accepted(self) -> None:
        compare = {"status": "ahead", "commits": [{"sha": SHA_B}]}
        pulls = {SHA_B: [
            {"merged_at": None, "base": {"ref": "main"}},
            {"merged_at": "2026-11-07T00:00:00Z", "base": {"ref": "develop"}},
        ]}
        self.assertEqual(
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_B, forced=False,
                compare=compare, pulls_by_sha=pulls,
            ),
            ["commit_without_merged_main_pr"],
        )

    def test_force_push_is_reported_even_with_associated_pr(self) -> None:
        compare = {"status": "ahead", "commits": [{"sha": SHA_B}]}
        pulls = {SHA_B: [{"merged_at": "2026-11-07T00:00:00Z", "base": {"ref": "main"}}]}
        self.assertIn(
            "forced_main_update",
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_B, forced=True,
                compare=compare, pulls_by_sha=pulls,
            ),
        )

    def test_non_fast_forward_history_is_reported(self) -> None:
        compare = {"status": "diverged", "commits": [{"sha": SHA_B}]}
        pulls = {SHA_B: [{"merged_at": "2026-11-07T00:00:00Z", "base": {"ref": "main"}}]}
        self.assertIn(
            "main_history_not_fast_forward",
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_B, forced=False,
                compare=compare, pulls_by_sha=pulls,
            ),
        )

    def test_oversized_push_range_fails_closed(self) -> None:
        compare = {"status": "ahead", "commits": [{"sha": SHA_B}] * 51}
        self.assertEqual(
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_B, forced=False,
                compare=compare, pulls_by_sha={},
            ),
            ["push_range_exceeds_review_limit"],
        )

    def test_invalid_push_range_fails_closed(self) -> None:
        self.assertEqual(
            classify_main_update(
                before_sha="bad", after_sha=SHA_B, forced=False,
                compare={"status": "ahead", "commits": [{"sha": SHA_B}]},
                pulls_by_sha={},
            ),
            ["invalid_push_range"],
        )

    def test_identical_sha_is_noop(self) -> None:
        self.assertEqual(
            classify_main_update(
                before_sha=SHA_A, after_sha=SHA_A, forced=False,
                compare={}, pulls_by_sha={},
            ),
            [],
        )


class GitHubApiTests(unittest.TestCase):
    def test_verify_push_uses_compare_and_commit_association(self) -> None:
        compare = {"status": "ahead", "commits": [{"sha": SHA_B}]}
        pull_list = [{"merged_at": "2026-11-07T00:00:00Z", "base": {"ref": "main"}}]
        with patch("detect_direct_main_update._request_json", side_effect=[compare, pull_list]) as mocked:
            result = verify_push(
                api_url="https://api.github.com",
                repository="yarsalam/marketsage",
                token="not-a-real-token",
                before_sha=SHA_A,
                after_sha=SHA_B,
                forced=False,
            )
        self.assertEqual(result, [])
        self.assertEqual(mocked.call_count, 2)
        self.assertIn("/compare/", mocked.call_args_list[0].args[0])
        self.assertIn(f"/commits/{SHA_B}/pulls", mocked.call_args_list[1].args[0])

    def test_sanitized_notice_does_not_include_token_or_commit_messages(self) -> None:
        class Response:
            status = 201
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        with patch("detect_direct_main_update.urllib.request.urlopen", return_value=Response()) as mocked:
            post_sanitized_notice(
                api_url="https://api.github.com",
                token="SECRET_TOKEN",
                repository="yarsalam/marketsage",
                run_url="https://github.com/yarsalam/marketsage/actions/runs/123",
                before_sha=SHA_A,
                after_sha=SHA_B,
                reasons=["commit_without_merged_main_pr"],
            )
        request = mocked.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))["body"]
        self.assertNotIn("SECRET_TOKEN", body)
        self.assertNotIn("DO_NOT_LEAK_COMMIT_TITLE", body)
        self.assertIn("commit_without_merged_main_pr", body)


if __name__ == "__main__":
    unittest.main()
