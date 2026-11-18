#!/usr/bin/env python3
"""
MarketSage — Iran Equity Adjustment Evidence Builder
Usage:
    python fetch_and_analyze.py --symbol وغدیر --out-dir /path/to/vaghdir
    python fetch_and_analyze.py --symbol فولاد --out-dir /path/to/foolad
"""
import argparse
import time
import json
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------- config
TSETMC_CDN = "https://cdn.tsetmc.com/api"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}

# ---------------------------------------------------------------- helpers
def get_ins_code(symbol: str) -> str:
    from urllib.parse import quote
    url = f"{TSETMC_CDN}/Instrument/GetInstrumentSearch/{quote(symbol)}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    js = r.json()
    if not js.get("instrumentSearch"):
        raise RuntimeError(f"نماد {symbol} پیدا نشد.")
    return js["instrumentSearch"][0]["insCode"]


def save_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ ذخیره شد: {path}")


def fetch_tsetmc_raw(symbol: str, out_dir: Path) -> dict:
    """دریافت داده خام TSETMC: جستجوی نماد، تغییر سهام، تعدیل قیمت."""
    print(f"\n=== دریافت داده TSETMC برای {symbol} ===")
    ins_code = get_ins_code(symbol)
    print(f"InsCode: {ins_code}")

    tsetmc_dir = out_dir / "raw" / "tsetmc"
    tsetmc_dir.mkdir(parents=True, exist_ok=True)

    # ۱. جستجوی نماد (لاگ)
    search_url = f"{TSETMC_CDN}/Instrument/GetInstrumentSearch/{symbol}"
    r = requests.get(search_url, headers=HEADERS, timeout=30)
    if r.status_code == 200:
        save_json(r.json(), tsetmc_dir / f"{symbol}_instrument_search.json")

    # ۲. تغییر تعداد سهام
    time.sleep(2)
    share_url = f"{TSETMC_CDN}/Instrument/GetInstrumentShareChange/{ins_code}"
    r = requests.get(share_url, headers=HEADERS, timeout=30)
    if r.status_code == 200 and "json" in r.headers.get("Content-Type", ""):
        save_json(r.json(), tsetmc_dir / f"{symbol}_share_change_raw.json")
    else:
        print(f"⚠️ GetInstrumentShareChange: HTTP {r.status_code} / {r.headers.get('Content-Type')}")

    # ۳. لیست تعدیل قیمت
    time.sleep(2)
    adj_url = f"{TSETMC_CDN}/PriceAdjust/GetPriceAdjustList/{ins_code}"
    r = requests.get(adj_url, headers=HEADERS, timeout=30)
    if r.status_code == 200 and "json" in r.headers.get("Content-Type", ""):
        save_json(r.json(), tsetmc_dir / f"{symbol}_price_adjust_raw.json")
    else:
        print(f"⚠️ GetPriceAdjustList: HTTP {r.status_code} / {r.headers.get('Content-Type')}")

    return {"ins_code": ins_code}


def fetch_iranquant(symbol: str, out_dir: Path):
    """دریافت تاریخچه قیمت تعدیل‌شده از iranquant."""
    print(f"\n=== دریافت iranquant برای {symbol} ===")
    try:
        import iranquant as iq
    except ImportError:
        print("❌ iranquant نصب نیست. pip install iranquant")
        return

    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        df_all = iq.history(symbol, adjust="all")
        df_cap = iq.history(symbol, adjust="capital_only")
        df_raw = iq.history(symbol, adjust="none")

        df_all.to_csv(raw_dir / f"{symbol}_adjusted_all.csv", index=False)
        df_cap.to_csv(raw_dir / f"{symbol}_adjusted_capital.csv", index=False)
        df_raw.to_csv(raw_dir / f"{symbol}_raw.csv", index=False)
        print(f"✅ سه فایل CSV ذخیره شد در {raw_dir}")
    except Exception as e:
        print(f"❌ خطای iranquant: {e}")


