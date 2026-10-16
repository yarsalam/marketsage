"""Quality-gated contracts and source registry for Iranian market data.

This module intentionally does not mark candidate sources as production-ready.
No Iranian instrument is included in live scoring until payloads, licensing,
history coverage, units, corporate actions and freshness have been independently
validated.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class MarketDataPoint:
    market: str
    symbol: str
    observed_at: date
    close: float
    currency: str
    price_unit: str
    source: str
    retrieved_at: datetime
    adjusted: bool
    volume: float | None = None


@dataclass(frozen=True)
class ProviderDefinition:
    market: str
    label: str
    status: str
    enabled_for_scoring: bool
    source: str | None
    notes: str
    candidate_endpoints: tuple[str, ...] = ()


PROVIDERS: tuple[ProviderDefinition, ...] = (
    ProviderDefinition(
        market="iran_equities",
        label="بورس و فرابورس ایران",
        status="candidate_requires_validation",
        enabled_for_scoring=False,
        source="TSETMC community-documented endpoints",
        notes=(
            "Historical daily prices and adjusted-price endpoints are candidates, "
            "not yet verified as a stable API contract. Validate symbol mapping, "
            "corporate actions, suspensions, history depth and access from the server."
        ),
        candidate_endpoints=(
            "https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/{query}",
            "https://cdn.tsetmc.com/api/ClosingPrice/GetClosingPriceDailyList/{insCode}/0",
            "https://cdn.tsetmc.com/api/ClosingPrice/GetPriceAdjustList/{insCode}",
        ),
    ),
    ProviderDefinition(
        market="iran_gold_coin",
        label="طلای ایران و سکه",
        status="provider_not_selected",
        enabled_for_scoring=False,
        source=None,
        notes=(
            "Need a licensed or otherwise permitted source with auditable daily history, "
            "clear gram/coin definitions and stable Rial/Toman units. No fallback to "
            "unverified pages or current quotes."
        ),
    ),
    ProviderDefinition(
        market="iran_fx",
        label="ارز بازار ایران",
        status="provider_not_selected",
        enabled_for_scoring=False,
        source=None,
        notes=(
            "Must distinguish free-market, exchange, official and other rates; store "
            "currency pair, market type and quote/base convention. Never merge series."
        ),
    ),
    ProviderDefinition(
        market="crypto_global",
        label="رمزارز جهانی",
        status="existing_global_provider",
        enabled_for_scoring=False,
        source="Yahoo Finance via yfinance",
        notes=(
            "Existing prototype feed only; separate from local Iranian exchange prices. "
            "This catalog does not change current scoring behavior."
        ),
    ),
    ProviderDefinition(
        market="crypto_local",
        label="رمزارز در صرافی‌های ایران",
        status="provider_not_selected",
        enabled_for_scoring=False,
        source=None,
        notes=(
            "Requires exchange-specific OHLCV, pair, quote currency, fees and availability; "
            "never combine toman prices with USD prices without a validated FX series."
        ),
    ),
)

EXPECTED_UNITS: dict[str, set[tuple[str, str]]] = {
    "iran_equities": {("IRR", "rial_per_share"), ("IRT", "toman_per_share")},
    "iran_gold_coin": {
        ("IRR", "rial_per_gram"),
        ("IRT", "toman_per_gram"),
        ("IRR", "rial_per_coin"),
        ("IRT", "toman_per_coin"),
    },
    "iran_fx": {
        ("IRR", "rial_per_foreign_currency_unit"),
        ("IRT", "toman_per_foreign_currency_unit"),
    },
    "crypto_global": {("USD", "usd_per_token")},
    "crypto_local": {("IRT", "toman_per_token"), ("IRR", "rial_per_token")},
}

MAX_OBSERVATION_AGE_DAYS = {
    "iran_equities": 5,
    "iran_gold_coin": 3,
    "iran_fx": 3,
    "crypto_global": 3,
    "crypto_local": 1,
}


class DataQualityError(ValueError):
    """Raised when data cannot safely enter downstream calculations."""


def provider_catalog() -> dict:
    """Return a JSON-serializable, transparent provider readiness catalog."""
    return {
        "policy": "No candidate provider is used for scoring until validated.",
        "markets": [
            {
                **asdict(provider),
                "candidate_endpoints": list(provider.candidate_endpoints),
            }
            for provider in PROVIDERS
        ],
    }


def validate_points(
    points: Iterable[MarketDataPoint],
    *,
    today: date | None = None,
    max_age_days: dict[str, int] | None = None,
) -> list[MarketDataPoint]:
    """Validate units, provenance, timestamps and duplicates without filling gaps.

    This validator does not certify source accuracy or corporate-action handling;
    those remain provider-specific acceptance criteria.
    """
    current_day = today or datetime.now(timezone.utc).date()
    age_limits = max_age_days or MAX_OBSERVATION_AGE_DAYS
    accepted: list[MarketDataPoint] = []
    seen: set[tuple[str, str, date]] = set()

    for point in points:
        if point.market not in EXPECTED_UNITS:
            raise DataQualityError(f"Unknown market: {point.market}")
        if not point.symbol.strip() or not point.source.strip():
            raise DataQualityError("Symbol and source provenance are required")
        if (point.currency, point.price_unit) not in EXPECTED_UNITS[point.market]:
            raise DataQualityError(
                f"Unit mismatch for {point.market}: {point.currency}/{point.price_unit}"
            )
        if not isfinite(point.close) or point.close <= 0:
            raise DataQualityError("Close must be a finite positive number")
        if point.market == "iran_equities" and not point.adjusted:
            raise DataQualityError(
                "Iranian equity scoring requires adjusted prices until a separate "
                "corporate-action-aware return pipeline is implemented"
            )
        if point.volume is not None and (
            not isfinite(point.volume) or point.volume < 0
        ):
            raise DataQualityError("Volume must be finite and non-negative")
        if point.retrieved_at.tzinfo is None or point.retrieved_at.utcoffset() is None:
            raise DataQualityError("retrieved_at must include a timezone")
        age = (current_day - point.observed_at).days
        if age < 0:
            raise DataQualityError("Future observations are not accepted")
        if age > age_limits[point.market]:
            raise DataQualityError(
                f"Stale observation for {point.market}: {age} days old"
            )
        key = (point.market, point.symbol, point.observed_at)
        if key in seen:
            raise DataQualityError(f"Duplicate observation: {key}")
        seen.add(key)
        accepted.append(point)

    return accepted
