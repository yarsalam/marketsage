# TSETMC remediation plan — 2026-11-05

## Current baseline

Workflow #41914919555 completed successfully in offline, memory-bounded mode. It processed 47 candidates: 47 quarantined, zero research-eligible, zero feature/forward-label rows. Seven parser/input errors were recorded. This is operational success, not source acceptance.

## Next stage: evidence and data remediation

Do not rerun the unchanged corpus or weaken acceptance thresholds. Keep the original staged dataset read-only and preserve its hashes.

### 1. Diagnose the seven parser/input errors
Inspect records locally; publish only aggregate reason codes. Distinguish malformed source data, schema drift, encoding/date defects, missing fields, duplicate/order defects, and parser bugs. Add deterministic fixtures and tests for each distinct parser-caused defect. Preserve malformed originals; any corrected dataset must be a separately versioned derivative with lineage.

### 2. Complete instrument identity
For each proposed candidate, map to an authoritative instrument master: stable ID, issuer/fund, instrument type, exchange/board, symbol history, effective dates, suspensions and delisting state. Every mapping needs an evidence reference and reviewer. Fuzzy symbol matching is not proof.

### 3. Establish source rights
Record the actual applicable terms and evidence for collection, historical storage, internal research, derived use and redistribution. Viewing permission is not assumed to grant retention or commercial-use permission. Unverified rights means exclusion.

### 4. Verify data semantics and corporate actions
Establish Rial/Toman, currency, scale, share/lot, volume and turnover units. Distinguish raw close, last trade, adjusted close, NAV, distributions and total return. Obtain complete price-adjustment and share-change events with effective dates, values, corrections and lineage. Never infer missing semantics or modify raw inputs.

### 5. Independent reconciliation
Select a lawful independent reference. Predeclare sample and tolerances. Compare dates, prices, volume, turnover, missing sessions, suspensions and corporate-action effects. Record discrepancies; do not tune tolerances to force a pass.

### 6. Point-in-time and history quality
Verify calendar, missing intervals, duplicates, stale values, publication/availability timestamps, revisions, delisted instruments and historical tradability. No observation may appear in replay before it was actually available. Check six-month history only after the prior evidence is complete.

### 7. Reprocess
Only after evidence-backed fixes, stage a new immutable dataset version, verify its manifest/hashes, run the existing manual-only workflow and compare decisions against the baseline. Independently review every candidate changing from quarantine to eligible.

## Immediate engineering action

Start with a local-only sanitized diagnostic of the seven parser/input errors and crosswalk coverage. Report counts by reason code and classify each issue as parser-caused or source/evidence-caused. Do not upload raw rows, prices, CSVs or local paths. Implement only proven parser fixes with regression tests.

## Owner/source evidence required

Engineering cannot fabricate:
- applicable TSETMC rights and retention terms;
- an authoritative instrument master;
- a lawful independent price/volume reference;
- an accountable reviewer for rights and semantic attestations.

If these cannot be obtained, keep TSETMC quarantined and evaluate another permissioned source.

## Safety boundary

No scoring, ranking, calibrated probabilities, strategy tuning, backtest, production deployment, broker access, trading or capital allocation. No live polling or scheduled local Runner. PR #6 remains open and must not be merged without separate explicit owner approval.
