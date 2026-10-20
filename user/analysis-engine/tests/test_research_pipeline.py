from __future__ import annotations

import pytest

from research_pipeline import build_research_snapshot


def _inputs():
    articles = [
        {
            "source_id": "global.gdelt_doc_api",
            "url": "https://example.test/news/1",
            "title": "Central bank announces agreement and growth",
            "first_seen_date": "2026-10-15",
        },
        {
            "source_id": "global.gdelt_doc_api",
            "url": "https://example.test/news/2",
            "title": "Missile attack raises sanctions concerns",
            "first_seen_date": "2026-10-16",
        },
        {
            "source_id": "global.gdelt_doc_api",
            "url": "https://example.test/future",
            "title": "Markets surge after agreement",
            "first_seen_date": "2026-10-19",
        },
    ]
    market_series = [
        {
            "symbol": "DEMO",
            "source_id": "fixture.market",
            "unit": "USD per unit",
            "currency": "USD",
            "unit_confirmed": True,
            "currency_confirmed": True,
            "source_approved": True,
            "observations": [
                {"date": "2026-10-13", "close": 100},
                {"date": "2026-10-14", "close": 110},
                {"date": "2026-10-15", "close": 99},
                {"date": "2026-10-17", "close": 108},
                {"date": "2026-10-20", "close": 1000},
            ],
        }
    ]
    return articles, market_series


def test_end_to_end_snapshot_joins_headline_signals_and_market_metrics_without_scoring():
    articles, market_series = _inputs()
    result = build_research_snapshot(
        as_of_date="2026-10-17",
        articles=articles,
        market_series=market_series,
    )

    assert result["pipeline_version"] == "research_snapshot_v1"
    assert result["news"]["articles_analyzed"] == 2
    assert result["news"]["future_articles_excluded"] == 1
    assert result["news"]["articles"][0]["sentiment_label"] == "positive"
    assert "macro_monetary" in result["news"]["articles"][0]["event_categories"]
    metrics = result["markets"][0]["metrics"]
    assert metrics["observations_used"] == 4
    assert metrics["last_observation_date"] == "2026-10-17"
    assert metrics["total_return"] == pytest.approx(0.08)
    assert result["investment_ranking"] is None
    assert result["investment_ranking_status"] == "disabled_until_source_and_model_acceptance"
    assert result["markets"][0]["eligible_for_scoring"] is False


def test_future_price_observations_do_not_leak_into_metrics():
    _, market_series = _inputs()
    before = build_research_snapshot(
        as_of_date="2026-10-17",
        articles=[],
        market_series=market_series,
    )
    after = build_research_snapshot(
        as_of_date="2026-10-20",
        articles=[],
        market_series=market_series,
    )

    assert before["markets"][0]["metrics"]["last_observation_date"] == "2026-10-17"
    assert before["markets"][0]["metrics"]["total_return"] != after["markets"][0]["metrics"]["total_return"]


def test_duplicate_article_urls_are_deduplicated():
    articles, market_series = _inputs()
    articles.append({**articles[0], "title": "Different duplicate title"})
    result = build_research_snapshot(
        as_of_date="2026-10-17",
        articles=articles,
        market_series=market_series,
    )
    assert result["news"]["articles_analyzed"] == 2


@pytest.mark.parametrize("bad_date", ["2026/10/17", "not-a-date", 20261017])
def test_invalid_cutoff_date_is_rejected(bad_date):
    with pytest.raises(ValueError, match="as_of_date"):
        build_research_snapshot(
            as_of_date=bad_date,
            articles=[],
            market_series=[],
        )


@pytest.mark.parametrize("bad_close", [0, -1, float("nan"), float("inf"), True, "100"])
def test_invalid_price_values_are_rejected(bad_close):
    with pytest.raises(ValueError, match="positive finite number"):
        build_research_snapshot(
            as_of_date="2026-10-17",
            articles=[],
            market_series=[{
                "symbol": "DEMO",
                "observations": [{"date": "2026-10-17", "close": bad_close}],
            }],
        )


def test_duplicate_price_dates_are_rejected():
    with pytest.raises(ValueError, match="duplicate observation date"):
        build_research_snapshot(
            as_of_date="2026-10-17",
            articles=[],
            market_series=[{
                "symbol": "DEMO",
                "observations": [
                    {"date": "2026-10-16", "close": 10},
                    {"date": "2026-10-16", "close": 11},
                ],
            }],
        )


def test_unknown_units_and_unapproved_source_are_explicitly_excluded():
    result = build_research_snapshot(
        as_of_date="2026-10-17",
        articles=[],
        market_series=[{
            "symbol": "UNKNOWN",
            "unit": None,
            "currency": None,
            "unit_confirmed": False,
            "currency_confirmed": False,
            "source_approved": False,
            "observations": [
                {"date": "2026-10-16", "close": 10},
                {"date": "2026-10-17", "close": 12},
            ],
        }],
    )
    assert result["markets"][0]["eligible_for_scoring"] is False
    assert set(result["markets"][0]["exclusion_reasons"]) == {
        "unit_not_confirmed",
        "currency_not_confirmed",
        "source_not_approved",
    }


def test_empty_history_returns_insufficient_history_not_fake_metrics():
    result = build_research_snapshot(
        as_of_date="2026-10-17",
        articles=[],
        market_series=[{"symbol": "EMPTY", "observations": []}],
    )
    assert result["markets"][0]["metrics"]["status"] == "insufficient_history"
    assert result["markets"][0]["metrics"]["total_return"] is None
    assert "insufficient_history" in result["markets"][0]["exclusion_reasons"]
