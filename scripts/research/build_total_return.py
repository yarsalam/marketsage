#!/usr/bin/env python3
"""Build Total Return series from adjusted_close (reinvested approximation)."""
import argparse, csv
from pathlib import Path


def build_total_return(adjusted_csv, out_csv):
    rows = []
    with open(adjusted_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({"date": r["date"], "adjusted_close": float(r["adjusted_close"])})
    if not rows:
        return 0
    base = rows[0]["adjusted_close"]
    prev = None
    out = []
    for r in rows:
        ac = r["adjusted_close"]
        tr_daily = (ac / prev - 1) if prev and prev > 0 else 0.0
        tr_cum = ac / base - 1 if base > 0 else 0.0
        out.append({"date": r["date"], "adjusted_close": round(ac, 4),
                    "tr_daily": round(tr_daily, 8), "tr_cumulative": round(tr_cum, 6)})
        prev = ac
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","adjusted_close","tr_daily","tr_cumulative"])
        w.writeheader(); w.writerows(out)
    return len(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol-dir", required=True)
    args = ap.parse_args()
    sd = Path(args.symbol_dir)
    adj = sd / "derived" / "adjusted_close.csv"
    out = sd / "derived" / "total_return.csv"
    if not adj.exists():
        print(f"missing {adj} - run build_adjusted_series.py first")
        return 1
    n = build_total_return(adj, out)
    print(f"total_return: {n} rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
