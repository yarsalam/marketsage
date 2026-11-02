from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from fred_alfred_provider import (
    FredAlfredClient,
    FredConfigurationError,
    FredProviderError,
    normalize_fred_observations,
)


def test_normalizes_values_and_preserves_vintage_without_claiming_release_time():
    rows = normalize_fred_observations({
        "observations": [
            {"date": "2024-01-01", "value": "5.25",
             "realtime_start": "2024-02-01", "realtime_end": "2024-02-28"},
            {"date": "2024-02-01", "value": ".",
             "realtime_start": "2024-03-01", "realtime_end": "9999-12-31"},
        ]
    }, series_id="FEDFUNDS")

    assert rows[0]["value"] == Decimal("5.25")
    assert rows[0]["observation_date"] == "2024-01-01"
    assert rows[0]["realtime_start"] == "2024-02-01"
    assert rows[0]["vintage_available_at"] == "2024-02-01T23:59:59+00:00"
    assert rows[0]["publication_timestamp"] is None
    assert rows[1]["value"] is None
    assert all(row["eligible_for_scoring"] is False for row in rows)


@pytest.mark.parametrize("payload", [
    None,
    {},
    {"observations": {}},
    {"observations": [None]},
    {"observations": [{"date": "bad", "value": "1", "realtime_start": "2024-01-01"}]},
    {"observations": [{"date": "2024-01-01", "value": "NaN", "realtime_start": "2024-01-02"}]},
])
def test_rejects_malformed_observations(payload):
    with pytest.raises(FredProviderError):
        normalize_fred_observations(payload, series_id="TEST")


def test_client_sends_key_and_series_but_never_returns_key():
    seen = {}

    def handler(request):
        seen.update(request.url.params)
        return httpx.Response(200, json={"observations": [
            {"date": "2024-01-01", "value": "1.5",
             "realtime_start": "2024-01-02", "realtime_end": "9999-12-31"}
        ]})

    with FredAlfredClient("unit-test-secret", transport=httpx.MockTransport(handler)) as client:
        rows = client.observations("DGS10", observation_start="2024-01-01")
    assert seen["api_key"] == "unit-test-secret"
    assert seen["series_id"] == "DGS10"
    assert rows[0]["value"] == Decimal("1.5")
    assert "unit-test-secret" not in repr(rows)


def test_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    with pytest.raises(FredConfigurationError):
        FredAlfredClient()


def test_bad_dates_and_pagination_are_rejected_before_request():
    with FredAlfredClient("test-key", transport=httpx.MockTransport(
        lambda request: pytest.fail("request should not be sent")
    )) as client:
        with pytest.raises(ValueError, match="observation_start"):
            client.observations("DGS10", observation_start="01-01-2024")
        with pytest.raises(ValueError, match="limit"):
            client.observations("DGS10", limit=0)



def test_network_timeout_is_sanitized_and_not_retried():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        raise httpx.ConnectTimeout("private host and query details")

    with FredAlfredClient("test-key", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(FredProviderError, match=r"FRED network timeout \(ConnectTimeout\)") as exc:
            client.observations("DGS10", limit=1)

    assert calls == ["/fred/series/observations"]
    assert "private host" not in str(exc.value)
