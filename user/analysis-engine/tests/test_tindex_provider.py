from __future__ import annotations

import httpx
import tindex_provider
import pytest

from tindex_provider import (
    TindexAuthenticationError,
    TindexClient,
    TindexConfigurationError,
    TindexEndpointDisabledError,
    TindexRateLimitError,
    tindex_connection_status,
)



@pytest.fixture(autouse=True)
def reset_process_local_quota():
    # Quota state is intentionally shared across clients in the same process.
    with tindex_provider._RATE_LOCK:
        tindex_provider._REQUEST_TIMES.clear()
        tindex_provider._SUCCESSFUL_REQUEST_TIMES.clear()
    yield
    with tindex_provider._RATE_LOCK:
        tindex_provider._REQUEST_TIMES.clear()
        tindex_provider._SUCCESSFUL_REQUEST_TIMES.clear()


def client_for(handler, **kwargs):
    return TindexClient(
        base_url="https://api.example.test",
        token="test-token",
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def test_currency_rates_uses_bearer_auth_and_returns_json():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"success": True, "data": []})

    with client_for(handler) as client:
        assert client.currency_rates() == {"success": True, "data": []}

    assert seen == {
        "path": "/api/public/currency-rates",
        "auth": "Bearer test-token",
    }


def test_tindex_410_is_reported_as_disabled_not_empty_data():
    def handler(request):
        return httpx.Response(410, json={"error": "gone"})

    with client_for(handler) as client:
        with pytest.raises(TindexEndpointDisabledError, match="410 Gone"):
            client.indicator_history("example-gold")


def test_401_is_a_configuration_error_not_silently_ignored():
    def handler(request):
        return httpx.Response(401)

    with client_for(handler) as client:
        with pytest.raises(TindexAuthenticationError, match="401"):
            client.currency_rates()


def test_disabled_categories_are_rejected_before_network_call():
    def handler(request):
        pytest.fail("disabled category must not be requested")

    with client_for(handler) as client:
        with pytest.raises(TindexEndpointDisabledError):
            client.indicators_by_category("macro-economy")


def test_path_segments_cannot_inject_extra_routes():
    def handler(request):
        pytest.fail("invalid path segment must not be requested")

    with client_for(handler) as client:
        with pytest.raises(ValueError):
            client.board("../currency-rates")


def test_local_rate_limit_is_one_request_per_minute_across_clients():
    calls = []
    now = [0.0]

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"ok": True})

    with client_for(handler, clock=lambda: now[0]) as first:
        first.currency_rates()
        with client_for(handler, clock=lambda: now[0]) as second:
            with pytest.raises(TindexRateLimitError, match="Local Tindex limit"):
                second.boards()
            now[0] = 60.0
            second.boards()

    assert len(calls) == 2


def test_local_success_daily_budget_is_enforced(monkeypatch):
    calls = []
    now = [0.0]
    monkeypatch.setattr(tindex_provider, "MAX_SUCCESSFUL_REQUESTS_PER_DAY", 2)

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"ok": True})

    with client_for(handler, clock=lambda: now[0]) as client:
        client.currency_rates()
        now[0] = 60.0
        client.boards()
        now[0] = 120.0
        with pytest.raises(TindexRateLimitError, match="daily success budget"):
            client.categories()

    assert len(calls) == 2


def test_missing_configuration_fails_closed(monkeypatch):
    monkeypatch.delenv("TINDEX_API_BASE_URL", raising=False)
    monkeypatch.delenv("TINDEX_API_TOKEN", raising=False)
    with pytest.raises(TindexConfigurationError, match="TINDEX_API_BASE_URL"):
        TindexClient()


def test_status_does_not_expose_token(monkeypatch):
    monkeypatch.setenv("TINDEX_API_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("TINDEX_API_TOKEN", "do-not-expose-me")
    status = tindex_connection_status()
    assert status["configured"] is True
    assert status["network_tested"] is False
    assert status["production_approved"] is False
    assert status["quota"]["requests_per_minute"] == 1
    assert status["quota"]["successful_requests_per_day"] == 100
    assert "do-not-expose-me" not in repr(status)
    assert "iran_equities" in status["disabled_data_families"]
