import json
from pathlib import Path

DATA = Path.home() / "marketsage-data"
daily = json.loads((DATA / "vaghdir_daily_raw.json").read_text(encoding="utf-8-sig"))["closingPriceDaily"]

# مرتب‌سازی بر اساس تاریخ
daily_sorted = sorted(daily, key=lambda r: r.get("dEven", 0))

# پیدا کردن جهش‌های قیمتی بزرگ (بیش از ۲۰٪)
print("PRICE JUMPS > 20% in daily adjusted series:\n")
print(f"{'date':<12} {'prev_close':>12} {'close':>12} {'change%':>10} {'vol':>15}")
print("-" * 70)

prev = None
jumps = []
for r in daily_sorted:
    d = r.get("dEven")
    c = r.get("pClosing")
    v = r.get("qTotTran5J", 0)
    if c is None or c == 0:
        continue
    if prev and prev["pClosing"] and prev["pClosing"] > 0:
        change = (c / prev["pClosing"] - 1) * 100
        if abs(change) > 20:
            jumps.append({
                "date": d,
                "prev_date": prev["dEven"],
                "prev_close": prev["pClosing"],
                "close": c,
                "change_pct": round(change, 2),
                "ratio": round(c / prev["pClosing"], 4),
                "vol": v,
            })
            print(f"{d} {prev['pClosing']:>12.1f} {c:>12.1f} {change:>+9.1f}% {v:>15.0f}")
    prev = r

print(f"\nTotal jumps > 20%: {len(jumps)}")

# ذخیره
out = DATA / "vaghdir_daily_jumps.json"
out.write_text(json.dumps(jumps, ensure_ascii=False, indent=2, default=str))
print(f"Saved: {out}")
