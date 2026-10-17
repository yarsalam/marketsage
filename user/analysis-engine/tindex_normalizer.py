"""Conservative normalization for the observed Tindex currency-rates envelope.

This module validates shape and primitive types only. It intentionally does not
assign a currency unit, market definition, observation timestamp, or scoring
eligibility without provider evidence.
"""
from __future__ import annotations

import math
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
