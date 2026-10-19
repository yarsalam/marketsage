from __future__ import annotations

from decimal import Decimal

import pytest

from tindex_normalizer import (\n    TindexPayloadError, normalize_currency_rates, normalize_indicator_candles,\n)


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



def valid_candle_payload():
    return {
        "success": True,
        "data": {
            "slug": "GOLD-18K",
            "range": "3m",
            "interval": "daily",
            "count": 4,
            "t": [20560, 1, 1, 1],
            "o": [10, 11, 12, 13],
            "h": [12, 13, 14, 14],
            "l": [9, 10, 11, 12],
            "c": [11, 12, 13, 13.5],
            "partial": [False, False, False, True],
            "unit": "تومان/گرم",
            "source": "تیندکس",
        },
    }


def test_normalizes_delta_encoded_candles_and_keeps_unit_and_partial_flag():
    rows = normalize_indicator_candles(valid_candle_payload())

    assert len(rows) == 4
    assert [row["observation_date"] for row in rows] == [
        "2026-04-17", "2026-04-18", "2026-04-19", "2026-04-20"
    ]
    assert rows[0]["instrument_key"] == "GOLD-18K"
    assert rows[0]["open"] == Decimal("10")
    assert rows[-1]["close"] == Decimal("13.5")
    assert rows[-1]["partial"] is True
    assert rows[0]["unit"] == "تومان/گرم"
    assert rows[0]["eligible_for_scoring"] is False


@pytest.mark.parametrize("mutate, message", [
    (lambda d: d.update(h=[12, 13]), "length must match"),
    (lambda d: d.update(count=99), "count must match"),
    (lambda d: d.update(t=[20560, 1, 0, 1]), "deltas must be positive"),
    (lambda d: d.update(partial=[False, False, "false", True]), "must be boolean"),
    (lambda d: d.update(c=[11, 12, float("nan"), 13.5]), "finite number"),
    (lambda d: d.update(h=[12, 13, 11, 14]), "OHLC high/low invariants"),
])
def test_rejects_invalid_candle_vectors(mutate, message):
    import copy

    payload = copy.deepcopy(valid_candle_payload())
    mutate(payload["data"])
    with pytest.raises(TindexPayloadError, match=message):
        normalize_indicator_candles(payload)


def test_rejects_unknown_or_incomplete_candle_envelopes():
    with pytest.raises(TindexPayloadError, match="success"):
        normalize_indicator_candles({"success": False, "data": {}})
    with pytest.raises(TindexPayloadError, match="data.t"):
        normalize_indicator_candles({
            "success": True,
            "data": {"slug": "btc", "o": [1], "h": [1], "l": [1], "c": [1], "partial": [False]},
        })
