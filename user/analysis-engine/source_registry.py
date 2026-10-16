"""Versioned registry of market-data sources and their acceptance status.

A source being listed is not approval for production use. The registry deliberately
separates prototype wiring, production approval, timestamp quality and validation gates.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


REGISTRY_VERSION = "1.0.0"


@dataclass(frozen=True)
class SourceDefinition:
    source_id: str
    market_scope: str
    asset_family: str
    provider: str | None
    status: str
    used_by_research_engine: bool
    approved_for_production: bool
    data_kinds: tuple[str, ...]
    timestamp_quality: str
    required_checks: tuple[str, ...]
    notes: str


SOURCES: tuple[SourceDefinition, ...] = (
    SourceDefinition(
        source_id="global.yahoo_finance.yfinance",
        market_scope="global",
        asset_family="equities_gold_fx_fixed_income_crypto_proxies",
        provider="Yahoo Finance via yfinance",
        status="research_only_existing",
        used_by_research_engine=True,
        approved_for_production=False,
        data_kinds=("adjusted_close",),
        timestamp_quality="retrieval_time_known; original publication time unavailable",
        required_checks=("terms_and_redistribution_rights", "historical_reconciliation",
                         "corporate_actions", "symbol_and_currency_mapping",
                         "missing_sessions_and_staleness"),
        notes=("Current prototype price source. US ETFs are global signal proxies, not "
               "claims that the instruments are tradable in Iran."),
    ),
    SourceDefinition(
        source_id="us.fred.alfred",
        market_scope="global",
        asset_family="macro_rates_yields_inflation",
        provider="Federal Reserve Bank of St. Louis FRED/ALFRED",
        status="adapter_implemented_not_scheduled",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("macro_observation_vintage",),
        timestamp_quality="vintage date is day-level; adapter uses conservative 23:59:59 UTC",
        required_checks=("series_specific_release_calendar", "api_limits_and_key",
                         "vintage_reconciliation", "exact_release_time_if_needed"),
        notes="Historical vintages can support source-vintage replay; not yet wired into scoring.",
    ),
    SourceDefinition(
        source_id="iran.tsetmc",
        market_scope="iran",
        asset_family="equities_and_funds",
        provider="TSETMC candidate endpoints",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("daily_ohlcv", "adjusted_price", "fund_quote"),
        timestamp_quality="not_verified",
        required_checks=("actual_host_connectivity", "terms_and_access_permission",
                         "symbol_identity", "adjusted_history", "suspensions",
                         "historical_depth", "unit_and_currency"),
        notes="Candidate only; no Iranian equity or fund feed is enabled for scoring.",
    ),
    SourceDefinition(
        source_id="iran.codal",
        market_scope="iran",
        asset_family="company_filings_and_corporate_events",
        provider="CODAL",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("issuer_disclosure", "corporate_event"),
        timestamp_quality="publication/update semantics need validation",
        required_checks=("publication_timestamp", "amendment_linkage",
                         "parser_fixtures", "historical_coverage"),
        notes="Use original disclosure and its publication time; do not infer event time from crawl time.",
    ),
    SourceDefinition(
        source_id="iran.official_macro",
        market_scope="iran",
        asset_family="macro_inflation_rates",
        provider="Central Bank of Iran and Statistical Center of Iran",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("macro_observation", "release_document"),
        timestamp_quality="release timestamps and revision history not yet verified",
        required_checks=("publication_time", "revision_history", "units_and_definitions",
                         "machine_readable_history"),
        notes="Official sources are candidates; release-time availability must be audited.",
    ),
    SourceDefinition(
        source_id="iran.tindex.public_api",
        market_scope="iran_and_global",
        asset_family="currency_precious_metals_crypto",
        provider="Tindex public developer API (free tier; current enabled endpoints only)",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("currency_rate", "precious_metal_quote", "crypto_indicator"),
        timestamp_quality="not_verified",
        required_checks=("terms_and_commercial_rights", "automated_collection_permission",
                         "payload_schema_and_units", "historical_depth", "publication_and_retrieval_times",
                         "revisions_and_missing_intervals", "independent_reconciliation"),
        notes=("Dashboard notice disables TSE/equities, news, inflation/macro, housing, and calendar "
               "endpoints (410 Gone). Only currency, precious metals, and crypto are candidate families; "
               "this entry is not production approval."),
    ),
    SourceDefinition(
        source_id="iran.gold_fx",
        market_scope="iran",
        asset_family="gold_coins_and_fx",
        provider=None,
        status="provider_not_selected",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("gold_gram", "coin_quote", "fx_quote"),
        timestamp_quality="not_available",
        required_checks=("two_provider_reconciliation", "legal_use_rights",
                         "free_market_vs_official_rate", "rial_toman_units",
                         "historical_depth", "timestamp_and_corrections"),
        notes="No source selected. Gold types and official/free-market FX must remain separate series.",
    ),
    SourceDefinition(
        source_id="iran.fixed_income",
        market_scope="iran",
        asset_family="fixed_income_and_funds",
        provider="TSETMC/CODAL candidates; fund-specific source TBD",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("fund_price", "nav", "yield_or_rate"),
        timestamp_quality="not_verified",
        required_checks=("price_vs_nav", "distribution_adjustments", "yield_definition",
                         "publication_time", "fund_identity"),
        notes="Do not combine NAV, exchange price, and yield without explicit definitions.",
    ),
    SourceDefinition(
        source_id="crypto.exchange_specific",
        market_scope="iran_and_global",
        asset_family="crypto_spot_and_liquidity",
        provider="Venue-specific exchange APIs; venue selection pending",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("ohlcv", "order_book", "volume", "fees"),
        timestamp_quality="venue-specific validation required",
        required_checks=("venue_terms", "pair_and_quote_currency", "missing_intervals",
                         "fees_and_liquidity", "history_depth", "clock_and_corrections"),
        notes="Keep each venue and quote currency distinct; do not merge local and USD prices blindly.",
    ),
    SourceDefinition(
        source_id="global.sec_edgar",
        market_scope="global",
        asset_family="company_filings",
        provider="SEC EDGAR",
        status="candidate_requires_validation",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("filing", "company_facts"),
        timestamp_quality="acceptance timestamp available but field mapping needs audit",
        required_checks=("filing_acceptance_time", "amendments", "point_in_time_field_mapping",
                         "request_policy"),
        notes="Candidate source for US issuer fundamentals and disclosures.",
    ),
    SourceDefinition(
        source_id="global.gdelt_news_discovery",
        market_scope="global_and_iran",
        asset_family="news_and_geopolitical_events",
        provider="GDELT discovery layer; original publishers for verification",
        status="discovery_only_not_verified",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("candidate_article", "candidate_event"),
        timestamp_quality="crawl/index timestamp is not proof of original publication time",
        required_checks=("original_source_verification", "publication_and_update_times",
                         "duplicates_and_corrections", "language_coverage", "licensing"),
        notes="Never treat a discovery/index result alone as verified event truth.",
    ),
    SourceDefinition(
        source_id="sentiment.provider_tbd",
        market_scope="iran_and_global",
        asset_family="social_sentiment",
        provider=None,
        status="provider_not_selected",
        used_by_research_engine=False,
        approved_for_production=False,
        data_kinds=("public_post_signal",),
        timestamp_quality="not_available",
        required_checks=("collection_and_retention_rights", "deletion_policy",
                         "bot_and_spam_controls", "persian_language_quality",
                         "sampling_bias", "historical_replay"),
        notes="No social source is connected; no sentiment signal affects decisions.",
    ),
)


def source_scoring_gate(source_id: str) -> dict:
    """Fail-closed production scoring gate; registry presence is never approval."""
    source = next((item for item in SOURCES if item.source_id == source_id), None)
    if source is None:
        return {
            "source_id": source_id,
            "eligible_for_production_scoring": False,
            "blocked_reasons": ["source_not_registered"],
        }

    blocked_reasons: list[str] = []
    if not source.approved_for_production:
        blocked_reasons.append("production_approval_missing")
    if source.status != "production_approved":
        blocked_reasons.append("source_status_not_production_approved")
    if source.timestamp_quality in {"not_verified", "not_available"}:
        blocked_reasons.append("timestamp_quality_not_verified")
    return {
        "source_id": source.source_id,
        "eligible_for_production_scoring": not blocked_reasons,
        "blocked_reasons": blocked_reasons,
    }


def source_catalog() -> dict:
    """Return JSON-serializable registry entries for API/UI and audit tooling."""
    entries = []
    for source in SOURCES:
        item = asdict(source)
        item["data_kinds"] = list(source.data_kinds)
        item["required_checks"] = list(source.required_checks)
        item["scoring_gate"] = source_scoring_gate(source.source_id)
        entries.append(item)
    return {
        "registry_version": REGISTRY_VERSION,
        "policy": "Listed does not mean production-approved; only explicitly approved sources may enter production scoring.",
        "summary": {
            "total_sources": len(entries),
            "production_approved": sum(s.approved_for_production for s in SOURCES),
            "research_wired": sum(s.used_by_research_engine for s in SOURCES),
            "pending_or_unapproved": sum(not s.approved_for_production for s in SOURCES),
        },
        "sources": entries,
    }
