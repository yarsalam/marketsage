#!/usr/bin/env python3
"""Detect main-branch pushes whose commits are not associated with merged PRs.

This is detection, not prevention. It never rewrites refs or attempts to block a
push. It uses read-only commit/PR metadata and posts a sanitized Issue #49 notice
when provenance cannot be verified or a commit lacks a merged PR into main.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_SHA = re.compile(r"^[0-9a-f]{40}$")
_MAX_COMMITS = 50


class VerificationError(RuntimeError):
    pass


def classify_main_update(
    *,
    before_sha: str,
    after_sha: str,
    forced: bool,
    compare: dict[str, Any],
    pulls_by_sha: dict[str, list[dict[str, Any]]],
) -> list[str]:
    """Return safe reason codes; an empty list means all commits map to merged PRs."""
    reasons: list[str] = []
    if not _SHA.fullmatch(before_sha) or not _SHA.fullmatch(after_sha):
        return ["invalid_push_range"]
    if before_sha == after_sha:
        return []
    if forced:
        reasons.append("forced_main_update")
    if compare.get("status") != "ahead":
        reasons.append("main_history_not_fast_forward")
    commits = compare.get("commits")
    if not isinstance(commits, list) or not commits:
        return sorted(set(reasons + ["commit_range_unverifiable"]))
    if len(commits) > _MAX_COMMITS:
        return sorted(set(reasons + ["push_range_exceeds_review_limit"]))

    for item in commits:
        if not isinstance(item, dict):
            reasons.append("commit_metadata_invalid")
            continue
        commit = item.get("sha")
        if not isinstance(commit, str) or not _SHA.fullmatch(commit):
            reasons.append("commit_sha_invalid")
            continue
        pulls = pulls_by_sha.get(commit, [])
        associated = any(
            isinstance(pull, dict)
            and pull.get("merged_at")
            and isinstance(pull.get("base"), dict)
            and pull["base"].get("ref") == "main"
            for pull in pulls
        )
        if not associated:
            reasons.append("commit_without_merged_main_pr")
    return sorted(set(reasons))


def _request_json(url: str, token: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "MarketSage-main-provenance-check/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise VerificationError("github_api_non_200")
            return json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError) as exc:
        raise VerificationError("github_api_unavailable") from exc


def verify_push(
    *,
    api_url: str,
    repository: str,
    token: str,
    before_sha: str,
    after_sha: str,
    forced: bool,
) -> list[str]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise VerificationError("repository_invalid")
    if not token:
        raise VerificationError("token_missing")
    if not before_sha or not after_sha:
        raise VerificationError("push_range_missing")
    if before_sha == after_sha:
        return []

    compare_url = (
        f"{api_url.rstrip('/')}/repos/{repository}/compare/"
        f"{urllib.parse.quote(before_sha, safe='')}...{urllib.parse.quote(after_sha, safe='')}"
    )
    compare = _request_json(compare_url, token)
    commits = compare.get("commits") if isinstance(compare, dict) else None
    if not isinstance(commits, list):
        raise VerificationError("compare_response_invalid")
    if len(commits) > _MAX_COMMITS:
        return ["push_range_exceeds_review_limit"]
    pulls_by_sha: dict[str, list[dict[str, Any]]] = {}
    for item in commits:
        commit_sha = item.get("sha") if isinstance(item, dict) else None
        if not isinstance(commit_sha, str) or not _SHA.fullmatch(commit_sha):
            raise VerificationError("commit_metadata_invalid")
        url = f"{api_url.rstrip('/')}/repos/{repository}/commits/{commit_sha}/pulls"
        associated = _request_json(url, token)
        if not isinstance(associated, list):
            raise VerificationError("pull_association_response_invalid")
        pulls_by_sha[commit_sha] = associated
    return classify_main_update(
        before_sha=before_sha,
        after_sha=after_sha,
        forced=forced,
        compare=compare,
        pulls_by_sha=pulls_by_sha,
    )


def post_sanitized_notice(
    *,
    api_url: str,
    token: str,
    repository: str,
    run_url: str,
    before_sha: str,
    after_sha: str,
    reasons: list[str],
) -> None:
    """Post only run URL, commit range and fixed reason codes."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise VerificationError("repository_invalid")
    allowed = {
        "forced_main_update",
        "main_history_not_fast_forward",
        "commit_range_unverifiable",
        "push_range_exceeds_review_limit",
        "commit_metadata_invalid",
        "commit_sha_invalid",
        "commit_without_merged_main_pr",
        "invalid_push_range",
        "commit_range_unverifiable",
    }
    safe_reasons = sorted(set(reason for reason in reasons if reason in allowed))
    if not safe_reasons:
        safe_reasons = ["commit_range_unverifiable"]
    body = (
        "### Main-branch provenance warning\n\n"
        f"Run: {run_url}\n"
        f"Before: {before_sha[:40]}\n"
        f"After: {after_sha[:40]}\n"
        f"Reason codes: {', '.join(safe_reasons)}\n\n"
        "This is a detection/alert only; it does not prevent or revert the update. "
        "Review the commit range and verify that every change entered through an "
        "approved pull request. No commit messages, diffs, logs, tokens or secrets "
        "are included in this notice."
    )
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/repos/{repository}/issues/49/comments",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "MarketSage-main-provenance-check/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status not in (200, 201):
                raise VerificationError("notice_delivery_failed")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise VerificationError("notice_delivery_failed") from exc


def main() -> int:
    env = os.environ
    required = ("API_URL", "REPOSITORY", "GITHUB_TOKEN", "BEFORE_SHA", "AFTER_SHA", "SERVER_URL", "RUN_ID")
    if any(not env.get(name) for name in required):
        print("Main provenance check could not read required workflow context.")
        return 2
    run_url = f"{env['SERVER_URL'].rstrip('/')}/{env['REPOSITORY']}/actions/runs/{env['RUN_ID']}"
    forced = env.get("FORCED", "").lower() == "true"
    try:
        reasons = verify_push(
            api_url=env["API_URL"],
            repository=env["REPOSITORY"],
            token=env["GITHUB_TOKEN"],
            before_sha=env["BEFORE_SHA"],
            after_sha=env["AFTER_SHA"],
            forced=forced,
        )
        if not reasons:
            print("Every commit in this main push is associated with a merged PR targeting main.")
            return 0
        post_sanitized_notice(
            api_url=env["API_URL"],
            token=env["GITHUB_TOKEN"],
            repository=env["REPOSITORY"],
            run_url=run_url,
            before_sha=env["BEFORE_SHA"],
            after_sha=env["AFTER_SHA"],
            reasons=reasons,
        )
        print("Main update provenance warning posted to Issue #49.")
        return 1
    except VerificationError:
        # Do not print exception details or request metadata.
        try:
            post_sanitized_notice(
                api_url=env["API_URL"],
                token=env["GITHUB_TOKEN"],
                repository=env["REPOSITORY"],
                run_url=run_url,
                before_sha=env["BEFORE_SHA"],
                after_sha=env["AFTER_SHA"],
                reasons=["commit_range_unverifiable"],
            )
        except VerificationError:
            print("Main provenance verification and sanitized notification both failed.")
            return 2
        print("Main provenance verification failed; sanitized warning posted.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
