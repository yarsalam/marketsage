#!/usr/bin/env python3
"""Emit aggregate-only diagnostics for private staged TSETMC input inventories.

The tool reads existing local pipeline outputs, verifies the inventory hash
against each run manifest, and never prints identifiers, filenames, paths,
raw error messages, prices, or source rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SAFE_INPUT_KINDS = {
    "daily_history_path",
    "adjusted_chart_path",
    "adjustment_events_path",
    "share_change_events_path",
    "identity_crosswalk",
}
SAFE_ERROR_CODES = {
    "ENCODING_ERROR",
    "MALFORMED_JSON",
    "MISSING_FILE",
    "PERMISSION_ERROR",
    "INVALID_PATH_TYPE",
    "MALFORMED_CSV",
    "OTHER_READ_ERROR",
}


class DiagnosticError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_error(message: str) -> str:
    """Map untrusted local error text to a closed, non-identifying code set."""
    value = str(message or "")
    if "UnicodeDecodeError" in value:
        return "ENCODING_ERROR"
    if "JSONDecodeError" in value:
        return "MALFORMED_JSON"
    if "FileNotFoundError" in value or "input file not found" in value:
        return "MISSING_FILE"
    if "PermissionError" in value:
        return "PERMISSION_ERROR"
    if "IsADirectoryError" in value or "NotADirectoryError" in value:
        return "INVALID_PATH_TYPE"
    if "csv.Error" in value:
        return "MALFORMED_CSV"
    return "OTHER_READ_ERROR"


def _verified_inventory(run_dir: Path) -> list[dict[str, str]]:
    if run_dir.is_symlink() or not run_dir.is_dir():
        raise DiagnosticError("unsafe_run_directory")
    manifest_path = run_dir / "run_manifest.json"
    inventory_path = run_dir / "input_inventory.csv"
    if manifest_path.is_symlink() or inventory_path.is_symlink():
        raise DiagnosticError("symlink_in_run_output")
    if not manifest_path.is_file() or not inventory_path.is_file():
        raise DiagnosticError("required_diagnostic_file_missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise DiagnosticError("run_manifest_unreadable") from None
    files = manifest.get("output_files")
    hashes = manifest.get("output_hashes_sha256")
    if not isinstance(files, list) or not isinstance(hashes, dict):
        raise DiagnosticError("run_manifest_invalid")
    if "input_inventory.csv" not in files or not re.fullmatch(
        r"[0-9a-f]{64}", str(hashes.get("input_inventory.csv", ""))
    ):
        raise DiagnosticError("inventory_hash_missing")
    if sha256_file(inventory_path) != hashes["input_inventory.csv"]:
        raise DiagnosticError("inventory_hash_mismatch")
    try:
        with inventory_path.open("r", encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    except (OSError, UnicodeDecodeError, csv.Error):
        raise DiagnosticError("inventory_unreadable") from None


def summarize(output_root: Path) -> dict[str, Any]:
    if output_root.is_symlink() or not output_root.is_dir():
        raise DiagnosticError("output_root_missing_or_unsafe")
    category_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    run_count = inventory_rows = error_rows = 0
    run_dirs = sorted(
        child for child in output_root.iterdir()
        if child.name.startswith("run_") and child.is_dir() and not child.is_symlink()
    )
    if not run_dirs:
        raise DiagnosticError("no_pipeline_runs_found")
    for run_dir in run_dirs:
        rows = _verified_inventory(run_dir)
        run_count += 1
        for row in rows:
            inventory_rows += 1
            if str(row.get("status", "")) != "error":
                continue
            error_rows += 1
            kind = str(row.get("input_kind", ""))
            safe_kind = kind if kind in SAFE_INPUT_KINDS else "OTHER_INPUT_KIND"
            kind_counts[safe_kind] += 1
            category_counts[classify_error(str(row.get("error", "")))] += 1
    return {
        "status": "COMPLETED_SANITIZED_DIAGNOSTICS",
        "pipeline_run_count": run_count,
        "inventory_rows_examined": inventory_rows,
        "input_error_count": error_rows,
        "error_category_counts": dict(sorted(category_counts.items())),
        "error_input_kind_counts": dict(sorted(kind_counts.items())),
        "raw_rows_emitted": False,
        "identifiers_emitted": False,
        "paths_emitted": False,
        "error_messages_emitted": False,
        "network_requests_made": False,
        "source_files_modified": False,
        "scoring_enabled": False,
        "backtest_run": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        default="/srv/marketsage/output/tsetmc-integrated-acceptance",
    )
    args = parser.parse_args(argv)
    try:
        result = summarize(Path(args.output_root).expanduser())
    except DiagnosticError as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "reason_code": str(exc),
            "raw_rows_emitted": False,
            "network_requests_made": False,
        }, sort_keys=True), file=sys.stderr)
        return 3
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
