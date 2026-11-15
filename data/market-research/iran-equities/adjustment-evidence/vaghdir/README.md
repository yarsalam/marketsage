# وغدیر — adjustment evidence

Instrument slug: `vaghdir`  
Local evidence root: `/home/nima/marketsage-data/tsetmc-three-adjusted`

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

## Known evidence leads — not blanket approval
- 2011 mixed-event reconstruction exists in the research notebook. The provider tuple relationship remains unresolved; a 23-Apr stale/no-trade 3,820 observation must not be confused with the 26-Apr traded close of 3,569.
- Candidate provider dates: 2012-02-20 and 2013-02-27 (cash-distribution candidates, terms not verified); 2012-12-08 and 2013-04-09 (capital-increase candidates, original EGM terms/effective sessions still required).
- 2026-04-18 provider price-reference row: 15,070 to 13,570 (difference 1,500 Rial; ratio 0.9004644990). Treat as a provider-confirmed price-reference observation and dividend candidate only. Do not label the final DPS or apply a factor until the original CODAL resolution and exact first affected trading session are verified.
- CODAL documents already identified locally: `155153_dividend_schedule_amended.html`, `155748_agm_attachment.html`, `156803_agm_summary.html`, plus `155748.html` and `document_extraction_report.json`. These filenames alone do not establish the event terms; inspect issuer identity, attachment contents, amendments and chronology.

## Rule
No historical series is approved for this symbol by this folder. Keep each event's provider ratio, terms-based ratio, effective date and relationship status in separate fields.

## Newly verified event-feed identity issue

The exact ticker record has primary InsCode 26014913469567886. Its 25 price-adjust rows use InsCode 26014913469567890, which is not present in the exact record's primary or insCode2/3/4 fields. Those price-adjust rows are retained but identity-quarantined. The 7 share-change rows use the primary InsCode. No alias is inferred and no provider price-adjust factor is accepted from this match alone.
