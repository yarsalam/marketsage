"""Batch acceptance invariants for source adapters.

These deterministic sweeps are robustness/regression evidence, not live-source
connectivity or classifier-accuracy evidence. No network calls or credentials.
"""
from __future__ import annotations

from gdelt_news_provider import normalize_gdelt_articles
from headline_signal_engine import analyze_headline
from source_registry import SOURCES


def test_headline_engine_batch_invariants_over_2000_inputs():
    """Exercise 2,000 deterministic variants in one test invocation."""
    stems = [
        "Markets surge after agreement",
        "Stocks crash amid sanctions",
        "Central bank announces rate decision",
        "دولت از توافق خبر داد و بازار رشد کرد",
        "حمله موشکی و تشدید جنگ منطقه‌ای",
        "بانک مرکزی نرخ بهره را اعلام کرد",
        "Officials discuss a new plan",
        "Inflation rises after policy announcement",
    ]
    wrappers = [
        "{headline}",
        "BREAKING: {headline}!",
        "  {headline}  ",
        "[market update] {headline} — reported today",
        "{headline} / {headline}",
    ]
    count = 0
    for i in range(400):
        stem = stems[i % len(stems)]
        wrapper = wrappers[(i // len(stems)) % len(wrappers)]
        headline = wrapper.format(headline=stem) + ("." * (i % 4))
        result = analyze_headline(headline)
        assert result["validated_model"] is False
        assert result["confidence_probability"] is None
        assert result["eligible_for_scoring"] is False
        assert result["source_id"] == "marketsage.headline_lexicon_baseline"
        assert result["sentiment_label"] in {
            "positive", "negative", "unknown", "mixed_or_neutral"
        }
        evidence = result["sentiment_evidence"]
        assert isinstance(evidence["positive_terms"], list)
        assert isinstance(evidence["negative_terms"], list)
        assert result["lexicon_score"] == (
            len(evidence["positive_terms"]) - len(evidence["negative_terms"])
        )
        assert result["event_categories"] == evidence["event_categories"]
        count += 1
    # Repeat with 1,600 generated combinations; deterministic, no external data.
    for i in range(1600):
        stem = stems[(i * 7 + 3) % len(stems)]
        suffix = ("!" * (i % 7)) + ("؟" if i % 2 else "...")
        result = analyze_headline(f"{stem}{suffix}")
        assert result["eligible_for_scoring"] is False
        assert result["confidence_probability"] is None
        assert result["sentiment_label"] in {
            "positive", "negative", "unknown", "mixed_or_neutral"
        }
        count += 1
    assert count == 2000


def test_gdelt_batch_url_canonicalization_deduplicates_1000_variants():
    """One thousand URL rows collapse to one canonical article, with no scoring."""
    articles = []
    for i in range(1000):
        # Host case and fragment are intentionally variable; URL identity is stable.
        host = "EXAMPLE.COM" if i % 2 else "example.com"
        fragment = f"#tracking-{i}"
        articles.append({
            "url": f"https://{host}/market/story?id=42{fragment}",
            "title": f"Headline variant {i}",
            "seendate": "20261016T103000",
        })
    rows = normalize_gdelt_articles({"articles": articles})
    assert len(rows) == 1
    row = rows[0]
    assert row["url"] == "https://example.com/market/story?id=42"
    assert row["publisher_published_at"] is None
    assert row["sentiment"] is None
    assert row["political_event_type"] is None
    assert row["verified"] is False
    assert row["eligible_for_scoring"] is False


def test_new_candidate_sources_remain_fail_closed_as_a_batch():
    """Registry cannot silently imply production approval for candidate adapters."""
    candidate_ids = {
        "us.fred.alfred",
        "iran.tsetmc",
        "iran.codal",
        "iran.tindex.public_api",
        "global.gdelt_doc_api",
        "marketsage.headline_lexicon_baseline",
    }
    by_id = {source.source_id: source for source in SOURCES}
    assert candidate_ids <= by_id.keys()
    for source_id in candidate_ids:
        source = by_id[source_id]
        assert source.approved_for_production is False, source_id
        assert source.used_by_research_engine is False, source_id
