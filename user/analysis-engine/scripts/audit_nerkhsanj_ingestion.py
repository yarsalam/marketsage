#!/usr/bin/env python3
"""Local metadata/statistical triage for a Nerkhsanj candidate-ingestion run.

This script performs no network requests. It prints and writes counts, date spans,
calendar gaps, repeat-value counts, and observation-to-observation change statistics.
It never includes raw provider values in the audit report and never approves data.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from ingest_nerkhsanj_archive import SOURCE_ID, jalali_to_gregorian

NORMALIZED_RELATIVE_PATH = Path("normalized/nerkhsanj_series_daily_values.csv")
MANIFEST_RELATIVE_PATH = Path("normalized/nerkhsanj_series_manifest.csv")
REPORT_RELATIVE_PATH = Path("ingestion_report.json")
REQUIRED_NORMALIZED_COLUMNS = {
    "source_id",
    "provider_series_key",
    "observation_date",
    "observation_date_jalali",
    "value",
    "value_unit",
    "value_semantics",
    "source_payload_sha256",
    "source_approved",
    "eligible_for_scoring",
}
REQUIRED_MANIFEST_COLUMNS = {
    "provider_series_key",
    "normalized_row_count",
    "source_row_count",
    "unique_date_count",
}


class AuditError(Exception):
    """Raised when the local ingestion artifacts cannot be audited safely."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read valid JSON from {path.name} ({type(exc).__name__})") from None
    if not isinstance(value, dict):
        raise AuditError(f"{path.name} must contain a JSON object")
    return value


def _read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = sorted(required - fields)
            if missing:
                raise AuditError(f"{path.name} is missing required columns: {', '.join(missing)}")
            return [dict(row) for row in reader]
    except OSError as exc:
        raise AuditError(f"cannot read {path.name} ({type(exc).__name__})") from None


def _positive_decimal(text: Any) -> Decimal | None:
    if text is None or isinstance(text, bool):
        return None
    try:
        number = Decimal(str(text).strip())
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def _iso_date(text: Any) -> date | None:
    if not isinstance(text, str):
        return None
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == text else None


def _percentage_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    try:
        return format(value, ".4f")
    except (InvalidOperation, ValueError):
        return "unrepresentable"


