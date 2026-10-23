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

## One-time local consolidation command

After the change reaches your Git remote, run this once from a terminal. It only fetches the script file into `~/.local/share`; it does **not** check out a branch or touch your working-tree changes. The script itself is offline.

```bash
set -euo pipefail
REPO="$HOME/projects/marketsage-acceptance"
INSTALL="$HOME/.local/share/marketsage/centralize_market_data.py"

mkdir -p "$(dirname "$INSTALL")"
git -C "$REPO" fetch origin feature/iran-live-data-dashboard
git -C "$REPO" show "FETCH_HEAD:user/analysis-engine/scripts/centralize_market_data.py" > "$INSTALL"
python3 "$INSTALL" --repo-root "$REPO" --data-root "$HOME/marketsage-data"
```

This copies the existing TSETMC corpus to `~/marketsage-data/tsetmc/tsetmc_history_pipeline/`, persists the known multi-asset run from `/tmp` if it is still present, records the existing TSETMC acceptance report, and generates `registry/local_data_index.json` plus local per-file SHA-256 manifests. It **does not merge different instruments into a misleading single CSV**; a common canonical registry/schema comes first, and normalized observations remain distinct where their units, time semantics, or adjustment status are not yet comparable. The script never deletes its source. If the old multi-asset folder has already disappeared from `/tmp`, the index records that fact rather than pretending the output was persisted.

## Downloads tool triage (2026-10-23)

The owner supplied a Downloads listing and the relevant Python files for static review. The selected canonical TSETMC sequence is:
1. `adjust_pipeline_v025.py` (v0.2.5): newest adjustment/evidence engine. Its v0.2.5 change makes the exact ISIN → insCode map from preferred `instrument_details.jsonl` authoritative, correcting the earlier false-ambiguity problem caused by weak symbol/name aliases. It operates offline and keeps generated adjusted series as unapproved candidates.
2. `audit_tsetmc_forensic_v3.py`: whole-corpus read-only raw/normalized/event-edge forensic audit with calendar/gap diagnostics and placebo controls.
3. `build_tsetmc_research_candidates_v1_1.py`: newest candidate builder; unlike v1.0 it can retain a valid close-only candidate when OHLC is not eligible, without fabricating OHLC.
4. `run_tsetmc_research_pipeline_v1_1.py`: orchestrates inventory, forensic re-use/rebuild, candidate build and validation.
5. `audit_tsetmc_research_candidate_suite_v1.py`: final QA once after the complete research-pipeline run.
   
**Known mismatch in the downloaded v1.1 orchestrator:** its default candidate helper lookup still names `build_tsetmc_research_candidates_v1.py`. Always pass the explicit v1.1 builder path, e.g. `--candidate-script ~/Downloads/build_tsetmc_research_candidates_v1_1.py`. The orchestration script's prior-run auto-discovery also doesn't explicitly list `/tmp/marketsage-tsetmc-adjustments`; supply the exact prior v0.2.5 run directory with `--prior-run` if that is where the matching adjustment result lives. Before reuse, validate that its `input_manifest.csv` hashes match the current normalized history and event inputs.

Use `audit_tsetmc_raw_normalization_v2.py`, not the earlier normalization audit: v2 adds the raw-source date key `dEvenRLC`. Keep `marketsage_multi_asset_bootstrap_v1.py` as the collector but do not rerun it just to reproduce the already-recorded run under `/tmp/marketsage-multi-asset-collection/run_20261022T185104629734Z`. Use existing `reconcile_tsetmc_corpus.py` results unless relevant inputs change.

Treat these files as superseded for future runs: `adjust_pipeline.py` v0.2.0, `adjust_pipeline_v021.py`–`adjust_pipeline_v024.py`, `build_tsetmc_research_candidates_v1.py`, `run_tsetmc_research_pipeline.py` v1.0, and `audit_tsetmc_raw_normalization.py`. `patch_tsetmc_corpus_semantics.py` modifies source code and must not be reapplied without reviewing its diff/backup. The older/parallel `stage_tsetmc_corpus_acceptance.py` is not part of the canonical sequence because it overlaps the current decision/queue outputs.

The recorded integrated runner `run_20261023T095517508480Z` is **not the full-corpus acceptance result**: it found only 47 instruments, quarantined all 47, and produced zero research features / labels, while previous corpus inventory notes record approximately 1,220 normalized histories. Do not rerun that same discovery path. Diagnose/fix its instrument coverage only if this runner is retained; otherwise use the existing full-corpus v0.2.5 → forensic-v3 → candidate-v1.1 workflow above.

The ZIPs and patches in the owner's listing are archival-only unless their exact content is inspected and a specific missing change is identified. Do not unpack/run overlapping package versions or apply successive patch files blindly.

### Previously generated full-corpus candidate output — reuse, do not regenerate blindly

Earlier project notes record a conservative TSETMC candidate builder producing **128 adjusted candidate series, 167,912 research-feature rows, and 151,784 forward-label rows**. Those outputs remain research-only. The remembered prior output root is `/tmp/marketsage-tsetmc-adjustments`; the exact run child and its manifest hashes must be preserved by the local centralization utility before that temporary directory is lost.

This prior work is why the 47-instrument run from `run_tsetmc_acceptance_pipeline.py` must not trigger another adjustment cycle. The 47-run is a separate incomplete discovery pass. The immediate task is to **preserve/index existing output and compare its run/input hashes**, not automatically re-run v0.2.5, forensic v3, builder v1.1, or the final QA suite. Re-run any of those stages only if no completed output exists or the recorded input/code hashes prove it stale. A candidate output's presence does not grant source licensing/semantics approval or enable investment scoring.

