#!/usr/bin/env python3
"""One-request, sanitized connectivity probe for Tindex public API."""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence

from tindex_provider import TindexClient, TindexError, tindex_connection_status


def describe_shape(value):
    if isinstance(value, Mapping):
        return {
            "type": "object",
            "keys": sorted(str(key) for key in value.keys())[:80],
            "field_types": {
                str(key): type(item).__name__
                for key, item in list(value.items())[:40]
            },
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return {
            "type": "array",
            "length": len(value),
            "first_item_shape": describe_shape(value[0]) if value else None,
        }
    return {"type": type(value).__name__}


def main() -> int:
    status = tindex_connection_status()
    print(json.dumps({"connection_config": status}, ensure_ascii=False, indent=2))
    if not status["configured"]:
        print("Not configured: set TINDEX_API_BASE_URL and TINDEX_API_TOKEN.", file=sys.stderr)
        return 2
    try:
        with TindexClient() as client:
            payload = client.currency_rates()
    except TindexError as exc:
        print(f"Probe failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "probe": "currency-rates",
        "http": "2xx",
        "payload_shape": describe_shape(payload),
        "payload_saved": False,
        "production_approved": False,
        "next_step": "Review provider terms and a sanitized sample before writing a normalizer.",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
