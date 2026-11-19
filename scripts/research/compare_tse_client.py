#!/usr/bin/env python3
"""Compare our adjusted_close with TSE Client 2.27.6 adjustInfo.

Supports two input formats:
  1) Raw TSE Client: ';'-separated records:
     date,adjOpen,adjHigh,adjLow,adjClose,volume,prevAdjClose;...
  2) Pre-split (one per line): same columns, one record per line.

Column F7 (index 6) = adjusted pClosing -- this is what we compare against.
"""
import argparse
import csv
from pathlib import Path


def parse_tse_client(path):
    """Parse both formats. Returns dict {date: adj_pclose}."""
    rows = {}
    content = Path(path).read_text(encoding="utf-8-sig")
    # Normalize: if file has ';', split by ';'; otherwise split by newlines
    if ";" in content:
        records = content.split(";")
    else:
        records = content.splitlines()

    for record in records:
        record = record.strip()
        if not record:
            continue
        parts = record.split(",")
        if len(parts) < 7:
            continue
        try:
            d = parts[0].strip()
            if not d.isdigit() or len(d) != 8:
                continue
            d_fmt = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
            adj_pclose = float(parts[6])  # F7 = adjusted pClosing
            if adj_pclose <= 0:
                continue
            rows[d_fmt] = adj_pclose
        except (ValueError, IndexError):
            continue
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tse-client", required=True)
    ap.add_argument("--adjusted-csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    tse = parse_tse_client(args.tse_client)
    ours = {}
    with open(args.adjusted_csv, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ours[r["date"]] = float(r["adjusted_close"])

    common = sorted(set(tse) & set(ours))
    if not common:
        print("NO COMMON DATES")
        return 1

    out_rows = []
    diffs_pct_high = []  # prices >= 10
    diffs_abs_all = []
    for d in common:
        t = tse[d]
        o = ours[d]
        abs_diff = abs(t - o)
        err_pct = (abs_diff / t * 100) if t > 0 else 0
        diffs_abs_all.append(abs_diff)
        if t >= 10:
            diffs_pct_high.append(err_pct)
        out_rows.append({
            "date": d,
            "tse_client_f7": t,
            "ours": round(o, 4),
            "abs_diff": round(abs_diff, 4),
            "err_pct": round(err_pct, 4),
        })

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","tse_client_f7","ours","abs_diff","err_pct"])
        w.writeheader()
        w.writerows(out_rows)

    diffs_pct_high.sort()
    n = len(diffs_pct_high)
    def pct(p):
        if not n:
            return 0
        return diffs_pct_high[min(int(n * p / 100), n - 1)]

    print(f"TSE Client rows: {len(tse)}")
    print(f"Our adjusted rows: {len(ours)}")
    print(f"Common dates: {len(common)}")
    print()
    print(f"For prices >= 10 rial ({n} rows):")
    print(f"  median err: {pct(50):.4f}%")
    print(f"  p95 err:    {pct(95):.4f}%")
    print(f"  max err:    {diffs_pct_high[-1]:.4f}%")
    bad = [r for r in out_rows if r["tse_client_f7"] >= 10 and r["abs_diff"] > 1.0]
    print(f"  rows with abs_diff > 1.0 (beyond truncation): {len(bad)}")
    for r in bad[:5]:
        print(f"    {r['date']}: tse={r['tse_client_f7']} ours={r['ours']} diff={r['abs_diff']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
