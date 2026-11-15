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

## Newly verified event-feed identity issue

The exact ticker record has primary InsCode 9481703061634967. Its 18 price-adjust rows use InsCode 9481703061634968, which is not present in the exact record's primary or insCode2/3/4 fields. Those price-adjust rows are retained but identity-quarantined. The 9 share-change rows use the primary InsCode. No alias is inferred and no provider price-adjust factor is accepted from this match alone.
