# Integrated TSETMC history acceptance pipeline

This is a **local/offline** orchestration stage for the existing TSETMC raw-history,
provider-adjusted-chart, and corporate-action evidence. It is intended to replace
repeated standalone audits with one deterministic run that emits per-instrument
decisions and a single run report.

It does not contact TSETMC, repair input files, infer or apply adjustment factors,
fill missing dates, overwrite raw inputs, enable production scoring, or run a
strategy backtest. Candidate rows and reports should be stored outside Git because
the source's rights and reuse terms are not yet approved.

## Run against a local corpus

Use the actual data directory only, not the entire repository and not the output
directory. The discovery mode recognizes common raw-history JSON/CSV names and
also looks for observation-date plus close fields in candidate files. For a
combined CSV with an instrument-code column it splits inventory rows by code.
Discovery is deliberately conservative about identity: a folder or filename is
not treated as ISIN evidence. If raw and derived files coexist, known raw-history
filenames receive deterministic priority and alternate file paths/hashes are kept
in the inventory; equally ranked candidates for the same instrument block acceptance
instead of being silently merged. Discovery alone cannot assert the selected series
is raw/unadjusted.

```bash
cd ~/projects/marketsage-acceptance
python3 user/analysis-engine/scripts/run_tsetmc_acceptance_pipeline.py \
  --discover-root /absolute/path/to/tsetmc-history-corpus \
  --output-root "$HOME/marketsage-data/tsetmc-acceptance"
```

The runner makes no network requests. It creates a fresh UTC-stamped directory
inside the output root and will not overwrite an earlier run.

## Explicit manifest mode

Use a CSV if the local corpus has nonstandard filenames. Required columns are:

- `instrument_code`, `symbol`, `isin`
- `daily_history_path`
- `adjusted_chart_path`
- `adjustment_events_path` for price-adjustment events
- `share_change_events_path` for share-count/capital-change events

For research-eligibility, also declare `history_close_semantics=raw_unadjusted` only if the reviewed evidence proves the selected input history is raw/unadjusted. Other accepted values are `provider_adjusted` and `unknown`, but they intentionally block factor-ratio acceptance and feature/label creation from the selected input. Header names or a nonempty OHLC field do not prove that a series is unadjusted.

Paths may be absolute or relative to the manifest's directory. Daily history
payloads may be a list of rows or a JSON object with a recognized daily-row array
such as `closingPriceDaily`; per-instrument CSV files are supported too. The
legacy adjusted chart can be a JSON date-to-array object, a JSON row list, a
normalized date-to-field object, or the legacy semicolon/comma-delimited response.

Example manifest:

```csv
instrument_code,symbol,isin,daily_history_path,adjusted_chart_path,adjustment_events_path,share_change_events_path,history_close_semantics,rights_status,semantics_verified,independent_reconciliation_passed,corporate_action_completeness_verified,identity_match_evidence_ref,rights_evidence_ref,semantics_evidence_ref,independent_reconciliation_evidence_ref,corporate_action_completeness_evidence_ref
46348559193224090,FOLAD,IRO1FOLD0001,raw/daily_history_raw.json,raw/chart_adjusted_raw.json,raw/price_adjustments_raw.json,raw/share_changes_raw.json,unknown,unreviewed,false,false,false,,,,,
```

Evidence gates require a traceable reference for identity, usage rights, semantics/
units, independent reconciliation, and corporate-action completeness. A reference
may be an HTTP(S) URL, a `sha256:<64 hex chars>` identifier, or a local evidence
file that exists. Boolean fields alone do not pass a gate. Do not mark a field
approved unless the associated evidence has actually been reviewed.

```bash
python3 user/analysis-engine/scripts/run_tsetmc_acceptance_pipeline.py \
  --manifest /absolute/path/to/instrument-manifest.csv \
  --output-root "$HOME/marketsage-data/tsetmc-acceptance"
```

