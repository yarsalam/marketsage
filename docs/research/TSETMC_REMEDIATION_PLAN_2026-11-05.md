# TSETMC remediation plan — 2026-11-05

## Current baseline

Workflow #41914919555 completed successfully in offline, memory-bounded mode. It processed 47 candidates: 47 quarantined, zero research-eligible, zero feature/forward-label rows. Seven discovery identity conflicts were recorded; the run reported zero input-file read errors. Pipeline v1.1.0 misleadingly counted these conflicts under `INPUT_OR_PARSER_ERROR`. This is operational success, not source acceptance.

## Next stage: evidence and data remediation

Do not rerun the unchanged corpus or weaken acceptance thresholds. Keep the original staged dataset read-only and preserve its hashes.

### 1. Reconcile the seven discovery identity conflicts
The successful run's preflight reports `identity_conflict_count=7` and `input_file_read_errors=0`. The pipeline code shows that these are conflicts between history-row `insCode`/ISIN values and sibling instrument-search/crosswalk metadata, not seven unreadable files. Inspect the seven records locally; publish only aggregate reason codes and pseudonymous references. Compare each mapping with an authoritative instrument master and historical symbol/venue mapping. Do not auto-select, fuzzy-match or overwrite the raw history. PR #39 merged the classification correction into the integration branch at `1dc6894c0823f6ffe77d27fd866576f5115a042c` after all five required job types passed. The corrected pipeline is v1.1.1; the seven identity conflicts themselves remain unresolved.

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

Start with a local-only review of the seven discovery identity conflicts and v2 crosswalk coverage. Report aggregate conflict categories and reviewed resolution status only. Do not upload raw rows, prices, CSVs or local paths. Investigate genuine parser defects separately only if the local evidence shows actual file/schema/date/field parsing failures.

## Owner/source evidence required

Engineering cannot fabricate:
- applicable TSETMC rights and retention terms;
- an authoritative instrument master;
- a lawful independent price/volume reference;
- an accountable reviewer for rights and semantic attestations.

If these cannot be obtained, keep TSETMC quarantined and evaluate another permissioned source. Owner actions and acceptance criteria are tracked in [Issue #40](https://github.com/yarsalam/marketsage/issues/40).

## Safety boundary

No scoring, ranking, calibrated probabilities, strategy tuning, backtest, production deployment, broker access, trading or capital allocation. No live polling or scheduled local Runner. PR #6 remains open and must not be merged without separate explicit owner approval.
