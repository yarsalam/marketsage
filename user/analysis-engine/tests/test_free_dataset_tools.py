import csv
import json
from pathlib import Path

from scripts.audit_candidate_dataset import audit_file, normalize_header
from scripts.create_source_evidence_templates import build_template
from scripts.discover_free_datasets import _summarize_search, parse_args


def test_angle_bracket_daily_csv_headers_are_recognized(tmp_path: Path):
    sample = tmp_path / "candidate.csv"
    with sample.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "<DTYYYYMMDD>", "<OPEN>", "<HIGH>", "<LOW>", "<CLOSE>", "<VOL>"
        ])
        writer.writeheader()
        writer.writerow({
            "<DTYYYYMMDD>": "20261001", "<OPEN>": "100", "<HIGH>": "110",
            "<LOW>": "90", "<CLOSE>": "105", "<VOL>": "10",
        })
        writer.writerow({
            "<DTYYYYMMDD>": "20261001", "<OPEN>": "100", "<HIGH>": "101",
            "<LOW>": "90", "<CLOSE>": "105", "<VOL>": "11",
        })
    report = audit_file(sample)
    assert report["row_count"] == 2
    assert report["columns_detected"]["date_or_period"] == "<DTYYYYMMDD>"
    assert report["duplicate_date_count"] == 1
    assert report["ohlc_violation_count"] == 1
    assert report["raw_values_emitted"] is False


def test_header_normalization_strips_brackets_and_case():
    assert normalize_header("<DTYYYYMMDD>") == "dtyyyymmdd"
    assert normalize_header(" Close-Price ") == "close_price"


def test_template_contains_every_registered_check_and_never_approves():
    from source_registry import SOURCES
    source = next(item for item in SOURCES if item.source_id == "global.world_bank_indicators")
    template = build_template(source.source_id)
    assert set(template["checks"]) == set(source.required_checks)
    assert all(item["status"] == "pending" for item in template["checks"].values())
    assert template["reviewed_at"] is None
    assert template["template_only"] is True


def test_discovery_defaults_to_inventory_without_live_requests():
    args = parse_args([])
    assert args.mode == "inventory"
    assert args.source is None


def test_tsetmc_search_summary_only_contains_metadata_and_counts():
    payload = {"instruments": [
        {"lVal30": "فولاد", "insCode": "12345", "internal_price": "999999"},
        {"lVal30": "فملی", "insCode": "67890"},
    ]}
    result = _summarize_search(payload, "فولاد")
    serialized = json.dumps(result, ensure_ascii=False)
    assert result["exact_name_match_count"] == 1
    assert result["exact_matches_with_numeric_instrument_id"] == 1
    assert result["exact_match_identity_samples"][0]["instrument_id"] == "12345"
    assert result["exact_match_identity_samples"][0]["provider_ticker"] == "فولاد"
    assert "999999" not in serialized

def test_annual_macro_csv_is_audited_without_faking_january_first(tmp_path: Path):
    sample = tmp_path / "world_bank.csv"
    sample.write_text(
        "observation_year,value,indicator_id\n2022,21.1,FP.CPI.TOTL.ZG\n2023,,FP.CPI.TOTL.ZG\n2024,25.0,FP.CPI.TOTL.ZG\n",
        encoding="utf-8",
    )
    report = audit_file(sample)
    assert report["status"] == "audited_candidate"
    assert report["date_precision"] == "year"
    assert report["first_date"] is None
    assert report["first_observation_year"] == 2022
    assert report["last_observation_year"] == 2024
    assert report["ohlc_violation_count"] is None
    assert report["missing_numeric_counts"]["value"] == 1


def test_missing_csv_is_reported_instead_of_crashing(tmp_path: Path):
    report = audit_file(tmp_path / "does-not-exist.csv")
    assert report["status"] == "audit_failed"
    assert report["error_type"] == "FileNotFoundError"
    assert report["raw_values_emitted"] is False
