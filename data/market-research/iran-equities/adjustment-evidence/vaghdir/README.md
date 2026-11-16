# وغدیر — adjustment evidence

**Status:** EVIDENCE_SUPPORTED — FINAL REPOSITORY ACCEPTANCE PENDING
**InsCode:** 26014913469567886
**Symbol:** وغدیر

Instrument slug: `vaghdir`
Local evidence root: `/home/nima/marketsage-data/tsetmc-three-adjusted`

## Purpose

This directory contains reproducible evidence for the 2011 corporate actions
of Vaghdir (وغدیر), specifically the cash dividend and capital increase that
caused the TSETMC price adjustment on 2011-04-23.

## Expected source groups

- `raw_provider_snapshots/vaghdir_price_adjust_raw.json`
- `raw_provider_snapshots/vaghdir_share_change_raw.json`
- `raw_provider_snapshots/vaghdir_daily_raw.json`
- `tse_client_validation/tse_client_adjust_info_events.json`
- `official_chart_validation/` (raw and adjusted official chart captures and comparison)
- `codal_vaghdir_dividend_20261114/`
- `codal_vaghdir_primary_docs_20261114/`
- `adjustment_factor_diagnostics/`
- `three_symbol_audit_runs/20261112T194429Z/`

## Evidence files added (2026-11-16)

### `codal/` — Official CODAL announcements

| File | TracingNo | Date (Jalali) | What it proves |
|------|-----------|---------------|----------------|
| `38803.pdf` | 38803 | 1390/02/04 | **DPS = 500 Rials** (مجمع عادی سالیانه) |
| `40620.pdf` | 40620 | 1390/02/15 | **Capital increase**: 6,075,000 → 12,000,000 million Rials, split: retained earnings 1,410,000 / reserves 2,721,000 / receivables+cash 1,794,000 |
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

## Key Findings (2011 only)

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

## Known evidence leads — not blanket approval

- 2011 mixed-event reconstruction exists in the research notebook. The provider tuple relationship remains unresolved; a 23-Apr stale/no-trade 3,820 observation must not be confused with the 26-Apr traded close of 3,569.
- Candidate provider dates: 2012-02-20 and 2013-02-27 (cash-distribution candidates, terms not verified); 2012-12-08 and 2013-04-09 (capital-increase candidates, original EGM terms/effective sessions still required).
- 2026-04-18 provider price-reference row: 15,070 to 13,570 (difference 1,500 Rial; ratio 0.9004644990). Treat as a provider-confirmed price-reference observation and dividend candidate only. Do not label the final DPS or apply a factor until the original CODAL resolution and exact first affected trading session are verified.
- CODAL documents already identified locally: `155153_dividend_schedule_amended.html`, `155748_agm_attachment.html`, `156803_agm_summary.html`, plus `155748.html` and `document_extraction_report.json`. These filenames alone do not establish the event terms; inspect issuer identity, attachment contents, amendments and chronology.

## Rule

No historical series is approved for this symbol by this folder.
Keep each event's provider ratio, terms-based ratio, effective date
and relationship status in separate fields.

## Event-feed identity verification — 2026-11-15

The exact ticker record has primary InsCode 26014913469567886. All 25 raw JSON
price-adjust rows and all 7 share-change rows contain this exact decimal token.
A prior apparent mismatch was caused by parsing the large InsCode as a
JavaScript Number, which rounded it. The raw source file was correct; no
price-adjust rows require identity quarantine. Keep InsCode values as strings
or BigInt in JavaScript clients.

## Reproducibility

Scripts in `scripts/research/iran-equities/adjustment/`:
- `reconcile_vaghdir.py` — match adjustment events with share changes
- `derive_K_and_verify.py` — derive K and reconstruct theoretical prices
- `scan_price_jumps.py` — detect price jumps > 20%

## Scope Limitations

- This evidence covers **one symbol (وغدیر)** and **one event year (2011)**.
- It does **not** approve investment ranking, backtesting, or production use.
- فولاد and پارسیان remain to be documented.
