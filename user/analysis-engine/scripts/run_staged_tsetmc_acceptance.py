#!/usr/bin/env python3
"""Run the pinned, offline TSETMC acceptance pipeline against the staged corpus.

This wrapper is intentionally fixed-path and fail-closed for the local Runner.
It emits only sanitized aggregate counts to stdout. Candidate-level CSVs,
source hashes and local paths remain under the private Runner output directory.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GIB = 1024 ** 3
MAX_DISCOVERED_ITEMS = 3000
MAX_INPUT_BYTES = 3 * GIB
MIN_AVAILABLE_MEMORY_BYTES = 16 * GIB
MIN_FREE_DISK_BYTES = 8 * GIB
PIPELINE_FALSE_FLAGS = (
    "raw_inputs_overwritten",
    "network_requests_made",
    "automatic_adjustment_applied",
    "forward_fill_applied",
    "production_scoring_enabled",
    "eligible_for_scoring",
    "adjusted_returns_approved",
    "eligible_for_backtest",
    "backtest_approved",
    "backtest_run",
)


class SafetyGateError(RuntimeError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def _resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def _assert_no_symlink_components(path: Path) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        if current.is_symlink():
            raise SafetyGateError("symlink_in_critical_path")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        _resolved(path).relative_to(_resolved(parent))
        return True
    except ValueError:
        return False


def _available_memory_bytes() -> int:
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    raise SafetyGateError("memory_availability_unreadable")


def _selected_paths(items: list[dict[str, Any]]) -> set[Path]:
    paths: set[Path] = set()
    for item in items:
        for key in (
            "daily_history_path",
            "adjusted_chart_path",
            "adjustment_events_path",
            "share_change_events_path",
            "identity_crosswalk_path",
        ):
            value = str(item.get(key, "") or "").strip()
            if value:
                paths.add(Path(value))
        for value in item.get("_alternative_history_paths", []):
            if value:
                paths.add(Path(str(value)))
    return paths


def summarize_discovered_items(items: list[dict[str, Any]]) -> dict[str, int]:
    unique_paths = _selected_paths(items)
    code_counts: Counter[str] = Counter()
    missing_adjusted = 0
    missing_price_events = 0
    missing_share_events = 0
    ambiguous_history = 0
    identity_conflicts = 0

    for item in items:
        code = str(item.get("instrument_code", "") or "").strip()
        if code:
            code_counts[code] += 1
        if not str(item.get("adjusted_chart_path", "") or "").strip():
            missing_adjusted += 1
        if not str(item.get("adjustment_events_path", "") or "").strip():
            missing_price_events += 1
        if not str(item.get("share_change_events_path", "") or "").strip():
            missing_share_events += 1
        ambiguous_history += int(bool(item.get("_discovery_ambiguous_history")))
        identity_conflicts += int(bool(item.get("_discovery_identity_conflict")))

    total_bytes = 0
    max_file_bytes = 0
    existing_files = 0
    for raw_path in unique_paths:
        path = _resolved(raw_path)
        if path.is_file():
            size = path.stat().st_size
            total_bytes += size
            max_file_bytes = max(max_file_bytes, size)
            existing_files += 1

    return {
        "discovered_items": len(items),
        "unique_instrument_codes": len(code_counts),
        "duplicate_instrument_codes": sum(1 for count in code_counts.values() if count > 1),
        "unique_input_files": len(unique_paths),
        "existing_input_files": existing_files,
        "selected_input_bytes": total_bytes,
        "largest_input_file_bytes": max_file_bytes,
        "missing_adjusted_chart_count": missing_adjusted,
        "missing_price_adjustment_event_count": missing_price_events,
        "missing_share_change_event_count": missing_share_events,
        "ambiguous_history_count": ambiguous_history,
        "identity_conflict_count": identity_conflicts,
    }


def validate_pipeline_flags(report: dict[str, Any]) -> None:
    flags = report.get("flags")
    if not isinstance(flags, dict):
        raise SafetyGateError("pipeline_flags_missing")
    for key in PIPELINE_FALSE_FLAGS:
        if flags.get(key) is not False:
            raise SafetyGateError("pipeline_fail_closed_flag_invalid")
    if report.get("mode") != "local_offline_acceptance_pipeline":
        raise SafetyGateError("unexpected_pipeline_mode")
    if report.get("source_id") != "iran.tsetmc":
        raise SafetyGateError("unexpected_pipeline_source")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_local_outputs(report: dict[str, Any], output_root: Path) -> tuple[Path, dict[str, Any]]:
    out_value = report.get("output_dir")
    if not isinstance(out_value, str) or not out_value:
        raise SafetyGateError("pipeline_output_directory_missing")
    out_dir = Path(out_value)
    _assert_no_symlink_components(out_dir)
    out_resolved = _resolved(out_dir)
    root_resolved = _resolved(output_root)
    if out_resolved.parent != root_resolved or not out_resolved.is_dir():
        raise SafetyGateError("pipeline_output_escaped_private_directory")

    required = (
        "data_quality_report.json",
        "backtest_gate.json",
        "run_manifest.json",
        "instrument_decisions.csv",
        "quarantine.csv",
    )
    for name in required:
        path = out_resolved / name
        if path.is_symlink() or not path.is_file():
            raise SafetyGateError("required_local_report_missing")

    manifest = json.loads((out_resolved / "run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("outputs_are_candidate_only") is not True:
        raise SafetyGateError("candidate_only_output_flag_invalid")
    if manifest.get("raw_inputs_overwritten") is not False:
        raise SafetyGateError("raw_input_write_flag_invalid")

    file_names = manifest.get("output_files")
    hashes = manifest.get("output_hashes_sha256")
    if not isinstance(file_names, list) or not isinstance(hashes, dict):
        raise SafetyGateError("output_manifest_invalid")
    if set(file_names) != set(hashes):
        raise SafetyGateError("output_manifest_hash_inventory_mismatch")

    for name in file_names:
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", "..", "run_manifest.json"}:
            raise SafetyGateError("unsafe_output_manifest_path")
        path = out_resolved / name
        if path.is_symlink() or not path.is_file() or _sha256(path) != hashes[name]:
            raise SafetyGateError("local_output_hash_verification_failed")

    quality = json.loads((out_resolved / "data_quality_report.json").read_text(encoding="utf-8"))
    quality_flags = quality.get("flags")
    if not isinstance(quality_flags, dict):
        raise SafetyGateError("quality_report_flags_missing")
    for key in PIPELINE_FALSE_FLAGS:
        if quality_flags.get(key) is not False:
            raise SafetyGateError("quality_report_fail_closed_flag_invalid")

    gate = json.loads((out_resolved / "backtest_gate.json").read_text(encoding="utf-8"))
    if gate.get("backtest_run") is not False:
        raise SafetyGateError("backtest_gate_invalid")
    if gate.get("eligible_for_scoring") is not False or gate.get("eligible_for_backtest") is not False:
        raise SafetyGateError("backtest_gate_invalid")

    aggregate_candidates = summarize_candidate_outputs(out_resolved)
    return out_resolved, {
        "manifest_files": len(file_names),
        "quality": quality,
        "backtest_gate": gate,
        "candidate_aggregates": aggregate_candidates,
    }


def summarize_candidate_outputs(output_dir: Path) -> dict[str, Any]:
    """Return aggregate-only diagnostics; never return symbols, codes, rows or paths."""
    quarantine_path = output_dir / "quarantine.csv"
    decisions_path = output_dir / "instrument_decisions.csv"
    for path in (quarantine_path, decisions_path):
        if path.is_symlink() or not path.is_file():
            raise SafetyGateError("candidate_summary_input_missing")

    reason_counts: Counter[str] = Counter()
    with quarantine_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            raw_reasons = str(row.get("reason_code", "") or "")
            for raw_reason in raw_reasons.split(";"):
                reason = raw_reason.strip()
                if not reason:
                    continue
                reason_counts[reason if re.fullmatch(r"[A-Z0-9_]+", reason) else "UNRECOGNIZED_REASON_CODE"] += 1

    semantics_counts: Counter[str] = Counter()
    identity_true = 0
    identity_false = 0
    identity_unknown = 0
    decision_rows = 0
    with decisions_path.open("r", encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            decision_rows += 1
            raw_semantics = str(row.get("price_input_semantics", "") or "").strip().lower()
            semantics = raw_semantics if raw_semantics in {
                "raw_unadjusted", "provider_adjusted", "unknown_unverified"
            } else "other_or_unrecognized"
            semantics_counts[semantics] += 1
            identity = str(row.get("identity_verified", "") or "").strip().lower()
            if identity in {"true", "1", "yes"}:
                identity_true += 1
            elif identity in {"false", "0", "no"}:
                identity_false += 1
            else:
                identity_unknown += 1

    return {
        "decision_rows": decision_rows,
        "quarantine_reason_code_counts": dict(sorted(reason_counts.items())),
        "price_input_semantics_counts": dict(sorted(semantics_counts.items())),
        "identity_verified_true_count": identity_true,
        "identity_verified_false_count": identity_false,
        "identity_verified_unknown_count": identity_unknown,
    }


def _write_local_diagnostic(output_root: Path, exc: BaseException) -> bool:
    try:
        root = _resolved(output_root)
        root.mkdir(parents=True, exist_ok=True)
        os.chmod(root, 0o700)
        diagnostic_dir = root / ".diagnostics"
        diagnostic_dir.mkdir(mode=0o700, exist_ok=True)
        os.chmod(diagnostic_dir, 0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = diagnostic_dir / f"integrated-tsetmc-failure-{stamp}.txt"
        path.write_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), encoding="utf-8")
        os.chmod(path, 0o600)
        return True
    except Exception:
        return False


def _load_pipeline(pipeline_root: Path):
    script_dir = _resolved(pipeline_root / "scripts")
    script_path = script_dir / "run_tsetmc_acceptance_pipeline.py"
    if not script_path.is_file() or script_path.is_symlink():
        raise SafetyGateError("pinned_pipeline_script_missing")
    sys.path.insert(0, str(script_dir))
    spec = importlib.util.spec_from_file_location("marketsage_tsetmc_pipeline", script_path)
    if spec is None or spec.loader is None:
        raise SafetyGateError("pinned_pipeline_import_failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run() -> dict[str, Any]:
    dataset_input = Path(os.environ["MARKETSAGE_DATASET_ROOT"]).expanduser()
    output_parent_input = Path(os.environ["MARKETSAGE_OUTPUT_PARENT"]).expanduser()
    output_root_input = Path(os.environ["MARKETSAGE_OUTPUT_ROOT"]).expanduser()
    pipeline_root_input = Path(os.environ["MARKETSAGE_PIPELINE_ROOT"]).expanduser()

    for path in (dataset_input, output_parent_input, output_root_input, pipeline_root_input):
        _assert_no_symlink_components(path)

    dataset_root = _resolved(dataset_input)
    output_parent = _resolved(output_parent_input)
    output_root = _resolved(output_root_input)
    pipeline_root = _resolved(pipeline_root_input)
    raw_root = dataset_root / "raw"
    crosswalk = dataset_root / "reconciliation_v2" / "instrument_details.jsonl"

    if not dataset_root.is_dir() or not os.access(dataset_root, os.R_OK | os.X_OK):
        raise SafetyGateError("staged_dataset_unreadable")
    if os.access(dataset_root, os.W_OK):
        raise SafetyGateError("staged_dataset_must_be_read_only")
    if not raw_root.is_dir() or not os.access(raw_root, os.R_OK | os.X_OK):
        raise SafetyGateError("raw_history_root_unreadable")
    if not _is_within(raw_root, dataset_root):
        raise SafetyGateError("raw_history_root_outside_dataset")
    if not crosswalk.is_file() or not os.access(crosswalk, os.R_OK):
        raise SafetyGateError("v2_identity_crosswalk_missing")
    if not _is_within(crosswalk, dataset_root):
        raise SafetyGateError("identity_crosswalk_outside_dataset")
    if not output_parent.is_dir() or not os.access(output_parent, os.W_OK | os.X_OK):
        raise SafetyGateError("private_output_parent_not_writable")
    if _is_within(output_root, dataset_root) or _is_within(dataset_root, output_root):
        raise SafetyGateError("output_must_be_separate_from_dataset")
    if output_root.exists() and not output_root.is_dir():
        raise SafetyGateError("output_root_not_directory")

    pipeline = _load_pipeline(pipeline_root)
    items = pipeline.discover_manifest(raw_root, identity_crosswalk_path=crosswalk)
    preflight = summarize_discovered_items(items)

    if not items:
        raise SafetyGateError("no_history_items_discovered")
    if len(items) > MAX_DISCOVERED_ITEMS:
        raise SafetyGateError("discovery_item_cap_exceeded")
    if preflight["selected_input_bytes"] > MAX_INPUT_BYTES:
        raise SafetyGateError("selected_input_size_cap_exceeded")
    if preflight["existing_input_files"] != preflight["unique_input_files"]:
        raise SafetyGateError("selected_input_file_missing")

    for selected_path in _selected_paths(items):
        _assert_no_symlink_components(selected_path)
        if not _is_within(selected_path, dataset_root):
            raise SafetyGateError("selected_input_outside_dataset")
        if selected_path.is_symlink():
            raise SafetyGateError("selected_input_symlink_detected")

    available_memory = _available_memory_bytes()
    free_disk = shutil.disk_usage(output_parent).free
    if available_memory < MIN_AVAILABLE_MEMORY_BYTES:
        raise SafetyGateError("insufficient_available_memory")
    if free_disk < MIN_FREE_DISK_BYTES:
        raise SafetyGateError("insufficient_output_disk_space")

    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_root, 0o700)
    os.umask(0o077)

    print(json.dumps({
        "stage": "preflight_passed",
        "discovery": preflight,
        "available_memory_bytes": available_memory,
        "free_output_disk_bytes": free_disk,
        "maximum_discovered_items": MAX_DISCOVERED_ITEMS,
        "minimum_available_memory_bytes": MIN_AVAILABLE_MEMORY_BYTES,
        "minimum_free_disk_bytes": MIN_FREE_DISK_BYTES,
        "candidate_outputs_private": True,
    }, sort_keys=True), flush=True)

    report = pipeline.run_pipeline(
        items,
        manifest_path=None,
        output_root=output_root,
        discovered=True,
    )
    validate_pipeline_flags(report)
    out_dir, local = verify_local_outputs(report, output_root)

    if os.access(dataset_root, os.W_OK):
        raise SafetyGateError("dataset_write_boundary_changed")

    summary = {
        "status": "COMPLETED_CANDIDATE_ONLY",
        "pipeline_version": report.get("pipeline_version"),
        "run_id": report.get("run_id"),
        "instrument_count": report.get("instrument_count"),
        "input_references_read": report.get("input_references_read"),
        "unique_input_files_hashed": report.get("unique_input_files_hashed"),
        "input_file_read_errors": report.get("input_file_read_errors"),
        "decision_status_counts": report.get("decision_status_counts"),
        "research_eligible_count": report.get("research_eligible_count"),
        "quarantine_count": report.get("quarantine_count"),
        "reprocessing_queue_count": report.get("reprocessing_queue_count"),
        "aggregate_history_rows": report.get("aggregate_history_rows"),
        "history_gap_intervals_over_7_days": report.get("history_gap_intervals_over_7_days"),
        "history_gap_intervals_over_30_days": report.get("history_gap_intervals_over_30_days"),
        "aggregate_adjusted_candidate_rows": report.get("aggregate_adjusted_candidate_rows"),
        "event_rows_audited": report.get("event_rows_audited"),
        "research_feature_rows": report.get("research_feature_rows"),
        "forward_label_rows": report.get("forward_label_rows"),
        "local_manifest_files_hash_verified": local["manifest_files"],
        "candidate_aggregate_diagnostics": local["candidate_aggregates"],
        "network_requests_made": False,
        "raw_inputs_overwritten": False,
        "eligible_for_scoring": False,
        "eligible_for_backtest": False,
        "backtest_approved": False,
        "backtest_run": False,
        "candidate_outputs_private": True,
        "local_output_created": True,
    }
    if not re.fullmatch(r"run_[0-9]{8}T[0-9]{6}[0-9]+Z", str(summary["run_id"] or "")):
        raise SafetyGateError("unexpected_run_identifier")
    return summary


def main() -> int:
    output_root = Path(os.environ.get(
        "MARKETSAGE_OUTPUT_ROOT",
        "/srv/marketsage/output/tsetmc-integrated-acceptance",
    ))
    try:
        result = run()
    except SafetyGateError as exc:
        print(json.dumps({
            "status": "BLOCKED_PREFLIGHT_OR_SAFETY_GATE",
            "reason_code": exc.reason_code,
        }, sort_keys=True), file=sys.stderr, flush=True)
        return 3
    except Exception as exc:
        saved = _write_local_diagnostic(output_root, exc)
        print(json.dumps({
            "status": "FAILED",
            "error_class": type(exc).__name__,
            "diagnostic_saved_locally": saved,
        }, sort_keys=True), file=sys.stderr, flush=True)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
