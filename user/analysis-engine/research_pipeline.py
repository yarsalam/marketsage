"""Fixture-backed end-to-end research snapshot for MarketSage.

This prototype joins bounded, already-normalized headline metadata to a supplied
market-price series and computes descriptive historical metrics. It is not a
production ingestion scheduler, does not infer publication timestamps, and never
emits an investment rank or scoring eligibility.
"""
from __future__ import annotations

import math
from datetime import date
from statistics import stdev
from typing import Any

from headline_signal_engine import analyze_headline

PIPELINE_VERSION = "research_snapshot_v1"
MAX_ARTICLES = 500
MAX_PRICE_POINTS = 5000


def _iso_date(value: Any, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be an ISO date YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be an ISO date YYYY-MM-DD")
    return parsed


def _positive_finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a positive finite number")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field} must be a positive finite number")
    return number


def _price_metrics(observations: list[dict[str, Any]], as_of: date) -> dict[str, Any]:
    if not isinstance(observations, list) or len(observations) > MAX_PRICE_POINTS:
        raise ValueError(f"observations must be a list of at most {MAX_PRICE_POINTS} items")

    by_day: dict[date, float] = {}
    for index, row in enumerate(observations):
        if not isinstance(row, dict):
            raise ValueError(f"observations[{index}] must be an object")
        day = _iso_date(row.get("date"), f"observations[{index}].date")
        close = _positive_finite_number(row.get("close"), f"observations[{index}].close")
        if day in by_day:
            raise ValueError(f"duplicate observation date: {day.isoformat()}")
        if day <= as_of:
            by_day[day] = close

    ordered = sorted(by_day.items())
    if len(ordered) < 2:
        return {
            "status": "insufficient_history",
            "observations_used": len(ordered),
            "first_observation_date": ordered[0][0].isoformat() if ordered else None,
            "last_observation_date": ordered[-1][0].isoformat() if ordered else None,
            "total_return": None,
            "daily_volatility": None,
            "max_drawdown": None,
        }

    prices = [price for _, price in ordered]
    returns = [prices[i] / prices[i - 1] - 1 for i in range(1, len(prices))]
    peak = prices[0]
    drawdowns: list[float] = []
    for price in prices:
        peak = max(peak, price)
        drawdowns.append(price / peak - 1)

    return {
        "status": "descriptive_metrics_available",
        "observations_used": len(ordered),
        "first_observation_date": ordered[0][0].isoformat(),
        "last_observation_date": ordered[-1][0].isoformat(),
        "total_return": prices[-1] / prices[0] - 1,
        "daily_volatility": stdev(returns) if len(returns) >= 2 else None,
        "max_drawdown": min(drawdowns),
    }


def build_research_snapshot(
    *,
    as_of_date: str,
    articles: list[dict[str, Any]],
    market_series: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a reproducible snapshot from normalized records and a fixed cutoff.

    Article date fields are day-level only. The pipeline therefore does not claim
    intraday point-in-time ordering or use headline signals in market returns.
    """
    as_of = _iso_date(as_of_date, "as_of_date")
    if not isinstance(articles, list) or len(articles) > MAX_ARTICLES:
        raise ValueError(f"articles must be a list of at most {MAX_ARTICLES} items")
    if not isinstance(market_series, list) or len(market_series) > 100:
        raise ValueError("market_series must be a list of at most 100 items")

    article_results: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    excluded_future_articles = 0
    for index, article in enumerate(articles):
        if not isinstance(article, dict):
            raise ValueError(f"articles[{index}] must be an object")
        title = article.get("title")
        url = article.get("url")
        first_seen_date = article.get("first_seen_date")
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"articles[{index}].url must be a non-empty string")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        day = _iso_date(first_seen_date, f"articles[{index}].first_seen_date")
        if day > as_of:
            excluded_future_articles += 1
            continue
        signal = analyze_headline(title)
        article_results.append({
            "source_id": article.get("source_id", "fixture.news"),
            "url": url,
            "title": title.strip(),
            "first_seen_date": day.isoformat(),
            "sentiment_label": signal["sentiment_label"],
            "sentiment_evidence": signal["sentiment_evidence"],
            "event_categories": signal["event_categories"],
            "confidence_probability": None,
            "validated_model": False,
            "eligible_for_scoring": False,
        })

    market_results: list[dict[str, Any]] = []
    seen_symbols: set[str] = set()
    for index, series in enumerate(market_series):
        if not isinstance(series, dict):
            raise ValueError(f"market_series[{index}] must be an object")
        symbol = series.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError(f"market_series[{index}].symbol must be a non-empty string")
        symbol = symbol.strip()
        if symbol in seen_symbols:
            raise ValueError(f"duplicate market symbol: {symbol}")
        seen_symbols.add(symbol)
        unit = series.get("unit")
        currency = series.get("currency")
        unit_confirmed = series.get("unit_confirmed") is True
        currency_confirmed = series.get("currency_confirmed") is True
        metrics = _price_metrics(series.get("observations", []), as_of)
        market_results.append({
            "symbol": symbol,
            "source_id": series.get("source_id", "fixture.market"),
            "unit": unit if isinstance(unit, str) else None,
            "currency": currency if isinstance(currency, str) else None,
            "unit_confirmed": unit_confirmed,
            "currency_confirmed": currency_confirmed,
            "metrics": metrics,
            "eligible_for_scoring": False,
            "exclusion_reasons": [
                reason for condition, reason in (
                    (not unit_confirmed, "unit_not_confirmed"),
                    (not currency_confirmed, "currency_not_confirmed"),
                    (series.get("source_approved") is not True, "source_not_approved"),
                    (metrics["status"] != "descriptive_metrics_available", "insufficient_history"),
                ) if condition
            ],
        })

    return {
        "pipeline_version": PIPELINE_VERSION,
        "as_of_date": as_of.isoformat(),
        "generated_for": "research_prototype",
        "news": {
            "articles_analyzed": len(article_results),
            "future_articles_excluded": excluded_future_articles,
            "articles": article_results,
            "publication_time_verified": False,
        },
        "markets": market_results,
        "investment_ranking": None,
        "investment_ranking_status": "disabled_until_source_and_model_acceptance",
        "point_in_time_limitations": [
            "Article dates are day-level first-seen dates, not verified publisher release times.",
            "Headline sentiment/event labels are an unvalidated keyword baseline.",
            "Price metrics are descriptive and do not establish tradability or future performance.",
        ],
    }
