"""Read-only GDELT DOC 2.0 article discovery client.

GDELT's seendate is treated as a first-seen/index timestamp, NOT the publisher's
original publication time. The API returns article metadata, not verified article
truth. Output is discovery-only and must not feed investment scoring directly.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx

SOURCE_ID = "global.gdelt_doc_api"
BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
USER_AGENT = "MarketSage/0.1 research-data-client"


class GdeltError(RuntimeError):
    pass


class GdeltPayloadError(GdeltError):
    pass


def _canonical_url(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        return ""
    # Keep the path/query; drop fragments and normalize scheme/host case.
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, ""))


def normalize_gdelt_articles(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("articles"), list):
        raise GdeltPayloadError("GDELT response must contain an articles list")
    result: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for index, article in enumerate(payload["articles"]):
        if not isinstance(article, dict):
            raise GdeltPayloadError(f"articles[{index}] must be an object")
        url = _canonical_url(article.get("url"))
        title = article.get("title")
        if not url or not isinstance(title, str) or not title.strip():
            # Keep malformed rows out of downstream NLP rather than guessing.
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        raw_seen = article.get("seendate")
        seen_at = None
        if isinstance(raw_seen, str):
            try:
                seen_at = datetime.strptime(raw_seen, "%Y%m%dT%H%M%S").isoformat()
            except ValueError:
                seen_at = None
        result.append({
            "source_id": SOURCE_ID,
            "url": url,
            "title": title.strip(),
            "domain": article.get("domain") if isinstance(article.get("domain"), str) else None,
            "language": article.get("language") if isinstance(article.get("language"), str) else None,
            "source_country": article.get("sourcecountry") if isinstance(article.get("sourcecountry"), str) else None,
            "first_seen_at": seen_at,
            "publisher_published_at": None,
            "sentiment": None,
            "political_event_type": None,
            "verified": False,
            "eligible_for_scoring": False,
        })
    return result


class GdeltDocClient:
    def __init__(self, *, timeout: float = 20.0, transport: httpx.BaseTransport | None = None):
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._client = httpx.Client(
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GdeltDocClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def search_articles(
        self, query: str, *, max_records: int = 50, start_datetime: str | None = None,
        end_datetime: str | None = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ValueError("query must contain 1-500 characters")
        if isinstance(max_records, bool) or not isinstance(max_records, int) or not 1 <= max_records <= 250:
            raise ValueError("max_records must be between 1 and 250")
        for label, value in (("start_datetime", start_datetime), ("end_datetime", end_datetime)):
            if value is not None and (
                not isinstance(value, str) or len(value) != 14 or not value.isdigit()
            ):
                raise ValueError(f"{label} must use YYYYMMDDHHMMSS")
        if start_datetime and end_datetime and start_datetime > end_datetime:
            raise ValueError("start_datetime must not be after end_datetime")
        params: dict[str, str | int] = {
            "query": query.strip(), "mode": "ArtList", "format": "json",
            "maxrecords": max_records, "sort": "HybridRel",
        }
        if start_datetime:
            params["startdatetime"] = start_datetime
        if end_datetime:
            params["enddatetime"] = end_datetime
        try:
            response = self._client.get(BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise GdeltError(f"GDELT request failed ({type(exc).__name__})") from None
        return normalize_gdelt_articles(payload)