The initial triage rules are versioned defaults, not evidence that a series is
correct: at least 252 valid history rows, adjusted-chart coverage of at least 95%,
and adjusted/input ratio range 0.05–20. The pipeline also checks adjusted-candidate
OHLC ordering and leaves invalid rows flagged rather than repairing them. Ratio triage is computed only when input semantics are explicitly `raw_unadjusted`; an unverified input is not labelled raw just because the filenames or field names look familiar. You can override them explicitly for
sensitivity checks with `--min-history-rows`, `--min-adjusted-coverage`,
`--factor-min`, and `--factor-max`. Do not change thresholds simply to turn
a failing series into a pass.

## Outputs

Each run directory contains:

| Output | Purpose |
| --- | --- |
| `instrument_decisions.csv` | One decision, reason codes, coverage, gaps and quality counters per instrument |
| `input_history_candidate.csv` | Input observations under neutral “candidate” names plus declared/inferred semantics; original input stays untouched |
| `raw_history_quality.csv` | Row-level malformed date/value, duplicate-date and input-OHLC flags |
| `history_gap_audit.csv` | Every interval over seven calendar days; gaps over 30 days block research until calendar/suspension/missing-data review |
| `adjusted_candidate_daily.csv` | Separate provider-adjusted candidate values with adjusted-OHLC QA flags and no fallback/fill |

| `event_reconciliation.csv` | Separately labeled price-adjustment and share-change event dates matched against input history/chart; overlap is evidence, not automatic confirmation |
| `adjustment_factor_audit.csv` | Adjusted/input ratios (only when input semantics are explicitly raw), extrema, out-of-range factors and abrupt factor changes |
| `research_eligible_manifest.csv` | Only series passing structural gates and traceable evidence gates |
| `quarantine.csv` | Open issues with reason codes and required action |
| `reprocessing_queue.csv` | Non-looping work queue with input hash, attempt count and resolution status |
| `research_features.csv` | Causal returns/volatility/drawdown features for evidence-accepted series only |
| `forward_labels_6m.csv` | Monthly decision dates and first accepted adjusted observation at or after six calendar months |
| `backtest_gate.json` | Explicit reason strategy evaluation is blocked or not yet run |
| `input_inventory.csv`, `data_quality_report.json`, `run_manifest.json` | Input hashes, decision totals, rule version and provenance |

Rows in all candidate outputs remain research-only. A structural pass is not a
source licence or independent price validation. In particular, exact event-date
overlap does not prove the event's effective date; the legacy chart positional
mapping is empirical and unapproved; and factor thresholds are anomaly flags, not
automatic correction rules.

Feature rows and six-month labels are created only if the manifest has complete,
traceable evidence for identity, source use, semantics/units, independent
reconciliation and corporate-action completeness and the technical gates pass.
Input dates are checked for large calendar gaps. Every gap longer than seven days
is recorded; any gap over 30 calendar days blocks research eligibility until an
exchange-calendar, suspension/delisting, or missing-collection explanation is
reviewed. These are triage thresholds, not an assumption that every gap is bad.
Missing data is never forward-filled. A chronological strategy backtest with
transaction costs, liquidity, drawdown, baseline comparisons and an untouched
holdout remains a separate review stage. Production scoring remains disabled by
the source registry.

## Statuses and remediation

- `needs_reprocessing`: unreadable inputs, invalid date/close fields, duplicate dates,
  non-monotonic row ordering, or OHLC defects.
- `quarantine_needs_independent_evidence`: identity evidence missing, suspicious
  adjusted/input ratios or factor steps, long history gaps requiring calendar/suspension
  review, or missing/unparseable price-adjustment/share-change event payloads.
- `retain_candidate_insufficient_history`: fewer than the minimum rows for
  six-month research.
- `retain_candidate_pending_evidence`: technical checks pass but one or more
  rights/units/semantics/independent-reference/action evidence gates are missing.
- `research_eligible_after_explicit_evidence_review`: technical checks pass and the
  manifest references the required reviewed evidence; this still does **not** allow
  production scoring.

Every rejected/pending candidate remains represented in the decision report and
queue. The runner never silently deletes duplicates, corrects a price, applies an
inferred factor, fills a gap or retries network requests.
