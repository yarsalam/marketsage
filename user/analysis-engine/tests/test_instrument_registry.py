import pytest

from instrument_registry import (
    EMPTY_UNIVERSES,
    _INSTRUMENT_ROWS,
    InstrumentDefinition,
    InstrumentRegistryError,
    instrument_catalog,
    validate_registry,
)


def test_freshness_policy_is_specific_to_registered_instrument_type():
    from instrument_registry import freshness_policy_for

    assert freshness_policy_for("global.yahoo_finance.yfinance", "BTC-USD")[0] == 3
    assert freshness_policy_for("global.yahoo_finance.yfinance", "SPY")[0] == 7
    assert freshness_policy_for("other.source", "CPIAUCSL")[0] is None
    assert freshness_policy_for("global.yahoo_finance.yfinance", "UNKNOWN")[0] is None


def test_catalog_uses_canonical_ids_separate_from_provider_symbols():
    catalog = instrument_catalog()
    assert catalog["registry_version"] == "1.0.0"
    assert catalog["summary"] == {
        "instrument_count": 11,
        "global_proxy_count": 11,
        "production_approved_count": 0,
        "iran_instrument_count": 0,
        "quarantined_iran_universes": 5,
    }
    assert all(item["instrument_id"] != item["provider_symbol"] for item in catalog["instruments"])
    assert len({item["instrument_id"] for item in catalog["instruments"]}) == 11


def test_global_proxy_units_are_explicit_and_typed():
    catalog = instrument_catalog()
    instruments = {item["provider_symbol"]: item for item in catalog["instruments"]}
    assert instruments["BTC-USD"]["quote_currency"] == "USD"
    assert instruments["BTC-USD"]["quote_unit"] == "usd_per_token"
    assert instruments["BTC-USD"]["price_basis"] == "provider_close"
    assert instruments["SPY"]["quote_currency"] == "USD"
    assert instruments["SPY"]["quote_unit"] == "usd_per_share"
    assert instruments["SPY"]["price_basis"] == "adjusted_close"


def test_iran_universes_are_empty_and_quarantined():
    catalog = instrument_catalog()
    assert catalog["empty_universes"] == [dict(item) for item in EMPTY_UNIVERSES]
    assert catalog["summary"]["iran_instrument_count"] == 0
    assert all(item["status"] == "empty_quarantined" for item in catalog["empty_universes"])


def test_no_instrument_is_approved_or_scoring_eligible():
    for instrument in instrument_catalog()["instruments"]:
        assert instrument["production_approved"] is False
        assert instrument["scoring_gate"]["eligible"] is False
        assert instrument["venue"] is None
        assert instrument["tradability_status"] == "not_assessed"


def test_duplicate_canonical_ids_are_rejected():
    duplicate = InstrumentDefinition(**{
        **_INSTRUMENT_ROWS[0].__dict__,
        "provider_symbol": "BTC-USD-SECOND-MAPPING",
    })
    with pytest.raises(InstrumentRegistryError, match="duplicate canonical"):
        validate_registry((*_INSTRUMENT_ROWS, duplicate))


def test_duplicate_source_symbol_mappings_are_rejected():
    duplicate = InstrumentDefinition(**{
        **_INSTRUMENT_ROWS[0].__dict__,
        "instrument_id": "global.proxy.crypto.bitcoin_alias",
    })
    with pytest.raises(InstrumentRegistryError, match="duplicate provider/source"):
        validate_registry((*_INSTRUMENT_ROWS, duplicate))


def test_wrong_quote_unit_fails_closed():
    invalid = InstrumentDefinition(**{
        **_INSTRUMENT_ROWS[0].__dict__,
        "instrument_id": "global.proxy.crypto.invalid_unit",
        "provider_symbol": "INVALID-USD",
        "quote_unit": "usd_per_share",
    })
    with pytest.raises(InstrumentRegistryError, match="quote_unit"):
        validate_registry((*_INSTRUMENT_ROWS, invalid))


def test_production_approval_cannot_be_granted_by_catalog():
    invalid = InstrumentDefinition(**{
        **_INSTRUMENT_ROWS[0].__dict__,
        "instrument_id": "global.proxy.crypto.invalid_approval",
        "provider_symbol": "APPROVED-USD",
        "production_approved": True,
    })
    with pytest.raises(InstrumentRegistryError, match="cannot grant production approval"):
        validate_registry((*_INSTRUMENT_ROWS, invalid))


def test_unknown_venue_and_tradability_cannot_be_inferred():
    invalid = InstrumentDefinition(**{
        **_INSTRUMENT_ROWS[0].__dict__,
        "instrument_id": "global.proxy.crypto.assumed_venue",
        "provider_symbol": "VENUE-USD",
        "venue": "assumed exchange",
    })
    with pytest.raises(InstrumentRegistryError, match="unknown venue"):
        validate_registry((*_INSTRUMENT_ROWS, invalid))
