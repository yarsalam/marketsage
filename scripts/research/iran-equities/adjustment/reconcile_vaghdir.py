import json
from pathlib import Path
from collections import defaultdict

DATA = Path.home() / "marketsage-data"

price_adjust = json.loads((DATA / "vaghdir_price_adjust_raw.json").read_text())["priceAdjust"]
share_change = json.loads((DATA / "vaghdir_share_change_raw.json").read_text())["instrumentShareChange"]
daily_raw = json.loads((DATA / "vaghdir_daily_raw.json").read_text())

# ساختار daily
daily_list = daily_raw.get("closingPriceDaily") or []
print(f"Price adjust events: {len(price_adjust)}")
print(f"Share change events: {len(share_change)}")
print(f"Daily rows: {len(daily_list)}")

# ایندکس تغییر سهام بر اساس تاریخ
share_by_date = {}
for s in share_change:
    d = s["dEven"]
    share_by_date.setdefault(d, []).append(s)

# ایندکس قیمت روزانه بر اساس تاریخ
daily_by_date = {}
for r in daily_list:
    d = r.get("dEven")
    if d:
        daily_by_date[d] = r

# تابع تبدیل تاریخ
def fmt(d):
    s = str(d)
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

# تطبیق هر رویداد تعدیل
print("\n" + "="*80)
print("RECONCILIATION: Price Adjust vs Share Change")
print("="*80)

results = []
for pa in sorted(price_adjust, key=lambda x: x["dEven"]):
    d = pa["dEven"]
    p_adj = pa["pClosing"]
    p_raw = pa["pClosingNotAdjusted"]
    diff = round(p_raw - p_adj, 2)
    ratio = round(p_adj / p_raw, 4) if p_raw else None

    # آیا در همان تاریخ تغییر سهام هست؟
    same_day = share_by_date.get(d, [])

    # تغییر سهام نزدیک (تا ۷ روز قبل)
    nearby_share = []
    for sd, items in share_by_date.items():
        if abs(sd - d) <= 7 and sd != d:
            for it in items:
                nearby_share.append((sd, it))

    if same_day:
        event_type = "CAPITAL_INCREASE"
        share_info = same_day[0]
        share_ratio = round(share_info["numberOfShareNew"] / share_info["numberOfShareOld"], 4)
        expected_ratio_from_shares = round(share_info["numberOfShareOld"] / share_info["numberOfShareNew"], 4)
    elif nearby_share:
        event_type = "NEAR_SHARE_CHANGE"
        share_info = nearby_share[0][1]
        share_ratio = round(share_info["numberOfShareNew"] / share_info["numberOfShareOld"], 4)
        expected_ratio_from_shares = round(share_info["numberOfShareOld"] / share_info["numberOfShareNew"], 4)
    else:
        event_type = "CASH_DIVIDEND"
        share_info = None
        share_ratio = None
        expected_ratio_from_shares = None

    # بررسی تطابق نسبت
    ratio_match = None
    if expected_ratio_from_shares is not None:
        ratio_match = abs(ratio - expected_ratio_from_shares) < 0.01

    results.append({
        "date": d,
        "date_fmt": fmt(d),
        "p_adjusted": p_adj,
        "p_raw": p_raw,
        "difference": diff,
        "ratio": ratio,
        "event_type": event_type,
        "share_old": share_info["numberOfShareOld"] if share_info else None,
        "share_new": share_info["numberOfShareNew"] if share_info else None,
        "share_ratio": share_ratio,
        "expected_ratio": expected_ratio_from_shares,
        "ratio_match": ratio_match,
    })

for r in results:
    print(f"\n{r['date_fmt']} | {r['event_type']:20s} | "
          f"adj={r['p_adjusted']:>10.1f} raw={r['p_raw']:>10.1f} "
          f"diff={r['difference']:>8.1f} ratio={r['ratio']}")
    if r['share_old'] is not None:
        print(f"  shares: {r['share_old']:,.0f} -> {r['share_new']:,.0f} "
              f"(x{r['share_ratio']}) expected_ratio={r['expected_ratio']} "
              f"match={r['ratio_match']}")

# رویدادهای تغییر سهام که در لیست تعدیل نیستند
print("\n" + "="*80)
print("SHARE CHANGES WITHOUT PRICE ADJUST EVENT")
print("="*80)

price_dates = {p["dEven"] for p in price_adjust}
for sd, items in sorted(share_by_date.items()):
    if sd not in price_dates:
        for it in items:
            print(f"\n{fmt(sd)}: {it['numberOfShareOld']:,.0f} -> {it['numberOfShareNew']:,.0f} "
                  f"(x{it['numberOfShareNew']/it['numberOfShareOld']:.4f})")
            print(f"  ⚠️  No matching price adjust event on same day")
            # بررسی آیا روز قبل/بعدش تعدیل هست
            for p in price_adjust:
                if abs(p["dEven"] - sd) <= 30:
                    print(f"  Nearby price adjust: {fmt(p['dEven'])} "
                          f"(adj={p['pClosing']} raw={p['pClosingNotAdjusted']})")

# تناقض‌های تاریخ یکسان
print("\n" + "="*80)
print("SAME-DATE CONFLICTS")
print("="*80)

by_date = defaultdict(list)
for p in price_adjust:
    by_date[p["dEven"]].append(p)

for d, items in by_date.items():
    if len(items) > 1:
        print(f"\n{fmt(d)}: {len(items)} conflicting records")
        for i, it in enumerate(items):
            print(f"  [{i+1}] adj={it['pClosing']} raw={it['pClosingNotAdjusted']} "
                  f"diff={it['pClosingNotAdjusted']-it['pClosing']:.1f}")

# ذخیره گزارش
report = {
    "summary": {
        "price_adjust_events": len(price_adjust),
        "share_change_events": len(share_change),
        "daily_rows": len(daily_list),
    },
    "reconciled_events": results,
    "unmatched_share_changes": [
        {"date": sd, "date_fmt": fmt(sd), **it}
        for sd, items in share_by_date.items()
        if sd not in price_dates
        for it in items
    ],
    "same_date_conflicts": [
        {"date": d, "date_fmt": fmt(d), "records": items}
        for d, items in by_date.items() if len(items) > 1
    ],
}

out = DATA / "vaghdir_reconciliation.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
print(f"\n\nReport saved: {out}")
