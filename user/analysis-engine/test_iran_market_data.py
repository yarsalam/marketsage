from datetime import date, datetime, timezone

import pytest

from iran_market_data import (
    DataQualityError,
    MarketDataPoint,
    provider_catalog,
    validate_points,
)


def point(**overrides):
    values = dict(
        market="iran_equities",
        symbol="IRO1TEST0001",
        observed_at=date(2026, 10, 15),
        close=12500.0,
        currency="IRT",
        price_unit="toman_per_share",
        source="fixture:test",
        retrieved_at=datetime(2026, 10, 16, 8, tzinfo=timezone.utc),
        adjusted=True,
        volume=1200.0,
    )
    values.update(overrides)
    return MarketDataPoint(**values)


def test_catalog_does_not_claim_unverified_iran_feeds_are_ready():
    catalog = provider_catalog()
    markets = {item["market"]: item for item in catalog["markets"]}
    assert {"iran_equities", "iran_gold_coin", "iran_fx", "crypto_global", "crypto_local"} <= set(markets)
    assert markets["iran_equities"]["enabled_for_scoring"] is False
    assert markets["iran_gold_coin"]["enabled_for_scoring"] is False
    assert markets["iran_fx"]["enabled_for_scoring"] is False
    assert markets["iran_equities"]["candidate_endpoints"]


def test_valid_point_is_preserved_without_currency_conversion():
    result = validate_points([point()], today=date(2026, 10, 16))
    assert len(result) == 1
    assert result[0].currency == "IRT"
    assert result[0].close == 12500.0


@pytest.mark.parametrize("overrides", [
    {"close": 0},
    {"close": float("nan")},
    {"currency": "USD"},
    {"price_unit": "usd_per_token"},
    {"retrieved_at": datetime(2026, 10, 16, 8)},
    {"observed_at": date(2026, 10, 17)},
    {"volume": -1},
])
def test_invalid_points_fail_closed(overrides):
    with pytest.raises(DataQualityError):
        validate_points([point(**overrides)], today=date(2026, 10, 16))


def test_duplicate_daily_observations_are_rejected():
    with pytest.raises(DataQualityError, match="Duplicate"):
        validate_points([point(), point()], today=date(2026, 10, 16))


def test_stale_observation_is_rejected():
    with pytest.raises(DataQualityError, match="Stale"):
        validate_points([point(observed_at=date(2026, 10, 1))], today=date(2026, 10, 16))
