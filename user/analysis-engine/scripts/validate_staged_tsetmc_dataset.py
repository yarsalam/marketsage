#!/usr/bin/env python3
"""Offline, read-only verification of the owner-staged MarketSage TSETMC corpus.

The only write performed is a sanitized JSON report under /srv/marketsage/output.
No network access, dependency installation, data mutation, candidate approval,
backtest approval, scoring, or trading is performed.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path, PurePosixPath

EXPECTED_SOURCE_FILES = 8801
EXPECTED_REPORT_ID = "marketsage_tsetmc_history_pipeline"
MAX_FILES = 9000
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024


def fail(message: str) -> None:
    raise RuntimeError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def safe_walk(root: Path) -> tuple[set[str], int, int]:
    files: set[str] = set()
    directories = 0
    total_bytes = 0
    stack = [root]

    while stack:
        directory = stack.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                info = entry.stat(follow_symlinks=False)
                mode = info.st_mode
                relative = Path(entry.path).relative_to(root).as_posix()

                require(not stat.S_ISLNK(mode), f"Symlink found in staged dataset: {relative}")

                if stat.S_ISDIR(mode):
                    directories += 1
                    stack.append(Path(entry.path))
                elif stat.S_ISREG(mode):
                    files.add(relative)
                    total_bytes += info.st_size
                    require(len(files) <= MAX_FILES, "Dataset exceeds bounded file-count limit")
                    require(total_bytes <= MAX_TOTAL_BYTES, "Dataset exceeds bounded size limit")
                else:
                    fail(f"Unsupported filesystem object in staged dataset: {relative}")

    return files, directories, total_bytes


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    require(path.is_file() and not path.is_symlink(), f"Required JSON missing or unsafe: {path.name}")
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    require(isinstance(value, dict), f"Expected JSON object: {path.name}")
    return value


def main() -> int:
    root = Path(os.environ.get("MARKETSAGE_DATASET_ROOT", "/srv/marketsage/data/tsetmc_history_20261022"))
    output = Path(os.environ.get("MARKETSAGE_OUTPUT_DIR", "/srv/marketsage/output"))
    run_id = os.environ.get("MARKETSAGE_RUN_ID", "manual")
    trigger_sha = os.environ.get("MARKETSAGE_TRIGGER_SHA", "unknown")
    trigger_actor = os.environ.get("MARKETSAGE_TRIGGER_ACTOR", "unknown")

    require(root.is_dir() and not root.is_symlink(), "Staged dataset root missing or unsafe")
    require(os.access(root, os.R_OK | os.X_OK), "Runner cannot read staged dataset")
    require(not os.access(root, os.W_OK), "Runner must not be able to write to staged dataset")
    require(output.is_dir() and os.access(output, os.W_OK | os.X_OK), "Separate Runner output directory is not writable")

    required_paths = [
        "SHA256SUMS",
        "STAGING_README.txt",
        "pipeline_metadata/pipeline_manifest.json",
        "discovery/instrument_universe.csv",
        "reconciliation_v2/corpus_manifest.json",
        "reconciliation_v2/instrument_details.jsonl",
        "acceptance/data_quality_report.json",
    ]
    for relative in required_paths:
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"Required staged file missing or unsafe: {relative}")

    # Verify the complete staged tree is regular files/directories only.
    actual_files, directory_count, total_bytes = safe_walk(root)

    # The checksum manifest covers source files only; two root-level staging documents
    # are intentionally outside that manifest.
    checksum_path = root / "SHA256SUMS"
    expected: dict[str, str] = {}
    with checksum_path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            line = line.rstrip("\n")
            require(len(line) > 66 and line[64:66] == "  ", f"Malformed checksum line {line_number}")
            digest, relative = line[:64].lower(), line[66:]
            require(all(ch in "0123456789abcdef" for ch in digest), f"Invalid digest at line {line_number}")
            parsed = PurePosixPath(relative)
            require(not parsed.is_absolute() and ".." not in parsed.parts and "\\" not in relative,
                    f"Unsafe checksum path at line {line_number}")
            require(relative not in expected, f"Duplicate checksum path: {relative}")
            expected[relative] = digest

    require(len(expected) == EXPECTED_SOURCE_FILES,
            f"Expected {EXPECTED_SOURCE_FILES} checksum entries, found {len(expected)}")

    expected_tree_files = set(expected) | {"SHA256SUMS", "STAGING_README.txt"}
    require(actual_files == expected_tree_files,
            "Staged tree does not exactly match the checksum manifest plus the two staging documents")

    verified_bytes = 0
    for index, (relative, digest) in enumerate(expected.items(), 1):
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"Checksum target missing or unsafe: {relative}")
        actual = sha256_file(path)
        require(actual == digest, f"SHA256 mismatch: {relative}")
        verified_bytes += path.stat().st_size
        if index % 1000 == 0:
            print(f"CHECKSUM_PROGRESS {index}/{EXPECTED_SOURCE_FILES}")

    pipeline = load_json(root / "pipeline_metadata/pipeline_manifest.json")
    require(pipeline.get("report_id") == EXPECTED_REPORT_ID, "Unexpected pipeline report_id")

    reconciliation = load_json(root / "reconciliation_v2/corpus_manifest.json")
    acceptance = load_json(root / "acceptance/data_quality_report.json")

    universe_path = root / "discovery/instrument_universe.csv"
    with universe_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, [])
        require(len(header) > 1, "Instrument universe CSV has no usable header")
        instrument_rows = sum(1 for _ in reader)

    # Candidate adjusted series must remain excluded from this staged corpus.
    candidate_dir = root / "reconciliation_v2/adjusted_candidates_research_only"
    require(not candidate_dir.exists(), "Adjusted research-only candidates must not be present in this staged dataset")

    report = {
        "status": "passed",
        "mode": "offline_read_only",
        "source_file_count": len(expected),
        "source_files_sha256_verified": len(expected),
        "source_bytes_verified": verified_bytes,
        "total_staged_files": len(actual_files),
        "directory_count": directory_count,
        "instrument_universe_rows": instrument_rows,
        "pipeline_report_id": pipeline.get("report_id"),
        "reconciliation_manifest_parsed": True,
        "acceptance_quality_report_parsed": True,
        "adjusted_candidates_included": False,
        "eligible_for_scoring": False,
        "approved_for_backtest": False,
        "trigger_actor": trigger_actor,
        "trigger_sha": trigger_sha,
        "run_id": run_id,
        "network_requests": 0,
        "dataset_modified": False,
    }

    output.mkdir(parents=True, exist_ok=True)
    report_path = output / f"tsetmc-offline-acceptance-{run_id}.json"
    fd, temporary_name = tempfile.mkstemp(prefix=".tsetmc-acceptance-", dir=output)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, report_path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)

    print("RESULT: PASS")
    print(f"SOURCE_FILES_SHA256_VERIFIED: {len(expected)}")
    print(f"SOURCE_BYTES_VERIFIED: {verified_bytes}")
    print(f"INSTRUMENT_UNIVERSE_ROWS: {instrument_rows}")
    print("NETWORK_REQUESTS: 0")
    print("DATASET_MODIFIED: false")
    print("SCORING_ENABLED: false")
    print("BACKTEST_APPROVED: false")
    print(f"SANITIZED_REPORT: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Never print source rows, raw payloads, or local file contents.
        print(f"RESULT: FAIL ({type(exc).__name__}): {str(exc)[:240]}", file=sys.stderr)
        raise SystemExit(1)
