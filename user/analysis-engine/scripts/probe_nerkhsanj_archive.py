#!/usr/bin/env python3
"""One-shot, metadata-only discovery probe for the publisher-announced Nerkhsanj archive.

This utility does not save raw provider payloads or emit price values. A successful
probe is schema/coverage evidence only; it is not licensing or scoring approval.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

SOURCE_ID = "iran.nerkhsanj.rates_archive"
ARCHIVE_URL = "https://nerkh.jahankhahan.shop/data/rates.json"
USER_AGENT = "MarketSage/0.1 source-discovery"
MAX_RESPONSE_BYTES = 12 * 1024 * 1024
_JALALI_DATE_PATTERN = re.compile(r"^\d{4}/\d{2}/\d{2}$")


class NerkhsanjProbeError(RuntimeError):
    """Sanitized error for the one-shot discovery probe."""


def _shape(value: Any, depth: int = 0) -> dict[str, Any]:
    """Return keys/types/counts only; never copy arbitrary provider values."""
    if depth >= 4:
        return {"type": type(value).__name__, "truncated": True}
    if isinstance(value, dict):
        return {
            "type": "object",
            "keys": sorted(str(key) for key in value.keys())[:80],
            "members": {
                str(key): _shape(member, depth + 1)
                for key, member in list(value.items())[:30]
            },
        }
    if isinstance(value, list):
        return {
            "type": "array",
            "length": len(value),
            "first_item_shape": _shape(value[0], depth + 1) if value else None,
        }
    return {"type": type(value).__name__}


def summarize_rates_archive(payload: Any) -> dict[str, Any]:
    """Audit the announced {series:[{key, days:[[jalali_date,rate],...]}]} schema.

    The report includes no numeric rates or raw rows. Dates are shape/order checked
    lexically as documented by the publisher; this does not validate Jalali calendar
    correctness or source-market accuracy.
    """
    report: dict[str, Any] = {
        "source_id": SOURCE_ID,
        "purpose": "one_shot_schema_and_coverage_discovery_only",
        "production_approved": False,
        "eligible_for_scoring": False,
        "raw_values_emitted": False,
        "raw_payload_saved": False,
        "publisher_attribution_required": True,
        "rights_reviewed": False,
        "response_shape": _shape(payload),
        "schema_status": "unrecognized",
        "series_count": 0,
        "series": [],
        "limitations": [
            "Publisher-announced schema has not yet been reconciled with an independently captured contract fixture.",
            "Jalali date strings are format/order-checked only; actual calendar validity is not checked by this script.",
            "A clean shape/coverage report does not prove source lineage, accuracy, usage rights or independent reconciliation.",
            "Missing dates can be market holidays; this script does not infer expected trading sessions.",
        ],
    }
    if not isinstance(payload, dict) or not isinstance(payload.get("series"), list):
        return report

    series_summaries: list[dict[str, Any]] = []
    for index, item in enumerate(payload["series"]):
        if not isinstance(item, dict):
            return {**report, "schema_status": "invalid_series_record", "invalid_series_index": index}
        key = item.get("key")
        days = item.get("days")
        if not isinstance(key, str) or not key.strip() or not isinstance(days, list):
            return {**report, "schema_status": "invalid_series_record", "invalid_series_index": index}

        dates: list[str] = []
        invalid_date_count = 0
        invalid_rate_count = 0
        valid_pair_count = 0
        for pair in days:
            if not isinstance(pair, list) or len(pair) != 2:
                invalid_date_count += 1
                continue
            date_value, rate_value = pair
            if not isinstance(date_value, str) or not _JALALI_DATE_PATTERN.fullmatch(date_value):
                invalid_date_count += 1
                continue
            dates.append(date_value)
            if isinstance(rate_value, bool) or not isinstance(rate_value, (int, float)):
                invalid_rate_count += 1
                continue
            if not math.isfinite(float(rate_value)) or float(rate_value) <= 0:
                invalid_rate_count += 1
                continue
            valid_pair_count += 1

        duplicate_count = len(dates) - len(set(dates))
        inversion_count = sum(1 for a, b in zip(dates, dates[1:]) if b < a)
        series_summaries.append({
            "series_key": key.strip(),
            "observation_count": len(days),
            "valid_pair_count": valid_pair_count,
            "invalid_or_malformed_date_pair_count": invalid_date_count,
            "invalid_numeric_rate_count": invalid_rate_count,
            "duplicate_date_count": duplicate_count,
            "date_order_inversion_count": inversion_count,
            "first_date": min(dates) if dates else None,
            "last_date": max(dates) if dates else None,
            "production_approved": False,
        })

    keys = [item["series_key"] for item in series_summaries]
    duplicate_keys = len(keys) - len(set(keys))
    report.update({
        "schema_status": "candidate_schema_parsed",
        "series_count": len(series_summaries),
        "duplicate_series_key_count": duplicate_keys,
        "total_observation_count": sum(x["observation_count"] for x in series_summaries),
        "total_invalid_date_pair_count": sum(x["invalid_or_malformed_date_pair_count"] for x in series_summaries),
        "total_invalid_numeric_rate_count": sum(x["invalid_numeric_rate_count"] for x in series_summaries),
        "series": series_summaries,
    })
    return report


def fetch_rates_archive(*, timeout: float = 15.0) -> tuple[Any, int]:
    """Make exactly one HTTPS GET; no retries, no redirects, no raw-body persistence."""
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        ) as client:
            with client.stream("GET", ARCHIVE_URL) as response:
                if response.status_code == 429:
                    raise NerkhsanjProbeError("Provider returned HTTP 429; stop and wait, no retry was attempted.")
                if response.status_code < 200 or response.status_code >= 300:
                    raise NerkhsanjProbeError(f"Provider returned HTTP {response.status_code}; no retry was attempted.")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise NerkhsanjProbeError("Archive response exceeded the local size ceiling; no payload was saved.")
                try:
                    payload = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    raise NerkhsanjProbeError("Archive response was not valid UTF-8 JSON; no payload was saved.") from None
                return payload, len(body)
    except NerkhsanjProbeError:
        raise
    except httpx.HTTPError as exc:
        raise NerkhsanjProbeError(f"Network request failed ({type(exc).__name__}); no retry was attempted.") from None


def require_vpn_on() -> bool:
    """Require interactive confirmation before the foreign-host request."""
    if not sys.stdin.isatty():
        print("VPN PRECHECK failed: interactive terminal required; no network request was made.", file=sys.stderr)
        return False
    print("VPN PRECHECK: this is an external host. Turn VPN ON before the one-request probe.")
    answer = input("Type VPN-ON to confirm: ").strip()
    if answer != "VPN-ON":
        print("VPN confirmation did not match; no network request was made.", file=sys.stderr)
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/marketsage-nerkhsanj-probe.json")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)

    if not require_vpn_on():
        return 2

    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        payload, response_bytes = fetch_rates_archive(timeout=args.timeout)
        report = summarize_rates_archive(payload)
        report.update({
            "status": "probe_completed",
            "endpoint": "/data/rates.json",
            "retrieved_at_utc": retrieved_at,
            "response_bytes": response_bytes,
            "http_requests_made": 1,
        })
    except NerkhsanjProbeError as exc:
        report = {
            "source_id": SOURCE_ID,
            "status": "probe_failed",
            "error": str(exc),
            "retrieved_at_utc": retrieved_at,
            "http_requests_made": 1,
            "raw_values_emitted": False,
            "raw_payload_saved": False,
            "production_approved": False,
            "eligible_for_scoring": False,
        }

    output = Path(args.output).expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report.get("status"),
        "source_id": SOURCE_ID,
        "output": str(output),
        "schema_status": report.get("schema_status"),
        "series_count": report.get("series_count"),
        "production_approved": False,
        "eligible_for_scoring": False,
        "raw_values_emitted": False,
        "raw_payload_saved": False,
    }, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "probe_completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