def audit_run(run_dir: str | Path) -> dict[str, Any]:
    """Audit one completed ingestion run without emitting its raw values."""
    root = Path(run_dir).expanduser().resolve()
    report_path = root / REPORT_RELATIVE_PATH
    normalized_path = root / NORMALIZED_RELATIVE_PATH
    manifest_path = root / MANIFEST_RELATIVE_PATH
    report = _read_json(report_path)
    if report.get("source_id") != SOURCE_ID:
        raise AuditError("ingestion report source_id does not match the Nerkhsanj archive adapter")
    if report.get("raw_payload_saved") is not False:
        raise AuditError("report does not confirm that the raw response was not saved")
    if report.get("status") != "COMPLETED_CANDIDATE_ONLY":
        raise AuditError("ingestion report is not a completed candidate-only run")

    rows = _read_csv(normalized_path, REQUIRED_NORMALIZED_COLUMNS)
    manifest = _read_csv(manifest_path, REQUIRED_MANIFEST_COLUMNS)
    expected_hash = str(report.get("source_payload_sha256") or "")

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    invalid_iso_dates = 0
    invalid_positive_values = 0
    jalali_calendar_mismatches = 0
    payload_hash_mismatches = 0
    source_id_mismatches = 0
    unit_semantics_mismatches = 0
    approval_flag_violations = 0
    for index, row in enumerate(rows):
        key = (row.get("provider_series_key") or "").strip()
        if key:
            groups[key].append(row)
        parsed_date = _iso_date(row.get("observation_date"))
        value = _positive_decimal(row.get("value"))
        if parsed_date is None:
            invalid_iso_dates += 1
        else:
        if value is None:
            invalid_positive_values += 1
        else:

        jalali_text = row.get("observation_date_jalali", "")
        if parsed_date is not None:
            try:
                converted = jalali_to_gregorian(jalali_text)
            except (TypeError, ValueError):
                jalali_calendar_mismatches += 1
            else:
                if converted != parsed_date:
                    jalali_calendar_mismatches += 1

        if row.get("source_payload_sha256", "") != expected_hash:
            payload_hash_mismatches += 1
        if row.get("source_id") != SOURCE_ID:
            source_id_mismatches += 1
        if (
            row.get("value_unit") != "UNKNOWN_UNVERIFIED"
            or row.get("value_semantics") != "DAILY_PROVIDER_VALUE_NOT_VALIDATED_AS_CLOSE"
        ):
            unit_semantics_mismatches += 1
        if any(
            (row.get(field, "").strip().lower() == "true")
            for field in ("source_approved", "eligible_for_scoring")
        ):
            approval_flag_violations += 1

    manifest_by_key = {
        (row.get("provider_series_key") or "").strip(): row
        for row in manifest
        if (row.get("provider_series_key") or "").strip()
    }
    manifest_count_mismatches: list[dict[str, Any]] = []
    for key in sorted(set(groups) | set(manifest_by_key)):
        actual_count = len(groups.get(key, []))
        manifest_row = manifest_by_key.get(key)
        declared_count = None
        if manifest_row is not None:
            try:
                declared_count = int(manifest_row.get("normalized_row_count", ""))
            except (TypeError, ValueError):
                declared_count = None
        if declared_count != actual_count:
            manifest_count_mismatches.append({
                "provider_series_key": key,
                "manifest_normalized_row_count": declared_count,
                "normalized_csv_row_count": actual_count,
            })

    series_results: list[dict[str, Any]] = []
    global_duplicate_excess_rows = 0
    global_conflicting_duplicate_dates = 0
    global_unchanged_intervals = 0
    global_intervals_gt_3 = 0
    global_intervals_gt_7 = 0
    global_intervals_gt_30 = 0
    global_changes_ge_20 = 0
    global_changes_ge_50 = 0
    global_changes_ge_100 = 0
    all_calendar_mismatch_keys: set[str] = set()

    for key in sorted(groups):
        series_rows = groups[key]
        date_values: dict[date, list[Decimal]] = defaultdict(list)
        series_invalid_dates = 0
        series_invalid_values = 0
        series_calendar_mismatches = 0
        original_dates: list[date] = []

        for row in series_rows:
            parsed_date = _iso_date(row.get("observation_date"))
            value = _positive_decimal(row.get("value"))
            if parsed_date is None:
                series_invalid_dates += 1
            else:
                original_dates.append(parsed_date)
                try:
                    converted = jalali_to_gregorian(row.get("observation_date_jalali", ""))
                except (TypeError, ValueError):
                    series_calendar_mismatches += 1
                else:
                    if converted != parsed_date:
                        series_calendar_mismatches += 1
            if value is None:
                series_invalid_values += 1
            if parsed_date is None or value is None:
                continue
            date_values[parsed_date].append(value)

        input_order_inversions = sum(
            1 for left, right in zip(original_dates, original_dates[1:]) if right < left
        )
        duplicate_excess_rows = sum(max(0, len(values) - 1) for values in date_values.values())
        conflicting_dates = sum(
            1 for values in date_values.values() if len(set(values)) > 1
        )
        ordered_dates = sorted(date_values)
        unique_daily_values: dict[date, Decimal] = {
            day: values[0]
            for day, values in date_values.items()
            if len(set(values)) == 1
        }
        clean_dates = sorted(unique_daily_values)
        intervals = [
            (right - left).days
            for left, right in zip(ordered_dates, ordered_dates[1:])
        ]
        intervals_gt_1 = sum(gap > 1 for gap in intervals)
        intervals_gt_3 = sum(gap > 3 for gap in intervals)
        intervals_gt_7 = sum(gap > 7 for gap in intervals)
        intervals_gt_30 = sum(gap > 30 for gap in intervals)

        unchanged_intervals = 0
        changes: list[tuple[Decimal, date]] = []
        changes_ge_20 = changes_ge_50 = changes_ge_100 = 0
        for left, right in zip(clean_dates, clean_dates[1:]):
            previous = unique_daily_values[left]
            current = unique_daily_values[right]
            if current == previous:
                unchanged_intervals += 1
            change = abs((current / previous - Decimal("1")) * Decimal("100"))
            changes.append((change, right))
            if change >= Decimal("20"):
                changes_ge_20 += 1
            if change >= Decimal("50"):
                changes_ge_50 += 1
            if change >= Decimal("100"):
                changes_ge_100 += 1

        changes.sort(key=lambda item: item[0], reverse=True)
        max_change = changes[0][0] if changes else None
        largest_changes = [
            {"observation_date": day.isoformat(), "abs_change_pct": _percentage_text(change)}
            for change, day in changes[:5]
        ]

        global_duplicate_excess_rows += duplicate_excess_rows
        global_conflicting_duplicate_dates += conflicting_dates
        global_unchanged_intervals += unchanged_intervals
        global_intervals_gt_3 += intervals_gt_3
        global_intervals_gt_7 += intervals_gt_7
        global_intervals_gt_30 += intervals_gt_30
        global_changes_ge_20 += changes_ge_20
        global_changes_ge_50 += changes_ge_50
        global_changes_ge_100 += changes_ge_100
        if series_calendar_mismatches:
            all_calendar_mismatch_keys.add(key)

        series_results.append({
            "provider_series_key": key,
            "normalized_rows": len(series_rows),
            "valid_iso_date_rows": len(original_dates),
            "unique_observation_dates": len(date_values),
            "first_observation_date": min(ordered_dates).isoformat() if ordered_dates else None,
            "last_observation_date": max(ordered_dates).isoformat() if ordered_dates else None,
            "invalid_iso_date_rows": series_invalid_dates,
            "invalid_positive_numeric_value_rows": series_invalid_values,
            "jalali_gregorian_mismatch_rows": series_calendar_mismatches,
            "input_order_inversions": input_order_inversions,
            "duplicate_date_excess_rows": duplicate_excess_rows,
            "conflicting_duplicate_dates": conflicting_dates,
            "calendar_intervals_gt_1_day": intervals_gt_1,
            "calendar_intervals_gt_3_days": intervals_gt_3,
            "calendar_intervals_gt_7_days": intervals_gt_7,
            "calendar_intervals_gt_30_days": intervals_gt_30,
            "max_calendar_interval_days": max(intervals) if intervals else None,
            "unchanged_adjacent_observation_pairs": unchanged_intervals,
            "observation_change_pairs_abs_pct_ge_20": changes_ge_20,
            "observation_change_pairs_abs_pct_ge_50": changes_ge_50,
            "observation_change_pairs_abs_pct_ge_100": changes_ge_100,
            "max_abs_observation_to_observation_change_pct": _percentage_text(max_change),
            "largest_observed_changes": largest_changes,
        })

    normalized_count_matches = len(rows) == report.get("normalized_rows")
    source_count_matches = report.get("source_rows") == report.get("normalized_rows") + report.get("quarantined_pairs")
    series_count_matches = len(groups) == report.get("series_count") == len(manifest)
    report_claimed_candidate_only = (
        report.get("source_approved") is False
        and report.get("eligible_for_scoring") is False
        and report.get("backtest_approved") is False
    )

    return {
        "audit_version": "1.0.0",
        "status": "COMPLETED_CANDIDATE_AUDIT",
        "audit_scope": "Local structural and descriptive-statistical triage only; not source, unit, rights, or investment acceptance.",
        "source_id": SOURCE_ID,
        "run_id": report.get("run_id"),
        "source_payload_sha256": expected_hash,
        "input_files": {
            "ingestion_report": str(report_path),
            "normalized_csv": str(normalized_path),
            "manifest_csv": str(manifest_path),
        },
        "counts": {
            "reported_series_count": report.get("series_count"),
            "observed_series_count": len(groups),
            "manifest_series_count": len(manifest),
            "reported_source_rows": report.get("source_rows"),
            "normalized_csv_rows": len(rows),
            "reported_quarantined_pairs": report.get("quarantined_pairs"),
            "invalid_iso_date_rows": invalid_iso_dates,
            "invalid_or_nonpositive_numeric_value_rows": invalid_positive_values,
            "jalali_gregorian_mismatch_rows": jalali_calendar_mismatches,
            "payload_hash_mismatch_rows": payload_hash_mismatches,
            "source_id_mismatch_rows": source_id_mismatches,
            "unit_or_semantics_mismatch_rows": unit_semantics_mismatches,
            "approval_flag_violation_rows": approval_flag_violations,
            "manifest_normalized_row_count_mismatches": len(manifest_count_mismatches),
            "duplicate_date_excess_rows": global_duplicate_excess_rows,
            "conflicting_duplicate_dates": global_conflicting_duplicate_dates,
            "unchanged_adjacent_observation_pairs": global_unchanged_intervals,
            "calendar_intervals_gt_3_days": global_intervals_gt_3,
            "calendar_intervals_gt_7_days": global_intervals_gt_7,
            "calendar_intervals_gt_30_days": global_intervals_gt_30,
            "observation_change_pairs_abs_pct_ge_20": global_changes_ge_20,
            "observation_change_pairs_abs_pct_ge_50": global_changes_ge_50,
            "observation_change_pairs_abs_pct_ge_100": global_changes_ge_100,
        },
        "consistency": {
            "normalized_count_matches_ingestion_report": normalized_count_matches,
            "source_normalized_quarantine_counts_reconcile": source_count_matches,
            "series_counts_reconcile": series_count_matches,
            "payload_hash_matches_every_normalized_row": payload_hash_mismatches == 0,
            "all_rows_have_expected_source_id": source_id_mismatches == 0,
            "all_rows_keep_units_and_value_semantics_unverified": unit_semantics_mismatches == 0,
            "no_row_claims_scoring_or_source_approval": approval_flag_violations == 0,
            "manifest_counts_match_normalized_csv": not manifest_count_mismatches,
            "report_remains_candidate_only": report_claimed_candidate_only,
        },
        "manifest_count_mismatches": manifest_count_mismatches,
        "series": series_results,
        "series_with_jalali_gregorian_mismatches": sorted(all_calendar_mismatch_keys),
        "limitations": [
            "Calendar-day intervals are descriptive only; provider trading calendar and expected weekends/holidays are unknown.",
            "Change statistics compare adjacent observed dates, which may span multiple calendar days; they are not guaranteed one-session returns.",
            "Large changes are flags for review, not automatically invalid observations.",
            "The report omits raw provider values. Inspect the local CSV privately only when a specific anomaly requires review.",
            "No value unit, key identity, quote convention, source lineage, legal rights, independent reference, or close-price semantics is validated.",
            "This audit never changes source registry or scoring/backtest approval.",
        ],
        "source_approved": False,
        "eligible_for_scoring": False,
        "adjusted_returns_approved": False,
        "backtest_approved": False,
        "investment_scoring_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, help="Completed run directory created by ingest_nerkhsanj_archive.py")
    parser.add_argument("--output", help="Output JSON path (default: <run-dir>/quality_audit.json)")
    args = parser.parse_args(argv)
    try:
        result = audit_run(args.run_dir)
    except AuditError as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    run_root = Path(args.run_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve() if args.output else run_root / "quality_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    counts = result["counts"]
    print(json.dumps({
        "status": result["status"],
        "run_id": result["run_id"],
        "series_count": counts["observed_series_count"],
        "normalized_rows": counts["normalized_csv_rows"],
        "invalid_iso_date_rows": counts["invalid_iso_date_rows"],
        "invalid_or_nonpositive_numeric_value_rows": counts["invalid_or_nonpositive_numeric_value_rows"],
        "jalali_gregorian_mismatch_rows": counts["jalali_gregorian_mismatch_rows"],
        "duplicate_date_excess_rows": counts["duplicate_date_excess_rows"],
        "conflicting_duplicate_dates": counts["conflicting_duplicate_dates"],
        "observation_change_pairs_abs_pct_ge_20": counts["observation_change_pairs_abs_pct_ge_20"],
        "observation_change_pairs_abs_pct_ge_50": counts["observation_change_pairs_abs_pct_ge_50"],
        "observation_change_pairs_abs_pct_ge_100": counts["observation_change_pairs_abs_pct_ge_100"],
        "report_remains_candidate_only": result["consistency"]["report_remains_candidate_only"],
        "output": str(output),
        "source_approved": False,
        "eligible_for_scoring": False,
        "backtest_approved": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
