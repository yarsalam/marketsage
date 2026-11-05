"""Read-only CODAL search adapter.

CODAL search responses and publication/amendment fields require fixture validation.
This client returns the source payload unchanged and never converts crawl time into
publication time or makes disclosure data eligible for investment scoring.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import httpx

SOURCE_ID = "iran.codal"
BASE_URL = "https://search.codal.ir/api/search/v2/q"
USER_AGENT = "MarketSage/0.1 data-connector"


class CodalError(RuntimeError):
    pass


class CodalClient:
    def __init__(self, *, timeout: float = 20.0, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CodalClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def search_disclosures(
        self, *, symbol: str | None = None, start_date: str | None = None,
        end_date: str | None = None, page: int = 1, page_size: int = 20,
    ) -> dict[str, Any]:
        if symbol is not None and (not symbol.strip() or len(symbol) > 80):
            raise ValueError("symbol must contain 1-80 characters")
        for label, value in (("start_date", start_date), ("end_date", end_date)):
            if value is not None:
                try:
                    date.fromisoformat(value)
                except ValueError:
                    raise ValueError(f"{label} must use YYYY-MM-DD") from None
        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date must not be after end_date")
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise ValueError("page must be a positive integer")
        if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")
        params: dict[str, str] = {"PageNumber": str(page), "Length": str(page_size)}
        if symbol:
            params["Symbol"] = symbol.strip()
        if start_date:
            params["FromDate"] = start_date
        if end_date:
            params["ToDate"] = end_date
        try:
            response = self._client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            retrieved_at = datetime.now(timezone.utc).isoformat()
        except (httpx.HTTPError, ValueError) as exc:
            raise CodalError(f"CODAL request failed ({type(exc).__name__})") from None
        if not isinstance(payload, dict):
            raise CodalError("CODAL search response must be a JSON object")
        # Capture when this response was retrieved, but do not infer publication time.
        # Provider-native fields remain unchanged until fixtures prove their semantics.
        return {
            "source_id": SOURCE_ID,
            "payload": payload,
            "publication_timestamp": None,
            "retrieved_at": retrieved_at,
            "eligible_for_scoring": False,
        }
