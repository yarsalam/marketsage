"""Canonical, provider-neutral instrument identities for the research universe.

Only the small global proxy universe already configured by the analysis service is
registered here. Provider symbols are aliases into this catalog, never canonical IDs.
No Iranian market instrument is admitted without identity and source evidence.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable


REGISTRY_VERSION = "1.0.0"
RESEARCH_SOURCE_ID = "global.yahoo_finance.yfinance"
_INSTRUMENT_ID = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z0-9]+)+$")


@dataclass(frozen=True)
class InstrumentDefinition:
    instrument_id: str
    display_name: str
    market_universe: str
    asset_family: str
    instrument_type: str
    research_role: str
    source_id: str
    provider_symbol: str
    quote_currency: str
    quote_unit: str
    price_basis: str
    venue: str | None
    identity_status: str
    tradability_status: str
    production_approved: bool
    aliases: tuple[str, ...] = ()


# These are the symbols used by the pre-existing global-proxy prototype.
# Venue, execution access and Iran tradability are deliberately not inferred.
_INSTRUMENT_ROWS: tuple[InstrumentDefinition, ...] = (
    InstrumentDefinition("global.proxy.crypto.bitcoin", "Bitcoin", "global_proxy", "crypto", "crypto_spot_pair", "research_proxy", RESEARCH_SOURCE_ID, "BTC-USD", "USD", "usd_per_token", "provider_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.crypto.ethereum", "Ethereum", "global_proxy", "crypto", "crypto_spot_pair", "research_proxy", RESEARCH_SOURCE_ID, "ETH-USD", "USD", "usd_per_token", "provider_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.crypto.solana", "Solana", "global_proxy", "crypto", "crypto_spot_pair", "research_proxy", RESEARCH_SOURCE_ID, "SOL-USD", "USD", "usd_per_token", "provider_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.gold", "Gold ETF (US proxy)", "global_proxy", "precious_metal_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "GLD", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.sp500", "S&P 500 ETF (US proxy)", "global_proxy", "equity_index_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "SPY", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.nasdaq100", "Nasdaq ETF (US proxy)", "global_proxy", "equity_index_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "QQQ", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.us_treasury", "US Treasury ETF", "global_proxy", "fixed_income_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "TLT", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.us_dollar", "US Dollar ETF", "global_proxy", "currency_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "UUP", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.oil", "Oil ETF (US proxy)", "global_proxy", "energy_commodity_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "USO", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.us_financials", "US Financials ETF", "global_proxy", "equity_sector_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "XLF", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
    InstrumentDefinition("global.proxy.etf.us_energy", "US Energy ETF", "global_proxy", "equity_sector_proxy", "exchange_traded_fund", "research_proxy", RESEARCH_SOURCE_ID, "XLE", "USD", "usd_per_share", "adjusted_close", None, "provider_symbol_identity_only", "not_assessed", False),
)

EMPTY_UNIVERSES: tuple[dict[str, str], ...] = (
    {"market_universe": "iran_equities", "status": "empty_quarantined", "reason": "No canonical instrument admitted; symbol identity, corporate actions, permissions and independent reconciliation remain open."},
    {"market_universe": "iran_gold_coin", "status": "empty_quarantined", "reason": "No provider or canonical product/weight/unit definition has passed evidence review."},
    {"market_universe": "iran_fx", "status": "empty_quarantined", "reason": "Official, exchange and free-market pairs must remain distinct; provider, quote convention and history are not accepted."},
    {"market_universe": "iran_fixed_income", "status": "empty_quarantined", "reason": "Fund identity, NAV versus exchange price, yield definition and publication time remain unverified."},
    {"market_universe": "iran_crypto", "status": "empty_quarantined", "reason": "No venue-specific pair, quote currency, fees, liquidity and historical contract has passed review."},
)


class InstrumentRegistryError(ValueError):
    """Raised when an instrument catalog violates identity or unit invariants."""


def validate_registry(
    instruments: Iterable[InstrumentDefinition] = _INSTRUMENT_ROWS,
) -> None:
    """Reject duplicate identities, ambiguous provider mappings and unsafe metadata."""
    rows = tuple(instruments)
    instrument_ids: set[str] = set()
    provider_mappings: set[tuple[str, str]] = set()

    for item in rows:
        if not _INSTRUMENT_ID.fullmatch(item.instrument_id):
            raise InstrumentRegistryError("instrument_id must be a stable dotted canonical identifier")
        if item.instrument_id in instrument_ids:
            raise InstrumentRegistryError("duplicate canonical instrument_id")
        instrument_ids.add(item.instrument_id)

        if not item.display_name.strip() or not item.provider_symbol.strip():
            raise InstrumentRegistryError("display_name and provider_symbol are required")
        if item.research_role != "research_proxy":
            raise InstrumentRegistryError("only explicitly marked research proxies are admitted")
        if item.market_universe != "global_proxy":
            raise InstrumentRegistryError("only the existing global_proxy universe is admitted")
        if item.source_id != RESEARCH_SOURCE_ID:
            raise InstrumentRegistryError("instrument source_id is not registered for this catalog")
        if item.production_approved:
            raise InstrumentRegistryError("instrument catalog cannot grant production approval")
        if item.tradability_status != "not_assessed" or item.venue is not None:
            raise InstrumentRegistryError("unknown venue/tradability must not be inferred")

        expected_unit = "usd_per_token" if item.instrument_type == "crypto_spot_pair" else "usd_per_share"
        if item.instrument_type not in {"crypto_spot_pair", "exchange_traded_fund"}:
            raise InstrumentRegistryError("unsupported instrument_type")
        if item.quote_currency != "USD" or item.quote_unit != expected_unit:
            raise InstrumentRegistryError("quote_currency and quote_unit do not match instrument_type")
        expected_basis = "provider_close" if item.instrument_type == "crypto_spot_pair" else "adjusted_close"
        if item.price_basis != expected_basis:
            raise InstrumentRegistryError("price_basis does not match the declared instrument_type")

        mapping = (item.source_id, item.provider_symbol)
        if mapping in provider_mappings:
            raise InstrumentRegistryError("duplicate provider/source symbol mapping")
        provider_mappings.add(mapping)

        if any(not alias.strip() for alias in item.aliases):
            raise InstrumentRegistryError("aliases cannot contain empty values")


def instrument_catalog() -> dict:
    """Return a deterministic catalog; presence does not grant investment eligibility."""
    validate_registry()
    entries = [asdict(item) for item in _INSTRUMENT_ROWS]
    for item in entries:
        item["aliases"] = list(item["aliases"])
        item["scoring_gate"] = {
            "eligible": False,
            "blocked_reasons": ["research_proxy_only", "production_approval_missing", "tradability_not_assessed"],
        }
    return {
        "registry_version": REGISTRY_VERSION,
        "policy": "Canonical identity is separate from provider symbols. All listed instruments are research proxies only and are not production-approved or confirmed tradable in Iran.",
        "summary": {
            "instrument_count": len(entries),
            "global_proxy_count": len(entries),
            "production_approved_count": 0,
            "iran_instrument_count": 0,
            "quarantined_iran_universes": len(EMPTY_UNIVERSES),
        },
        "instruments": entries,
        "empty_universes": [dict(item) for item in EMPTY_UNIVERSES],
    }
