"""Conservative client for Tindex's documented public indicator API.

Only documented API routes are used. The client never scrapes the website or
bypasses authentication, and HTTP success is not licensing or production approval.
"""
from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Any
from urllib.parse import quote

import httpx


SOURCE_ID = "iran.tindex.public_api"
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_REQUESTS_PER_MINUTE = 1
MAX_SUCCESSFUL_REQUESTS_PER_DAY = 100
_REQUEST_WINDOW_SECONDS = 60.0
_DAY_WINDOW_SECONDS = 86400.0

# Shared across instances in this process; cannot count activity on other hosts.
_RATE_LOCK = threading.Lock()
_REQUEST_TIMES: deque[float] = deque()
_SUCCESSFUL_REQUEST_TIMES: deque[float] = deque()

class TindexError(RuntimeError):
    """Base class for sanitized Tindex adapter errors."""


class TindexConfigurationError(TindexError):
    """Required connection configuration is missing or unsafe."""


class TindexAuthenticationError(TindexError):
    """Tindex rejected the configured token (401)."""


class TindexAccessDisabledError(TindexError):
    """Tindex disabled the API account (403)."""


class TindexRateLimitError(TindexError):
    """The local or provider rate limit was reached (429)."""


class TindexEndpointDisabledError(TindexError):
    """The provider says the endpoint is disabled (410 Gone)."""


class TindexProviderError(TindexError):
    """Unexpected provider/network/response error."""


