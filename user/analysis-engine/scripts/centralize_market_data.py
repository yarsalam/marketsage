#!/usr/bin/env python3
"""Safely copy existing MarketSage datasets into one local data root.

This utility is deliberately offline and additive:
- it never changes or deletes source files;
- it verifies SHA-256 after every copy;
- it skips identical destination files;
- it stops rather than overwriting a destination file with different content;
- it writes a local-only index and per-file manifests (never commit these artifacts).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPO_ROOT = Path.home() / "projects" / "marketsage-acceptance"
DEFAULT_DATA_ROOT = Path.home() / "marketsage-data"
DEFAULT_MULTI_ASSET_RUN = Path(
    "/tmp/marketsage-multi-asset-collection/run_20261022T185104629734Z"
)
DEFAULT_TSETMC_RUN_ID = "run_20261023T095517508480Z"


class DataConflictError(RuntimeError):
    """Raised when a destination contains different bytes from the source."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sync_tree(source: Path, destination: Path) -> dict[str, Any]:
    """Copy a tree without deleting/overwriting data; return its integrity summary."""
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if not source.is_dir():
        return {
            "status": "source_missing",
            "source_path": str(source),
            "destination_path": str(destination),
            "file_count": 0,
            "copied_count": 0,
            "already_present_count": 0,
            "total_bytes": 0,
            "files": [],
        }

    source_files = sorted(path for path in source.rglob("*") if path.is_file())
    if not source_files:
        return {
            "status": "source_empty",
            "source_path": str(source),
            "destination_path": str(destination),
            "file_count": 0,
            "copied_count": 0,
            "already_present_count": 0,
            "total_bytes": 0,
            "files": [],
        }

    entries: list[dict[str, Any]] = []
    copied_count = 0
    present_count = 0
    total_bytes = 0

    for source_file in source_files:
        relative = source_file.relative_to(source)
        target = destination / relative
        source_hash = sha256_file(source_file)
        size_bytes = source_file.stat().st_size
        total_bytes += size_bytes

        if target.exists():
            if not target.is_file():
                raise DataConflictError(
                    f"Destination exists but is not a regular file: {target}"
                )
            destination_hash = sha256_file(target)
            if destination_hash != source_hash:
                raise DataConflictError(
                    "Refusing to overwrite different content. "
                    f"Source={source_file}; destination={target}; "
                    f"source_sha256={source_hash}; destination_sha256={destination_hash}"
                )
            action = "already_present_verified"
            present_count += 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target)
            destination_hash = sha256_file(target)
            if destination_hash != source_hash:
                target.unlink(missing_ok=True)
                raise DataConflictError(
                    f"SHA-256 mismatch after copying {source_file} to {target}"
                )
            action = "copied_and_verified"
            copied_count += 1

        entries.append(
            {
                "relative_path": relative.as_posix(),
                "size_bytes": size_bytes,
                "sha256": source_hash,
                "action": action,
            }
        )

    return {
        "status": "copied_and_verified" if copied_count else "already_current",
        "source_path": str(source),
        "destination_path": str(destination),
        "file_count": len(entries),
        "copied_count": copied_count,
        "already_present_count": present_count,
        "total_bytes": total_bytes,
        "files": entries,
    }


