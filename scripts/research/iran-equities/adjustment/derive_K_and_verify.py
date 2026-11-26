#!/usr/bin/env python3
"""Derive preemptive price K from TSETMC data and verify adjustments."""
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

DATA = Path.home() / "marketsage-data"
price_adjust = json.loads((DATA / "vaghdir_price_adjust_raw.json").read_text(encoding="utf-8-sig"))["priceAdjust"]
share_change = json.loads((DATA / "vaghdir_share_change_raw.json").read_text(encoding="utf-8-sig"))["instrumentShareChange"]

share_by_date = {s["dEven"]: s for s in share_change}

def fmt(d):
    s = str(d); return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

print("=" * 100)
print(f"{'Date':<12} {'P_old':>10} {'P_new':>10} {'N_old':>15} {'N_new':>15} {'pure_K':>10} {'K_rial':>10}")
print("=" * 100)

for pa in sorted(price_adjust, key=lambda x: x["dEven"]):
    d = pa["dEven"]
    sc = share_by_date.get(d)
    if not sc:
        continue
    p_old = Decimal(str(pa["pClosingNotAdjusted"]))
    p_new = Decimal(str(pa["pClosing"]))
    n_old = Decimal(str(sc["numberOfShareOld"]))
    n_new = Decimal(str(sc["numberOfShareNew"]))
    n_extra = n_new - n_old

    # Expected ratio if pure stock dividend
    pure_ratio = n_old / n_new
    actual_ratio = p_new / p_old
    pure_K = (p_new * n_new - p_old * n_old) / n_extra if n_extra > 0 else Decimal(0)

    marker = "✅ pure" if abs(actual_ratio - pure_ratio) < Decimal("0.01") else "⚠️  combined"

    print(f"{fmt(d):<12} {float(p_old):>10.1f} {float(p_new):>10.1f} "
          f"{float(n_old):>15,.0f} {float(n_new):>15,.0f} "
          f"{float(pure_K):>10.2f} {int(pure_K):>10,}  {marker}")

print("\n" + "=" * 100)
print("VERIFICATION: apply derived K and check reconstructed P_new")
print("=" * 100)

for pa in sorted(price_adjust, key=lambda x: x["dEven"]):
    d = pa["dEven"]
    sc = share_by_date.get(d)
    if not sc:
        continue
    p_old = Decimal(str(pa["pClosingNotAdjusted"]))
    p_new_actual = Decimal(str(pa["pClosing"]))
    n_old = Decimal(str(sc["numberOfShareOld"]))
    n_new = Decimal(str(sc["numberOfShareNew"]))
    n_extra = n_new - n_old

    pure_K = (p_new_actual * n_new - p_old * n_old) / n_extra if n_extra > 0 else Decimal(0)
    # Round K to nearest rial (Iranian stocks use integer rials)
    K_rounded = pure_K.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    p_new_reconstructed = (p_old * n_old + K_rounded * n_extra) / n_new
    error = abs(p_new_reconstructed - p_new_actual)
    error_pct = (error / p_new_actual * 100) if p_new_actual else Decimal(0)

    status = "✅" if error_pct < Decimal("0.5") else "⚠️"
    print(f"{fmt(d)}: K={K_rounded} → P_rec={p_new_reconstructed:.2f} "
          f"(actual {p_new_actual:.2f}, error {error_pct:.3f}%) {status}")
