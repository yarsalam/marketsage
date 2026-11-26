from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.research.adjustment_orchestrator import (
    PipelineError, compare_records, file_diff, fingerprint, previous_run,
)


def test_fingerprint_ignores_manifests_but_detects_payload_revision(tmp_path):
    root = tmp_path / "capture"
    root.mkdir()
    raw = root / "foolad_daily_raw.json"
    raw.write_text(json.dumps({"closingPriceDaily": [{"dEven": 20261125, "pClosing": 5420}]}))
    (root / "manifest.json").write_text('{"created_at":"first"}')
    first = fingerprint(root)
    (root / "manifest.json").write_text('{"created_at":"second"}')
    assert fingerprint(root)["sha256"] == first["sha256"]
    raw.write_text(json.dumps({"closingPriceDaily": [{"dEven": 20261125, "pClosing": 5430}]}))
    assert fingerprint(root)["sha256"] != first["sha256"]


def test_file_diff_reports_added_removed_and_modified():
    old = {"files": {"a": {"sha256": "1"}, "b": {"sha256": "2"}}}
    new = {"files": {"b": {"sha256": "3"}, "c": {"sha256": "4"}}}
    assert file_diff(old, new) == {
        "added": ["c"], "removed": ["a"], "modified": ["b"]
    }


def test_compare_records_finds_new_trading_day_and_corrected_old_day(tmp_path):
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    old.write_text(json.dumps({"closingPriceDaily": [
        {"dEven": 20261125, "pClosing": 5420, "qTotTran5J": 100}
    ]}))
    new.write_text(json.dumps({"closingPriceDaily": [
        {"dEven": 20261125, "pClosing": 5430, "qTotTran5J": 101},
        {"dEven": 20261126, "pClosing": 5500, "qTotTran5J": 200}
    ]}))
    result = compare_records(old, new, {
        "array_path": "closingPriceDaily", "key_field": "dEven"
    })
    assert result["added"] == ["20261126"]
    assert result["removed"] == []
    assert result["modified"] == [
        {"key": "20261125", "changed_fields": ["pClosing", "qTotTran5J"]}
    ]


def test_duplicate_record_keys_fail_closed(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"rows": [{"dEven": 1}, {"dEven": 1}]}))
    with pytest.raises(PipelineError, match="Duplicate"):
        compare_records(None, path, {"array_path": "rows", "key_field": "dEven"})


def test_fingerprint_rejects_symlinks_and_empty_capture(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(PipelineError):
        fingerprint(empty)
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    capture = tmp_path / "capture"
    capture.mkdir()
    (capture / "linked.json").symlink_to(outside)
    with pytest.raises(PipelineError, match="Symlink"):
        fingerprint(capture)


def test_previous_run_keeps_blocked_recalculation_pending(tmp_path):
    runs = tmp_path / "runs"
    prior = runs / "20261125"
    current = runs / "20261126"
    prior.mkdir(parents=True)
    current.mkdir()
    (prior / "run_manifest.json").write_text(json.dumps({
        "run_id": "20261125",
        "state": "BLOCKED_RECONCILIATION_NOT_CONFIGURED",
        "completed_at": "2026-11-25T18:00:00+03:30",
        "source_fingerprints": {"tsetmc:foolad": {"sha256": "abc"}},
        "change_plan": {"recalculation_required": True},
        "adjustment_completed": False
    }))
    assert previous_run(runs, "20261126")["run_id"] == "20261125"
