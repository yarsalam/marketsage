#!/usr/bin/env python3
"""Read-only acquisition of TSETMC's historical instrument-state table.

The legacy Loader.aspx Partree=15131L page is used by public TSETMC client
implementations to display a symbol's historical state changes. This script
captures the exact response bytes, response metadata, SHA-256 and parsed table
rows. It does not infer a halt reason or alter market data.

No credentials are embedded or required by this public-page route.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SYMBOLS = {
    "vaghdir": {"ticker": "وغدیر", "insCode": "26014913469567886"},
    "foolad": {"ticker": "فولاد", "insCode": "46348559193224090"},
    "parsian": {"ticker": "پارسیان", "insCode": "9481703061634967"},
}
ENDPOINT = "http://old.tsetmc.com/Loader.aspx"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36 MarketSageResearch/1.0"
)


class TableRows(HTMLParser):
    """Extract table cell text without depending on BeautifulSoup/lxml."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(value.strip() for value in self._row):
                self.rows.append(self._row)
            self._row = None
            self._cell = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_one(symbol: str, info: dict[str, str], output_dir: Path) -> dict[str, Any]:
    query = urlencode({"i": info["insCode"], "Partree": "15131L"})
    url = f"{ENDPOINT}?{query}"
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fa,en-US;q=0.8,en;q=0.6",
            "Cache-Control": "no-cache",
        },
        method="GET",
    )
    retrieved_at = utc_now()
    try:
        with urlopen(request, timeout=18) as response:
            body = response.read()
            status = int(response.status)
            final_url = response.geturl()
            content_type = response.headers.get("Content-Type")
            server_date = response.headers.get("Date")
            response_headers = {
                "Content-Type": content_type,
                "Date": server_date,
                "ETag": response.headers.get("ETag"),
                "Last-Modified": response.headers.get("Last-Modified"),
            }
    except HTTPError as exc:
        body = exc.read()
        status = int(exc.code)
        final_url = exc.geturl()
        content_type = exc.headers.get("Content-Type")
        response_headers = {
            "Content-Type": content_type,
            "Date": exc.headers.get("Date"),
            "ETag": exc.headers.get("ETag"),
            "Last-Modified": exc.headers.get("Last-Modified"),
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "symbol": symbol,
            "ticker": info["ticker"],
            "insCode": info["insCode"],
            "request_url": url,
            "retrieved_at_utc": retrieved_at,
            "retrieval_status": "network_error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    digest = hashlib.sha256(body).hexdigest()
    raw_path = output_dir / f"{symbol}_tsetmc_historical_state_changes.html"
    raw_path.write_bytes(body)

    encoding = "utf-8"
    if content_type and "charset=" in content_type.lower():
        encoding = content_type.lower().split("charset=", 1)[1].split(";", 1)[0].strip(" \"'")
    html = body.decode(encoding or "utf-8", errors="replace")
    parser = TableRows()
    parser.feed(html)

    rows = []
    for cells in parser.rows:
        if len(cells) >= 3:
            rows.append({
                "date_text": cells[0],
                "time_text": cells[1],
                "new_state_text": cells[2],
                "all_cells": cells,
            })

    if status != 200:
        parse_status = "http_error_response_captured"
    elif not body:
        parse_status = "empty_response"
    elif rows:
        parse_status = "parsed_state_rows"
    else:
        parse_status = "no_state_rows_parsed"

    return {
        "symbol": symbol,
        "ticker": info["ticker"],
        "insCode": info["insCode"],
        "request_url": url,
        "final_url": final_url,
        "retrieved_at_utc": retrieved_at,
        "http_status": status,
        "response_headers": response_headers,
        "content_type": content_type,
        "response_bytes": len(body),
        "response_sha256": digest,
        "raw_response_file": raw_path.name,
        "parse_status": parse_status,
        "parsed_state_row_count": len(rows),
        "state_rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tsetmc-historical-state-acquisition"),
        help="Directory for immutable HTML captures and the parsed JSON manifest",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    results = []
    for index, (symbol, info) in enumerate(SYMBOLS.items()):
        if index:
            time.sleep(1.0)
        try:
            results.append(fetch_one(symbol, info, args.output))
        except Exception as exc:  # retain per-symbol failure without losing other captures
            results.append({
                "symbol": symbol,
                "ticker": info["ticker"],
                "insCode": info["insCode"],
                "retrieved_at_utc": utc_now(),
                "retrieval_status": "unexpected_error",
                "error_type": type(exc).__name__,
                "error": str(exc),
            })

    successes = sum(1 for item in results if item.get("http_status") == 200)
    report = {
        "schema_version": "1.0.0",
        "research_scope": "three-symbol historical instrument-state acquisition",
        "source_owner": "TSETMC",
        "source_route": ENDPOINT,
        "page_parameter": "Partree=15131L (historical instrument status table)",
        "method_limit": (
            "The route is a public legacy page identified in independent client "
            "implementations; its contents must be validated against visible table "
            "semantics and, where available, the authenticated TSETMC InstrumentsStateChange service."
        ),
        "started_at_utc": None,
        "completed_at_utc": utc_now(),
        "symbols_requested": len(SYMBOLS),
        "http_200_responses": successes,
        "results": results,
    }
    report["started_at_utc"] = results[0].get("retrieved_at_utc") if results else utc_now()
    manifest_path = args.output / "tsetmc_historical_state_acquisition.json"
    manifest_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("TSETMC_HISTORICAL_STATE_ACQUISITION_JSON_BEGIN")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("TSETMC_HISTORICAL_STATE_ACQUISITION_JSON_END")
    print(f"MANIFEST_PATH={manifest_path}")
    return 0 if successes == len(SYMBOLS) else 2


if __name__ == "__main__":
    raise SystemExit(main())