## Verified local index result (owner output, 2026-10-23 16:04:08 UTC)

The owner ran the one-time centralizer and inspected `registry/local_data_index.json`. This is the authoritative local snapshot as of that run:

- Canonical TSETMC corpus: source `~/projects/marketsage-acceptance/data/source_snapshots/tsetmc_history_pipeline`; destination `~/marketsage-data/tsetmc/tsetmc_history_pipeline`; **8,904 files, 1,353,906,530 bytes; 8,904 files already present with matching hashes; no new copies needed in that run**. Central storage for the TSETMC source corpus is complete.
- Latest integrated acceptance report is preserved under `~/marketsage-data/tsetmc-acceptance/run_20261023T095517508480Z` and indexed with 17 output files/hashes. It remains a 47-instrument partial discovery result (47 queued, 0 eligible), not a full-corpus acceptance result.
- The expected previous outputs under `/tmp/marketsage-tsetmc-adjustments`, `/tmp/marketsage-tsetmc-adjust-v025`, `/tmp/marketsage-tsetmc-research-pipeline*`, and the prior multi-asset run under `/tmp/marketsage-multi-asset-collection/run_20261022T185104629734Z` were absent when indexed. The index correctly records them as `source_missing`; it did not re-download them.
- Therefore: **do not rerun the 47-instrument acceptance runner**. TSETMC raw corpus storage is complete; existing adjusted-candidate files inside the corpus must be counted/reused before deciding whether any adjustment stage needs a one-time rebuild. The missing prior full-pipeline output directory is not, by itself, proof that all derived data are lost.
- The earlier multi-asset result (7,637 rows / 8 series and 180 unique news items, from previous run notes) is not present at its known temporary path and has not been durably copied. Check local archive/source files for recoverable result data; if no underlying outputs exist elsewhere, that dataset will need one new collector run directed directly at the canonical data root. This is collection recovery, not a diagnostic-test loop.
- Decision order is now: (1) reuse the central TSETMC corpus and its in-corpus adjustment candidates; (2) recover an existing full-corpus adjustment/research run from other local locations if one exists; (3) only if no compatible run output exists, perform one full-corpus v0.2.5/forensic-v3/candidate-v1.1 pass with output under `~/marketsage-data/tsetmc-research/`; (4) recover existing multi-asset output or, if absent, collect once into `~/marketsage-data/multi-asset-collection/`. After those state transitions are recorded, do not repeat the process without changed inputs or code.

## Follow-up interpretation of the recovery inventory (owner output)

- The full-corpus legacy report at `corpus_acceptance_run_20261022T064551Z` covers **1,220 instruments**, 7,032 event-comparison rows and 9,978 event-inventory rows. Decisions: 1,080 `KEEP_RAW_QUARANTINE_ADJUSTMENT`, 47 `REPROCESS`, 93 `QUARANTINE`. It produced 0 candidate-feature rows and 0 forward labels; its research-eligible manifest is empty. This was an offline triage report, not completed price-adjustment acceptance.
- The 14 files under `corpus_reconciliation/adjusted_candidates_research_only/` contain 51,872 rows. Their actual column is `candidate_adjusted_close` (also a plain `close` column exists); the initial recovery-inventory counter only checked other column aliases and therefore incorrectly printed `close rows=0`. That counter must not be used to infer the price values are absent.
- The v2 corpus report lists 93 candidate CSV files, which differs from the 14 files in the specifically named adjusted-candidate subdirectory. Treat these as different discovery scopes until the exact file inventory and ISIN coverage are compared. Do not infer complete 1,220-instrument adjusted coverage from either number.
- Next allowed work: one bounded **full-corpus research run** using the downloaded v0.2.5 adjustment runner plus forensic-v3 and candidate-builder-v1.1, only after saving inputs/results under `~/marketsage-data/tsetmc-research/`. Use explicit v1.1 candidate-builder path (not the orchestrator's v1.0 default). Record all run IDs, SHA-256 hashes and resulting counts. Do not rerun the integrated 47-instrument acceptance runner or the previous audits independently.
- The old multi-asset run is missing from its recorded temporary path and there is no copy under the canonical data root. If it cannot be recovered from another saved local artifact, a single multi-asset re-collection must write directly to `~/marketsage-data/multi-asset-collection/`; no further collection is allowed until its outputs are saved and indexed.

## Single final full-corpus TSETMC run command

The guarded runner is now versioned at `user/analysis-engine/scripts/run_tsetmc_research_finalization_once.sh`. It performs one v0.2.5 full-corpus pass using the existing 1,220 normalized histories and raw event files, then runs forensic-v3, the explicit candidate-builder-v1.1, and final candidate-suite QA. Outputs go into a unique timestamped directory under `~/marketsage-data/tsetmc-research/`; logs are in `~/marketsage-data/logs/tsetmc-finalization.log`. A `flock` prevents two finalization jobs from running concurrently. The script writes a final hash/count inventory and updates the local data index after success. Raw inputs and the source corpus are not the output target.

This is justified because the old full-corpus triage report produced no research features or labels and only 14 adjusted-candidate files (51,872 rows) exist in the named adjustment subdirectory. It is **one end-to-end processing pass, not another series of standalone audits**. If its exact v0.2.5 input contract fails, stop on that single log; do not try multiple path permutations or re-run the pipeline repeatedly. The source-acceptance, rights, and investment-scoring gates remain fail-closed even after candidate generation.
