# فولاد — adjustment evidence

Instrument slug: `foolad`  
Local evidence root: `/home/nima/marketsage-data/tsetmc-three-adjusted`

## Expected source groups
- `raw_provider_snapshots/foolad_price_adjust_raw.json`
- `raw_provider_snapshots/foolad_share_change_raw.json`
- `raw_provider_snapshots/foolad_daily_raw.json`
- `tse_client_validation/tse_client_adjust_info_events.json`
- `official_chart_validation/`
- `adjustment_factor_diagnostics/`
- `three_symbol_audit_runs/20261112T194429Z/`

## Existing discovery evidence
- Local candidate daily history: 4,680 rows.
- Preserved event feed: 23 price-adjust rows and 12 share-change rows.
- TSE Client diagnostic previously reported 23/23 and 12/12 matches within a ±7-day discovery window. This is not exact row-level proof and must not be used as an event join rule.
- Public yfinance-ir fixtures were found for the same Foulad InsCode and the same 23/12 event counts. This is instrument/count/schema overlap only; no hash-level comparison against owner raw files has been completed.
- Seven share-change rows were unpaired under a ±3-day diagnostic. They remain unresolved; do not classify every unmatched share increase as a bonus issue.
- A public extractor notes a 2026-03-30 share-count change from 1.5T to 1.935T and suggests price-discontinuity inference. This is a discovery lead only; CODAL terms and effective session are required.

No factor or adjusted interval is accepted. Reconcile raw hashes, exact row identifiers, original CODAL terms and official chart fields before calculation.

## Event-feed identity verification — 2026-11-15

The exact ticker record has primary InsCode 46348559193224090. All 23 raw JSON price-adjust rows and all 12 share-change rows contain this exact decimal token. This verifies feed-level identity only; issuer terms, first affected sessions and adjustment factors still require independent evidence. Keep InsCode values as strings or BigInt in JavaScript clients.
