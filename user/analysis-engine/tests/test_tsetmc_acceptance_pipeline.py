from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_tsetmc_acceptance_pipeline import (  # noqa: E402
    audit_history,
    classify_price_input_semantics,
    discover_manifest,
    load_manifest,
    looks_like_history,
    run_pipeline,
)


def _fixture(root: Path, *, duplicate_date: bool = False, with_evidence: bool = True, history_semantics: str = "raw_unadjusted") -> tuple[Path, list[Path]]:
    root.mkdir(parents=True, exist_ok=True)
    daily, chart, event = [], {}, []
    start = date(2020, 1, 1)
    for i in range(400):
        day = start + timedelta(days=i)
        close = 1000 + i
        daily.append({
            "dEven": int(day.strftime("%Y%m%d")),
            "pClosing": close,
            "pDrCotVal": close + 1,
            "priceFirst": close - 2,
            "priceMax": close + 4,
            "priceMin": close - 4,
            "priceYesterday": close - 3,
            "qTotTran5J": 100 + i,
            "qTotCap": (100 + i) * close,
        })
        chart[day.strftime("%Y%m%d")] = [
            day.strftime("%Y%m%d"), close * .84 + 4, close * .84 - 4,
            close * .84 - 2, close * .84 + 1, 100 + i, close * .84,
        ]
    if duplicate_date:
        daily.append(dict(daily[10]))
    daily_path, chart_path, event_path, share_path = (
        root / "daily_history_raw.json", root / "chart_adjusted_raw.json",
        root / "price_adjustments_raw.json", root / "share_changes_raw.json",
    )
    daily_path.write_text(json.dumps({"closingPriceDaily": daily}), encoding="utf-8")
    chart_path.write_text(json.dumps(chart), encoding="utf-8")
    event_path.write_text(json.dumps({"priceAdjust": [{"dEven": "20200111", "eventType": "split"}]}), encoding="utf-8")
    share_path.write_text(json.dumps({"instrumentShareChange": [{"dEven": "20200211", "eventType": "share_change"}]}), encoding="utf-8")

    evidence = {}
    evidence_paths = []
    if with_evidence:
        for key in ("identity", "rights", "semantics", "independent", "corporate_actions"):
            p = root / f"{key}_evidence.txt"
            p.write_text(f"synthetic local test evidence: {key}", encoding="utf-8")
            evidence[key] = str(p)
            evidence_paths.append(p)

    manifest = root / "manifest.csv"
    columns = [
        "instrument_code", "symbol", "isin", "daily_history_path", "adjusted_chart_path",
        "adjustment_events_path", "share_change_events_path", "history_close_semantics", "rights_status", "semantics_verified",
        "independent_reconciliation_passed", "corporate_action_completeness_verified",
        "identity_match_evidence_ref", "rights_evidence_ref", "semantics_evidence_ref",
        "independent_reconciliation_evidence_ref", "corporate_action_completeness_evidence_ref",
    ]
    with manifest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        row = {
            "instrument_code": "46348559193224090",
            "symbol": "FOLAD",
            "isin": "IRTEST000001",
            "daily_history_path": str(daily_path),
            "adjusted_chart_path": str(chart_path),
            "adjustment_events_path": str(event_path),
            "share_change_events_path": str(share_path),
            "history_close_semantics": history_semantics,
            "rights_status": "approved",
            "semantics_verified": "true",
            "independent_reconciliation_passed": "true",
            "corporate_action_completeness_verified": "true",
        }
        if with_evidence:
            row.update({
                "identity_match_evidence_ref": evidence["identity"],
                "rights_evidence_ref": evidence["rights"],
                "semantics_evidence_ref": evidence["semantics"],
                "independent_reconciliation_evidence_ref": evidence["independent"],
                "corporate_action_completeness_evidence_ref": evidence["corporate_actions"],
            })
        writer.writerow(row)
    return manifest, [daily_path, chart_path, event_path, share_path, *evidence_paths]


