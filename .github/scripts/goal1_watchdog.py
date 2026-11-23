#!/usr/bin/env python3
"""Read-only GitHub Actions health assessment with sanitized issue handoff."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

_MARKER = "<!-- marketsage-goal1-watchdog-state -->"
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_FAILURES = {"failure", "timed_out", "startup_failure", "action_required"}


class WatchdogError(RuntimeError):
    pass


def parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("missing timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp has no timezone")
    return parsed.astimezone(timezone.utc)


def trusted_run(run: dict[str, Any]) -> bool:
    event = run.get("event")
    branch = run.get("head_branch", "")
    return event == "schedule" or branch == "main" or (
        isinstance(branch, str) and branch.startswith("infra/")
    )


def assess_runs(runs: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    if not isinstance(runs, list):
        raise ValueError("invalid workflow run collection")
    reasons: set[str] = set()
    queued = 0
    running = 0
    trusted: list[dict[str, Any]] = []
    schedules: list[dict[str, Any]] = []

    for run in runs:
        if not isinstance(run, dict) or not trusted_run(run):
            continue
        trusted.append(run)
        event = run.get("event")
        status = run.get("status")
        try:
            created = parse_time(run.get("created_at", ""))
        except (TypeError, ValueError):
            reasons.add("run_timestamp_unverifiable")
            continue

        if event == "schedule" and status == "completed":
            schedules.append(run)

        if status == "queued":
            queued += 1
            if now - created > timedelta(minutes=20):
                reasons.add("queued_run_overdue")
        elif status == "in_progress":
            running += 1
            try:
                started = parse_time(run.get("run_started_at") or run.get("created_at", ""))
            except (TypeError, ValueError):
                reasons.add("run_timestamp_unverifiable")
            else:
                if now - started > timedelta(minutes=35):
                    reasons.add("running_run_overdue")

    if not runs:
        reasons.add("no_ci_runs")
    if not schedules:
        reasons.add("schedule_not_observed")
    else:
        try:
            latest_schedule = max(schedules, key=lambda item: parse_time(item["created_at"]))
            schedule_age = now - parse_time(latest_schedule["created_at"])
            if schedule_age > timedelta(hours=26):
                reasons.add("schedule_stale")
        except (KeyError, TypeError, ValueError):
            reasons.add("schedule_timestamp_unverifiable")

    completed = []
    for run in trusted:
        if run.get("status") == "completed":
            try:
                completed.append((parse_time(run.get("created_at", "")), run))
            except (TypeError, ValueError):
                reasons.add("run_timestamp_unverifiable")
    if completed:
        latest = max(completed, key=lambda item: item[0])[1]
        if latest.get("conclusion") in _FAILURES:
            reasons.add("latest_trusted_ci_failed")

    safe_reasons = sorted(reasons)
    return {
        "state": "degraded" if safe_reasons else "healthy",
        "reasons": safe_reasons,
        "queued": queued,
        "running": running,
    }


def build_comment(assessment: dict[str, Any], repository: str) -> str:
    if not _REPOSITORY.fullmatch(repository):
        raise ValueError("invalid repository")
    state = assessment.get("state")
    if state not in {"healthy", "degraded"}:
        raise ValueError("invalid health state")
    reasons = assessment.get("reasons", [])
    if not isinstance(reasons, list) or any(
        not isinstance(item, str) or not re.fullmatch(r"[a-z0-9_]{1,64}", item)
        for item in reasons
    ):
        raise ValueError("invalid reason codes")
    reason_text = ", ".join(sorted(set(reasons))) if reasons else "none"
    return (
        f"{_MARKER}\n"
        "### MarketSage Goal 1 automation health\n\n"
        f"State: {state}\n"
        f"Queued runs: {int(assessment.get('queued', 0))}\n"
        f"Running runs: {int(assessment.get('running', 0))}\n"
        f"Reasons: {reason_text}\n\n"
        f"Actions overview: https://github.com/{repository}/actions\n\n"
        "This report uses aggregate workflow metadata only. It contains no run IDs, "
        "commit identifiers, job logs, artifacts, raw market data, prices, local "
        "paths, credentials, or secret values. The observer does not cancel, rerun, "
        "or restart jobs."
    )


def latest_state(comments: list[dict[str, Any]]) -> tuple[str, tuple[str, ...]] | None:
    for item in reversed(comments):
        body = item.get("body", "") if isinstance(item, dict) else ""
        if _MARKER not in body:
            continue
        state_match = re.search(r"(?m)^State: (healthy|degraded)$", body)
        reasons_match = re.search(r"(?m)^Reasons: (.*)$", body)
        if state_match and reasons_match:
            reasons = tuple(
                sorted(code for code in reasons_match.group(1).split(", ") if code and code != "none")
            )
            return state_match.group(1), reasons
    return None


def request_json(url: str, token: str) -> Any:
    for attempt in range(2):
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "MarketSage-Goal1-Watchdog/1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise WatchdogError("github_api_rejected")
                return json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if attempt == 0 and 500 <= exc.code < 600:
                time.sleep(2)
                continue
            raise WatchdogError("github_api_rejected") from exc
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeDecodeError) as exc:
            if attempt == 0:
                time.sleep(2)
                continue
            raise WatchdogError("github_api_unavailable") from exc
    raise WatchdogError("github_api_unavailable")


def post_comment(api_url: str, repository: str, issue_number: str, token: str, body: str) -> None:
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/repos/{repository}/issues/{issue_number}/comments",
        data=payload,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "MarketSage-Goal1-Watchdog/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            if response.status not in (200, 201):
                raise WatchdogError("notice_delivery_failed")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise WatchdogError("notice_delivery_failed") from exc


def main() -> int:
    env = os.environ
    api_url = env.get("API_URL", "")
    repository = env.get("REPOSITORY", "")
    token = env.get("GH_TOKEN", "")
    issue_number = env.get("ISSUE_NUMBER", "49")
    parsed = urllib.parse.urlparse(api_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.path
        or not _REPOSITORY.fullmatch(repository)
        or not issue_number.isdigit()
        or not token
    ):
        print("GOAL1_HEALTH=unknown REASON=watchdog_configuration_invalid")
        return 2

    try:
        run_data = request_json(
            f"{api_url.rstrip('/')}/repos/{repository}/actions/workflows/ci.yml/runs?per_page=100",
            token,
        )
        runs = run_data.get("workflow_runs") if isinstance(run_data, dict) else None
        if not isinstance(runs, list):
            raise WatchdogError("workflow_run_response_invalid")
        assessment = assess_runs(runs, datetime.now(timezone.utc))
        comments_data = request_json(
            f"{api_url.rstrip('/')}/repos/{repository}/issues/{issue_number}/comments?per_page=100",
            token,
        )
        if not isinstance(comments_data, list):
            raise WatchdogError("issue_comment_response_invalid")
        current = (assessment["state"], tuple(assessment["reasons"]))
        if latest_state(comments_data) != current:
            post_comment(
                api_url,
                repository,
                issue_number,
                token,
                build_comment(assessment, repository),
            )
        reasons = ",".join(assessment["reasons"]) if assessment["reasons"] else "none"
        print(
            f"GOAL1_HEALTH={assessment['state']} "
            f"QUEUED={assessment['queued']} RUNNING={assessment['running']} "
            f"REASONS={reasons}"
        )
        return 0 if assessment["state"] == "healthy" else 1
    except WatchdogError:
        print("GOAL1_HEALTH=unknown REASON=watchdog_api_unavailable")
        return 2
    except Exception:
        print("GOAL1_HEALTH=unknown REASON=watchdog_internal_error")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
