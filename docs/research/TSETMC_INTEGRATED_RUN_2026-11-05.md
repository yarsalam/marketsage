# TSETMC integrated local run — 2026-11-05

## Execution record

- Workflow: `.github/workflows/local-tsetmc-integrated-acceptance.yml`
- Run: [41914919555](https://github.com/yarsalam/marketsage/actions/runs/41914919555)
- Event/ref: manually dispatched on `main`
- Executed commit: `554fe2200ccb3a523442b0e241e81a748becfa44`
- Runner: `marketsage-local-01`
- Job conclusion: success
- Pipeline status: `COMPLETED_CANDIDATE_ONLY`
- Pipeline version: `1.1.0`

The memory-bounded execution completed in two batches (32 and 15 candidates). The resource preflight and per-batch resource rechecks passed. The run created private local outputs, verified output-manifest file hashes, made no provider/network requests, did not overwrite raw inputs, and did not upload artifacts.

## Sanitized aggregate findings

| Measure | Result |
|---|---:|
| Discovered instruments | 47 |
| Unique input files | 95 |
| Input read errors | 0 |
| Candidate decision rows | 47 |
| Quarantined candidates | 47 |
| Research-eligible candidates | 0 |
| Eligible for scoring | No |
| Eligible for backtest | No |
| Backtest run/approved | No |
| Forward-label rows | 0 |
| Research-feature rows | 0 |

All 47 candidates have unverified identity evidence references and unrecognized price-input semantics. The aggregate quarantine reasons include:

- Usage rights not verified or evidence reference missing: 47
- Instrument identity evidence reference missing: 47
- Price semantics/units not verified or evidence reference missing: 47
- Price input not explicitly identified as raw/unadjusted: 47
- Independent reconciliation not passed or evidence reference missing: 47
- Corporate-action completeness not verified or evidence reference missing: 47
- Corporate-action event payload missing: 47
- Adjusted coverage below triage threshold: 47
- Raw-history structural defects: 47
- History too short for six-month research: 35
- Discovery identity conflicts: 7 (pipeline v1.1.0 also mislabeled these as `INPUT_OR_PARSER_ERROR`; the run reported `input_file_read_errors=0`).

No candidate-level data, raw prices, local paths, or private output files are included in this record.

## Interpretation

This run validates the operational path for bounded, offline local candidate processing. It does **not** validate TSETMC as an accepted investment data source. The 47 candidates remain quarantined and must not enter scoring, ranking, probability calibration, or backtesting.

The dominant blockers are evidence and data completeness, not Runner execution:

1. Obtain documented source-use/storage rights and preserve the exact applicable terms.
2. Supply a reviewed instrument identity crosswalk with evidence references and historical symbol/venue mapping.
3. Explicitly establish price and volume units, currency, and raw versus adjusted/total-return semantics.
4. Supply complete price-adjustment and share-change/corporate-action event payloads with auditable lineage.
5. Complete lawful independent reconciliation against a separate reference.
6. Resolve adjusted-history coverage, six-month minimum history, structural defects, and the seven discovery identity conflicts; do not assume they are parser failures.
7. Establish calendar, publication/availability time, revisions, point-in-time tradability, and survivorship controls before any strategy evaluation.

Do not solve these failures by weakening thresholds, auto-adjusting prices, inferring identities, fabricating evidence references, or promoting unknown values to pass. Reprocessing should occur only after the underlying source/evidence files are corrected and independently reviewed.

## Safety and release posture

Research-only. No source approval, investment scoring/ranking, calibrated probabilities, backtest approval, production deployment, broker access, trading, or capital allocation is authorized by this run. PR #6 remains open and must not be merged without separate explicit owner approval.

## Discovery classification correction

The workflow log for run [41914919555](https://github.com/yarsalam/marketsage/actions/runs/41914919555) reports `discovery.identity_conflict_count=7` and `input_file_read_errors=0`. The seven generic `INPUT_OR_PARSER_ERROR` flags arose because pipeline v1.1.0 appended discovery identity conflicts to the same error list used for payload/parser failures. The source code identifies the specific condition as `insCode_conflicts_with_sibling_search_metadata`.

[PR #39](https://github.com/yarsalam/marketsage/pull/39) merged the separate reason codes and remediation stages into the integration branch at `1dc6894c0823f6ffe77d27fd866576f5115a042c` after five CI job types passed in run `42050542208`. The historical run remains a v1.1.0 result; the corrected pipeline is v1.1.1. The correction does not resolve the seven mappings. They still require local review against an authoritative instrument master and remain quarantined. See [owner action Issue #40](https://github.com/yarsalam/marketsage/issues/40).
