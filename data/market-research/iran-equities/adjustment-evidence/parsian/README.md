# پارسیان — adjustment evidence

Instrument slug: `parsian`  
Local evidence root: `/home/nima/marketsage-data/tsetmc-three-adjusted`

## Expected source groups
- `raw_provider_snapshots/parsian_price_adjust_raw.json`
- `raw_provider_snapshots/parsian_share_change_raw.json`
- `raw_provider_snapshots/parsian_daily_raw.json`
- `tse_client_validation/tse_client_adjust_info_events.json`
- `official_chart_validation/`
- `adjustment_factor_diagnostics/`
- `three_symbol_audit_runs/20261112T194429Z/`

## Existing discovery evidence
- Local candidate daily history: 3,866 rows.
- Preserved event feed: 18 price-adjust rows and 9 share-change rows.
- TSE Client diagnostic previously reported 12/18 price-adjust and 7/9 share-change matches in a ±7-day window. These are discovery diagnostics only; exact row-level identity and chronology remain to be reconciled.
- A prior diagnostic isolated at least one price-adjust-only candidate dated 2019, but the exact event terms, effective session and final factor must be read from the original raw payload and issuer documents before it is added as an event.

No factor or adjusted interval is accepted. Preserve unresolved events and quarantine affected intervals.

## Event-feed identity verification — 2026-11-15

The exact ticker record has primary InsCode 9481703061634967. All 18 raw JSON price-adjust rows and all 9 share-change rows contain this exact decimal token. A prior apparent mismatch was caused by parsing the large InsCode as a JavaScript Number, which rounded it. The raw source file was correct; no price-adjust rows require identity quarantine. Keep InsCode values as strings or BigInt in JavaScript clients.
