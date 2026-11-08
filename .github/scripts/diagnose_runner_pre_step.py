#!/usr/bin/env python3
"""Read-only, sanitized classifier for GitHub Actions Runner pre-step failures.

Reads only recent runner diagnostic logs. It never emits log lines, filenames,
local paths, environment values, tokens, URLs, or host identifiers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

_MAX_FILES = 12
_MAX_BYTES_PER_FILE = 1024 * 1024

_PATTERNS = {
    "authentication": re.compile(
        r"(authentication failed|unauthorized|http(?: status)?[=: ]+401|bad credentials|invalid runner token)",
        re.IGNORECASE,
    ),
    "network_connectivity": re.compile(
        r"(connection timed out|timed out|connection refused|connection reset|"
        r"temporary failure in name resolution|proxy error|no route to host|"
        r"could not resolve host|failed to connect)",
        re.IGNORECASE,
    ),
    "filesystem_permission": re.compile(
        r"(permission denied|access is denied|operation not permitted|read-only file system)",
        re.IGNORECASE,
    ),
    "resource_exhaustion": re.compile(
        r"(no space left on device|disk quota exceeded|too many open files|"
        r"cannot allocate memory|not enough memory)",
        re.IGNORECASE,
    ),
    "session_conflict": re.compile(
        r"(already has an active session|another runner instance|session.*already exists)",
        re.IGNORECASE,
    ),
    "runner_configuration": re.compile(
        r"(runner is not configured|not configured|configuration file.*not found|"
        r"listener.*not configured|remove this runner)",
        re.IGNORECASE,
    ),
    "process_start": re.compile(
        r"(failed to start process|failed to spawn|fork/exec|exec format error)",
        re.IGNORECASE,
    ),
}

_VERSION = re.compile(
    r"Runner(?:\.Listener)?(?:\s+version)?\s*[:=]\s*(\d+\.\d+\.\d+)",
    re.IGNORECASE,
)


def _recent_logs(diag_dir: Path) -> list[Path]:
    candidates = [item for item in diag_dir.glob("*.log") if item.is_file()]
    return sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)[:_MAX_FILES]


def inspect_diagnostics(runner_dir: str | Path) -> dict[str, object]:
    """Return categories and version only; never return source log text or paths."""
    root = Path(runner_dir).expanduser()
    diag_dir = root / "_diag"
    if not diag_dir.is_dir():
        return {
            "status": "insufficient_evidence",
            "reason_code": "diagnostic_directory_unavailable",
            "diagnostic_files_scanned": 0,
            "diagnostic_read_errors": 0,
            "runner_version": None,
            "failure_categories": {},
        }

    try:
        files = _recent_logs(diag_dir)
    except OSError:
        files = []
    counts = {key: 0 for key in _PATTERNS}
    read_errors = 0
    runner_version = None

    for path in files:
        try:
            with path.open("rb") as stream:
                stream.seek(0, 2)
                size = stream.tell()
                stream.seek(max(0, size - _MAX_BYTES_PER_FILE))
                content = stream.read(_MAX_BYTES_PER_FILE).decode("utf-8", errors="replace")
        except OSError:
            read_errors += 1
            continue

        if runner_version is None:
            version_match = _VERSION.search(content)
            if version_match:
                runner_version = version_match.group(1)
        for category, pattern in _PATTERNS.items():
            counts[category] += len(pattern.findall(content))

    observed = {key: value for key, value in counts.items() if value}
    status = "ok" if files and read_errors < len(files) else "insufficient_evidence"
    return {
        "status": status,
        "reason_code": "classified" if observed else "no_known_signature_found",
        "diagnostic_files_scanned": len(files) - read_errors,
        "diagnostic_read_errors": read_errors,
        "runner_version": runner_version,
        "failure_categories": observed,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sanitized read-only Runner diagnostics")
    parser.add_argument("--runner-dir", required=True, help="Runner installation directory")
    args = parser.parse_args(argv)
    result = inspect_diagnostics(args.runner_dir)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
