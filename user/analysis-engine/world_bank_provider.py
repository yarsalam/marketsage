"""No-key World Bank Indicators API client for research-only macro candidates.

The API provides annual/period observations, not necessarily release timestamps.
All rows stay blocked from MarketSage scoring until source-specific acceptance.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

SOURCE_ID = "global.world_bank_indicators"
BASE_URL = "https://api.worldbank.org/v2"
_YEAR_RE = re.compile(r"^\d{4}$")
_COUNTRY_RE = re.compile(r"^[A-Za-z]{2,3}$")
_INDICATOR_RE = re.compile(r"^[A-Za-z0-9_.-]{2,80}$")


class WorldBankError(RuntimeError):
    """Sanitized World Bank API or response error."""


def _aware_utc(value: datetime | None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    return value.astimezone(timezone.utc)


def normalize_indicator_payload(
    payload: Any,
    *,
    country: str,
    indicator: str,
    retrieved_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Normalize World Bank's [metadata, observations] JSON envelope.

    Values are Decimal or None. Years are deliberately not converted to exact
    publication timestamps. Provider units are preserved separately when given.
    """
    captured_at = _aware_utc(retrieved_at).isoformat()
    if not isinstance(payload, list) or len(payload) < 2:
        raise WorldBankError("unexpected World Bank response envelope")
    metadata = payload[0]
    observations = payload[1]
    if not isinstance(metadata, dict):
        raise WorldBankError("World Bank metadata must be an object")
    if metadata.get("message"):
        raise WorldBankError("World Bank returned an API message/error")
    if observations is None:
        observations = []
    if not isinstance(observations, list):
        raise WorldBankError("World Bank observations must be a list")

    rows: list[dict[str, Any]] = []
    seen_years: set[str] = set()
    for index, item in enumerate(observations):
        if not isinstance(item, dict):
            raise WorldBankError(f"observation {index} must be an object")
        year = item.get("date")
        if not isinstance(year, str) or not _YEAR_RE.fullmatch(year):
            raise WorldBankError(f"observation {index} has an invalid annual date")
        if year in seen_years:
            raise WorldBankError(f"duplicate observation year: {year}")
        seen_years.add(year)

        raw_value = item.get("value")
        if raw_value in (None, ""):
            value = None
        else:
            try:
                value = Decimal(str(raw_value))
            except (InvalidOperation, ValueError):
                raise WorldBankError(f"observation {index} has a non-numeric value") from None
            if not value.is_finite():
                raise WorldBankError(f"observation {index} has a non-finite value")

        country_record = item.get("country")
        indicator_record = item.get("indicator")
        country_name = country_record.get("value") if isinstance(country_record, dict) else None
        indicator_name = indicator_record.get("value") if isinstance(indicator_record, dict) else None
        rows.append({
            "source_id": SOURCE_ID,
            "country_code_requested": country.upper(),
            "country_code_provider": item.get("countryiso3code") or country.upper(),
            "country_name_provider": country_name,
            "indicator_id": indicator,
            "indicator_name_provider": indicator_name,
            "observation_year": year,
            "value": value,
            "provider_unit": item.get("unit") or None,
            "observation_period": year,
            "publication_timestamp": None,
            "retrieved_at": captured_at,
            "eligible_for_scoring": False,
        })

    rows.sort(key=lambda row: row["observation_year"])
    return rows


class WorldBankClient:
    """Read-only client; no API key is required by the World Bank Indicators API."""

    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        timeout: float = 12.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url.startswith("https://"):
            raise ValueError("World Bank base URL must use HTTPS")
        self._client = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            headers={"Accept": "application/json", "User-Agent": "MarketSage/0.1 research-data"},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "WorldBankClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def indicator(
        self,
        country: str,
        indicator: str,
        *,
        start_year: int = 2000,
        end_year: int | None = None,
        per_page: int = 1000,
    ) -> list[dict[str, Any]]:
        country = country.strip().upper()
        indicator = indicator.strip()
        end_year = end_year if end_year is not None else datetime.now(timezone.utc).year
        if not _COUNTRY_RE.fullmatch(country):
            raise ValueError("country must be a two- or three-letter ISO code")
        if not _INDICATOR_RE.fullmatch(indicator):
            raise ValueError("invalid World Bank indicator identifier")
        if isinstance(start_year, bool) or not isinstance(start_year, int) or start_year < 1960 or start_year > 2200:
            raise ValueError("start_year must be an integer between 1960 and 2200")
        if isinstance(end_year, bool) or not isinstance(end_year, int) or end_year < start_year or end_year > 2200:
            raise ValueError("end_year must be an integer in range and >= start_year")
        if isinstance(per_page, bool) or not isinstance(per_page, int) or not 1 <= per_page <= 1000:
            raise ValueError("per_page must be between 1 and 1000")

        try:
            response = self._client.get(
                f"country/{country}/indicator/{indicator}",
                params={
                    "format": "json",
                    "date": f"{start_year}:{end_year}",
                    "per_page": per_page,
                },
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise WorldBankError(f"World Bank request failed ({type(exc).__name__})") from None
        return normalize_indicator_payload(
            payload, country=country, indicator=indicator
        )
