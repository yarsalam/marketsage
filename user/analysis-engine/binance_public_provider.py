"""Unauthenticated Binance Spot public-kline client.

This adapter reads public market data only. It does not place orders, infer quote
currency from concatenated symbols, or approve legal/commercial use or scoring.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx

SOURCE_ID = "global.binance_spot_public"
BASE_URL = "https://data-api.binance.vision"
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,20}$")
_ALLOWED_INTERVALS = {
    "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h",
    "12h", "1d", "3d", "1w", "1M",
}


class BinancePublicError(RuntimeError):
    """Sanitized public Binance market-data error."""


def _decimal(value: Any, field: str, row_index: int, *, positive: bool = False) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise BinancePublicError(f"kline {row_index} has invalid {field}")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BinancePublicError(f"kline {row_index} has invalid {field}") from None
    if not result.is_finite() or (result <= 0 if positive else result < 0):
        raise BinancePublicError(f"kline {row_index} has invalid {field}")
    return result


def _epoch_ms(value: Any, field: str, row_index: int) -> int:
    if isinstance(value, bool):
        raise BinancePublicError(f"kline {row_index} has invalid {field}")
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError):
        raise BinancePublicError(f"kline {row_index} has invalid {field}") from None
    if result < 0 or str(result) != str(value).strip():
        raise BinancePublicError(f"kline {row_index} has invalid {field}")
    return result


def _iso_ms(value: int) -> str:
    try:
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        raise BinancePublicError("kline timestamp is out of range") from None


def normalize_klines(
    payload: Any,
    *,
    symbol: str,
    interval: str = "1d",
    retrieved_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Validate 12-field Spot kline arrays, preserving exact pair and UTC times."""
    symbol = symbol.strip().upper()
    if not _SYMBOL_RE.fullmatch(symbol):
        raise ValueError("symbol must be an uppercase Binance market symbol")
    if interval not in _ALLOWED_INTERVALS:
        raise ValueError("unsupported Binance kline interval")
    captured = retrieved_at or datetime.now(timezone.utc)
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    captured = captured.astimezone(timezone.utc)

    if not isinstance(payload, list):
        raise BinancePublicError("Binance klines must be a list")
    rows: list[dict[str, Any]] = []
    seen_open_times: set[int] = set()
    previous_open_time: int | None = None
    for index, item in enumerate(payload):
        if not isinstance(item, list) or len(item) < 12:
            raise BinancePublicError(f"kline {index} must contain at least 12 fields")
        open_ms = _epoch_ms(item[0], "open time", index)
        close_ms = _epoch_ms(item[6], "close time", index)
        if close_ms < open_ms:
            raise BinancePublicError(f"kline {index} closes before it opens")
        if open_ms in seen_open_times:
            raise BinancePublicError(f"duplicate kline open time: {open_ms}")
        if previous_open_time is not None and open_ms < previous_open_time:
            raise BinancePublicError("kline rows are not in chronological order")
        seen_open_times.add(open_ms)
        previous_open_time = open_ms

        open_price = _decimal(item[1], "open", index, positive=True)
        high_price = _decimal(item[2], "high", index, positive=True)
        low_price = _decimal(item[3], "low", index, positive=True)
        close_price = _decimal(item[4], "close", index, positive=True)
        base_volume = _decimal(item[5], "base volume", index)
        quote_volume = _decimal(item[7], "quote volume", index)
        trades_raw = item[8]
        if isinstance(trades_raw, bool):
            raise BinancePublicError(f"kline {index} has invalid trade count")
        try:
            trade_count = int(trades_raw)
        except (TypeError, ValueError, OverflowError):
            raise BinancePublicError(f"kline {index} has invalid trade count") from None
        if trade_count < 0 or str(trade_count) != str(trades_raw).strip():
            raise BinancePublicError(f"kline {index} has invalid trade count")
        if high_price < max(open_price, close_price, low_price) or low_price > min(open_price, close_price):
            raise BinancePublicError(f"kline {index} violates OHLC consistency")

        rows.append({
            "source_id": SOURCE_ID,
            "instrument_key": symbol,
            "interval": interval,
            "observation_time_utc": _iso_ms(open_ms),
            "bar_close_time_utc": _iso_ms(close_ms),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "base_volume": base_volume,
            "quote_volume": quote_volume,
            "trade_count": trade_count,
            "retrieved_at": captured.isoformat(),
            "bar_complete_at_retrieval": close_ms <= int(captured.timestamp() * 1000),
            "quote_asset": None,
            "publication_timestamp": None,
            "eligible_for_scoring": False,
        })
    return rows


class BinancePublicClient:
    """Read-only, unauthenticated Spot market data. Calls are deliberately bounded."""

    def __init__(
        self,
        *,
        base_url: str = BASE_URL,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url.startswith("https://"):
            raise ValueError("Binance base URL must use HTTPS")
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"Accept": "application/json", "User-Agent": "MarketSage/0.1 research-data"},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BinancePublicClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def klines(
        self,
        symbol: str = "BTCUSDT",
        *,
        interval: str = "1d",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        symbol = symbol.strip().upper()
        if not _SYMBOL_RE.fullmatch(symbol):
            raise ValueError("symbol must be an uppercase Binance market symbol")
        if interval not in _ALLOWED_INTERVALS:
            raise ValueError("unsupported Binance kline interval")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        try:
            response = self._client.get(
                "/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise BinancePublicError(f"Binance public-data request failed ({type(exc).__name__})") from None
        return normalize_klines(payload, symbol=symbol, interval=interval)
