#!/usr/bin/env python3
"""Audit TSETMC corporate-action feed identifiers against exact instrument identities.

The audit is deliberately conservative: only the exact ticker record's primary
InsCode is accepted automatically. insCode2/3/4 are reported as related IDs but
never promoted to aliases. A mismatch is a quarantine/research finding, not a
reason to discard rows or to infer a mapping.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SYMBOLS = {
    "vaghdir": {"ticker": "وغدیر", "primary_inscode": "26014913469567886"},
    "foolad": {"ticker": "فولاد", "primary_inscode": "46348559193224090"},
    "parsian": {"ticker": "پارسیان", "primary_inscode": "9481703061634967"},
}
BASE = Path("data/market-research/iran-equities/adjustment-evidence")


def norm(value: Any) -> str:
    if isinstance(value, float):
        raise ValueError(
            "InsCode was decoded as float; precision may already be lost. "
            "Read the raw decimal JSON token or parse it as an arbitrary-precision integer."
        )
    return str(value or "").strip().replace("ي", "ی").replace("ك", "ک")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def feed_summary(records: list[dict[str, Any]], primary: str,
                 related_ids: dict[str, str]) -> dict[str, Any]:
    ids: dict[str, int] = {}
    related_matches: dict[str, int] = {key: 0 for key in related_ids}
    primary_rows = 0
    missing_id_rows = 0

    for record in records:
        identifier = norm(record.get("insCode"))
        if not identifier:
            missing_id_rows += 1
            continue
        ids[identifier] = ids.get(identifier, 0) + 1
        if identifier == primary:
            primary_rows += 1
        for field, related in related_ids.items():
            if identifier == related:
                related_matches[field] += 1

    mismatch_rows = len(records) - primary_rows - missing_id_rows
    if not records:
        status = "empty_feed"
    elif mismatch_rows == 0 and missing_id_rows == 0:
        status = "matched_primary"
    elif primary_rows == 0:
        status = "unresolved_identifier_mismatch"
    else:
        status = "mixed_primary_and_unresolved_identifiers"

    return {
        "status": status,
        "row_count": len(records),
        "primary_insCode": primary,
        "matched_primary_rows": primary_rows,
        "unresolved_identifier_rows": mismatch_rows,
        "missing_identifier_rows": missing_id_rows,
        "identifier_row_counts": dict(sorted(ids.items())),
        "related_field_match_counts_unverified": related_matches,
        "related_ids_used_as_aliases": False,
    }


def audit_symbol(repo_root: Path, symbol: str) -> dict[str, Any]:
    expected = SYMBOLS[symbol]
    instrument_dir = repo_root / BASE / symbol
    identity = read_json(instrument_dir / "identity.json")
    primary = norm(identity.get("primary_insCode"))
    if primary != expected["primary_inscode"]:
        raise ValueError(
            f"{symbol}: identity.json primary InsCode {primary!r} "
            f"does not match the reviewed pilot value {expected['primary_inscode']!r}"
        )

    search = read_json(instrument_dir / "raw" / "tsetmc" / f"{symbol}_instrument_search.json")
    records = search.get("instrumentSearch", [])
    exact = [row for row in records if norm(row.get("lVal18AFC")) == expected["ticker"]]
    if len(exact) != 1:
        raise ValueError(f"{symbol}: expected one exact ticker record, found {len(exact)}")
    exact_record = exact[0]
    if norm(exact_record.get("insCode")) != primary:
        raise ValueError(f"{symbol}: raw instrument search primary InsCode differs from identity.json")

    related_ids = {
        field: norm(exact_record.get(field))
        for field in ("insCode2", "insCode3", "insCode4")
        if norm(exact_record.get(field))
    }

    price_obj = read_json(instrument_dir / "raw" / "tsetmc" / f"{symbol}_price_adjust_raw.json")
    price_rows = price_obj.get("priceAdjust", [])
    share_obj = read_json(instrument_dir / "raw" / "tsetmc" / f"{symbol}_share_change_raw.json")
    share_rows = share_obj.get("instrumentShareChange", [])

    price = feed_summary(price_rows, primary, related_ids)
    shares = feed_summary(share_rows, primary, related_ids)
    overall = (
        "matched_primary"
        if price["status"] == "matched_primary" and shares["status"] == "matched_primary"
        else "requires_identity_research"
    )

    return {
        "symbol": symbol,
        "ticker": expected["ticker"],
        "primary_insCode": primary,
        "related_ids_unverified": related_ids,
        "exact_instrument_search_records": len(exact),
        "instrument_search_record_count": len(records),
        "price_adjust": price,
        "share_change": shares,
        "overall_status": overall,
        "policy": "Only exact ticker record primary InsCode is accepted automatically; insCode2/3/4 are never assumed aliases.",
        "numeric_precision_note": "Python json integer parsing preserves arbitrary-precision InsCode values. JavaScript Number cannot exactly represent integers above 2^53-1; use decimal strings or BigInt and never coerce InsCode to Number.",
    }


def audit_all(repo_root: Path) -> dict[str, Any]:
    return {
        "audit_version": "1.0.0",
        "repository_path": str(BASE),
        "symbol_count": len(SYMBOLS),
        "numeric_precision_note": "InsCode is a decimal identifier, not a quantity. Values above 2^53-1 must be carried as strings or BigInt in JavaScript and as text/64-bit exact integers in storage.",
        "symbols": {symbol: audit_symbol(repo_root, symbol) for symbol in SYMBOLS},
        "summary": {
            "matched_primary_symbols": 0,
            "symbols_requiring_identity_research": 0,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--strict", action="store_true",
                        help="Return exit code 2 if any event feed has unresolved identifiers.")
    args = parser.parse_args()

    report = audit_all(args.repo_root.resolve())
    rows = report["symbols"]
    matched = sum(item["overall_status"] == "matched_primary" for item in rows.values())
    unresolved = len(rows) - matched
    report["summary"]["matched_primary_symbols"] = matched
    report["summary"]["symbols_requiring_identity_research"] = unresolved

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(rendered, end="")
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(rendered, encoding="utf-8")
    return 2 if args.strict and unresolved else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"IDENTITY AUDIT ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
