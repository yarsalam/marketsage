#!/usr/bin/env python3
"""Download a small Yahoo Finance daily-price research sample.

Research-only helper. It does not approve Yahoo data for production scoring,
and it does not download or represent Iranian-market instruments.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_TICKERS = (
    "BTC-USD", "ETH-USD", "SOL-USD", "GLD", "SPY", "QQQ",
    "TLT", "UUP", "USO", "XLF", "XLE",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2015-01-01", help="Inclusive YYYY-MM-DD start date (default: 2015-01-01)")
    parser.add_argument("--end", default=None, help="Exclusive YYYY-MM-DD end date (default: today's UTC date; avoids partial current-day bar)")
    parser.add_argument("--tickers", nargs="+", default=list(DEFAULT_TICKERS), help="Yahoo Finance symbols")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".cache" / "marketsage" / "research" / "yahoo",
        help="Output directory (default is outside the Git repository)",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace files for requested symbols and manifest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        start = datetime.strptime(args.start, "%Y-%m-%d").date()
        end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else datetime.now(timezone.utc).date()
    except ValueError as exc:
        print(f"ERROR: dates must use YYYY-MM-DD: {exc}", file=sys.stderr)
        return 2

    if end <= start:
        print("ERROR: --end must be later than --start (end is exclusive).", file=sys.stderr)
        return 2

    tickers = list(dict.fromkeys(symbol.strip().upper() for symbol in args.tickers if symbol.strip()))
    if not tickers:
        print("ERROR: provide at least one ticker.", file=sys.stderr)
        return 2

    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    expected = [output / f"{symbol.replace('/', '_')}.csv" for symbol in tickers]
    manifest_path = output / "manifest.json"
    existing = [path for path in [*expected, manifest_path] if path.exists()]
    if existing and not args.overwrite:
        print("ERROR: output already contains requested files. Choose another --output or pass --overwrite.", file=sys.stderr)
        for path in existing:
            print(f"  {path}", file=sys.stderr)
        return 2

    try:
        import yfinance as yf
    except ImportError:
        print("ERROR: yfinance is missing. Activate the project venv and install project requirements.", file=sys.stderr)
        return 2

    manifest = {
        "schema_version": 1,
        "purpose": "research_only_unapproved",
        "provider": "Yahoo Finance via yfinance",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_start_inclusive": start.isoformat(),
        "requested_end_exclusive": end.isoformat(),
        "interval": "1d",
        "auto_adjust": False,
        "actions_requested": True,
        "symbols": {},
        "limitations": [
            "This mixed US-listed funds/equities and crypto sample is not representative of Iranian markets.",
            "Currency, licensing/permission, historical revisions, survivorship, execution prices and point-in-time availability require separate review.",
            "Close and Adj Close are kept as separate provider fields; neither is silently substituted for the other.",
            "A successful download proves reachability only, not source acceptance or predictive performance.",
        ],
    }

    failures = 0
    for symbol in tickers:
        destination = output / f"{symbol.replace('/', '_')}.csv"
        print(f"Fetching {symbol} ...")
        try:
            frame = yf.Ticker(symbol).history(
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1d",
                auto_adjust=False,
                actions=True,
                repair=False,
                raise_errors=True,
                timeout=20,
            )
            if frame is None or frame.empty:
                raise ValueError("provider returned no rows")
            frame.index.name = "Date"
            frame.to_csv(destination, index=True)
            manifest["symbols"][symbol] = {
                "status": "downloaded_unapproved",
                "file": destination.name,
                "row_count": int(len(frame)),
                "first_date": frame.index.min().isoformat(),
                "last_date": frame.index.max().isoformat(),
                "columns": [str(column) for column in frame.columns],
                "currency": "unknown_pending_metadata_review",
            }
            print(f"  rows={len(frame)}; range={frame.index.min().date()}..{frame.index.max().date()}")
        except Exception as exc:  # provider/library exceptions vary by version
            failures += 1
            manifest["symbols"][symbol] = {
                "status": "failed",
                "error_type": type(exc).__name__,
            }
            print(f"  FAILED ({type(exc).__name__}); details intentionally omitted from report.", file=sys.stderr)

    manifest["downloaded_count"] = sum(item["status"] == "downloaded_unapproved" for item in manifest["symbols"].values())
    manifest["failed_count"] = failures
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Manifest: {manifest_path}")
    print(f"Downloaded: {manifest['downloaded_count']}; failed: {failures}")
    print("Status remains research-only/unapproved; do not enable investment ranking from this dataset.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
