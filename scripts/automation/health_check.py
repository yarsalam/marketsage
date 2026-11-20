#!/usr/bin/env python3
"""Read-only, aggregate-only GitHub Actions health observer."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

WATCHDOG_NAME = "MarketSage Infrastructure Watchdog"
CI_NAME = "MarketSage Infrastructure CI"
INFRA_NAMES = {WATCHDOG_NAME, CI_NAME}
MAX_QUEUE_AGE_MINUTES = 20
MAX_RUN_AGE_MINUTES = 20
MAX_JOB_AGE_MINUTES = 12
MAX_SCHEDULE_AGE_HOURS = 8
MAX_ACTIVE_RUNS_TO_INSPECT = 10


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _age_seconds(value: str | None, now: datetime) -> float | None:
    parsed = parse_timestamp(value)
    if parsed is None:
        return None
    return max(0.0, (now - parsed).total_seconds())


def assess_health(
    runs: list[dict],
    jobs_by_run: dict[str, list[dict]],
    current_run_id: str,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    relevant = [
        run for run in runs
        if run.get("name") in INFRA_NAMES
        and str(run.get("id", "")) != str(current_run_id)
    ]

    stale_queued = 0
    stale_running = 0
    stale_jobs = 0

    active = sorted(
        (run for run in relevant if run.get("status") == "in_progress"),
        key=lambda run: run.get("created_at", ""),
        reverse=True,
    )[:MAX_ACTIVE_RUNS_TO_INSPECT]

    for run in relevant:
        status = run.get("status")
        if status == "queued":
            age = _age_seconds(run.get("created_at"), now)
            if age is not None and age > MAX_QUEUE_AGE_MINUTES * 60:
                stale_queued += 1
        elif status == "in_progress":
            age = _age_seconds(run.get("run_started_at") or run.get("created_at"), now)
            if age is not None and age > MAX_RUN_AGE_MINUTES * 60:
                stale_running += 1

    for run in active:
        run_id = str(run.get("id", ""))
        for job in jobs_by_run.get(run_id, []):
            if job.get("status") != "in_progress":
                continue
            age = _age_seconds(job.get("started_at"), now)
            if age is not None and age > MAX_JOB_AGE_MINUTES * 60:
                stale_jobs += 1

    successful_schedules = [
        run for run in relevant
        if run.get("name") == WATCHDOG_NAME
        and run.get("event") == "schedule"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
    ]
    last_schedule_age_hours = None
    if successful_schedules:
        latest = max(
            successful_schedules,
            key=lambda run: run.get("run_started_at") or run.get("created_at") or "",
        )
        age = _age_seconds(latest.get("run_started_at") or latest.get("created_at"), now)
        if age is not None:
            last_schedule_age_hours = round(age / 3600, 2)
            schedule_state = (
                "stale" if age > MAX_SCHEDULE_AGE_HOURS * 3600 else "fresh"
            )
        else:
            schedule_state = "unknown"
    else:
        schedule_state = "bootstrap_pending"

    degraded = (
        stale_queued > 0
        or stale_running > 0
        or stale_jobs > 0
        or schedule_state in {"stale", "unknown"}
    )
    if degraded:
        status = "degraded"
    elif schedule_state == "bootstrap_pending":
        status = "bootstrap_pending"
    else:
        status = "healthy"

    return {
        "status": status,
        "inspected_infrastructure_runs": len(relevant),
        "stale_queued_runs": stale_queued,
        "stale_running_runs": stale_running,
        "stale_running_jobs": stale_jobs,
        "schedule_freshness": schedule_state,
        "last_successful_schedule_age_hours": last_schedule_age_hours,
    }


def github_get_json(url: str, token: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "marketsage-infra-health-check",
        },
        method="GET",
    )
    for attempt in range(2):
        try:
            with urlopen(request, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            if attempt == 1:
                raise RuntimeError("github_api_unavailable") from None
            time.sleep(1)
    raise RuntimeError("github_api_unavailable")


def main() -> int:
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    current_run_id = os.environ.get("GITHUB_RUN_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) or not token or not current_run_id:
        print(json.dumps({"status": "error", "reason": "missing_context"}))
        return 2

    base_url = f"https://api.github.com/repos/{repo}"
    try:
        payload = github_get_json(f"{base_url}/actions/runs?per_page=100", token)
        runs = payload.get("workflow_runs", [])
        if not isinstance(runs, list):
            raise RuntimeError("invalid_api_response")

        active_runs = sorted(
            (
                run for run in runs
                if run.get("name") in INFRA_NAMES
                and run.get("status") == "in_progress"
                and str(run.get("id", "")) != current_run_id
            ),
            key=lambda run: run.get("created_at", ""),
            reverse=True,
        )[:MAX_ACTIVE_RUNS_TO_INSPECT]

        jobs_by_run: dict[str, list[dict]] = {}
        for run in active_runs:
            run_id = str(run.get("id", ""))
            jobs_payload = github_get_json(
                f"{base_url}/actions/runs/{run_id}/jobs?per_page=100", token
            )
            jobs = jobs_payload.get("jobs", [])
            jobs_by_run[run_id] = jobs if isinstance(jobs, list) else []

        report = assess_health(
            runs,
            jobs_by_run,
            current_run_id,
            datetime.now(timezone.utc),
        )
    except Exception:
        print(json.dumps({"status": "error", "reason": "github_api_unavailable"}))
        return 2

    print(json.dumps(report, sort_keys=True))
    return 1 if report["status"] == "degraded" else 0


if __name__ == "__main__":
    sys.exit(main())
