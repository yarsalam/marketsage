"""Read-only aggregate audit of legacy global price-basis semantics.

This command never updates the database and never prints symbols, prices, payloads,
record keys, or filesystem paths. It is safe to run against a stopped or live SQLite
database opened in read-only mode.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from instrument_registry import RESEARCH_SOURCE_ID, temporal_price_metadata_for


def audit_database(database: str | Path) -> dict:
    path = Path(database)
    if not path.is_file():
        raise FileNotFoundError("database file does not exist or is not a regular file")

    uri = f"file:{quote(str(path.resolve()), safe='/')}?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=10)
    except sqlite3.Error as exc:
        raise RuntimeError("database could not be opened in read-only mode") from exc

    counts: Counter[str] = Counter()
    try:
        connection.execute("PRAGMA query_only = ON")
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='temporal_records'"
        ).fetchone()
        if table is None:
            raise RuntimeError("temporal record table is missing")

        rows = connection.execute(
            """
            SELECT data_kind, payload_json
            FROM temporal_records
            WHERE source_id = ? AND market = 'global_proxy'
            """,
            (RESEARCH_SOURCE_ID,),
        )

        for data_kind, payload_json in rows:
            counts["audited_records"] += 1
            try:
                payload = json.loads(payload_json)
            except (TypeError, json.JSONDecodeError):
                counts["invalid_metadata_records"] += 1
                continue

            symbol = payload.get("symbol") if isinstance(payload, dict) else None
            if not isinstance(symbol, str) or not symbol.strip():
                counts["unmapped_records"] += 1
                continue

            try:
                expected = temporal_price_metadata_for(RESEARCH_SOURCE_ID, symbol)
            except ValueError:
                counts["unmapped_records"] += 1
                continue

            observed = {
                "data_kind": data_kind,
                "canonical_instrument_id": payload.get("canonical_instrument_id"),
                "currency": payload.get("currency"),
                "price_unit": payload.get("price_unit"),
                "price_basis": payload.get("price_basis"),
                "adjustment_policy": payload.get("adjustment_policy"),
            }
            if all(observed[key] == value for key, value in expected.items()):
                counts["consistent_records"] += 1
            else:
                counts["legacy_mismatch_records"] += 1
    except sqlite3.Error as exc:
        raise RuntimeError("database read-only audit failed") from exc
    finally:
        connection.close()

    result_counts = {
        key: int(counts[key])
        for key in (
            "audited_records",
            "consistent_records",
            "legacy_mismatch_records",
            "unmapped_records",
            "invalid_metadata_records",
        )
    }
    if result_counts["audited_records"] == 0:
        status = "no_records"
    elif result_counts["legacy_mismatch_records"] or result_counts["unmapped_records"] or result_counts["invalid_metadata_records"]:
        status = "review_required"
    else:
        status = "pass"

    return {
        "audit_version": "1.0.0",
        "status": status,
        "read_only": True,
        "scope": "global_yahoo_price_records_only",
        "counts": result_counts,
        "mutations_performed": 0,
        "raw_values_emitted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Path to the SQLite temporal database")
    args = parser.parse_args(argv)
    try:
        result = audit_database(args.db)
    except (FileNotFoundError, RuntimeError) as exc:
        print(json.dumps({
            "status": "error",
            "error": str(exc),
            "mutations_performed": 0,
            "raw_values_emitted": False,
        }, sort_keys=True))
        return 2

    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] in {"pass", "no_records"} else 1


if __name__ == "__main__":
    sys.exit(main())
