#!/usr/bin/env python3
"""Run one bounded live smoke probe per configured source and emit sanitized JSON.

This script checks reachability and response shape only. It does not save raw
payloads, print credentials, infer publication times, or approve scoring.
Run from the analysis-engine directory with its virtualenv activated.
"""
from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from codal_provider import CodalClient
from fred_alfred_provider import FredAlfredClient
from gdelt_news_provider import GdeltDocClient, GdeltError
from tindex_provider import TindexClient
from tsetmc_provider import TsetmcClient


def shape(value: Any) -> dict[str, Any]:
    """Summarize a response without emitting its values."""
    if isinstance(value, Mapping):
        items = list(value.items())
        return {
            "type": "object",
            "keys": sorted(str(k) for k in value.keys())[:80],
            "field_types": {str(k): type(v).__name__ for k, v in items[:40]},
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return {
            "type": "array",
            "length": len(value),
            "first_item_shape": shape(value[0]) if value else None,
        }
    return {"type": type(value).__name__}


def safe_error_detail(source_id: str, exc: Exception) -> str | None:
    """Expose detail only for GDELT's deliberately sanitized exception contract."""
    if source_id == "global.gdelt_doc_api" and isinstance(exc, GdeltError):
        return str(exc)
    return None


def run_probe(report: dict[str, Any], source_id: str, operation) -> None:
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = operation()
        report["sources"][source_id] = {
            "status": "reachable_response_received",
            "probe_started_at": started,
            "response_shape": shape(result),
            "raw_payload_saved": False,
            "eligible_for_scoring": False,
        }
    except Exception as exc:  # arbitrary exception text may contain URLs/secrets
        item = {
            "status": "probe_failed",
            "probe_started_at": started,
            "error_type": type(exc).__name__,
            "error_detail_redacted": True,
            "raw_payload_saved": False,
            "eligible_for_scoring": False,
        }
        detail = safe_error_detail(source_id, exc)
        if detail is not None:
            item["safe_error_detail"] = detail
            item["error_detail_redacted"] = False
        report["sources"][source_id] = item


def main() -> int:
    report: dict[str, Any] = {
        "report_version": "1.1",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "bounded live smoke test; not source validation or production approval",
        "sources": {},
        "summary": {
            "live_probes_attempted": 0,
            "skipped_missing_credentials": [],
            "production_approved": False,
        },
    }

    # One request per public source. The query is intentionally small.
    run_probe(
        report, "global.gdelt_doc_api",
        lambda: _gdelt_probe(),
    )
    run_probe(
        report, "iran.tsetmc",
        lambda: _tsetmc_probe(),
    )
    run_probe(
        report, "iran.codal",
        lambda: _codal_probe(),
    )

    # Tindex has a local/provider quota. This pack makes exactly one request.
    if os.getenv("TINDEX_API_BASE_URL", "").strip() and os.getenv("TINDEX_API_TOKEN", "").strip():
        run_probe(report, "iran.tindex.public_api", _tindex_probe)
    else:
        report["sources"]["iran.tindex.public_api"] = {
            "status": "skipped_missing_credentials",
            "raw_payload_saved": False,
            "eligible_for_scoring": False,
        }
        report["summary"]["skipped_missing_credentials"].append("iran.tindex.public_api")

    # FRED is optional because it requires a key. Never include the key in output.
    if os.getenv("FRED_API_KEY", "").strip():
        run_probe(report, "us.fred.alfred", _fred_probe)
    else:
        report["sources"]["us.fred.alfred"] = {
            "status": "skipped_missing_credentials",
            "raw_payload_saved": False,
            "eligible_for_scoring": False,
        }
        report["summary"]["skipped_missing_credentials"].append("us.fred.alfred")

    report["summary"]["live_probes_attempted"] = sum(
        1 for item in report["sources"].values()
        if item["status"] in {"reachable_response_received", "probe_failed"}
    )
    report["summary"]["reachable"] = sum(
        1 for item in report["sources"].values()
        if item["status"] == "reachable_response_received"
    )
    report["summary"]["failed"] = sum(
        1 for item in report["sources"].values()
        if item["status"] == "probe_failed"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Network reachability is diagnostic; print the whole batch even if a source is down.
    # Exit non-zero when any attempted probe fails so CI/shell automation can detect it.
    return 1 if report["summary"]["failed"] else 0


def _gdelt_probe():
    with GdeltDocClient(timeout=20.0) as client:
        return client.search_articles("Iran", max_records=3)


def _tsetmc_probe():
    with TsetmcClient(timeout=15.0) as client:
        return client.search_instruments("فولاد")


def _codal_probe():
    with CodalClient(timeout=20.0) as client:
        return client.search_disclosures(page=1, page_size=3)


def _tindex_probe():
    with TindexClient(timeout=15.0) as client:
        return client.currency_rates()


def _fred_probe():
    with FredAlfredClient(timeout=15.0) as client:
        return client.observations("FEDFUNDS", limit=3)


if __name__ == "__main__":
    raise SystemExit(main())
