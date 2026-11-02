"""Candidate-only CODAL disclosure search adapter.

The search endpoint/schema is based on community reverse-engineered references.
Publication timestamps are preserved as source text but are NOT converted into
published_at until Jalali-calendar and timezone semantics are independently verified.
Consequently these records remain quarantined and cannot enter production scoring.
"""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from temporal_data import PointInTimeStore, TemporalRecord

SOURCE_ID = "iran.codal"
SEARCH_URL = "https://search.codal.ir/api/search/v2/q"
USER_AGENT = "MarketSage research adapter/0.1 (candidate data; contact: maintainer)"


class CODALDataError(ValueError):
    """Raised when CODAL response data cannot be safely normalized."""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(parent: ET.Element, field: str) -> str | None:
    for child in parent.iter():
        if _local_name(child.tag) == field:
            value = (child.text or "").strip()
            return value or None
    return None


def parse_search_xml(
    xml_payload: bytes | str,
    *,
    retrieved_at: datetime,
    requested_symbol: str | None = None,
) -> list[TemporalRecord]:
    """Parse candidate CODAL letter headers; preserve, but do not trust, source times."""
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise CODALDataError("retrieved_at must be timezone-aware")
    try:
        root = ET.fromstring(xml_payload)
    except (ET.ParseError, TypeError, ValueError) as exc:
        raise CODALDataError("CODAL search response is not valid XML") from exc

    letters = [node for node in root.iter() if _local_name(node.tag) == "CodalLetterHeaderDto"]
    if not letters:
        raise CODALDataError("CODAL XML contains no CodalLetterHeaderDto entries")

    retrieved_utc = retrieved_at.astimezone(timezone.utc)
    raw_digest = hashlib.sha256(
        xml_payload.encode("utf-8") if isinstance(xml_payload, str) else xml_payload
    ).hexdigest()
    records: list[TemporalRecord] = []
    seen: set[str] = set()

    for index, letter in enumerate(letters):
        tracing_no = _text(letter, "TracingNo")
        title = _text(letter, "Title")
        symbol = _text(letter, "Symbol") or requested_symbol
        if not tracing_no or not tracing_no.isdigit():
            raise CODALDataError(f"letter {index}: missing or invalid TracingNo")
        if tracing_no in seen:
            raise CODALDataError(f"duplicate TracingNo: {tracing_no}")
        seen.add(tracing_no)
        if not title:
            raise CODALDataError(f"letter {index}: missing Title")
        if not symbol:
            raise CODALDataError(f"letter {index}: symbol unavailable; cannot safely identify issuer")

        payload: dict[str, Any] = {
            "tracing_no": tracing_no,
            "symbol_candidate": symbol,
            "title": title,
            "letter_code": _text(letter, "LetterCode"),
            "publish_datetime_source_text": _text(letter, "PublishDateTime"),
            "sent_datetime_source_text": _text(letter, "SentDateTime"),
            "url_candidate": _text(letter, "Url"),
            "source_response_sha256": raw_digest,
            "publication_timestamp_status": "unverified_jalali_timezone_semantics",
            "normalization_status": "candidate_quarantined",
        }
        records.append(TemporalRecord(
            record_key=f"{symbol}:{tracing_no}",
            source_id=SOURCE_ID,
            market="iran_candidate",
            data_kind="issuer_disclosure_candidate",
            observed_at=retrieved_utc,
            retrieved_at=retrieved_utc,
            published_at=None,
            source_revision=raw_digest,
            payload=payload,
        ))
    return records


def fetch_search_xml(
    symbol: str,
    *,
    page: int = 1,
    timeout: float = 20.0,
) -> bytes:
    """Fetch one search page. Callers must respect access policy and back off on blocks."""
    if not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 64:
        raise CODALDataError("symbol must be a non-empty string of at most 64 characters")
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise CODALDataError("page must be a positive integer")
    query = urlencode({"Symbol": symbol.strip(), "PageNumber": page})
    request = Request(
        f"{SEARCH_URL}?{query}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise CODALDataError(f"CODAL request failed ({type(exc).__name__}); no data ingested") from exc
    if not body:
        raise CODALDataError("CODAL returned an empty response")
    return body


def ingest_search_page(
    store: PointInTimeStore,
    symbol: str,
    *,
    retrieved_at: datetime | None = None,
    page: int = 1,
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Explicit opt-in candidate ingestion; never grants production scoring approval."""
    captured_at = retrieved_at or datetime.now(timezone.utc)
    raw = fetch_search_xml(symbol, page=page, timeout=timeout)
    records = parse_search_xml(raw, retrieved_at=captured_at, requested_symbol=symbol)
    ids = [store.append(record) for record in records]
    return {
        "source_id": SOURCE_ID,
        "symbol": symbol,
        "page": page,
        "records_seen": len(records),
        "records_inserted_or_existing": len(ids),
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "normalization_status": "candidate_quarantined",
        "production_scoring_enabled": False,
    }