def analyze_adjustments(symbol: str, out_dir: Path):
    """تحلیل نقاط تغییر نسبت تعدیل و تخمین رویدادها."""
    print(f"\n=== تحلیل تعدیل برای {symbol} ===")
    raw_dir = out_dir / "raw"
    val_dir = out_dir / "validation"
    val_dir.mkdir(parents=True, exist_ok=True)

    try:
        raw = pd.read_csv(raw_dir / f"{symbol}_raw.csv")
        all_adj = pd.read_csv(raw_dir / f"{symbol}_adjusted_all.csv")
        cap_adj = pd.read_csv(raw_dir / f"{symbol}_adjusted_capital.csv")
    except FileNotFoundError as e:
        print(f"❌ فایل‌های iranquant یافت نشد: {e}")
        return

    def find_price_col(df):
        for c in ["close", "final", "pc", "pClosing", "adj_close", "Close"]:
            if c in df.columns:
                return c
        raise ValueError(f"ستون قیمت پیدا نشد: {df.columns.tolist()}")

    pc_raw, pc_all, pc_cap = find_price_col(raw), find_price_col(all_adj), find_price_col(cap_adj)

    for df in (raw, all_adj, cap_adj):
        df["date"] = pd.to_datetime(df["date"])

    raw = raw.sort_values("date")
    all_adj = all_adj.sort_values("date")
    cap_adj = cap_adj.sort_values("date")

    m = (
        raw[["date", pc_raw]].rename(columns={pc_raw: "raw"})
        .merge(all_adj[["date", pc_all]].rename(columns={pc_all: "all"}), on="date", how="inner")
        .merge(cap_adj[["date", pc_cap]].rename(columns={pc_cap: "cap"}), on="date", how="inner")
    )
    m["ratio_all"] = m["all"] / m["raw"]
    m["ratio_cap"] = m["cap"] / m["raw"]
    m["ratio_all_r"] = m["ratio_all"].round(8)
    m["ratio_cap_r"] = m["ratio_cap"].round(8)
    m["change_all"] = m["ratio_all_r"].diff().abs() > 1e-8
    m["change_cap"] = m["ratio_cap_r"].diff().abs() > 1e-8

    changes = m[m["change_all"] | m["change_cap"]].copy()
    changes["prev_ratio_all"] = m["ratio_all_r"].shift(1)
    changes["prev_ratio_cap"] = m["ratio_cap_r"].shift(1)
    changes.to_csv(val_dir / f"{symbol}_adjustment_changes.csv", index=False)
    m.to_csv(val_dir / f"{symbol}_adjustment_comparison.csv", index=False)

    # تخمین درصد رویداد
    prev_all = m["ratio_all_r"].shift(1)
    prev_cap = m["ratio_cap_r"].shift(1)
    rows = []
    for i, row in m.iterrows():
        if not (row["change_all"] or row["change_cap"]):
            continue
        ev = {"date": row["date"].date(), "raw_close": row["raw"]}
        if row["change_cap"]:
            f_cap = prev_cap.iloc[i] / row["ratio_cap_r"]
            ev["capital_increase_pct"] = round((1 / f_cap - 1) * 100, 2)
        if row["change_all"]:
            div_curr = row["ratio_all_r"] / row["ratio_cap_r"]
            div_prev = prev_all.iloc[i] / prev_cap.iloc[i]
            f_div = div_prev / div_curr
            ev["dividend_yield_pct"] = round((1 / f_div - 1) * 100, 2)
        rows.append(ev)

    events = pd.DataFrame(rows)
    events.to_csv(val_dir / f"{symbol}_events_estimated.csv", index=False)
    print(f"✅ تحلیل ذخیره شد در {val_dir}")
    print(f"\nتعداد رویدادهای استخراج‌شده: {len(events)}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--skip-iranquant", action="store_true")
    ap.add_argument("--skip-analysis", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    fetch_tsetmc_raw(args.symbol, out_dir)
    if not args.skip_iranquant:
        fetch_iranquant(args.symbol, out_dir)
    if not args.skip_analysis:
        analyze_adjustments(args.symbol, out_dir)

    print(f"\n✅ همه کارها تمام شد. خروجی در {out_dir}")


if __name__ == "__main__":
    main()
