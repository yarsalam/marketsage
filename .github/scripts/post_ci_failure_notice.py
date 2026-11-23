#!/usr/bin/env python3
"""Post a sanitized GitHub Actions failure notice to the MarketSage infra issue."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any


_JOB_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_DIGITS = re.compile(r"^[0-9]+$")


def failed_job_names(needs: dict[str, Any]) -> list[str]:
    if not isinstance(needs, dict):
        raise ValueError("needs must be an object")
    names = []
    for name, result in needs.items():
        if (
            isinstance(name, str)
            and _JOB_NAME.fullmatch(name)
            and isinstance(result, dict)
            and result.get("result") == "failure"
        ):
            names.append(name)
    return sorted(names)


def build_comment(
    *,
    needs: dict[str, Any],
    server_url: str,
    repository: str,
    run_id: str,
    run_number: str,
    run_attempt: str,
) -> str | None:
    """Build a minimal notice; never serialize run IDs, logs, outputs, or exceptions."""
    failures = failed_job_names(needs)
    if not failures:
        return None
    if not _REPOSITORY.fullmatch(repository):
        raise ValueError("invalid repository identifier")
    if not all(_DIGITS.fullmatch(value) for value in (run_id, run_number, run_attempt)):
        raise ValueError("invalid workflow run identifier")

    parsed = urllib.parse.urlparse(server_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path:
        raise ValueError("invalid GitHub server URL")

    jobs = ", ".join(chr(96) + name + chr(96) for name in failures)
    actions_url = f"{server_url.rstrip('/')}/{repository}/actions"
    return (
        "### Automated CI failure notice\n\n"
        f"Failed jobs: {jobs}\n"
        f"Actions overview: {actions_url}\n\n"
        "This notice contains aggregate job names only. It does not include run or "
        "commit identifiers, logs, artifacts, raw market data, prices, credentials, "
        "local paths, or unfiltered exception text."
    )


def post_comment(*, api_url: str, token: str, repository: str, body: str) -> None:
    parsed = urllib.parse.urlparse(api_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path:
        raise ValueError("invalid GitHub API URL")
    if not token or not _REPOSITORY.fullmatch(repository):
        raise ValueError("missing token or invalid repository")

    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/repos/{repository}/issues/49/comments",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status not in (200, 201):
            raise RuntimeError("GitHub did not accept the comment")


def main() -> int:
    try:
        needs = json.loads(os.environ.get("NEEDS_JSON", "{}"))
        body = build_comment(
            needs=needs,
            server_url=os.environ["SERVER_URL"],
            repository=os.environ["REPOSITORY"],
            run_id=os.environ["RUN_ID"],
            run_number=os.environ["RUN_NUMBER"],
            run_attempt=os.environ["RUN_ATTEMPT"],
        )
        if body is None:
            print("No failed CI jobs to report.")
            return 0

        if os.environ.get("DRY_RUN") == "1":
            print("Sanitized failure notice payload validated.")
            return 0

        post_comment(
            api_url=os.environ["API_URL"],
            token=os.environ["GH_TOKEN"],
            repository=os.environ["REPOSITORY"],
            body=body,
        )
        print("Sanitized failure notice posted to infrastructure issue.")
        return 0
    except Exception:
        print("Sanitized failure notice could not be delivered.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
