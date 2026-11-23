#!/usr/bin/env python3
"""Fail-closed classifier for the Goal 1 GitHub-automation-only change set."""

from __future__ import annotations

import os
import subprocess
from pathlib import PurePosixPath

ALLOWED_EXACT = {
    ".github/workflows/ci.yml",
    ".github/workflows/goal1-watchdog.yml",
    ".github/scripts/classify_ci_scope.py",
    ".github/scripts/test_classify_ci_scope.py",
    ".github/scripts/goal1_watchdog.py",
    ".github/scripts/test_goal1_watchdog.py",
    ".github/scripts/post_ci_failure_notice.py",
    ".github/scripts/test_post_ci_failure_notice.py",
    ".github/scripts/detect_direct_main_update.py",
    ".github/scripts/test_detect_direct_main_update.py",
    "docs/automation/GOAL1_GITHUB_AUTOMATION.md",
}


def is_allowed_path(path: str) -> bool:
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
    ):
        return False
    return PurePosixPath(path).as_posix() in ALLOWED_EXACT


def is_infrastructure_only(event_name: str, branch_name: str, changed_paths: list[str]) -> bool:
    if event_name == "schedule":
        return True
    if event_name not in {"push", "pull_request"} or not changed_paths:
        return False
    allowed_branch = branch_name.startswith("infra/") or (
        event_name == "push" and branch_name == "main"
    )
    return allowed_branch and all(is_allowed_path(path) for path in changed_paths)


def changed_paths_from_git(event_name: str, base_sha: str, before_sha: str) -> list[str]:
    if event_name == "pull_request":
        if not base_sha:
            raise ValueError("missing pull request base")
        revision = f"{base_sha}...HEAD"
    elif event_name == "push":
        if not before_sha:
            raise ValueError("missing push predecessor")
        if set(before_sha) == {"0"}:
            revision = "origin/main...HEAD"
        else:
            revision = f"{before_sha}..HEAD"
    else:
        return []

    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", "-z", revision],
        check=True,
        capture_output=True,
        text=False,
        timeout=20,
    )
    return [os.fsdecode(item) for item in result.stdout.split(b"\0") if item]


def main() -> int:
    event_name = os.environ.get("EVENT_NAME", "")
    branch_name = os.environ.get("BRANCH_NAME", "")
    try:
        paths = changed_paths_from_git(
            event_name,
            os.environ.get("BASE_SHA", ""),
            os.environ.get("BEFORE_SHA", ""),
        )
        allowed = is_infrastructure_only(event_name, branch_name, paths)
    except (OSError, subprocess.SubprocessError, ValueError):
        allowed = False

    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return 2
    with open(output, "a", encoding="utf-8") as stream:
        stream.write(f"infra_only={'true' if allowed else 'false'}\n")
    print(f"CI_SCOPE={'goal1_infrastructure_only' if allowed else 'blocked_non_infrastructure_or_unknown'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
