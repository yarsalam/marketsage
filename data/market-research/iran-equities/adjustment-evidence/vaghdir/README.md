# Vaghdir (وغدیر) — Adjustment Evidence

**Status:** EVIDENCE_SUPPORTED — FINAL REPOSITORY ACCEPTANCE PENDING
**InsCode:** 26014913469567886
**Symbol:** وغدیر

## Purpose

This directory contains reproducible evidence for the 2011 corporate actions
of Vaghdir (وغدیر), specifically the cash dividend and capital increase that
caused the TSETMC price adjustment on 2011-04-23.

## Evidence Files

### `codal/` — Official CODAL announcements

| File | TracingNo | Date (Jalali) | What it proves |
|------|-----------|---------------|----------------|
| `38803.pdf` | 38803 | 1390/02/04 | **DPS = 500 Rials** (مجمع عادی سالیانه) |
| `40620.pdf` | 40620 | 1390/02/15 | **Capital increase**: 6,075,000 → 12,000,000 million Rials, split into: retained earnings 1,410,000 / reserves 2,721,000 / receivables+cash 1,794,000 |
| `38805.pdf` | 38805 | 1390/01/31 | Extraordinary general meeting approving the capital increase |

### `raw/` — Raw TSETMC API responses (immutable)

| File | Source endpoint | Content |
|------|-----------------|---------|
| `vaghdir_price_adjust_raw.json` | `GetPriceAdjustList` | 25 price-adjustment events (2009–2026) |
| `vaghdir_share_change_raw.json` | `GetInstrumentShareChange` | 7 share-count changes (2011–2024) |
| `vaghdir_daily_raw.json` | `GetClosingPriceDailyList` | Full daily series, 5,691 rows |

### `diagnostics/` — Reconciliation output

| File | Content |
|------|---------|
| `vaghdir_reconciliation.json` | Match of price-adjust events vs share-count changes |

## Key Findings

1. **Cash dividend:** 500 Rials per share (confirmed by `codal/38803.pdf`).
2. **Capital increase ratio:** 6,075,000,000 → 12,000,000,000 shares (×1.9753).
3. **Sources of capital increase** (from `codal/40620.pdf`):
   - Retained earnings: 1,410,000 million Rials
   - Reserves: 2,721,000 million Rials
   - Receivables & cash: 1,794,000 million Rials
   - **Total: 5,925,000 million Rials**
4. **TSETMC adjustment (2011-04-23):** 7,252 → 3,820 Rials
   - This matches the capital increase **only** (K ≈ 301 Rials, no cash dividend applied).
   - `pClosing` in the daily series excludes the cash dividend.
5. **Market reopening (2011-04-26):** 3,569 Rials
   - Theoretical price after cash dividend: 3,567.7 Rials
   - Difference: ~1.3 Rials (tick-level volatility).

## Reproducibility

Scripts in `scripts/research/iran-equities/adjustment/`:
- `reconcile_vaghdir.py` — match adjustment events with share changes
- `derive_K_and_verify.py` — derive K and reconstruct theoretical prices
- `scan_price_jumps.py` — detect price jumps > 20%

## Scope Limitations

- This evidence covers **one symbol (وغدیر)** and **one event year (2011)**.
- It does **not** approve investment ranking, backtesting, or production use.
- فولاد and پارسیان remain to be documented.
- Three scanned PDFs (`38805_att0.pdf`, `40620_att0.pdf`, `41761_att0.pdf`)
  are image-only and require OCR for full text extraction.
