from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest

from binance_public_provider import (
    BinancePublicClient,
    BinancePublicError,
    normalize_klines,
)


KLINES = [
    [1700000000000, "100", "110", "90", "105", "5",
     1700086399999, "500", 100, "2", "210", "0"],
    [1700086400000, "105", "115", "102", "111", "6",
     1700172799999, "660", 110, "3", "330", "0"],
]


def test_normalizes_public_klines_and_marks_candidate_only():
    rows = normalize_klines(
        KLINES, symbol="BTCUSDT", interval="1d",
        retrieved_at=datetime(2023, 11, 20, tzinfo=timezone.utc),
    )
    assert len(rows) == 2
    assert rows[0]["open"] == Decimal("100")
    assert rows[0]["base_volume"] == Decimal("5")
    assert rows[0]["quote_volume"] == Decimal("500")
    assert rows[0]["instrument_key"] == "BTCUSDT"
    assert rows[0]["quote_asset"] is None
    assert rows[0]["eligible_for_scoring"] is False
    assert rows[0]["observation_time_utc"].endswith("+00:00")


def test_client_uses_unauthenticated_public_market_data_endpoint():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        seen["api_key_header"] = request.headers.get("X-MBX-APIKEY")
        return httpx.Response(200, json=KLINES[:1])

    with BinancePublicClient(base_url="https://binance.example.test",
                             transport=httpx.MockTransport(handler)) as client:
        rows = client.klines("BTCUSDT", interval="1d", limit=1)

    assert seen["path"] == "/api/v3/klines"
    assert seen["params"] == {"symbol": "BTCUSDT", "interval": "1d", "limit": "1"}
    assert seen["api_key_header"] is None
    assert len(rows) == 1


def test_ohlc_anomalies_and_duplicate_times_are_rejected():
    broken = [list(KLINES[0])]
    broken[0][2] = "99"  # high below open and close
    with pytest.raises(BinancePublicError, match="OHLC"):
        normalize_klines(broken, symbol="BTCUSDT")

    with pytest.raises(BinancePublicError, match="duplicate"):
        normalize_klines([KLINES[0], KLINES[0]], symbol="BTCUSDT")


def test_errors_do_not_echo_provider_body_or_request_details():
    def handler(request):
        return httpx.Response(429, json={"msg": "sensitive diagnostic body"})

    with BinancePublicClient(base_url="https://binance.example.test",
                             transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(BinancePublicError) as caught:
            client.klines("BTCUSDT")
    assert "sensitive diagnostic body" not in str(caught.value)


def test_bad_limits_and_intervals_fail_before_network():
    with BinancePublicClient(base_url="https://binance.example.test",
                             transport=httpx.MockTransport(
                                 lambda request: pytest.fail("unexpected network call"))) as client:
        with pytest.raises(ValueError):
            client.klines("BTCUSDT", limit=1001)
        with pytest.raises(ValueError):
            client.klines("BTCUSDT", interval="5y")
