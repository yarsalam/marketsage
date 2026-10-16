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