def test_complete_pipeline_emits_features_and_six_month_labels_only_after_evidence(tmp_path: Path) -> None:
    manifest, inputs = _fixture(tmp_path / "input")
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    rows = load_manifest(manifest)
    summary = run_pipeline(rows, manifest_path=manifest, output_root=tmp_path / "out", min_history=252)
    out = Path(summary["output_dir"])

    with (out / "instrument_decisions.csv").open(encoding="utf-8", newline="") as f:
        decision = next(csv.DictReader(f))
    assert decision["decision_status"] == "research_eligible_after_explicit_evidence_review"
    assert decision["eligible_for_research"] == "True"
    assert decision["eligible_for_scoring"] == "False"
    assert summary["research_eligible_count"] == 1
    assert summary["flags"]["network_requests_made"] is False
    assert summary["flags"]["raw_inputs_overwritten"] is False

    with (out / "research_features.csv").open(encoding="utf-8", newline="") as f:
        features = list(csv.DictReader(f))
    with (out / "forward_labels_6m.csv").open(encoding="utf-8", newline="") as f:
        labels = list(csv.DictReader(f))
    assert len(features) == 400
    assert labels
    assert all(int(row["horizon_calendar_days"]) >= 180 for row in labels)
    assert all(row["instrument_code"] == "46348559193224090" for row in features)
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs} == before
    assert (out / "input_history_candidate.csv").is_file()
    assert (out / "adjusted_candidate_daily.csv").is_file()
    assert (out / "event_reconciliation.csv").is_file()
    with (out / "event_reconciliation.csv").open(encoding="utf-8", newline="") as f:
        reconciled_events = list(csv.DictReader(f))
    assert {row["event_family"] for row in reconciled_events} == {"price_adjustment", "share_change"}
    assert decision["eligible_for_backtest"] == "False"
    assert summary["flags"]["backtest_approved"] is False
    assert (out / "history_gap_audit.csv").is_file()
    assert (out / "adjustment_factor_audit.csv").is_file()
    assert (out / "reprocessing_queue.csv").is_file()


def test_missing_traceable_evidence_keeps_series_out_of_research_manifest(tmp_path: Path) -> None:
    manifest, _ = _fixture(tmp_path / "input", with_evidence=False)
    summary = run_pipeline(load_manifest(manifest), manifest_path=manifest, output_root=tmp_path / "out", min_history=252)
    out = Path(summary["output_dir"])
    assert summary["research_eligible_count"] == 0
    with (out / "research_features.csv").open(encoding="utf-8", newline="") as f:
        assert list(csv.DictReader(f)) == []
    with (out / "research_eligible_manifest.csv").open(encoding="utf-8", newline="") as f:
        assert list(csv.DictReader(f)) == []
    assert summary["flags"]["production_scoring_enabled"] is False


def test_duplicate_history_is_queued_not_silently_deduplicated(tmp_path: Path) -> None:
    manifest, _ = _fixture(tmp_path / "input", duplicate_date=True)
    summary = run_pipeline(load_manifest(manifest), manifest_path=manifest, output_root=tmp_path / "out", min_history=252)
    out = Path(summary["output_dir"])
    with (out / "instrument_decisions.csv").open(encoding="utf-8", newline="") as f:
        decision = next(csv.DictReader(f))
    assert decision["duplicate_history_date_rows"] == "1"
    assert decision["decision_status"] == "needs_reprocessing"
    assert decision["eligible_for_research"] == "False"
    assert summary["reprocessing_queue_count"] == 1


def test_discovery_splits_combined_csv_by_instrument_code(tmp_path: Path) -> None:
    path = tmp_path / "prices.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["instrument_code", "symbol", "isin", "date", "close"])
        writer.writeheader()
        writer.writerow({"instrument_code": "46348559193224090", "symbol": "FOLAD", "isin": "IRTEST000001", "date": "2020-01-01", "close": 100})
        writer.writerow({"instrument_code": "12345678901234567", "symbol": "TEST2", "isin": "IRTEST000002", "date": "2020-01-01", "close": 200})
    items = discover_manifest(tmp_path)
    assert {row["instrument_code"] for row in items} == {"46348559193224090", "12345678901234567"}


