from source_acceptance import evaluate_acceptance
from source_registry import SOURCES


def _complete_evidence(source_id):
    source = next(item for item in SOURCES if item.source_id == source_id)
    return {
        "source_id": source_id,
        "reviewer": "data-review",
        "reviewed_at": "2026-10-16T12:00:00+00:00",
        "rights_review": "passed",
        "host_connectivity": "passed",
        "timestamp_quality": "passed",
        "historical_coverage": "passed",
        "unit_reconciliation": "passed",
        "checks": {
            name: {"status": "passed", "evidence": f"evidence/{name}.md"}
            for name in source.required_checks
        },
    }


def test_complete_evidence_is_not_automatically_production_approval():
    evidence = _complete_evidence("iran.tsetmc")
    report = evaluate_acceptance("iran.tsetmc", evidence)
    assert report["evidence_complete"] is True
    assert report["missing_items"] == []
    assert report["failed_items"] == []
    assert report["production_scoring_allowed"] is False
    assert report["production_scoring_gate"]["eligible_for_production_scoring"] is False


def test_missing_and_failed_evidence_are_reported_separately():
    evidence = _complete_evidence("iran.codal")
    evidence["checks"].pop("publication_timestamp")
    evidence["checks"]["amendment_linkage"]["status"] = "failed"
    report = evaluate_acceptance("iran.codal", evidence)
    assert "check:publication_timestamp" in report["missing_items"]
    assert "check:amendment_linkage" in report["failed_items"]
    assert report["evidence_complete"] is False


def test_evidence_requires_timezone_aware_review_timestamp():
    evidence = _complete_evidence("global.yahoo_finance.yfinance")
    evidence["reviewed_at"] = "2026-10-16T12:00:00"
    report = evaluate_acceptance("global.yahoo_finance.yfinance", evidence)
    assert "reviewed_at_timezone_aware" in report["missing_items"]


def test_unknown_source_fails_closed():
    report = evaluate_acceptance("unknown.provider", {})
    assert report["evidence_complete"] is False
    assert report["missing_items"] == ["source_not_registered"]
    assert report["production_scoring_allowed"] is False


def test_unknown_check_names_are_not_silently_accepted():
    evidence = _complete_evidence("iran.tsetmc")
    evidence["checks"]["made_up_check"] = {
        "status": "passed", "evidence": "evidence/fake.md"
    }
    report = evaluate_acceptance("iran.tsetmc", evidence)
    assert "unexpected_check:made_up_check" in report["missing_items"]
    assert report["evidence_complete"] is False


def test_non_object_evidence_fails_closed_without_exception():
    report = evaluate_acceptance("iran.tsetmc", None)
    assert report["evidence_complete"] is False
    assert report["production_scoring_allowed"] is False
    assert report["missing_items"] == ["evidence_object"]


def test_pending_top_level_review_is_not_treated_as_passed():
    evidence = _complete_evidence("iran.codal")
    evidence["rights_review"] = "pending"
    report = evaluate_acceptance("iran.codal", evidence)
    assert "rights_review" in report["failed_items"]
    assert report["evidence_complete"] is False

def test_cli_prints_json_and_returns_one_when_evidence_is_complete_but_source_is_blocked(tmp_path, capsys):
    import json
    from source_acceptance import main

    evidence = _complete_evidence("iran.tsetmc")
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(evidence), encoding="utf-8")

    assert main([str(path)]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["evidence_complete"] is True
    assert output["production_scoring_allowed"] is False


def test_cli_returns_two_for_incomplete_evidence(tmp_path, capsys):
    import json
    from source_acceptance import main

    path = tmp_path / "evidence.json"
    path.write_text(json.dumps({"source_id": "iran.tsetmc"}), encoding="utf-8")

    assert main([str(path)]) == 2
    output = json.loads(capsys.readouterr().out)
    assert output["evidence_complete"] is False
    assert output["missing_items"]


def test_cli_returns_three_for_malformed_json(tmp_path, capsys):
    from source_acceptance import main

    path = tmp_path / "evidence.json"
    path.write_text("{not-json", encoding="utf-8")

    assert main([str(path)]) == 3
    output = capsys.readouterr().out
    assert '"error"' in output


def test_cli_returns_three_for_missing_file(tmp_path, capsys):
    from source_acceptance import main

    assert main([str(tmp_path / "missing.json")]) == 3
    assert '"error"' in capsys.readouterr().out


def test_cli_requires_exactly_one_argument(capsys):
    from source_acceptance import main

    assert main([]) == 3
    assert "Usage:" in capsys.readouterr().err



def test_unit_reconciliation_failure_blocks_source_acceptance():
    evidence = _complete_evidence("iran.tsetmc")
    evidence["unit_reconciliation"] = "failed"

    report = evaluate_acceptance("iran.tsetmc", evidence)

    assert "unit_reconciliation" in report["failed_items"]
    assert report["evidence_complete"] is False
    assert report["production_scoring_allowed"] is False
    assert report["production_scoring_gate"]["eligible_for_production_scoring"] is False
