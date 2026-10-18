from __future__ import annotations

import httpx
import pytest

from tindex_provider import (
    TindexAuthenticationError,
    TindexClient,
    TindexConfigurationError,
    TindexEndpointDisabledError,
    TindexRateLimitError,
    tindex_connection_status,
)


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


def test_currently_documented_macro_category_is_not_blocked_locally():
    seen = []

    def handler(request):
        seen.append(request.url.path)
        return httpx.Response(200, json={
            "success": True,
            "data": {"category": {"slug": "macro-economy"}, "rows": []},
        })

    with client_for(handler) as client:
        payload = client.indicators_by_category("macro-economy")

    assert payload["success"] is True
    assert seen == ["/api/public/indicators/by-category/macro-economy"]


def test_path_segments_cannot_inject_extra_routes():
    def handler(request):
        pytest.fail("invalid path segment must not be requested")

    with client_for(handler) as client:
        with pytest.raises(ValueError):
            client.board("../currency-rates")


def test_local_rate_limit_is_three_requests_per_minute():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(200, json={"ok": True})

    with client_for(handler) as client:
        client.currency_rates()
        client.boards()
        client.categories()
        with pytest.raises(TindexRateLimitError, match="Local Tindex limit"):
            client.movers()

    assert len(calls) == 3


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
    assert "do-not-expose-me" not in repr(status)
    assert "stock_energy_indices" in status["documented_data_families"]
    assert "news_feed" in status["not_implemented_or_not_confirmed"]



def test_success_false_json_envelope_is_not_treated_as_data():
    from tindex_provider import TindexProviderError

    with client_for(lambda request: httpx.Response(
        200, json={"success": False, "message": "Unknown slug"}
    )) as client:
        with pytest.raises(TindexProviderError, match="success=false"):
            client.indicator_history("unknown-slug")
