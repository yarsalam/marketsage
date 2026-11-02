"""Create deterministic operational alerts from the analysis API /data-quality payload.

Usage:
  MARKET_SAGE_DATA_QUALITY_URL=http://127.0.0.1:8100/data-quality \
    python data_quality_report.py --output /var/lib/marketsage/data-quality-latest.json

Exit codes: 0=healthy, 1=warnings, 2=critical data-quality gaps, 3=configuration/fetch error.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def build_report(payload: dict[str, Any], generated_at: str | None = None) -> dict[str, Any]:
    """Convert /data-quality output into stable, machine-readable alerts."""
    alerts: list[dict[str, str]] = []
    sources = payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("payload must contain a sources list")

    for source in sources:
        if not isinstance(source, dict) or not source.get("source_id"):
            alerts.append({
                "severity": "critical",
                "code": "malformed_source_entry",
                "message": "A source registry entry is missing its source_id.",
            })
            continue

        source_id = str(source["source_id"])
        status = source.get("runtime_status")
        series = source.get("runtime_series") or []
        research_wired = source.get("used_by_research_engine") is True

        # Missing data is actionable only for a source the research engine uses.
        # Candidate providers are intentionally unconnected and should not page.
        if research_wired and status == "no_data_captured":
            alerts.append({
                "severity": "critical",
                "code": "research_source_has_no_captured_data",
                "source_id": source_id,
                "message": f"Research-wired source {source_id} has no captured temporal data.",
            })

        for item in series:
            if not isinstance(item, dict):
                alerts.append({
                    "severity": "warning",
                    "code": "malformed_series_entry",
                    "source_id": source_id,
                    "message": f"Source {source_id} contains a malformed series entry.",
                })
                continue
            key = str(item.get("series_key", "unknown"))
            freshness = item.get("freshness", "unknown")
            if freshness == "stale":
                alerts.append({
                    "severity": "warning",
                    "code": "series_stale",
                    "source_id": source_id,
                    "series_key": key,
                    "message": f"Series {source_id}/{key} is stale.",
                })
            elif freshness == "unknown":
                alerts.append({
                    "severity": "warning",
                    "code": "series_freshness_unknown",
                    "source_id": source_id,
                    "series_key": key,
                    "message": f"Freshness cannot be evaluated for {source_id}/{key}.",
                })

    severity_rank = {"critical": 2, "warning": 1}
    highest = max((severity_rank.get(a["severity"], 0) for a in alerts), default=0)
    status = "critical" if highest == 2 else "warning" if highest == 1 else "ok"
    return {
        "report_version": "1.0.0",
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_count": len(sources),
        "alert_count": len(alerts),
        "critical_count": sum(a["severity"] == "critical" for a in alerts),
        "warning_count": sum(a["severity"] == "warning" for a in alerts),
        "alerts": alerts,
        "policy": (
            "Unconnected candidate sources are informational; missing data is critical only "
            "for sources marked used_by_research_engine. Stale or unknown-freshness series warn. "
            "This report does not certify provider accuracy, publication timestamps, licensing, "
            "or strategy performance."
        ),
    }


def fetch_payload(url: str, timeout: float = 15.0) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "MarketSage-DataQuality/1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"data-quality endpoint returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("data-quality endpoint must return a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--url",
        default=os.getenv("MARKET_SAGE_DATA_QUALITY_URL"),
        help="Analysis API /data-quality URL (or MARKET_SAGE_DATA_QUALITY_URL)",
    )
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--output", type=Path, help="Optional path for an atomic JSON report file")
    args = parser.parse_args(argv)

    if not args.url:
        print("ERROR: pass --url or set MARKET_SAGE_DATA_QUALITY_URL", file=sys.stderr)
        return 3
    try:
        payload = fetch_payload(args.url, timeout=args.timeout)
        report = build_report(payload)
        serialized = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_suffix(args.output.suffix + ".tmp")
            temporary.write_text(serialized, encoding="utf-8")
            os.replace(temporary, args.output)
        print(serialized, end="")
        return {"ok": 0, "warning": 1, "critical": 2}[report["status"]]
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: data-quality report failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
