#!/usr/bin/env python3
"""Local, read-only inventory of candidate research data files.

The report contains file metadata and schema/quality summaries only; it does not
print sample rows or cell values. It does not fetch data or approve sources.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build",
}
DATA_SUFFIXES = {".csv", ".parquet", ".json", ".jsonl", ".feather"}
MAX_BYTES = 250 * 1024 * 1024
DATE_HINTS = ("date", "time", "timestamp", "datetime", "period")
PRICE_HINTS = ("close", "adj close", "adjusted close", "price", "settle", "value", "nav")


def parse_date(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        import pandas as pd
        parsed = pd.to_datetime(value, errors="coerce", utc=True)
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    except Exception:
        return None


def safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def inspect_tabular(path: Path) -> dict[str, Any]:
    import pandas as pd

    result: dict[str, Any] = {"format": path.suffix.lower(), "inspection": "metadata_only"}
    if path.suffix.lower() == ".csv":
        frame = pd.read_csv(path, low_memory=False)
    elif path.suffix.lower() == ".parquet":
        frame = pd.read_parquet(path)
    elif path.suffix.lower() == ".feather":
        frame = pd.read_feather(path)
    else:
        raise ValueError("not a tabular format")

    result["rows"] = int(len(frame))
    result["columns"] = [str(c) for c in frame.columns]
    result["missing_by_column"] = {
        str(c): int(n) for c, n in frame.isna().sum().items() if int(n) > 0
    }
    date_cols = [
        c for c in frame.columns
        if any(hint in str(c).strip().lower().replace("_", " ") for hint in DATE_HINTS)
    ]
    result["date_columns"] = [str(c) for c in date_cols]
    result["date_ranges"] = {}
    result["duplicate_date_rows"] = {}
    for col in date_cols:
        parsed = pd.to_datetime(frame[col], errors="coerce", utc=True)
        valid = parsed.dropna()
        result["date_ranges"][str(col)] = (
            {"min_utc": valid.min().isoformat(), "max_utc": valid.max().isoformat(),
             "unparseable_or_missing": int(parsed.isna().sum())}
            if not valid.empty else
            {"min_utc": None, "max_utc": None, "unparseable_or_missing": int(parsed.isna().sum())}
        )
        result["duplicate_date_rows"][str(col)] = int(parsed.duplicated(keep=False).sum())

    price_cols = [
        c for c in frame.columns
        if any(hint in str(c).strip().lower().replace("_", " ") for hint in PRICE_HINTS)
    ]
    result["candidate_price_columns"] = [str(c) for c in price_cols]
    result["candidate_price_checks"] = {}
    for col in price_cols:
        numeric = pd.to_numeric(frame[col], errors="coerce")
        finite = numeric.map(lambda x: math.isfinite(float(x)) if pd.notna(x) else False)
        result["candidate_price_checks"][str(col)] = {
            "non_numeric_or_missing": int((~numeric.notna()).sum()),
            "non_finite": int((numeric.notna() & ~finite).sum()),
            "non_positive": int((numeric.notna() & (numeric <= 0)).sum()),
        }
    return result


def inspect_json(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"format": path.suffix.lower(), "inspection": "metadata_only"}
    if path.suffix.lower() == ".jsonl":
        rows = 0
        keys: set[str] = set()
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                rows += 1
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        keys.update(str(k) for k in obj.keys())
                except json.JSONDecodeError:
                    result["invalid_json_lines"] = result.get("invalid_json_lines", 0) + 1
        result["rows"] = rows
        result["top_level_keys_union"] = sorted(keys)
        return result

    with path.open("r", encoding="utf-8") as handle:
        obj = json.load(handle)
    if isinstance(obj, list):
        result["rows"] = len(obj)
        result["top_level_shape"] = "list"
        if obj and isinstance(obj[0], dict):
            result["record_keys"] = sorted(str(k) for k in obj[0].keys())
    elif isinstance(obj, dict):
        result["top_level_shape"] = "object"
        result["top_level_keys"] = sorted(str(k) for k in obj.keys())
        for key in ("data", "prices", "observations", "history", "results", "records"):
            value = obj.get(key)
            if isinstance(value, list):
                result["candidate_array_lengths"] = result.get("candidate_array_lengths", {})
                result["candidate_array_lengths"][key] = len(value)
                if value and isinstance(value[0], dict):
                    result.setdefault("candidate_array_record_keys", {})[key] = sorted(
                        str(k) for k in value[0].keys()
                    )
    else:
        result["top_level_shape"] = type(obj).__name__
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("user/analysis-engine"))
    parser.add_argument("--output", type=Path, default=Path("/tmp/marketsage-data-audit.json"))
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"root directory does not exist: {root}")

    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in DATA_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        files.append(path)

    entries = []
    for path in sorted(files):
        item: dict[str, Any] = {
            "path": safe_rel(path, root),
            "bytes": path.stat().st_size,
            "format": path.suffix.lower(),
        }
        try:
            if item["bytes"] > MAX_BYTES:
                item["status"] = "skipped_size_limit"
            elif path.suffix.lower() in {".csv", ".parquet", ".feather"}:
                item.update(inspect_tabular(path))
                item["status"] = "inspected"
            else:
                item.update(inspect_json(path))
                item["status"] = "inspected"
        except Exception as exc:
            # Error class only: avoid copying file content or credentials into the report.
            item["status"] = "inspection_error"
            item["error_type"] = type(exc).__name__
        entries.append(item)

    report = {
        "report_version": "marketsage_local_data_inventory_v1",
        "root": str(root),
        "files_found": len(entries),
        "files_inspected": sum(1 for x in entries if x.get("status") == "inspected"),
        "files_with_errors": sum(1 for x in entries if x.get("status") == "inspection_error"),
        "files": entries,
        "limitations": [
            "Inventory only; no source approval, licensing review, or predictive validation.",
            "Column names and date ranges are heuristics; inspect source contracts separately.",
            "JSON report includes key names and counts, not sample records or values.",
            "A zero duplicate count per date column does not prove unique (symbol, date) pairs.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Root: {root}")
    print(f"Data-like files found: {report['files_found']}")
    print(f"Inspected: {report['files_inspected']}; errors: {report['files_with_errors']}")
    print(f"Report: {args.output}")
    for item in entries:
        print(f"- {item['path']} | {item['format']} | {item['bytes']} bytes | {item['status']}")
        if item.get("status") == "inspected":
            if "rows" in item:
                print(f"  rows={item['rows']}")
            if item.get("date_ranges"):
                for col, span in item["date_ranges"].items():
                    print(f"  date[{col}]={span['min_utc']}..{span['max_utc']}")
            if item.get("candidate_price_checks"):
                print(f"  candidate price columns={', '.join(item['candidate_price_checks'])}")
        elif item.get("status") == "inspection_error":
            print(f"  inspection error type={item.get('error_type', 'unknown')}")
    print("NOTE: this is inventory metadata only; unknown provenance/units/rights remain unapproved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
