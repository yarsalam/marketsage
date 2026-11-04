#!/usr/bin/env python3
"""Run the pinned, offline TSETMC acceptance pipeline against the staged corpus.

This wrapper is intentionally fixed-path and fail-closed for the local Runner.
It emits only sanitized aggregate counts to stdout. Candidate-level CSVs,
source hashes and local paths remain under the private Runner output directory.
"""
from __future__ import annotations

import csv
import gc
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
MIN_AVAILABLE_MEMORY_BYTES = 4 * GIB
MIN_FREE_DISK_BYTES = 8 * GIB
MAX_BATCH_ITEMS = 32
MAX_BATCH_INPUT_BYTES = 32 * 1024 * 1024
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


def _read_optional_integer(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="ascii").strip()
        if raw in {"", "max"}:
            return None
        value = int(raw)
        return value if value >= 0 else None
    except (OSError, ValueError):
        return None


def _memory_snapshot() -> dict[str, int | None]:
    """Use the tightest available memory value across host and ancestor cgroups."""
    host_available = _available_memory_bytes()
    cgroup_root = Path("/sys/fs/cgroup")
    candidate_dirs: list[tuple[Path, bool]] = []

    try:
        for line in Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines():
            parts = line.split(":", 2)
            if len(parts) != 3:
                continue
            hierarchy, controllers, relative = parts
            relative_path = Path(relative.lstrip("/"))
            if hierarchy == "0" and not controllers:
                candidate_dirs.append((cgroup_root / relative_path, True))
            elif "memory" in controllers.split(","):
                candidate_dirs.append((Path("/sys/fs/cgroup/memory") / relative_path, False))
    except OSError:
        pass

    # Walk from this process' cgroup to the mount root so parent MemoryMax
    # limits are respected as well as any limit on the service itself.
    cgroup_available_values: list[tuple[int, int, int]] = []
    seen: set[Path] = set()
    for directory, is_v2 in candidate_dirs:
        current = directory
        mount_root = cgroup_root if is_v2 else Path("/sys/fs/cgroup/memory")
        while current not in seen and (current == mount_root or mount_root in current.parents):
            seen.add(current)
            if is_v2:
                limit = _read_optional_integer(current / "memory.max")
                used = _read_optional_integer(current / "memory.current")
            else:
                limit = _read_optional_integer(current / "memory.limit_in_bytes")
                used = _read_optional_integer(current / "memory.usage_in_bytes")
            if limit is not None and used is not None and limit < (1 << 60):
                cgroup_available_values.append((max(0, limit - used), limit, used))
            if current == mount_root:
                break
            current = current.parent

    if not cgroup_available_values:
        # Fallback for runners where /proc/self/cgroup is hidden or unusual.
        for is_v2, directory in (
            (True, cgroup_root),
            (False, Path("/sys/fs/cgroup/memory")),
        ):
            if is_v2:
                limit = _read_optional_integer(directory / "memory.max")
                used = _read_optional_integer(directory / "memory.current")
            else:
                limit = _read_optional_integer(directory / "memory.limit_in_bytes")
                used = _read_optional_integer(directory / "memory.usage_in_bytes")
            if limit is not None and used is not None and limit < (1 << 60):
                cgroup_available_values.append((max(0, limit - used), limit, used))

    if cgroup_available_values:
        cgroup_available, cgroup_limit, cgroup_current = min(
            cgroup_available_values, key=lambda row: row[0]
        )
    else:
        cgroup_available = cgroup_limit = cgroup_current = None

    effective = min(host_available, cgroup_available if cgroup_available is not None else host_available)
    return {
        "host_available_bytes": host_available,
        "cgroup_limit_bytes": cgroup_limit,
        "cgroup_current_bytes": cgroup_current,
        "cgroup_available_bytes": cgroup_available,
        "effective_available_bytes": effective,
    }


