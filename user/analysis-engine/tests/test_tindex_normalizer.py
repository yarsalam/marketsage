from __future__ import annotations

from decimal import Decimal

import pytest

from tindex_normalizer import TindexPayloadError, normalize_currency_rates


def valid_payload():
    return {
        "success": True,
        "data": [
            {"key": "usd", "name": "USD rate", "rate": 123456, "decimals": 0},
            {"key": "gold", "name": "Gold quote", "rate": 123456.75, "decimals": 2},
        ],
    }


def test_normalizes_observed_envelope_without_guessing_semantics():
    rows = normalize_currency_rates(valid_payload())

    assert len(rows) == 2
    assert rows[0]["source_id"] == "iran.tindex.public_api"
    assert rows[0]["instrument_key"] == "usd"
    assert rows[0]["raw_rate"] == Decimal("123456")
    assert rows[1]["raw_rate"] == Decimal("123456.75")
    for row in rows:
        assert row["unit"] is None
        assert row["market_definition"] is None
        assert row["observed_at"] is None
        assert row["retrieved_at"] is None
        assert row["eligible_for_scoring"] is False


def test_empty_data_is_valid_but_returns_no_rows():
    assert normalize_currency_rates({"success": True, "data": []}) == []


@pytest.mark.parametrize("payload", [
    None,
    [],
    {"success": False, "data": []},
    {"success": True},
    {"success": True, "data": {}},
])
def test_rejects_invalid_envelopes(payload):
    with pytest.raises(TindexPayloadError):
        normalize_currency_rates(payload)


@pytest.mark.parametrize("rate", [
    None, True, False, "123", -1, float("nan"), float("inf"), float("-inf"),
])
def test_rejects_invalid_rates(rate):
    payload = {"success": True, "data": [
        {"key": "usd", "name": "USD", "rate": rate, "decimals": 2}
    ]}
    with pytest.raises(TindexPayloadError, match="rate"):
        normalize_currency_rates(payload)


@pytest.mark.parametrize("record", [
    {"key": "", "name": "USD", "rate": 1, "decimals": 2},
    {"key": "usd", "name": " ", "rate": 1, "decimals": 2},
    {"key": "usd", "name": "USD", "rate": 1, "decimals": True},
    {"key": "usd", "name": "USD", "rate": 1, "decimals": -1},
])
def test_rejects_invalid_record_fields(record):
    with pytest.raises(TindexPayloadError):
        normalize_currency_rates({"success": True, "data": [record]})


def test_rejects_duplicate_instrument_keys():
    payload = {"success": True, "data": [
        {"key": "usd", "name": "USD", "rate": 1, "decimals": 2},
        {"key": " usd ", "name": "Dollar", "rate": 2, "decimals": 2},
    ]}
    with pytest.raises(TindexPayloadError, match="duplicated"):
        normalize_currency_rates(payload)
