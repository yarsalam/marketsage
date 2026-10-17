#!/usr/bin/env python3
"""Run bounded live smoke probes and emit sanitized JSON.

By default, probes all sources in the pack. Use --source SOURCE_ID (repeatable)
to limit requests to specific sources. This checks reachability and response
shape only; it does not save raw payloads, print credentials, infer publication
times, or approve scoring.
Run from the analysis-engine directory with its virtualenv activated.
"""
from __future__ import annotations

import argparse
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

SOURCE_IDS = (
    "global.gdelt_doc_api",
    "iran.tsetmc",
    "iran.codal",
    "iran.tindex.public_api",
    "us.fred.alfred",
)


def parse_source_selection(argv: Sequence[str] | None = None) -> set[str]:
    """Return selected source IDs; no --source means the full original pack."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        action="append",
        choices=SOURCE_IDS,
        dest="sources",
        help="probe only this source; may be repeated to select multiple sources",
    )
    args = parser.parse_args(argv)
    return set(args.sources) if args.sources else set(SOURCE_IDS)


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


def main(argv: Sequence[str] | None = None) -> int:
    selected = parse_source_selection(argv)
    report: dict[str, Any] = {
        "report_version": "1.2",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "bounded live smoke test; not source validation or production approval",
        "selected_sources": [source_id for source_id in SOURCE_IDS if source_id in selected],
        "sources": {},
        "summary": {
            "live_probes_attempted": 0,
            "skipped_missing_credentials": [],
            "skipped_not_selected": [],
            "production_approved": False,
        },
    }

    probes = {
        "global.gdelt_doc_api": _gdelt_probe,
        "iran.tsetmc": _tsetmc_probe,
        "iran.codal": _codal_probe,
        "iran.tindex.public_api": _tindex_probe,
        "us.fred.alfred": _fred_probe,
    }
    credential_requirements = {
        "iran.tindex.public_api": ("TINDEX_API_BASE_URL", "TINDEX_API_TOKEN"),
        "us.fred.alfred": ("FRED_API_KEY",),
    }

    for source_id in SOURCE_IDS:
        if source_id not in selected:
            report["sources"][source_id] = {
                "status": "skipped_not_selected",
                "raw_payload_saved": False,
                "eligible_for_scoring": False,
            }
            report["summary"]["skipped_not_selected"].append(source_id)
            continue

        required_env = credential_requirements.get(source_id, ())
        if required_env and not all(os.getenv(name, "").strip() for name in required_env):
            report["sources"][source_id] = {
                "status": "skipped_missing_credentials",
                "raw_payload_saved": False,
                "eligible_for_scoring": False,
            }
            report["summary"]["skipped_missing_credentials"].append(source_id)
            continue

        run_probe(report, source_id, probes[source_id])

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
