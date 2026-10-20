"""Read-only TSETMC adapter; candidate data is quarantined from scoring.

The CDN endpoints are reverse-engineered and may change or block non-Iranian IPs.
Do not disable TLS verification, scrape alternate hosts, or infer units/timestamps.
"""
from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

SOURCE_ID = "iran.tsetmc"
BASE_URL = "https://cdn.tsetmc.com/api"
USER_AGENT = "MarketSage/0.1 data-connector"


class TsetmcError(RuntimeError):
    pass


class TsetmcPayloadError(TsetmcError):
    pass


class TsetmcClient:
    def __init__(self, *, timeout: float = 15.0, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "TsetmcClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _get_json(self, path: str) -> Any:
        try:
            response = self._client.get(path)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TsetmcError(f"TSETMC request failed ({type(exc).__name__})") from None

    def search_instruments(self, query: str) -> Any:
        query = query.strip()
        if not query or len(query) > 100:
            raise ValueError("query must contain 1-100 characters")
        return self._get_json("/Instrument/GetInstrumentSearch/" + quote(query, safe=""))

    def daily_history(self, instrument_code: str, limit: int = 0) -> list[dict[str, Any]]:
        code = str(instrument_code).strip()
        if not code.isdigit() or not 1 <= len(code) <= 20:
            raise ValueError("instrument_code must be a numeric TSETMC insCode")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0 or limit > 10000:
            raise ValueError("limit must be an integer between 0 and 10000")
        payload = self._get_json(f"/ClosingPrice/GetClosingPriceDailyList/{code}/{limit}")
        if not isinstance(payload, dict) or not isinstance(payload.get("closingPriceDaily"), list):
            raise TsetmcPayloadError("unexpected TSETMC daily-history envelope")
        return payload["closingPriceDaily"]


def normalize_daily_history(payload_rows: Any) -> list[dict[str, Any]]:
    """Normalize only observed numeric/date fields; keep price unit and eligibility unknown."""
    if not isinstance(payload_rows, list):
        raise TsetmcPayloadError("daily history must be a list")
    result: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for i, row in enumerate(payload_rows):
        if not isinstance(row, dict):
            raise TsetmcPayloadError(f"row {i} must be an object")
        raw_date = row.get("dEven")
        if isinstance(raw_date, bool) or not isinstance(raw_date, (int, str)):
            raise TsetmcPayloadError(f"row {i} dEven must be YYYYMMDD")
        date_text = str(raw_date)
        try:
            datetime.strptime(date_text, "%Y%m%d")
        except ValueError:
            raise TsetmcPayloadError(f"row {i} dEven must be YYYYMMDD") from None
        if date_text in seen_dates:
            raise TsetmcPayloadError(f"duplicate trading date: {date_text}")
        seen_dates.add(date_text)
        normalized: dict[str, Any] = {
            "source_id": SOURCE_ID,
            "trading_date": date_text,
            "unit": None,
            "observed_at": None,
            "retrieved_at": None,
            "eligible_for_scoring": False,
        }
        for source_key, target_key in (
            ("pClosing", "close"), ("pDrCotVal", "last"), ("priceFirst", "open"),
            ("priceMin", "low"), ("priceMax", "high"), ("priceYesterday", "previous_close"),
            ("qTotTran5J", "volume"), ("qTotCap", "value"),
        ):
            value = row.get(source_key)
            if value is None:
                normalized[target_key] = None
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float, str)):
                raise TsetmcPayloadError(f"row {i} {source_key} must be numeric or null")
            try:
                number = Decimal(str(value))
            except InvalidOperation:
                raise TsetmcPayloadError(f"row {i} {source_key} must be numeric or null") from None
            if not number.is_finite() or number < 0:
                raise TsetmcPayloadError(f"row {i} {source_key} must be finite and non-negative")
            normalized[target_key] = number
        result.append(normalized)
    return result