def _assert_allowed_slug(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 160:
        raise ValueError(f"{label} must contain 1-160 characters")
    if any(ch in cleaned for ch in ("/", "\\", "?", "#")):
        raise ValueError(f"{label} must be a single path segment")
    return cleaned


class TindexClient:
    """Small, rate-limited client; provider quota remains authoritative.

    Set TINDEX_API_BASE_URL to the API origin shown in the current Tindex
    developer dashboard (do not guess the host), and TINDEX_API_TOKEN to a
    token created for this project. The base URL must use HTTPS.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.BaseTransport | None = None,
        clock=time.monotonic,
    ) -> None:
        configured_url = (base_url or os.getenv("TINDEX_API_BASE_URL", "")).strip()
        configured_token = (token or os.getenv("TINDEX_API_TOKEN", "")).strip()
        if not configured_url:
            raise TindexConfigurationError(
                "TINDEX_API_BASE_URL is missing; copy the API origin from Tindex's current docs."
            )
        parsed = httpx.URL(configured_url)
        if parsed.scheme != "https" or not parsed.host or parsed.path not in ("", "/"):
            raise TindexConfigurationError(
                "TINDEX_API_BASE_URL must be an HTTPS origin without an API path."
            )
        if not configured_token:
            raise TindexConfigurationError(
                "TINDEX_API_TOKEN is missing; create a token in the Tindex dashboard."
            )
        self._client = httpx.Client(
            base_url=str(parsed).rstrip("/"),
            headers={
                "Authorization": f"Bearer {configured_token}",
                "Accept": "application/json",
                "User-Agent": "MarketSage/0.1 data-connector",
            },
            timeout=timeout,
            transport=transport,
        )
        self._clock = clock

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TindexClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _reserve_request_slot(self) -> None:
        # Share local minute/day accounting across TindexClient instances.
        # Provider-side accounting is still authoritative across processes and hosts.
        # Never retry HTTP 429 automatically.
        with _RATE_LOCK:
            now = self._clock()
            while _REQUEST_TIMES and now - _REQUEST_TIMES[0] >= _REQUEST_WINDOW_SECONDS:
                _REQUEST_TIMES.popleft()
            while (
                _SUCCESSFUL_REQUEST_TIMES
                and now - _SUCCESSFUL_REQUEST_TIMES[0] >= _DAY_WINDOW_SECONDS
            ):
                _SUCCESSFUL_REQUEST_TIMES.popleft()
            if len(_SUCCESSFUL_REQUEST_TIMES) >= MAX_SUCCESSFUL_REQUESTS_PER_DAY:
                raise TindexRateLimitError(
                    "Local Tindex daily success budget reached; stop requests until its rolling window expires."
                )
            if len(_REQUEST_TIMES) >= MAX_REQUESTS_PER_MINUTE:
                wait_for = _REQUEST_WINDOW_SECONDS - (now - _REQUEST_TIMES[0])
                raise TindexRateLimitError(
                    f"Local Tindex limit reached; retry after about {max(1, int(wait_for))} seconds."
                )
            _REQUEST_TIMES.append(now)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self._reserve_request_slot()
        try:
            response = self._client.get(path, params=params)
        except httpx.HTTPError as exc:
            raise TindexProviderError(
                f"Network error while contacting Tindex ({type(exc).__name__})."
            ) from None

        if response.status_code == 410:
            raise TindexEndpointDisabledError(
                "Tindex returned 410 Gone. This endpoint is disabled; no fallback or scraping was attempted."
            )
        if response.status_code == 401:
            raise TindexAuthenticationError(
                "Tindex returned 401. Check the token in the local environment; do not paste it into chat."
            )
        if response.status_code == 403:
            raise TindexAccessDisabledError(
                "Tindex returned 403. The account may be disabled; contact Tindex support."
            )
        if response.status_code == 429:
            raise TindexRateLimitError(
                "Tindex returned 429. Stop requests and wait; no automatic retry was made."
            )
        if response.status_code < 200 or response.status_code >= 300:
            raise TindexProviderError(
                f"Tindex returned unexpected HTTP status {response.status_code}."
            )
        # Count all 2xx responses against the local success budget, including malformed bodies.
        with _RATE_LOCK:
            _SUCCESSFUL_REQUEST_TIMES.append(self._clock())
        try:
            payload = response.json()
        except ValueError:
            raise TindexProviderError("Tindex returned a successful response that was not valid JSON.") from None
        # Tindex may encode resource-level failures in a 2xx JSON envelope.
        # Never treat success=false as a valid empty dataset.
        if isinstance(payload, dict) and payload.get("success") is False:
            raise TindexProviderError(
                f"Tindex returned success=false (HTTP {response.status_code}); "
                "check the documented slug/category and response message locally."
            )
        if isinstance(payload, dict) and "success" in payload and payload.get("success") is not True:
            raise TindexProviderError("Tindex response has an invalid success flag.")
        return payload

    def currency_rates(self) -> Any:
        """Fetch the documented public currency-rate endpoint."""
        return self._get_json("/api/public/currency-rates")

    def boards(self) -> Any:
        """Fetch the public board index; provider response may omit disabled categories."""
        return self._get_json("/api/public/boards")

    def board(self, key: str) -> Any:
        key = _assert_allowed_slug(key, "board key")
        return self._get_json(f"/api/public/boards/{quote(key, safe='')}")

    def categories(self) -> Any:
        """Fetch current public categories (never assume removed categories exist)."""
        return self._get_json("/api/public/categories")

    def movers(self) -> Any:
        return self._get_json("/api/public/indicators/movers")

    def indicator_history(self, slug: str, *, range: str = "3m") -> Any:
        """Fetch daily history; Tindex clamps longer ranges to its latest 100 days."""
        slug = _assert_allowed_slug(slug, "indicator slug")
        if range not in {"1d", "1w", "1m", "3m"}:
            raise ValueError("history range must be one of: 1d, 1w, 1m, 3m")
        return self._get_json(
            f"/api/public/indicators/{quote(slug, safe='')}/history",
            params={"range": range, "lang": "en"},
        )

    def indicator_candles(
        self, slug: str, *, range: str = "3m", interval: str = "daily"
    ) -> Any:
        """Fetch documented daily/weekly candles within the provider's 100-day cap."""
        slug = _assert_allowed_slug(slug, "indicator slug")
        if range not in {"1m", "3m"}:
            raise ValueError("candles range must be one of: 1m, 3m")
        if interval not in {"daily", "weekly"}:
            raise ValueError("candles interval must be daily or weekly")
        return self._get_json(
            f"/api/public/indicators/{quote(slug, safe='')}/candles",
            params={"range": range, "interval": interval, "lang": "en"},
        )

    def indicators_by_category(self, category_slug: str) -> Any:
        category_slug = _assert_allowed_slug(category_slug, "category slug")
        return self._get_json(
            f"/api/public/indicators/by-category/{quote(category_slug, safe='')}"
        )

    def indicator(self, category_slug: str, indicator_slug: str) -> Any:
        category_slug = _assert_allowed_slug(category_slug, "category slug")
        indicator_slug = _assert_allowed_slug(indicator_slug, "indicator slug")
        return self._get_json(
            f"/api/public/indicators/{quote(category_slug, safe='')}/"
            f"{quote(indicator_slug, safe='')}"
        )


def tindex_connection_status() -> dict[str, Any]:
    """Report configuration without exposing credentials or making network calls."""
    base_url = os.getenv("TINDEX_API_BASE_URL", "").strip()
    token_present = bool(os.getenv("TINDEX_API_TOKEN", "").strip())
    return {
        "source_id": SOURCE_ID,
        "configured": bool(base_url and token_present),
        "base_url_configured": bool(base_url),
        "token_configured": token_present,
        "network_tested": False,
        "production_approved": False,
        # These are documented families, not yet production-accepted data.
        "documented_data_families": [
            "currency", "precious_metals", "cryptocurrency",
            "stock_energy_indices", "housing_indicators", "automotive_indicators",
            "macro_economy_indicators",
        ],
        "not_implemented_or_not_confirmed": [
            "stock_screener_and_per_stock_history",
            "news_feed",
            "inflation_series_semantics",
            "calendar",
        ],
        "empty_categories_per_current_docs": ["commodities", "technology", "sentiment"],
        "quota": {
            "requests_per_minute": MAX_REQUESTS_PER_MINUTE,
            "successful_requests_per_day": MAX_SUCCESSFUL_REQUESTS_PER_DAY,
            "local_daily_guard_persistent": False,
            "note": (
                "Current public docs specify 1 request/minute and 100 successful requests/day. "
                "The local rolling guard is process-memory only; provider accounting remains "
                "authoritative across processes and hosts."
            ),
        },
    }
