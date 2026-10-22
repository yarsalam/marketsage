from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from audit_nerkhsanj_ingestion import audit_run  # noqa: E402
from ingest_nerkhsanj_archive import CSV_FIELDS, MANIFEST_FIELDS, SOURCE_ID  # noqa: E402


PAYLOAD_HASH = "a" * 64


def _row(day: str, jalali: str, value: str, **overrides: str) -> dict[str, str]:
    row = {field: "" for field in CSV_FIELDS}
    row.update({
        "source_id": SOURCE_ID,
        "provider_series_key": "dollar",
        "candidate_asset_id": "IR_USD_ISSUE_CANDIDATE",
        "candidate_asset_family": "fx",
        "candidate_mapping_status": "KEY_NAME_CANDIDATE_ONLY",
        "candidate_interpretation": "Unverified candidate mapping",
        "observation_date": day,
        "observation_date_jalali": jalali,
        "value": value,
        "value_unit": "UNKNOWN_UNVERIFIED",
        "value_semantics": "DAILY_PROVIDER_VALUE_NOT_VALIDATED_AS_CLOSE",
        "row_quality_status": "CANDIDATE_VALID_UNAPPROVED",
        "source_payload_sha256": PAYLOAD_HASH,
        "source_approved": "false",
        "eligible_for_scoring": "false",
    })
    row.update(overrides)
    return row


def _manifest(normalized_count: int, source_count: int | None = None) -> dict[str, str]:
    row = {field: "" for field in MANIFEST_FIELDS}
    row.update({
        "source_id": SOURCE_ID,
        "provider_series_key": "dollar",
        "candidate_asset_id": "IR_USD_ISSUE_CANDIDATE",
        "candidate_asset_family": "fx",
        "candidate_mapping_status": "KEY_NAME_CANDIDATE_ONLY",
        "candidate_interpretation": "Unverified candidate mapping",
        "source_row_count": str(normalized_count if source_count is None else source_count),
        "normalized_row_count": str(normalized_count),
        "quarantined_row_count": str((normalized_count if source_count is None else source_count) - normalized_count),
        "unique_date_count": str(normalized_count),
        "duplicate_date_count": "0",
        "conflicting_duplicate_date_count": "0",
        "first_date_jalali": "1405/07/25",
        "last_date_jalali": "1405/07/29",
        "first_date_gregorian": "2026-10-17",
        "last_date_gregorian": "2026-10-21",
        "invalid_date_count": "0",
        "invalid_value_count": "0",
        "value_unit": "UNKNOWN_UNVERIFIED",
        "value_semantics": "DAILY_PROVIDER_VALUE_NOT_VALIDATED_AS_CLOSE",
        "rights_status": "UNREVIEWED",
        "source_approved": "false",
        "eligible_for_scoring": "false",
    })
    return row


def _write_run(
    root: Path,
    rows: list[dict[str, str]],
    manifest_rows: list[dict[str, str]],
    *,
    source_rows: int | None = None,
) -> Path:
    normalized_dir = root / "normalized"
    normalized_dir.mkdir(parents=True)
    report = {
        "source_id": SOURCE_ID,
        "status": "COMPLETED_CANDIDATE_ONLY",
        "run_id": "run_test_fixture",
        "source_payload_sha256": PAYLOAD_HASH,
        "raw_payload_saved": False,
        "series_count": len(manifest_rows),
        "source_rows": len(rows) if source_rows is None else source_rows,
        "normalized_rows": len(rows),
        "quarantined_pairs": 0 if source_rows is None else source_rows - len(rows),
        "source_approved": False,
        "eligible_for_scoring": False,
        "backtest_approved": False,
    }
    (root / "ingestion_report.json").write_text(
        json.dumps(report), encoding="utf-8"
    )
    for path, fields, contents in [
        (normalized_dir / "nerkhsanj_series_daily_values.csv", CSV_FIELDS, rows),
        (normalized_dir / "nerkhsanj_series_manifest.csv", MANIFEST_FIELDS, manifest_rows),
    ]:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(contents)
    return root


def test_audit_reports_gaps_repeats_and_large_observed_changes_without_values(tmp_path: Path) -> None:
    rows = [
        _row("2026-10-17", "1405/07/25", "100"),
        _row("2026-10-19", "1405/07/27", "100"),
        _row("2026-10-20", "1405/07/28", "100"),
        _row("2026-10-21", "1405/07/29", "150"),
    ]
    run = _write_run(tmp_path, rows, [_manifest(4)])
    result = audit_run(run)

    assert result["status"] == "COMPLETED_CANDIDATE_AUDIT"
    assert result["counts"]["normalized_csv_rows"] == 4
    assert result["counts"]["invalid_iso_date_rows"] == 0
    assert result["counts"]["jalali_gregorian_mismatch_rows"] == 0
    assert result["counts"]["unchanged_adjacent_observation_pairs"] == 2
    assert result["series"][0]["calendar_intervals_gt_1_day"] == 1
    assert result["counts"]["observation_change_pairs_abs_pct_ge_20"] == 1
    assert result["counts"]["observation_change_pairs_abs_pct_ge_50"] == 1
    assert result["series"][0]["max_abs_observation_to_observation_change_pct"] == "50.0000"
    assert result["consistency"]["report_remains_candidate_only"] is True
    assert result["source_approved"] is False
    assert result["backtest_approved"] is False
    serialized = json.dumps(result)
    assert '"value": "100"' not in serialized
    assert '"value": "150"' not in serialized


def test_audit_flags_conflicting_duplicate_dates_and_manifest_mismatch(tmp_path: Path) -> None:
    rows = [
        _row("2026-10-20", "1405/07/28", "100"),
        _row("2026-10-20", "1405/07/28", "120"),
        _row("2026-10-21", "1405/07/29", "120"),
    ]
    run = _write_run(tmp_path, rows, [_manifest(2)])
    result = audit_run(run)

    assert result["counts"]["duplicate_date_excess_rows"] == 1
    assert result["counts"]["conflicting_duplicate_dates"] == 1
    assert result["counts"]["manifest_normalized_row_count_mismatches"] == 1
    assert result["series"][0]["unique_observation_dates"] == 2
    assert result["series"][0]["conflicting_duplicate_dates"] == 1


def test_audit_flags_calendar_mismatch_and_approval_claim(tmp_path: Path) -> None:
    rows = [
        _row(
            "2026-10-21",
            "1405/07/28",
            "100",
            source_approved="true",
        )
    ]
    run = _write_run(tmp_path, rows, [_manifest(1)])
    result = audit_run(run)

    assert result["counts"]["jalali_gregorian_mismatch_rows"] == 1
    assert result["counts"]["approval_flag_violation_rows"] == 1
    assert result["consistency"]["no_row_claims_scoring_or_source_approval"] is False
    assert result["series_with_jalali_gregorian_mismatches"] == ["dollar"]