def build_batches(
    items: list[dict[str, Any]],
    *,
    max_items: int = MAX_BATCH_ITEMS,
    max_bytes: int = MAX_BATCH_INPUT_BYTES,
) -> list[list[dict[str, Any]]]:
    """Partition candidates by unique on-disk input size before loading payloads."""
    if max_items < 1 or max_bytes < 1:
        raise SafetyGateError("invalid_batch_limits")

    size_cache: dict[Path, int] = {}

    def file_size(path: Path) -> int:
        resolved = _resolved(path)
        if resolved not in size_cache:
            if resolved.is_symlink() or not resolved.is_file():
                raise SafetyGateError("selected_input_file_missing_or_unsafe")
            size_cache[resolved] = resolved.stat().st_size
        return size_cache[resolved]

    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_paths: set[Path] = set()
    current_bytes = 0

    for item in items:
        paths = {_resolved(path) for path in _selected_paths([item])}
        if not paths:
            raise SafetyGateError("candidate_has_no_selected_input_files")
        item_bytes = sum(file_size(path) for path in paths)
        if item_bytes > max_bytes:
            raise SafetyGateError("single_candidate_input_exceeds_batch_memory_budget")

        additional_paths = paths - current_paths
        additional_bytes = sum(file_size(path) for path in additional_paths)
        if current and (
            len(current) >= max_items or current_bytes + additional_bytes > max_bytes
        ):
            batches.append(current)
            current = []
            current_paths = set()
            current_bytes = 0
            additional_paths = paths
            additional_bytes = item_bytes

        current.append(item)
        current_paths.update(additional_paths)
        current_bytes += additional_bytes

    if current:
        batches.append(current)
    return batches


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

    batches = build_batches(items)
    memory = _memory_snapshot()
    free_disk = shutil.disk_usage(output_parent).free

    resource_report = {
        "stage": "resource_preflight",
        "discovery": preflight,
        "batch_count": len(batches),
        "maximum_items_per_batch": MAX_BATCH_ITEMS,
        "maximum_input_bytes_per_batch": MAX_BATCH_INPUT_BYTES,
        "memory": memory,
        "minimum_effective_available_memory_bytes": MIN_AVAILABLE_MEMORY_BYTES,
        "free_output_disk_bytes": free_disk,
        "minimum_free_disk_bytes": MIN_FREE_DISK_BYTES,
        "candidate_outputs_private": True,
    }
    print(json.dumps(resource_report, sort_keys=True), flush=True)

    if int(memory["effective_available_bytes"] or 0) < MIN_AVAILABLE_MEMORY_BYTES:
        raise SafetyGateError("insufficient_available_memory_for_bounded_batching")
    if free_disk < MIN_FREE_DISK_BYTES:
        raise SafetyGateError("insufficient_output_disk_space")

    output_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output_root, 0o700)
    os.umask(0o077)

    totals: Counter[str] = Counter()
    decision_status_counts: Counter[str] = Counter()
    quarantine_reason_counts: Counter[str] = Counter()
    semantics_counts: Counter[str] = Counter()
    identity_true = identity_false = identity_unknown = 0
    batch_run_ids: list[str] = []
    minimum_memory_observed = int(memory["effective_available_bytes"] or 0)
    minimum_disk_observed = free_disk

    for index, batch in enumerate(batches, start=1):
        current_memory = _memory_snapshot()
        current_available = int(current_memory["effective_available_bytes"] or 0)
        minimum_memory_observed = min(minimum_memory_observed, current_available)
        current_disk = shutil.disk_usage(output_parent).free
        minimum_disk_observed = min(minimum_disk_observed, current_disk)

        print(json.dumps({
            "stage": "batch_start",
            "batch": index,
            "batch_count": len(batches),
            "candidate_count": len(batch),
            "effective_available_memory_bytes": current_available,
            "free_output_disk_bytes": current_disk,
        }, sort_keys=True), flush=True)

        if current_available < MIN_AVAILABLE_MEMORY_BYTES:
            raise SafetyGateError("insufficient_available_memory_before_next_batch")
        if current_disk < MIN_FREE_DISK_BYTES:
            raise SafetyGateError("insufficient_output_disk_space_before_next_batch")

        report = pipeline.run_pipeline(
            batch,
            manifest_path=None,
            output_root=output_root,
            discovered=True,
        )
        validate_pipeline_flags(report)
        out_dir, local = verify_local_outputs(report, output_root)

        if os.access(dataset_root, os.W_OK):
            raise SafetyGateError("dataset_write_boundary_changed")

        batch_run_ids.append(str(report.get("run_id") or ""))
        for key in (
            "instrument_count",
            "input_references_read",
            "input_file_read_errors",
            "research_eligible_count",
            "quarantine_count",
            "reprocessing_queue_count",
            "aggregate_history_rows",
            "history_gap_intervals_over_7_days",
            "history_gap_intervals_over_30_days",
            "aggregate_adjusted_candidate_rows",
            "event_rows_audited",
            "research_feature_rows",
            "forward_label_rows",
        ):
            totals[key] += int(report.get(key) or 0)
        totals["local_manifest_files_hash_verified"] += int(local["manifest_files"])
        decision_status_counts.update(report.get("decision_status_counts") or {})

        candidate_aggregates = local["candidate_aggregates"]
        quarantine_reason_counts.update(candidate_aggregates.get("quarantine_reason_code_counts") or {})
        semantics_counts.update(candidate_aggregates.get("price_input_semantics_counts") or {})
        identity_true += int(candidate_aggregates.get("identity_verified_true_count") or 0)
        identity_false += int(candidate_aggregates.get("identity_verified_false_count") or 0)
        identity_unknown += int(candidate_aggregates.get("identity_verified_unknown_count") or 0)

        print(json.dumps({
            "stage": "batch_completed",
            "batch": index,
            "batch_count": len(batches),
            "candidate_count": int(report.get("instrument_count") or 0),
            "decision_status_counts": report.get("decision_status_counts") or {},
            "quarantine_count": int(report.get("quarantine_count") or 0),
            "local_output_manifest_files_hash_verified": int(local["manifest_files"]),
            "eligible_for_scoring": False,
            "eligible_for_backtest": False,
        }, sort_keys=True), flush=True)

        partial_summary = {
            "status": "PARTIAL_CANDIDATE_AUDIT",
            "completed_batches": index,
            "total_batches": len(batches),
            "completed_candidates": totals["instrument_count"],
            "decision_status_counts": dict(sorted(decision_status_counts.items())),
            "quarantine_reason_code_counts": dict(sorted(quarantine_reason_counts.items())),
            "price_input_semantics_counts": dict(sorted(semantics_counts.items())),
            "identity_verified_true_count": identity_true,
            "identity_verified_false_count": identity_false,
            "identity_verified_unknown_count": identity_unknown,
            "eligible_for_scoring": False,
            "eligible_for_backtest": False,
            "backtest_approved": False,
            "backtest_run": False,
        }
        partial_path = output_root / "integrated-progress.json"
        partial_path.write_text(json.dumps(partial_summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.chmod(partial_path, 0o600)
        del report, local, out_dir
        gc.collect()

    if os.access(dataset_root, os.W_OK):
        raise SafetyGateError("dataset_write_boundary_changed")

    summary = {
        "status": "COMPLETED_CANDIDATE_ONLY",
        "pipeline_version": getattr(pipeline, "VERSION", None),
        "run_id": batch_run_ids[0] if batch_run_ids else None,
        "batch_run_count": len(batch_run_ids),
        "batch_input_budget_bytes": MAX_BATCH_INPUT_BYTES,
        "batch_maximum_instruments": MAX_BATCH_ITEMS,
        "instrument_count": totals["instrument_count"],
        "input_references_read": totals["input_references_read"],
        "unique_input_files_hashed": preflight["unique_input_files"],
        "input_file_read_errors": totals["input_file_read_errors"],
        "decision_status_counts": dict(sorted(decision_status_counts.items())),
        "research_eligible_count": totals["research_eligible_count"],
        "quarantine_count": totals["quarantine_count"],
        "reprocessing_queue_count": totals["reprocessing_queue_count"],
        "aggregate_history_rows": totals["aggregate_history_rows"],
        "history_gap_intervals_over_7_days": totals["history_gap_intervals_over_7_days"],
        "history_gap_intervals_over_30_days": totals["history_gap_intervals_over_30_days"],
        "aggregate_adjusted_candidate_rows": totals["aggregate_adjusted_candidate_rows"],
        "event_rows_audited": totals["event_rows_audited"],
        "research_feature_rows": totals["research_feature_rows"],
        "forward_label_rows": totals["forward_label_rows"],
        "local_manifest_files_hash_verified": totals["local_manifest_files_hash_verified"],
        "candidate_aggregate_diagnostics": {
            "decision_rows": totals["instrument_count"],
            "quarantine_reason_code_counts": dict(sorted(quarantine_reason_counts.items())),
            "price_input_semantics_counts": dict(sorted(semantics_counts.items())),
            "identity_verified_true_count": identity_true,
            "identity_verified_false_count": identity_false,
            "identity_verified_unknown_count": identity_unknown,
        },
        "effective_memory_minimum_observed_bytes": minimum_memory_observed,
        "free_disk_minimum_observed_bytes": minimum_disk_observed,
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
    final_path = output_root / f"integrated-summary-{summary['run_id']}.json"
    final_path.write_text(json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.chmod(final_path, 0o600)
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
