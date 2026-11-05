from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_tsetmc_history.py"
SPEC = importlib.util.spec_from_file_location("audit_tsetmc_history", SCRIPT)
assert SPEC and SPEC.loader
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)
audit_history = audit_module.audit_history

INS_CODE = "46348559193224090"


def row(day, close, *, open_price=None, low=None, high=None, ins_code=INS_CODE):
    return {
        "dEven": day,
        "insCode": ins_code,
        "pClosing": close,
        "pDrCotVal": close,
        "priceFirst": open_price if open_price is not None else close,
        "priceMin": low if low is not None else close,
        "priceMax": high if high is not None else close,
        "priceYesterday": close,
        "qTotTran5J": 100,
        "qTotCap": 1000,
    }


def test_audit_sorts_dates_for_metrics_but_reports_source_order():
    report = audit_history([
        row(20261016, 110),
        row(20261015, 100),
        row(20261014, 105),
    ], expected_ins_code=INS_CODE)
    assert report["source_date_order"] == "descending" or report["source_date_order"] == "mixed"
    assert report["date_range"] == {"first": "2026-10-14", "last": "2026-10-16"}
    assert report["positive_close_rows"] == 3
    assert report["eligible_for_production_scoring"] is False
    assert report["approval_status"] == "not_approved"


def test_audit_flags_duplicate_and_invalid_dates():
    report = audit_history([
        row(20261015, 100),
        row("20261015", 101),
        row("not-a-date", 102),
    ], expected_ins_code=INS_CODE)
    assert report["duplicate_date_count"] == 1
    assert report["invalid_date_rows"] == 1


def test_audit_flags_instrument_mismatch_and_missing_values():
    bad = row(20261015, 100, ins_code="999")
    bad["qTotCap"] = None
    report = audit_history([bad], expected_ins_code=INS_CODE)
    assert report["instrument_mismatch_rows"] == 1
    assert report["missing_value_counts"]["qTotCap"] == 1


def test_audit_flags_zero_prices_and_ohlc_inconsistency():
    bad = row(20261015, 120, open_price=150, low=100, high=130)
    bad["pDrCotVal"] = 0
    report = audit_history([bad], expected_ins_code=INS_CODE)
    assert report["zero_or_negative_price_counts"]["pDrCotVal"] == 1
    assert report["ohlc_consistency_flag_count"] == 1
    assert "open_outside_low_high" in report["ohlc_consistency_flags_sample"][0]["flags"]


def test_audit_flags_large_returns_and_long_calendar_gaps():
    report = audit_history([
        row(20261001, 100),
        row(20261010, 150),
    ], expected_ins_code=INS_CODE, outlier_threshold=0.30)
    assert report["large_return_flag_count_sample_capped"] == 1
    assert report["large_return_flags"][0]["return"] == 0.5
    assert report["calendar_gap_flag_count_sample_capped"] == 1
    assert "Iranian trading calendar" in report["calendar_gap_flags"][0]["note"]


def test_audit_rejects_bad_input_and_threshold():
    with pytest.raises(ValueError, match="JSON array"):
        audit_history({})
    with pytest.raises(ValueError, match="outlier_threshold"):
        audit_history([], outlier_threshold=0)


def test_audit_report_never_approves_scoring():
    report = audit_history([row(20261015, 100)], expected_ins_code=INS_CODE)
    assert report["eligible_for_production_scoring"] is False
    assert report["approval_status"] == "not_approved"
    assert "commercial reuse rights" in " ".join(report["limitations"])