def load_last_json_object(path: Path) -> dict[str, Any] | None:
    """Read the final JSON summary object from the acceptance log, if present."""
    if not path.is_file():
        return None
    content = path.read_text(encoding="utf-8", errors="replace")
    decoder = json.JSONDecoder()
    for position in reversed([i for i, char in enumerate(content) if char == "{"]):
        try:
            value, _ = decoder.raw_decode(content[position:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and "run_id" in value and "status" in value:
            return value
    return None


def report_run(data_root: Path, run_id: str, log_path: Path) -> dict[str, Any]:
    run_dir = data_root / "tsetmc-acceptance" / run_id
    if not run_dir.is_dir():
        return {
            "status": "run_report_missing",
            "run_id": run_id,
            "path": str(run_dir),
        }

    files = sorted(path for path in run_dir.rglob("*") if path.is_file())
    summary = load_last_json_object(log_path)
    file_hashes = {
        path.relative_to(run_dir).as_posix(): sha256_file(path)
        for path in files
    }
    recorded = {
        "status": "existing_report_indexed",
        "run_id": run_id,
        "path": str(run_dir),
        "file_count": len(files),
        "file_hashes": file_hashes,
    }
    if summary:
        recorded["run_summary"] = {
            key: summary.get(key)
            for key in (
                "status", "run_id", "instrument_count", "decision_status_counts",
                "research_eligible_count", "quarantine_count",
                "reprocessing_queue_count", "research_feature_rows",
                "forward_label_rows", "network_requests_made",
                "raw_inputs_overwritten", "production_scoring_enabled",
                "backtest_run",
            )
            if key in summary
        }
    return recorded


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely centralize existing MarketSage datasets and write a local hash index."
    )
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--multi-asset-run", type=Path, default=DEFAULT_MULTI_ASSET_RUN)
    parser.add_argument(
        "--streamdata-dir",
        type=Path,
        default=None,
        help="Optional directory containing the original seller-provided StreamData exports.",
    )
    parser.add_argument("--tsetmc-run-id", default=DEFAULT_TSETMC_RUN_ID)
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    data_root = args.data_root.expanduser().resolve()
    registry_dir = data_root / "registry"
    manifest_dir = registry_dir / "manifests"
    registry_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    sources: dict[str, dict[str, Any]] = {}
    specs = [
        (
            "tsetmc_history_pipeline",
            repo_root / "data" / "source_snapshots" / "tsetmc_history_pipeline",
            data_root / "tsetmc" / "tsetmc_history_pipeline",
        ),
        (
            "multi_asset_collection",
            args.multi_asset_run,
            data_root / "multi-asset-collection" / args.multi_asset_run.name,
        ),
    ]
    # Persist existing offline adjustment/research outputs too. These are source
    # artifacts from earlier work, not instructions to rerun their pipelines.
    # Missing optional output roots are recorded but never trigger new collection.
    tmp_root = Path("/tmp")
    known_run_roots = [
        ("tsetmc_adjustment_v025", tmp_root / "marketsage-tsetmc-adjustments"),
        ("tsetmc_adjust_v025", tmp_root / "marketsage-tsetmc-adjust-v025"),
        ("tsetmc_adjust_legacy", tmp_root / "marketsage-tsetmc-adjust"),
        ("tsetmc_acceptance_legacy", tmp_root / "tsetmc_acceptance_runs"),
        ("tsetmc_research_pipeline", tmp_root / "marketsage-tsetmc-research-pipeline"),
        ("tsetmc_research_pipeline_v1_1", tmp_root / "marketsage-tsetmc-research-pipeline-v1_1"),
    ]
    seen_run_paths: set[Path] = set()
    for key, source in known_run_roots:
        try:
            source_resolved = source.resolve()
        except OSError:
            source_resolved = source
        if source_resolved in seen_run_paths:
            continue
        seen_run_paths.add(source_resolved)
        specs.append((
            key,
            source,
            data_root / "tsetmc-research" / "previous_runs" / source.name,
        ))

    # Preserve prior compatible forensic reports and any other explicitly versioned
    # v0.2.5/research run roots, without crawling the whole /tmp tree.
    glob_specs = [
        ("tsetmc_forensic", "marketsage-tsetmc-forensic-v3*"),
        ("tsetmc_adjust_versioned", "marketsage-tsetmc-adjust-*"),
        ("tsetmc_research_versioned", "marketsage-tsetmc-research-pipeline*"),
    ]
    for prefix, pattern in glob_specs:
        for source in sorted(tmp_root.glob(pattern)):
            try:
                source_resolved = source.resolve()
            except OSError:
                source_resolved = source
            if source_resolved in seen_run_paths or not source.is_dir():
                continue
            seen_run_paths.add(source_resolved)
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in source.name)
            specs.append((
                f"{prefix}_{safe_name}",
                source,
                data_root / "tsetmc-research" / "previous_runs" / safe_name,
            ))

    if args.streamdata_dir is not None:
        stream_source = args.streamdata_dir.expanduser().resolve()
        specs.append(
            (
                "streamdata_source_exports",
                stream_source,
                data_root / "streamdata" / "source_exports" / stream_source.name,
            )
        )

    missing_required: list[str] = []
    for key, source, destination in specs:
        result = sync_tree(source, destination)
        manifest_path = manifest_dir / f"{key}.jsonl"
        manifest_lines = [
            json.dumps(entry, ensure_ascii=False, sort_keys=True)
            for entry in result.pop("files", [])
        ]
        manifest_path.write_text(
            "\n".join(manifest_lines) + ("\n" if manifest_lines else ""),
            encoding="utf-8",
        )
        result["file_manifest"] = str(manifest_path)
        result["file_manifest_sha256"] = sha256_file(manifest_path)
        sources[key] = result
        if result["status"] in {"source_missing", "source_empty"} and key != "streamdata_source_exports":
            missing_required.append(key)

    log_path = data_root / "logs" / "tsetmc-acceptance.log"
    acceptance = report_run(data_root, args.tsetmc_run_id, log_path)
    index = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_root": str(data_root),
        "network_requests_made": False,
        "source_files_modified_or_deleted": False,
        "conflicting_destination_files_overwritten": False,
        "sources": sources,
        "existing_runs": {"tsetmc_acceptance": acceptance},
        "notes": [
            "This index and its hash manifests are local operational metadata; do not commit them.",
            "Collected does not mean research-accepted or scoring-approved.",
            "The original source trees are retained; this tool only adds verified copies.",
            "Existing /tmp adjustment, forensic, and research-run outputs are copied for preservation; no pipeline is rerun.",
            "Missing optional /tmp run roots are indexed as missing, not re-downloaded.",
        ],
    }
    index_path = registry_dir / "local_data_index.json"
    atomic_write_json(index_path, index)

    print("MarketSage local data centralization finished.")
    print(f"Data root: {data_root}")
    print(f"Index: {index_path}")
    for key, result in sources.items():
        print(
            f"{key}: status={result['status']} files={result['file_count']} "
            f"copied={result['copied_count']} already_present={result['already_present_count']} "
            f"bytes={result['total_bytes']}"
        )
        if result["status"] in {"source_missing", "source_empty"}:
            print(f"  SOURCE NOT COPIED (no rerun attempted): {result['source_path']}")
    print(
        "tsetmc_acceptance: "
        f"status={acceptance['status']} path={acceptance.get('path', '')}"
    )

    if missing_required:
        print(
            "WARNING: one or more required source folders were missing/empty: "
            + ", ".join(missing_required),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
