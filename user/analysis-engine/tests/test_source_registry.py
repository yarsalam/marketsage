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
    vendor = entries["vendor.streamdata_export"]
    assert vendor["scoring_gate"]["eligible_for_production_scoring"] is False
    assert vendor["approved_for_production"] is False
    assert "unit_currency_and_quote_convention" in vendor["required_checks"]




def test_new_official_global_candidates_are_registered_but_remain_fail_closed():
    expected = {
        "global.sec_edgar",
        "global.ecb_data_portal",
        "global.us_treasury_yield_curve",
        "global.eia_energy_api",
        "global.imf_sdmx_api",
    }
    entries = {source.source_id: source for source in SOURCES}
    assert expected <= set(entries)
    for source_id in expected:
        source = entries[source_id]
        assert source.status == "candidate_requires_validation"
        assert source.used_by_research_engine is False
        assert source.approved_for_production is False
        assert source_scoring_gate(source_id)["eligible_for_production_scoring"] is False

def test_iran_cbi_macro_and_bond_auction_candidates_remain_fail_closed():
    catalog = source_catalog()
    entries = {item["source_id"]: item for item in catalog["sources"]}
    expected = {
        "iran.official_macro",
        "iran.cbi.bond_auction_results",
    }
    assert expected <= set(entries)
    macro = entries["iran.official_macro"]
    bond = entries["iran.cbi.bond_auction_results"]
    assert "official_transfer_fx_candidate" in macro["data_kinds"]
    assert "weekly_policy_rate_candidate" in macro["data_kinds"]
    assert "government_bond_auction_result_candidate" in bond["data_kinds"]
    for source_id in expected:
        source = next(source for source in SOURCES if source.source_id == source_id)
        assert source.status == "candidate_requires_validation"
        assert source.used_by_research_engine is False
        assert source.approved_for_production is False
        assert source_scoring_gate(source_id)["eligible_for_production_scoring"] is False

