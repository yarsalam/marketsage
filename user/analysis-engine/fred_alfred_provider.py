"""Small, read-only FRED/ALFRED observations adapter.

Requires a FRED API key supplied via FRED_API_KEY. Tests use an HTTP mock and
never contact FRED. Returned observations are research data only; callers must
respect realtime/vintage dates and series-specific release calendars.
"""
from __future__ import annotations

import os
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

FRED_API_BASE_URL = "https://api.stlouisfed.org/fred"
DEFAULT_TIMEOUT_SECONDS = 15.0


class FredConfigurationError(ValueError):
    pass


class FredProviderError(RuntimeError):
    pass


def normalize_fred_observations(payload: Any, *, series_id: str) -> list[dict[str, Any]]:
    """Normalize FRED observations while preserving vintage metadata.

    FRED's '.' marker means a missing value. observation_date is the period
    date, not the publication time; realtime_start is the available vintage
    boundary and is not claimed to be an exact release timestamp.
    """
    if not isinstance(payload, dict):
        raise FredProviderError("FRED response must be an object")
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise FredProviderError("FRED response observations must be a list")
    if not isinstance(series_id, str) or not series_id.strip():
        raise FredProviderError("series_id must be a non-empty string")

    result: list[dict[str, Any]] = []
    for i, row in enumerate(observations):
        if not isinstance(row, dict):
            raise FredProviderError(f"observations[{i}] must be an object")
        try:
            period_date = date.fromisoformat(row["date"])
            vintage_date = date.fromisoformat(row["realtime_start"])
            realtime_end = date.fromisoformat(row.get("realtime_end", "9999-12-31"))
        except (KeyError, TypeError, ValueError):
            raise FredProviderError(f"observations[{i}] has invalid date/vintage metadata") from None

        raw_value = row.get("value")
        if not isinstance(raw_value, str):
            raise FredProviderError(f"observations[{i}].value must be a string")
        if raw_value == ".":
            value = None
        else:
            try:
                value = Decimal(raw_value)
            except (InvalidOperation, ValueError):
                raise FredProviderError(f"observations[{i}].value is not numeric") from None
            if not value.is_finite():
                raise FredProviderError(f"observations[{i}].value must be finite")

        result.append({
            "source_id": "us.fred.alfred",
            "series_id": series_id.strip(),
            "observation_date": period_date.isoformat(),
            "value": value,
            "realtime_start": vintage_date.isoformat(),
            "realtime_end": realtime_end.isoformat(),
            "vintage_available_at": datetime.combine(
                vintage_date, time(23, 59, 59), tzinfo=timezone.utc
            ).isoformat(),
            "publication_timestamp": None,
            "eligible_for_scoring": False,
        })
    return result


class FredAlfredClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key or os.getenv("FRED_API_KEY")
        if not self._api_key:
            raise FredConfigurationError("FRED_API_KEY is required")
        if timeout <= 0:
            raise FredConfigurationError("timeout must be positive")
        self._client = httpx.Client(
            base_url=FRED_API_BASE_URL,
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "FredAlfredClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def observations(
        self,
        series_id: str,
        *,
        observation_start: str | None = None,
        observation_end: str | None = None,
        realtime_start: str | None = None,
        realtime_end: str | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if not isinstance(series_id, str) or not series_id.strip():
            raise ValueError("series_id must be non-empty")
        if not 1 <= limit <= 100_000 or offset < 0:
            raise ValueError("limit must be 1..100000 and offset non-negative")
        params: dict[str, str | int] = {
            "series_id": series_id.strip(),
            "api_key": self._api_key,
            "file_type": "json",
            "limit": limit,
            "offset": offset,
        }
        for name, value in (
            ("observation_start", observation_start),
            ("observation_end", observation_end),
            ("realtime_start", realtime_start),
            ("realtime_end", realtime_end),
        ):
            if value is not None:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError):
                    raise ValueError(f"{name} must use YYYY-MM-DD") from None
                params[name] = value
        try:
            response = self._client.get("/series/observations", params=params)
        except httpx.TimeoutException as exc:
            raise FredProviderError(
                f"FRED network timeout ({type(exc).__name__}); no automatic retry was made"
            ) from None
        except httpx.HTTPError as exc:
            raise FredProviderError(
                f"FRED network error ({type(exc).__name__}); no automatic retry was made"
            ) from None
        if response.status_code in (401, 403):
            raise FredProviderError(f"FRED authorization failed ({response.status_code})")
        if response.status_code == 429:
            raise FredProviderError("FRED rate limit reached; retry later")
        if response.status_code >= 400:
            raise FredProviderError(f"FRED request failed ({response.status_code})")
        try:
            payload = response.json()
        except ValueError:
            raise FredProviderError("FRED returned invalid JSON") from None
        return normalize_fred_observations(payload, series_id=series_id)
