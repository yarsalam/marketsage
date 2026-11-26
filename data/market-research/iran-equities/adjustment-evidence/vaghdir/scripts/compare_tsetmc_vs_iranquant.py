#!/usr/bin/env python3
"""
مقایسه داده TSETMC با رویدادهای iranquant برای وغدیر.
این تطبیق، مبنای پذیرش یا قرنطینه رویدادهاست.
"""
import json
import pandas as pd
from pathlib import Path

VAGHDIR_DIR = Path(__file__).resolve().parent.parent

# ---------- ۱. بارگذاری TSETMC priceAdjust
with open(VAGHDIR_DIR / "raw/tsetmc/vaghdir_price_adjust_raw.json") as f:
    price_adj = json.load(f)["priceAdjust"]

df_pa = pd.DataFrame(price_adj)
df_pa["date"] = pd.to_datetime(df_pa["dEven"].astype(str), format="%Y%m%d")
df_pa = df_pa.sort_values("date").reset_index(drop=True)
print(f"=== TSETMC PriceAdjust: {len(df_pa)} رکورد ===")
print(df_pa[["date", "pClosing", "pClosingNotAdjusted"]].to_string(index=False))

# محاسبه نسبت تعدیل
df_pa["ratio"] = df_pa["pClosing"] / df_pa["pClosingNotAdjusted"]
df_pa["ratio_r"] = df_pa["ratio"].round(8)

# ---------- ۲. بارگذاری TSETMC shareChange
with open(VAGHDIR_DIR / "raw/tsetmc/vaghdir_share_change_raw.json") as f:
    share_change = json.load(f)["instrumentShareChange"]

df_sc = pd.DataFrame(share_change)
df_sc["date"] = pd.to_datetime(df_sc["dEven"].astype(str), format="%Y%m%d")
df_sc = df_sc.sort_values("date").reset_index(drop=True)
df_sc["ratio"] = df_sc["numberOfShareOld"] / df_sc["numberOfShareNew"]
df_sc["increase_pct"] = (1 / df_sc["ratio"] - 1) * 100
print(f"\n=== TSETMC ShareChange: {len(df_sc)} رکورد ===")
print(df_sc[["date", "numberOfShareOld", "numberOfShareNew", "increase_pct"]].to_string(index=False))

# ---------- ۳. بارگذاری رویدادهای iranquant
df_iq = pd.read_csv(VAGHDIR_DIR / "validation/vaghdir_events_estimated.csv")
df_iq["date"] = pd.to_datetime(df_iq["date"])
df_iq = df_iq.sort_values("date").reset_index(drop=True)
print(f"\n=== iranquant Events: {len(df_iq)} رویداد ===")
print(df_iq.to_string(index=False))

# ---------- ۴. تطبیق نزدیک‌ترین تاریخ‌ها (پنجره ۷ روزه)
def match_nearest(ts_date, candidates):
    if len(candidates) == 0:
        return None
    diffs = (candidates["date"] - ts_date).abs()
    idx = diffs.idxmin()
    if diffs[idx].days <= 7:
        return candidates.loc[idx]
    return None

# تطبیق shareChange با capital_increase_pct
print("\n=== تطبیق ShareChange (TSETMC) با Capital Increase (iranquant) ===")
iq_cap = df_iq[df_iq["capital_increase_pct"].notna()].copy()
matched_rows = []
for _, ts_row in df_sc.iterrows():
    m = match_nearest(ts_row["date"], iq_cap)
    matched_rows.append({
        "ts_date": ts_row["date"].date(),
        "ts_increase_pct": round(ts_row["increase_pct"], 2),
        "iq_date": m["date"].date() if m is not None else None,
        "iq_increase_pct": m["capital_increase_pct"] if m is not None else None,
        "match": "✅" if m is not None else "❌",
    })
print(pd.DataFrame(matched_rows).to_string(index=False))

# تطبیق priceAdjust با هر رویداد iranquant
print("\n=== تطبیق PriceAdjust (TSETMC) با رویدادهای iranquant ===")
matched_rows2 = []
for _, ts_row in df_pa.iterrows():
    m = match_nearest(ts_row["date"], df_iq)
    matched_rows2.append({
        "ts_date": ts_row["date"].date(),
        "ts_ratio": round(ts_row["ratio"], 6),
        "iq_date": m["date"].date() if m is not None else None,
        "iq_div_pct": m["dividend_yield_pct"] if m is not None else None,
        "iq_cap_pct": m["capital_increase_pct"] if m is not None else None,
        "match": "✅" if m is not None else "❌",
    })
print(pd.DataFrame(matched_rows2).to_string(index=False))

# ---------- ۵. ذخیره نتایج
out = VAGHDIR_DIR / "validation" / "tsetmc_vs_iranquant_comparison.csv"
df_cmp = pd.DataFrame(matched_rows2)
df_cmp.to_csv(out, index=False)
print(f"\n✅ نتیجه تطبیق در {out} ذخیره شد.")
