#!/usr/bin/env python3
"""Read-only, bounded health assessment for MarketSage Goal 1 automation."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any

API_ATTEMPTS = 3
API_TIMEOUT_SECONDS = 8
MAX_RUN_PAGES = 5
PAGE_SIZE = 100
RECENT_FAILURE_WINDOW = timedelta(hours=24)
QUEUED_LIMIT = timedelta(minutes=15)
RUNNING_LIMIT = timedelta(minutes=30)
HEARTBEAT_LIMIT = timedelta(minutes=75)
WATCHED_WORKFLOWS = {"MarketSage CI", "MarketSage Goal 1 Watchdog"}
BAD_CONCLUSIONS = {"failure", "timed_out", "startup_failure", "action_required"}
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class ApiReadError(RuntimeError):
    """Raised when a bounded, read-only GitHub API request cannot be completed."""


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _age(now: datetime, timestamp: datetime | None) -> timedelta | None:
    if timestamp is None:
        return None
    return max(now - timestamp, timedelta(0))


def _is_relevant_branch(branch: Any) -> bool:
    return (
        isinstance(branch, str)
        and (
            branch == "main"
            or branch.startswith("infra/")
            or branch.startswith("ci/")
        )
    )


def evaluate_runs(
    runs: list[dict[str, Any]],
    *,
    current_run_id: str | int | None = None,
    now: datetime | None = None,
    history_truncated: bool = False,
    repository: str | None = None,
) -> dict[str, Any]:
    """Return aggregate metrics only; never return branch names, SHAs, or run IDs."""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)

    relevant: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        if run.get("name") not in WATCHED_WORKFLOWS:
            continue
        if repository is not None:
            head_repository = run.get("head_repository")
            if (
                not isinstance(head_repository, dict)
                or head_repository.get("full_name") != repository
            ):
                continue
        if not _is_relevant_branch(run.get("head_branch")):
            continue
        if current_run_id is not None and str(run.get("id")) == str(current_run_id):
            continue
        relevant.append(run)

    stale_queued = 0
    stale_running = 0
    recent_failures = 0
    recent_cancelled = 0
    completed_by_stream: dict[tuple[str, str, str], list[dict[str, Any]]] = {}

    for run in relevant:
        status = run.get("status")
        created = parse_timestamp(run.get("created_at"))
        if status == "queued":
            age = _age(current, created)
            if age is not None and age > QUEUED_LIMIT:
                stale_queued += 1
        elif status == "in_progress":
            started = parse_timestamp(run.get("run_started_at")) or created
            age = _age(current, started)
            if age is not None and age > RUNNING_LIMIT:
                stale_running += 1

        if status == "completed":
            updated = parse_timestamp(run.get("updated_at")) or created
            age = _age(current, updated)
            conclusion = run.get("conclusion")
            if age is not None and age <= RECENT_FAILURE_WINDOW and conclusion == "cancelled":
                recent_cancelled += 1

            head_repository = run.get("head_repository")
            repository_name = (
                head_repository.get("full_name")
                if isinstance(head_repository, dict)
                else ""
            )
            stream_key = (
                str(run.get("name") or ""),
                str(run.get("head_branch") or ""),
                str(repository_name or ""),
            )
            completed_by_stream.setdefault(stream_key, []).append(run)

    for stream_runs in completed_by_stream.values():
        def completion_order(run: dict[str, Any]) -> tuple[datetime, int]:
            timestamp = (
                parse_timestamp(run.get("updated_at"))
                or parse_timestamp(run.get("created_at"))
                or datetime.min.replace(tzinfo=timezone.utc)
            )
            raw_id = str(run.get("id", ""))
            numeric_id = int(raw_id) if raw_id.isdigit() else -1
            return timestamp, numeric_id

        latest_success_order = max(
            (
                completion_order(run)
                for run in stream_runs
                if run.get("conclusion") == "success"
            ),
            default=None,
        )
        unresolved_failures = [
            run
            for run in stream_runs
            if run.get("conclusion") in BAD_CONCLUSIONS
            and (
                latest_success_order is None
                or completion_order(run) > latest_success_order
            )
        ]
        if unresolved_failures:
            latest_failure = max(unresolved_failures, key=completion_order)
            updated = (
                parse_timestamp(latest_failure.get("updated_at"))
                or parse_timestamp(latest_failure.get("created_at"))
            )
            age = _age(current, updated)
            if age is not None and age <= RECENT_FAILURE_WINDOW:
                recent_failures += 1

    successful_heartbeats = [
        run
        for run in relevant
        if run.get("name") == "MarketSage Goal 1 Watchdog"
        and run.get("event") == "schedule"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    latest_heartbeat = None
    if successful_heartbeats:
        latest_heartbeat = max(
            successful_heartbeats,
            key=lambda run: parse_timestamp(run.get("updated_at"))
            or parse_timestamp(run.get("created_at"))
            or datetime.min.replace(tzinfo=timezone.utc),
        )

    heartbeat_time = None
    if latest_heartbeat is not None:
        heartbeat_time = (
            parse_timestamp(latest_heartbeat.get("updated_at"))
            or parse_timestamp(latest_heartbeat.get("created_at"))
        )
    heartbeat_age = _age(current, heartbeat_time)
    heartbeat_stale = heartbeat_age is not None and heartbeat_age > HEARTBEAT_LIMIT
    heartbeat_observed = heartbeat_age is not None
    heartbeat_missing = not heartbeat_observed

    degraded = bool(
        stale_queued
        or stale_running
        or recent_failures
        or heartbeat_stale
        or heartbeat_missing
        or history_truncated
    )
    status = "DEGRADED" if degraded else "HEALTHY"

    heartbeat_state = (
        "stale"
        if heartbeat_stale
        else "within_window"
        if heartbeat_observed
        else "not_yet_observed"
    )

    return {
        "status": status,
        "inspected_runs": len(relevant),
        "recent_failures": recent_failures,
        "stale_queued": stale_queued,
        "stale_running": stale_running,
        "recent_cancelled": recent_cancelled,
        "heartbeat_state": heartbeat_state,
        "heartbeat_age_minutes": (
            int(heartbeat_age.total_seconds() // 60)
            if heartbeat_age is not None
            else None
        ),
        "history_truncated": bool(history_truncated),
    }


def build_summary(metrics: dict[str, Any]) -> str:
    status = metrics["status"]
    heartbeat = {
        "within_window": "A successful scheduled heartbeat was observed within the monitoring window.",
        "stale": "The last successful scheduled heartbeat is older than the allowed window.",
        "not_yet_observed": "No successful scheduled heartbeat is present in the recent monitoring window; health remains degraded until a scheduled success is observed.",
    }.get(metrics["heartbeat_state"], "Heartbeat state is unknown.")

    lines = [
        "# MarketSage Goal 1 health",
        "",
        f"Status: **{status}**",
        "",
        f"- Relevant workflow runs inspected: {metrics['inspected_runs']}",
        f"- Unrecovered latest failed or timed-out workflow results (24h): {metrics['recent_failures']}",
        f"- Queued runs older than 15 minutes: {metrics['stale_queued']}",
        f"- Running jobs older than 30 minutes: {metrics['stale_running']}",
        f"- Cancelled or superseded runs (24h; not counted as failures): {metrics['recent_cancelled']}",
        f"- Scheduled heartbeat: {heartbeat}",
        f"- Workflow history truncated at the safety limit: {'yes' if metrics['history_truncated'] else 'no'}",
        "",
    ]
    if status == "DEGRADED" and metrics["heartbeat_state"] == "not_yet_observed":
        lines.extend(
            [
                "Human handoff: no successful scheduled heartbeat is present in the recent window. "
                "Verify that the Watchdog is enabled on the default branch and inspect its latest run; "
                "do not treat this state as healthy.",
                "",
            ]
        )
    elif status == "DEGRADED":
        lines.extend(
            [
                "Human handoff: inspect the latest relevant run in the GitHub Actions overview. "
                "Do not blindly rerun a workflow; identify the failed step and retry only after review.",
                "",
            ]
        )
    else:
        lines.extend(["No operator action is indicated by this read-only check.", ""])
    lines.append(
        "This report contains aggregate status only. It excludes run identifiers, commit hashes, "
        "branch names, logs, artifacts, raw market data, prices, private paths, credentials, and tokens."
    )
    return "\n".join(lines)


def _request_runs_page(
    api_url: str,
    repository: str,
    token: str,
    page: int,
) -> dict[str, Any]:
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ApiReadError("repository_invalid")
    if not token:
        raise ApiReadError("token_missing")
    parsed = urllib.parse.urlparse(api_url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path:
        raise ApiReadError("api_url_invalid")

    cutoff = datetime.now(timezone.utc) - RECENT_FAILURE_WINDOW
    cutoff_text = cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    query = urllib.parse.urlencode(
        {
            "per_page": PAGE_SIZE,
            "page": page,
            "created": f"{cutoff_text}..*",
        }
    )
    url = f"{api_url.rstrip('/')}/repos/{repository}/actions/runs?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "MarketSage-goal1-watchdog/1.0",
        },
    )

    for attempt in range(API_ATTEMPTS):
        retryable = False
        try:
            with urllib.request.urlopen(request, timeout=API_TIMEOUT_SECONDS) as response:
                if response.status != 200:
                    raise ApiReadError("api_non_200")
                payload = json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("workflow_runs"), list):
                raise ApiReadError("api_response_invalid")
            return payload
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if not retryable:
                raise ApiReadError("api_permission_or_request_error") from None
        except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            retryable = True

        if not retryable:
            break
        if attempt + 1 < API_ATTEMPTS:
            time.sleep(2 ** attempt)

    raise ApiReadError("api_unavailable_after_bounded_retries")


def _request_runs(
    api_url: str,
    repository: str,
    token: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Read at most five pages; report truncation instead of silently trusting partial history."""
    collected: list[dict[str, Any]] = []
    total_count: int | None = None

    for page in range(1, MAX_RUN_PAGES + 1):
        payload = _request_runs_page(api_url, repository, token, page)
        page_runs = [
            run for run in payload["workflow_runs"] if isinstance(run, dict)
        ]
        collected.extend(page_runs)
        raw_total = payload.get("total_count")
        if isinstance(raw_total, int) and raw_total >= 0:
            total_count = raw_total

        if len(page_runs) < PAGE_SIZE:
            return collected, False
        if total_count is not None and len(collected) >= total_count:
            return collected, False

    truncated = total_count is None or len(collected) < total_count
    return collected, truncated


def _write_summary(summary: str) -> None:
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(summary + "\n")
    else:
        print(summary)


def main() -> int:
    try:
        runs, truncated = _request_runs(
            os.environ.get("GITHUB_API_URL", ""),
            os.environ.get("GITHUB_REPOSITORY", ""),
            os.environ.get("GH_TOKEN", ""),
        )
        metrics = evaluate_runs(
            runs,
            current_run_id=os.environ.get("GITHUB_RUN_ID"),
            history_truncated=truncated,
            repository=os.environ.get("GITHUB_REPOSITORY"),
        )
        _write_summary(build_summary(metrics))
        return 1 if metrics["status"] == "DEGRADED" else 0
    except ApiReadError:
        _write_summary(
            "# MarketSage Goal 1 health\n\n"
            "Status: **UNKNOWN**\n\n"
            "The read-only GitHub Actions API check could not complete after bounded retries. "
            "Review this Watchdog run and verify the Actions API permission and service status.\n\n"
            "No raw response, request details, credentials, or tokens are included."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
