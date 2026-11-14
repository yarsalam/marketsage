# Iranian equity adjustment evidence store

Status: research-only, evidence collection and validation; no factor or series is approved by this directory.

## Instruments
- `vaghdir/` — وغدیر
- `foolad/` — فولاد
- `parsian/` — پارسیان

## Per-symbol layout
Each symbol directory keeps these evidence classes separate:
- `raw/`: immutable TSETMC/TSE Client source payloads and daily history snapshots
- `codal/`: original CODAL notices, attachments, amendments and extracted text
- `other_sources/`: issuer notices, official publications, exchange notices and clearly-labelled secondary locators
- `calculations/`: reproducible event-term calculations and factor direction/units
- `outputs/`: candidate price-basis and total-return series, never overwriting raw series
- `validation/`: manifests, hashes, coverage, chart comparisons and test reports

Large raw datasets and binary CODAL attachments should remain in the owner-controlled data store until a reviewed storage policy exists. This Git directory contains indexes, manifests, source references and reproducible code; do not commit secrets or overwrite raw snapshots.

## Source-of-truth boundary
A provider adjustment row or a price gap is a discovery lead, not proof of event type or terms. CODAL/issuer primary evidence establishes economic terms; actual market records establish the first affected trading session; calculations are independent; provider and external chart data are reconciliation targets, not economic authority.

Keep separate:
1. raw market prices;
2. corporate-action price-basis adjusted prices;
3. total-return series.

Never apply an unresolved factor. Unknown, conflicting or incomplete events must remain quarantined.

## Local source store
Previously recorded owner-side source root:
`/home/nima/marketsage-data/tsetmc-three-adjusted`

This local path is not automatically available to GitHub or this remote session. The manifests in each symbol folder record expected source artifacts and their current evidence state. Import data only with SHA-256, retrieval metadata and original filenames preserved.

## Acceptance
An interval can be considered only after security identity, event terms, chronology/effective session, independent calculation, provider reconciliation and official-chart comparison have all passed. This directory does not itself approve investment use, scoring, ranking, backtesting or production.