def test_unknown_input_semantics_blocks_feature_and_label_creation(tmp_path: Path) -> None:
    manifest, _ = _fixture(tmp_path / "input", history_semantics="unknown")
    summary = run_pipeline(load_manifest(manifest), manifest_path=manifest, output_root=tmp_path / "out", min_history=252)
    out = Path(summary["output_dir"])
    assert summary["research_eligible_count"] == 0
    assert summary["research_feature_rows"] == 0
    assert summary["forward_label_rows"] == 0
    with (out / "instrument_decisions.csv").open(encoding="utf-8", newline="") as f:
        decision = next(csv.DictReader(f))
    assert decision["price_input_semantics"] == "unknown_unverified"
    assert "PRICE_INPUT_SEMANTICS_NOT_EXPLICITLY_RAW_UNADJUSTED" in decision["decision_reason_codes"]


def test_standard_tsetmc_angle_bracket_csv_headers_are_recognized_but_semantics_stay_unknown() -> None:
    rows = [
        {"<DTYYYYMMDD>": "20200101", "<OPEN>": "100", "<HIGH>": "105", "<LOW>": "95", "<CLOSE>": "101", "<VOL>": "1000"},
        {"<DTYYYYMMDD>": "20200102", "<OPEN>": "101", "<HIGH>": "106", "<LOW>": "100", "<CLOSE>": "104", "<VOL>": "1100"},
    ]
    assert looks_like_history(rows)
    audited = audit_history(rows)
    assert audited["invalid_date_rows"] == 0
    assert audited["invalid_or_nonpositive_close_rows"] == 0
    assert audited["ohlc_violation_rows"] == 0
    assert classify_price_input_semantics(rows, "") == "unknown_unverified"
    assert classify_price_input_semantics([{"dEven": 20200101, "pClosing": 100}], "") == "tsetmc_pClosing_candidate_unverified"


def test_long_history_gaps_are_quarantined_and_reported_without_filling(tmp_path: Path) -> None:
    manifest, inputs = _fixture(tmp_path / "input")
    daily_path, chart_path = inputs[0], inputs[1]
    payload = json.loads(daily_path.read_text(encoding="utf-8"))
    rows = payload["closingPriceDaily"]
    kept = rows[:150] + rows[195:]
    keep_dates = {str(row["dEven"]) for row in kept}
    payload["closingPriceDaily"] = kept
    daily_path.write_text(json.dumps(payload), encoding="utf-8")

    chart = json.loads(chart_path.read_text(encoding="utf-8"))
    chart_path.write_text(json.dumps({day: row for day, row in chart.items() if day in keep_dates}), encoding="utf-8")

    summary = run_pipeline(load_manifest(manifest), manifest_path=manifest, output_root=tmp_path / "out", min_history=252)
    out = Path(summary["output_dir"])
    with (out / "instrument_decisions.csv").open(encoding="utf-8", newline="") as f:
        decision = next(csv.DictReader(f))
    assert decision["decision_status"] == "quarantine_needs_independent_evidence"
    assert int(decision["gap_intervals_gt_30_days"]) == 1
    assert "LONG_HISTORY_GAPS_NEED_CALENDAR_OR_SUSPENSION_REVIEW" in decision["decision_reason_codes"]
    assert summary["research_eligible_count"] == 0
    assert summary["research_feature_rows"] == 0
    assert summary["forward_label_rows"] == 0

    with (out / "history_gap_audit.csv").open(encoding="utf-8", newline="") as f:
        gaps = list(csv.DictReader(f))
    long_gaps = [row for row in gaps if row["severity"] == "LONG_GAP_OVER_30_DAYS"]
    assert len(long_gaps) == 1
    assert int(long_gaps[0]["calendar_gap_days"]) > 30
    assert long_gaps[0]["review_status"] == "pending_calendar_suspension_or_missing-data_review"


def test_history_audit_flags_invalid_dates_values_duplicate_and_ohlc() -> None:
    result = audit_history([
        {"dEven": 20200101, "pClosing": 100, "priceFirst": 101, "priceMax": 99, "priceMin": 95},
        {"dEven": 20200101, "pClosing": 0},
        {"dEven": "bad", "pClosing": 120},
    ])
    assert result["invalid_date_rows"] == 1
    assert result["invalid_or_nonpositive_close_rows"] == 1
    assert result["duplicate_history_date_rows"] == 1
    assert result["ohlc_violation_rows"] >= 1
