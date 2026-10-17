from decimal import Decimal

import httpx
import pytest

from tsetmc_provider import (
    TsetmcClient, TsetmcPayloadError, normalize_daily_history,
)


def test_daily_history_uses_expected_endpoint_and_envelope():
    def handler(request):
        assert request.url.path.endswith("/ClosingPrice/GetClosingPriceDailyList/12345/0")
        return httpx.Response(200, json={"closingPriceDaily": [{"dEven": 20261015, "pClosing": 1200}]})
    with TsetmcClient(transport=httpx.MockTransport(handler)) as client:
        rows = client.daily_history("12345")
    assert rows[0]["pClosing"] == 1200


def test_rejects_non_numeric_instrument_code():
    with TsetmcClient(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={}))) as client:
        with pytest.raises(ValueError):
            client.daily_history("FOLD")


def test_normalizer_keeps_unit_and_scoring_disabled():
    rows = normalize_daily_history([{"dEven": 20261015, "pClosing": "1234.5", "qTotTran5J": 20}])
    assert rows[0]["close"] == Decimal("1234.5")
    assert rows[0]["volume"] == Decimal("20")
    assert rows[0]["unit"] is None
    assert rows[0]["eligible_for_scoring"] is False


@pytest.mark.parametrize("rows", [None, {}, [{"dEven": "2026-10-15"}], [{"dEven": 20261015, "pClosing": -1}]])
def test_rejects_invalid_history(rows):
    with pytest.raises(TsetmcPayloadError):
        normalize_daily_history(rows)


def test_rejects_duplicate_dates():
    with pytest.raises(TsetmcPayloadError, match="duplicate"):
        normalize_daily_history([{"dEven": 20261015}, {"dEven": "20261015"}])
