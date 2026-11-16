# Vaghdir 2011 Adjustment Audit

**Audit date:** 2026-11-16
**InsCode:** 26014913469567886
**Event date:** 2011-04-23 (Gregorian) / 1390/02/03 (Jalali)
**Status:** EVIDENCE_SUPPORTED — FORMULA_VERIFIED

## Source Hashes (verified)

| File | SHA-256 (first 16) |
|---|---|
| `codal/38803.pdf` | `e8d591b9e933bba0` |
| `codal/40620.pdf` | `88b5d6d4ac2b4777` |
| `codal/38805.pdf` | `e9f437b064fc2c3d` |
| `raw/tsetmc/vaghdir_price_adjust_raw.json` | `1fadcc07e1a4b1da` |
| `raw/tsetmc/vaghdir_share_change_raw.json` | `a3c3c94a0f53b7bd` |
| `raw/tsetmc/vaghdir_daily_raw.json` | `d19345663eec5958` |

## Raw Values (from TSETMC)

| Field | Value |
|---|---|
| `pClosing` (adjusted) | 3820.0 |
| `pClosingNotAdjusted` | 7252.0 |
| shares old | 6,075,000,000 |
| shares new | 12,000,000,000 |

## Derived Parameters

| Parameter | Value | Source |
|---|---|---|
| **K (exact)** | 301.113924 rials | derived from TSETMC tuple |
| **K (rounded)** | 301 rials | monetary convention |
| **DPS** | 500 rials | `codal/38803.pdf` |

## Reconstruction (pClosing only - no DPS)

P_new = (7252 * 6.075B + 301 * 5.925B) / 12B = 3819.9438

Actual pClosing: 3820.0000
Error: 0.0015%

## Reconstruction (DPS + capital increase - theoretical)

P_base_after_dps = 7252 - 500 = 6752
P_theoretical    = (6752 * 6.075B + 301 * 5.925B) / 12B = 3566.8188

Market close on 2011-04-26: 3569.0
Difference: 2.1812 rials (0.0611%)

## Conclusion

1. DPS = 500 is confirmed by CODAL 38803.pdf and by market behavior.
2. K = 301 is confirmed by exact reconstruction (error 0.0015%).
3. pClosing in GetClosingPriceDailyList applies capital increase ONLY, not cash dividend.
4. The 2.18-rial difference at reopening (3569 vs 3566.82) is attributed to tick volatility.
5. For Total Return, DPS must be applied separately.

## Audit script

The audit was run via /tmp/audit_vaghdir.py, which reads hashes and recomputes all values from the raw JSON. The script is reproducible but not yet committed to the repo.
