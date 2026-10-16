from source_registry import SOURCES, source_catalog, source_scoring_gate


def test_every_current_source_fails_closed_for_production_scoring():
    catalog = source_catalog()
    assert catalog["summary"]["production_approved"] == 0
    for source in SOURCES:
        gate = source_scoring_gate(source.source_id)
        assert gate["eligible_for_production_scoring"] is False
        assert "production_approval_missing" in gate["blocked_reasons"]
        assert "source_status_not_production_approved" in gate["blocked_reasons"]


def test_unknown_source_is_blocked_by_default():
    gate = source_scoring_gate("unregistered.provider")
    assert gate == {
        "source_id": "unregistered.provider",
        "eligible_for_production_scoring": False,
        "blocked_reasons": ["source_not_registered"],
    }


def test_registry_exposes_gate_decision_for_audit_clients():
    catalog = source_catalog()
    entries = {item["source_id"]: item for item in catalog["sources"]}
    iran = entries["iran.tsetmc"]
    assert iran["scoring_gate"]["eligible_for_production_scoring"] is False
    assert "production_approval_missing" in iran["scoring_gate"]["blocked_reasons"]
