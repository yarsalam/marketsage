"""Conservative normalization for the observed Tindex currency-rates envelope.

This module validates shape and primitive types only. It intentionally does not
assign a currency unit, market definition, observation timestamp, or scoring
eligibility without provider evidence.
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from tindex_provider import SOURCE_ID


class TindexPayloadError(ValueError):
    """The provider payload does not match the validated envelope/schema."""


def normalize_currency_rates(payload: Any) -> list[dict[str, Any]]:
    """Validate and normalize a Tindex currency-rates payload.

    Expected observed envelope: {"success": true, "data": [...]}.
    Unknown semantics stay explicitly unknown and scoring stays disabled.
    """
    if not isinstance(payload, dict):
        raise TindexPayloadError("payload must be an object")
    if payload.get("success") is not True:
        raise TindexPayloadError("payload success must be true")
    data = payload.get("data")
    if not isinstance(data, list):
        raise TindexPayloadError("payload data must be a list")

    normalized: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for index, item in enumerate(data):
        prefix = f"data[{index}]"
        if not isinstance(item, dict):
            raise TindexPayloadError(f"{prefix} must be an object")

        key = item.get("key")
        name = item.get("name")
        if not isinstance(key, str) or not key.strip():
            raise TindexPayloadError(f"{prefix}.key must be a non-empty string")
        if not isinstance(name, str) or not name.strip():
            raise TindexPayloadError(f"{prefix}.name must be a non-empty string")

        clean_key = key.strip()
        if clean_key in seen_keys:
            raise TindexPayloadError(f"{prefix}.key is duplicated")
        seen_keys.add(clean_key)

        rate = item.get("rate")
        if isinstance(rate, bool) or not isinstance(rate, (int, float, Decimal)):
            raise TindexPayloadError(f"{prefix}.rate must be a finite non-negative number")
        try:
            rate_decimal = Decimal(str(rate))
        except (InvalidOperation, ValueError):
            raise TindexPayloadError(f"{prefix}.rate must be a finite non-negative number") from None
        if not rate_decimal.is_finite() or rate_decimal < 0:
            raise TindexPayloadError(f"{prefix}.rate must be a finite non-negative number")
        if isinstance(rate, float) and not math.isfinite(rate):
            raise TindexPayloadError(f"{prefix}.rate must be a finite non-negative number")

        decimals = item.get("decimals")
        if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
            raise TindexPayloadError(f"{prefix}.decimals must be a non-negative integer")

        normalized.append({
            "source_id": SOURCE_ID,
            "instrument_key": clean_key,
            "display_name": name.strip(),
            "raw_rate": rate_decimal,
            "provider_decimals": decimals,
            "unit": None,
            "market_definition": None,
            "observed_at": None,
            "retrieved_at": None,
            "eligible_for_scoring": False,
        })
    return normalized



def normalize_indicator_candles(payload: Any) -> list[dict[str, Any]]:
    """Normalize Tindex's documented columnar candle payload.

    Tindex encodes `data.t` as integer days since 1970-01-01, delta-encoded
    from the second value onward. Price arrays are parallel to the decoded dates.
    The result keeps provider units but does not infer currency or observation
    publication time, and every row remains unavailable for production scoring.
    """
    if not isinstance(payload, dict):
        raise TindexPayloadError("payload must be an object")
    if payload.get("success") is not True:
        raise TindexPayloadError("payload success must be true")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise TindexPayloadError("payload data must be an object")

    slug = data.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        raise TindexPayloadError("data.slug must be a non-empty string")
    unit = data.get("unit")
    if unit is not None and (not isinstance(unit, str) or not unit.strip()):
        raise TindexPayloadError("data.unit must be a non-empty string when supplied")

    names = ("t", "o", "h", "l", "c", "partial")
    arrays: dict[str, list[Any]] = {}
    for name in names:
        value = data.get(name)
        if not isinstance(value, list) or not value:
            raise TindexPayloadError(f"data.{name} must be a non-empty list")
        arrays[name] = value

    size = len(arrays["t"])
    for name in ("o", "h", "l", "c", "partial"):
        if len(arrays[name]) != size:
            raise TindexPayloadError(f"data.{name} length must match data.t")
    count = data.get("count")
    if count is not None and (
        isinstance(count, bool) or not isinstance(count, int) or count != size
    ):
        raise TindexPayloadError("data.count must match candle array length")

    epoch = date(1970, 1, 1)
    dates: list[date] = []
    epoch_day = None
    for index, value in enumerate(arrays["t"]):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TindexPayloadError(f"data.t[{index}] must be an integer day/delta")
        if value < 0 or (index > 0 and value <= 0):
            raise TindexPayloadError(f"data.t[{index}] must be non-negative; deltas must be positive")
        epoch_day = value if index == 0 else int(epoch_day) + value
        try:
            day = epoch + timedelta(days=epoch_day)
        except (OverflowError, ValueError) as exc:
            raise TindexPayloadError(f"data.t[{index}] is outside the supported date range") from exc
        if dates and day <= dates[-1]:
            raise TindexPayloadError("decoded candle dates must be strictly increasing")
        dates.append(day)

    def decimal_value(value: Any, field: str, index: int) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise TindexPayloadError(f"data.{field}[{index}] must be a finite number")
        try:
            result = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise TindexPayloadError(f"data.{field}[{index}] must be a finite number") from None
        if not result.is_finite():
            raise TindexPayloadError(f"data.{field}[{index}] must be a finite number")
        return result

    normalized: list[dict[str, Any]] = []
    for index, day in enumerate(dates):
        if not isinstance(arrays["partial"][index], bool):
            raise TindexPayloadError(f"data.partial[{index}] must be boolean")
        open_ = decimal_value(arrays["o"][index], "o", index)
        high = decimal_value(arrays["h"][index], "h", index)
        low = decimal_value(arrays["l"][index], "l", index)
        close = decimal_value(arrays["c"][index], "c", index)
        if high < max(open_, low, close) or low > min(open_, high, close):
            raise TindexPayloadError(f"candle {index} violates OHLC high/low invariants")

        normalized.append({
            "source_id": SOURCE_ID,
            "instrument_key": slug.strip(),
            "display_name": data.get("name") if isinstance(data.get("name"), str) else None,
            "observation_date": day.isoformat(),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "partial": arrays["partial"][index],
            "unit": unit.strip() if isinstance(unit, str) else None,
            "provider_source": data.get("source") if isinstance(data.get("source"), str) else None,
            "requested_range": data.get("range") if isinstance(data.get("range"), str) else None,
            "interval": data.get("interval") if isinstance(data.get("interval"), str) else None,
            "eligible_for_scoring": False,
        })
    return normalized
