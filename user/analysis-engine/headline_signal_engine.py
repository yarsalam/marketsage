"""Transparent Persian/English headline signal baseline.

This is a deterministic keyword baseline for pipeline smoke tests, not a validated
sentiment model or political-event truth detector. It abstains when no lexicon
evidence exists and must not be used for investment scoring until benchmarked on
a representative, independently labelled dataset.
"""
from __future__ import annotations

import re
from typing import Any

SOURCE_ID = "marketsage.headline_lexicon_baseline"

_POSITIVE = {
    "gain", "gains", "growth", "rise", "rises", "surge", "surges", "recovery",
    "agreement", "ceasefire", "approval", "improve", "improves", "strong",
    "افزایش", "رشد", "صعود", "رونق", "توافق", "آتش‌بس", "آتش بس", "بهبود", "مثبت",
}
_NEGATIVE = {
    "fall", "falls", "drop", "drops", "crash", "crashes", "decline", "declines",
    "loss", "losses", "crisis", "attack", "attacks", "war", "sanctions", "default",
    "کاهش", "سقوط", "ریزش", "بحران", "حمله", "جنگ", "تحریم", "ورشکستگی", "منفی",
}
_EVENT_TERMS = {
    "politics": {"election", "parliament", "government", "minister", "president", "policy",
                 "انتخابات", "مجلس", "دولت", "وزیر", "رئیس جمهور", "سیاست"},
    "conflict": {"war", "attack", "missile", "strike", "ceasefire", "conflict",
                 "جنگ", "حمله", "موشک", "حمله نظامی", "آتش‌بس", "آتش بس", "درگیری"},
    "sanctions": {"sanction", "sanctions", "embargo", "تحریم", "تحریم‌ها", "تحریم ها"},
    "macro_monetary": {"central bank", "inflation", "interest rate", "rate decision", "currency", "gdp",
                       "بانک مرکزی", "تورم", "نرخ بهره", "نرخ ارز", "ارز", "تولید ناخالص داخلی"},
}


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+(?:'[a-z]+)?|[\u0600-\u06FF]+", text.casefold()))


def analyze_headline(title: str) -> dict[str, Any]:
    if not isinstance(title, str) or not title.strip() or len(title) > 2000:
        raise ValueError("title must contain 1-2000 characters")
    normalized = title.casefold()
    tokens = _tokens(normalized)
    pos_hits = sorted(term for term in _POSITIVE if (term in normalized if " " in term else term in tokens))
    neg_hits = sorted(term for term in _NEGATIVE if (term in normalized if " " in term else term in tokens))
    score = len(pos_hits) - len(neg_hits)
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "unknown" if not pos_hits and not neg_hits else "mixed_or_neutral"
    categories = sorted(
        category for category, terms in _EVENT_TERMS.items()
        if any(term in normalized if " " in term else term in tokens for term in terms)
    )
    evidence = {
        "positive_terms": pos_hits,
        "negative_terms": neg_hits,
        "event_categories": categories,
    }
    return {
        "source_id": SOURCE_ID,
        "sentiment_label": label,
        "lexicon_score": score,
        "sentiment_evidence": evidence,
        "event_categories": categories,
        "method": "transparent_keyword_lexicon_v1",
        "validated_model": False,
        "confidence_probability": None,
        "eligible_for_scoring": False,
    }
