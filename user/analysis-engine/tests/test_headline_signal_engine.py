import pytest

from headline_signal_engine import analyze_headline


@pytest.mark.parametrize(("headline", "label", "category"), [
    ("Central bank announces inflation rate decision", "unknown", "macro_monetary"),
    ("Markets surge after ceasefire agreement", "positive", "conflict"),
    ("Stocks crash amid new sanctions", "negative", "sanctions"),
    ("دولت از توافق جدید خبر داد و بازار رشد کرد", "positive", "politics"),
    ("حمله موشکی و تشدید جنگ منطقه‌ای", "negative", "conflict"),
    ("بانک مرکزی نرخ بهره را اعلام کرد", "unknown", "macro_monetary"),
])
def test_known_headline_signals(headline, label, category):
    result = analyze_headline(headline)
    assert result["sentiment_label"] == label
    assert category in result["event_categories"]
    assert result["validated_model"] is False
    assert result["confidence_probability"] is None
    assert result["eligible_for_scoring"] is False


def test_unknown_headline_abstains_instead_of_inventing_sentiment():
    result = analyze_headline("Officials met to discuss the new plan")
    assert result["sentiment_label"] == "unknown"
    assert result["lexicon_score"] == 0
    assert result["event_categories"] == []


def test_exposes_auditable_word_evidence():
    result = analyze_headline("Markets crash after attack")
    assert result["sentiment_evidence"]["negative_terms"] == ["attack", "crash"]
    assert result["event_categories"] == ["conflict"]


@pytest.mark.parametrize("title", ["", "   ", None, 123, "x" * 2001])
def test_rejects_invalid_titles(title):
    with pytest.raises(ValueError):
        analyze_headline(title)
