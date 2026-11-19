#!/usr/bin/env python3
"""Small, read-only probes for registered MarketSage source candidates.

This script intentionally does not persist market payloads. It records only
HTTP metadata, response hashes, and a small structural summary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROBES = [
    {
        "source_id": "tsetmc_public",
        "url": "https://cdn.tsetmc.com/api/Instrument/GetInstrumentSearch/%D9%81%D9%88%D9%84%D8%A7%D8%AF",
        "asset_class": "iran_equity",
    },
    {
        "source_id": "tgju_history",
        "url": "https://api.tgju.org/v1/market/indicator/summary-table-data/geram18",
        "asset_class": "iran_gold",
    },
    {
        "source_id": "nerkhara_history",
        "url": "https://nerkhara.com/api/v1/index.json",
        "asset_class": "iran_gold_fx",
    },
    {
        "source_id": "netarz_fx",
        "url": "https://netarz.ir/api/fx/v1/currencies",
        "asset_class": "iran_fx",
    },
    {
        "source_id": "nobitex_public",
        "url": "https://apiv2.nobitex.ir/market/stats?srcCurrency=btc&dstCurrency=rls",
        "asset_class": "iran_crypto_exchange",
    },
    {
        "source_id": "wallex_public",
        "url": "https://api.wallex.ir/v1/markets",
        "asset_class": "iran_crypto_exchange",
    },
    {
        "source_id": "alpha_vantage",
        "url": "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo",
        "asset_class": "global_equity",
    },
]


def summarize(body: bytes, content_type: str) -> dict:
    summary = {"content_type": content_type, "bytes": len(body)}
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        summary["format"] = "non_json_or_invalid_utf8"
        return summary

    summary["format"] = "json"
    summary["top_level_type"] = type(parsed).__name__
    if isinstance(parsed, dict):
        summary["top_level_keys"] = sorted(str(key) for key in parsed.keys())[:40]
        for key, value in parsed.items():
            if isinstance(value, list):
                summary["first_list_key"] = str(key)
                summary["first_list_length"] = len(value)
                if value and isinstance(value[0], dict):
                    summary["first_item_keys"] = sorted(value[0].keys())[:40]
                break
    elif isinstance(parsed, list):
        summary["list_length"] = len(parsed)
        if parsed and isinstance(parsed[0], dict):
            summary["first_item_keys"] = sorted(parsed[0].keys())[:40]
    return summary


def probe(item: dict, timeout: int) -> dict:
    request = Request(
        item["url"],
        headers={
            "User-Agent": "MarketSage-SourceProbe/0.1 (+read-only; contact: project-owner)",
            "Accept": "application/json,text/plain,*/*",
        },
        method="GET",
    )
    result = {
        "source_id": item["source_id"],
        "asset_class": item["asset_class"],
        "url": item["url"],
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "status": "SOURCE_FAILED",
    }
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read(256 * 1024 + 1)
            if len(body) > 256 * 1024:
                result["status"] = "RESPONSE_TOO_LARGE_FOR_PROBE"
                body = body[:256 * 1024]
            else:
                result["status"] = "HTTP_OK"
            result["http_status"] = response.status
            result["sha256"] = hashlib.sha256(body).hexdigest()
            result["summary"] = summarize(
                body, response.headers.get_content_type()
            )
    except HTTPError as exc:
        result["status"] = "HTTP_ERROR"
        result["http_status"] = exc.code
        result["error"] = str(exc.reason)
    except (URLError, TimeoutError, OSError) as exc:
        result["status"] = "NETWORK_ERROR"
        result["error"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:  # probe must continue for other providers
        result["status"] = "PROBE_ERROR"
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--output", default="source-probe-report.json")
    args = parser.parse_args()

    results = []
    for index, item in enumerate(PROBES):
        results.append(probe(item, args.timeout))
        if index + 1 < len(PROBES):
            time.sleep(max(0.0, args.delay))

    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "probe_policy": "read_only_minimal_no_payload_persistence",
        "source_count": len(results),
        "status_counts": counts,
        "results": results,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(output), "status_counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
