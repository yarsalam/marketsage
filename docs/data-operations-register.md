# MarketSage Data Operations Register

**Register date:** 2026-10-23  
**Purpose:** One durable record of what has been collected, where it lives, what was actually audited, and what is still unapproved. Update this register after a collection/audit run; do not restart completed work just to rediscover its status.

## Non-negotiable workflow

1. **One local data root:** `$HOME/marketsage-data/`. New raw captures, derived candidates, run reports, hashes, and local indexes belong under this root. Existing sources may be copied into it after integrity verification; never delete the original as part of centralization.
2. **Git stores control-plane metadata, not market data:** commit source contracts, schemas, scripts, small sanitized fixtures, this register, and status summaries. Do not commit raw market archives, vendor exports, API keys, or bulky generated rows unless licensing and repository policy explicitly permit them.
3. **Raw is immutable:** collection writes a dated source snapshot; normalization writes to a separate path; audits write to a new run directory. No overwrite/repair of the source snapshot.
4. **One run, one durable report:** record run ID, code commit, input/output paths, hashes, row counts, quality blockers, and acceptance state. Reuse an existing report when neither the inputs nor logic changed.
5. **Status words have distinct meanings:** *collected* means bytes were retrieved; *audited* means checks were run; *research-accepted* requires reviewed evidence and reconciled semantics; *scoring-accepted* requires explicit approval. Reachability or a passing fixture test is not source acceptance.
6. **Cross-asset integration is a common schema and registry, not blindly concatenating unlike series.** Keep source-native raw fields, and map supported values into shared tables with units, currency, observation time, retrieval time, calendar, adjusted/raw semantics, and provenance. Unknown values stay unknown.

## Canonical local layout

The consolidation utility is intended to place/keep data as follows:

```text
$HOME/marketsage-data/
  tsetmc/
    tsetmc_history_pipeline/      # copy of the existing corpus; same internal layout
  tsetmc-acceptance/
    run_<UTC timestamp>/          # already-used offline acceptance reports
  multi-asset-collection/
    run_<collection timestamp>/   # persisted copy of the collection currently in /tmp
  streamdata/
    source_exports/                # optional local copy of original vendor exports
  registry/
    local_data_index.json          # generated locally; paths, counts, hashes and run references
    manifests/                     # generated local per-file integrity manifests
```

The raw-source directory still lives in the legacy repository path until the one-time copy is executed. The multi-asset run under `/tmp` is also not yet considered durably stored. The centralization utility must be idempotent: matching files are skipped; a different file at an existing destination is a hard conflict, never silently overwritten. It must not make network requests.

## Inventory and current state

### A. TSETMC historical prices and corporate actions

| Field | Recorded state |
|---|---|
| Existing corpus | `~/projects/marketsage-acceptance/data/source_snapshots/tsetmc_history_pipeline/` |
| Raw-history subdirectory | `.../tsetmc_history_pipeline/raw/<ISIN>/` |
| Existing adjusted-candidate path | `.../tsetmc_history_pipeline/corpus_reconciliation/adjusted_candidates_research_only/<ISIN>.adjusted_candidate.csv` |
| Latest integrated local run | `~/marketsage-data/tsetmc-acceptance/run_20261023T095517508480Z` |
| Run ID | `run_20261023T095517508480Z` |
| Discovered instruments in this run | 47 |
| Decision result | 47 `needs_reprocessing`; 0 research-eligible; 47 quarantined; 47 queued |
| Research features / six-month labels | 0 / 0 |
| Network / raw-input behavior | No network requests; original raw inputs not overwritten |
| Scoring / backtest | Disabled / not run |

**Important discrepancy to resolve in code, not by repeating this same report:** this run discovered 47 instruments, while earlier project notes described a much larger historical corpus. The run also reports zero adjusted-chart coverage in the shown instrument decisions, and `invalid_numeric_field_rows` can be several times the history-row count (example observed: 237 against 79 rows). The existing adjusted-candidate files therefore need a path/identity/parse coverage audit, and the optional-field counter needs interpretation from its field-level reason codes. Do not conclude the entire source archive is bad from these counters, and do not treat this run as acceptance of the full corpus.

