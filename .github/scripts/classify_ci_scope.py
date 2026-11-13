#!/usr/bin/env python3
"""Fail-closed CI scope classifier for the temporary infrastructure-only freeze."""

from __future__ import annotations

import os
import subprocess
from pathlib import PurePosixPath


ALLOWED_EXACT = {
    ".circleci/config.yml",
    ".github/scripts/classify_ci_scope.py",
    ".github/scripts/diagnose_runner_pre_step.py",
    ".github/scripts/test_classify_ci_scope.py",
    ".github/scripts/test_diagnose_runner_pre_step.py",
    ".github/scripts/test_post_ci_failure_notice.py",
    ".github/workflows/ci.yml",
    ".github/workflows/docker-worker-acceptance.yml",
    ".github/workflows/self-hosted-worker-acceptance.yml",
    "requirements-infra.txt",
    "schemas/infra-task-v1.schema.json",
}
ALLOWED_PREFIXES = (
    "docs/automation/",
    "docs/governance/",
    "docs/infra/",
    "infra/control_plane/",
    "infra/systemd/",
    "infra/worker-image/",
)


def is_allowed_infrastructure_path(path: str) -> bool:
    normalized = str(PurePosixPath(path))
    if normalized in ALLOWED_EXACT:
        return True
    return any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def is_infrastructure_only(event_name: str, branch_name: str, changed_paths: list[str]) -> bool:
    if event_name == "schedule":
        return True
    if event_name not in {"push", "pull_request"}:
        return False
    if not changed_paths:
        return False

    # A merge commit delivered to main must still be classified from its actual
    # changed paths. Otherwise the default-branch push would fail the freeze
    # gate even when it contains only allowlisted infrastructure changes.
    allowed_branch = branch_name.startswith("infra/") or (
        event_name == "push" and branch_name == "main"
    )
    if not allowed_branch:
        return False
    return all(is_allowed_infrastructure_path(path) for path in changed_paths)


def changed_paths_from_git(event_name: str, base_sha: str, before_sha: str) -> list[str]:
    if event_name == "pull_request":
        if not base_sha:
            raise ValueError("missing pull request base")
        revision = f"{base_sha}...HEAD"
    elif event_name == "push":
        if not before_sha or set(before_sha) == {"0"}:
            raise ValueError("missing push predecessor")
        revision = f"{before_sha}..HEAD"
    else:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", revision],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return [line for line in result.stdout.splitlines() if line]


def main() -> int:
    event_name = os.environ.get("EVENT_NAME", "")
    branch_name = os.environ.get("BRANCH_NAME", "")
    try:
        paths = changed_paths_from_git(
            event_name,
            os.environ.get("BASE_SHA", ""),
            os.environ.get("BEFORE_SHA", ""),
        )
        infra_only = is_infrastructure_only(event_name, branch_name, paths)
    except (OSError, subprocess.SubprocessError, ValueError):
        # An unknown diff must never authorize the infrastructure-only bypass.
        infra_only = False

    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return 2
    with open(output, "a", encoding="utf-8") as stream:
        stream.write(f"infra_only={'true' if infra_only else 'false'}\n")
    print(f"CI_SCOPE={'infrastructure_only' if infra_only else 'non_infrastructure_or_unknown'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