Primary missing acceptance evidence remains: traceable instrument identity; documented usage/storage/reuse rights; explicit price semantics and units; independent reconciliation; complete corporate-action evidence; and verified history/chart coverage. Do not make synthetic evidence or flip eligibility flags merely to get rows into the feature table.

### B. Multi-asset collection (Iran and global candidate sources)

| Field | Recorded state |
|---|---|
| Latest known collection output | `/tmp/marketsage-multi-asset-collection/run_20261022T185104629734Z` |
| Known collection summary | 17 source attempts; 13 accessible; 4 failures |
| Market rows | 7,637 across 8 series |
| News | 180 unique candidate items |
| TGJU | 30 gold rows and 30 coin rows |
| Free-market FX | No rows in that run |
| Yahoo Finance | Five-year candidates for six global/crypto series |
| Binance | HTTP 451 in one probe; not usable evidence of data acceptance |
| Nerkhsanj | Metadata probe reported 28 series / 91,245 count; units, history semantics, licensing and usability remain unaccepted |
| Durability | Output was under `/tmp`; persist it under `$HOME/marketsage-data/multi-asset-collection/` before relying on it as the durable record |

**Interpretation:** 13 accessible sources means a response was obtained, not that all 13 produced comparable, legally reusable historical prices. Gold/coin candidate rows exist; free FX is still a gap in the recorded run. Do not mark these sources “fixed” or accepted without a stored run report and per-series units, timestamps, history depth and reconciliation evidence.

### C. Seller-provided StreamData export audit — PR #11

PR #11, **“Audit and normalize seller-provided StreamData CSV exports,”** is merged into `feature/iran-live-data-dashboard` (2026-10-19). The PR records a local-only audit and candidate exporter; raw vendor files were not committed.

Recorded rows in the supplied files: AYAR 123; BTCUSDT 184; 18K gold 184; free-market USD 176, captured from 2026-04-19 to 2026-10-19. The audit found no duplicate dates or source-order inversions, flagged one AYAR OHLC inconsistency on 2026-10-14 (close exceeded high), and left AYAR clock/time-zone semantics unresolved. These four datasets are **audited candidates, not research/scoring accepted**. Their original local file paths were not captured in this Git record; keep the exports and the PR's audit/candidate outputs under the single local data root.

### D. Provider and source-gate findings

- TSETMC and CODAL had previously been reachable in bounded probes, but their evidence gates were not passed; response reachability is not data acceptance.
- FRED/ALFRED credentials were previously missing; GDELT previously returned HTTP 429. Respect the existing retry budget instead of repeating probes without a changed hypothesis.
- Tindex remains optional and credential/quota-dependent; keep its fail-closed restrictions in force.
- This register does not approve any source for production scoring.

## Next work, in order

1. **Centralize existing artifacts once** using the checked-in local utility: copy the TSETMC corpus into the canonical root, persist the known multi-asset run from `/tmp`, and generate a local index plus per-file SHA-256 manifests. The utility must preserve the original source paths and fail on content conflicts.
2. **Correct the TSETMC discovery/coverage defects** by tracing why this run finds 47 instruments and does not match the existing adjusted candidates; inspect field-level invalid-number reasons. Reuse the existing run as the reproduction fixture. Do not ask the owner to rerun the same diagnostic pipeline before a code change.
3. **Create a shared normalized observation contract** for all assets, retaining source-native raw values and explicit `unit`, `currency`, `observed_at`, `retrieved_at`, `adjustment_semantics`, `source_id`, and quality/provenance fields. Do not union series until compatible semantics have been established.
4. **Make one bounded validation run after a relevant code/data change.** Record the new code SHA and run ID here; do not run an endless succession of overlapping tests or live probes.
5. Only after provenance, units, licensing, adjusted history and corporate actions are reviewed should the research gate advance. Scoring and backtesting remain disabled until separate explicit acceptance.

## Update protocol

Every new collection or audit updates this document with: exact source/run ID, durable local path, code commit, row counts, start/end date, structural findings, unresolved contract/licensing checks, and status. Do not write “done,” “fixed,” or “accepted” when only the request succeeded or the test fixture passed.
