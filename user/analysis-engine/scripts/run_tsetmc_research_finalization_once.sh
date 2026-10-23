#!/usr/bin/env bash
# One full-corpus TSETMC research finalization pass.
# Uses existing local corpus; no network calls to market-data providers.
# Outputs live outside the corpus; never modifies the raw source tree.
set -Eeuo pipefail
umask 027

REPO="${MARKETSAGE_REPO:-$HOME/projects/marketsage-acceptance}"
DATA="${MARKETSAGE_DATA_ROOT:-$HOME/marketsage-data}"
DL="${MARKETSAGE_DOWNLOADS:-$HOME/Downloads}"
CORPUS="$DATA/tsetmc/tsetmc_history_pipeline"
HISTORY="$CORPUS/corpus_reconciliation_v2"
RAW="$CORPUS/raw"

ADJ="$DL/adjust_pipeline_v025.py"
FORENSIC="$DL/audit_tsetmc_forensic_v3.py"
BUILDER="$DL/build_tsetmc_research_candidates_v1_1.py"
PIPELINE="$DL/run_tsetmc_research_pipeline_v1_1.py"
QA="$DL/audit_tsetmc_research_candidate_suite_v1.py"

LOG_DIR="$DATA/logs"
mkdir -p "$LOG_DIR" "$DATA/tsetmc-research"
exec 9>"$LOG_DIR/tsetmc-finalization.lock"
if ! flock -n 9; then
  echo "A TSETMC finalization job already holds the lock. Do not start another."
  exit 3
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_ROOT="$DATA/tsetmc-research/finalize_$STAMP"
V025_ROOT="$RUN_ROOT/v025-runs"
PIPE_ROOT="$RUN_ROOT/research-pipeline"
mkdir -p "$V025_ROOT" "$PIPE_ROOT"

echo "TSETMC finalization started at $(date -Is)"
echo "Run root: $RUN_ROOT"
echo "Repository: $REPO"
echo "Corpus: $CORPUS"
echo "Normalized histories: $HISTORY"
echo "Raw histories/events: $RAW"
echo "Market-data network requests: none expected"

for p in "$REPO" "$CORPUS" "$HISTORY" "$RAW"; do
  if [ ! -d "$p" ]; then
    echo "ERROR: required directory missing: $p"
    exit 10
  fi
done
for p in "$ADJ" "$FORENSIC" "$BUILDER" "$PIPELINE" "$QA"; do
  if [ ! -s "$p" ]; then
    echo "ERROR: required script missing/empty: $p"
    exit 11
  fi
done
if ! command -v flock >/dev/null 2>&1; then
  echo "ERROR: flock command is required to prevent duplicate runs."
  exit 12
fi

echo "===== Input corpus inventory (existing files only) ====="
printf "History archives: "
find "$RAW" -mindepth 2 -maxdepth 2 -type f -name 'history_archive.json' | wc -l
printf "Normalized CSV files: "
find "$HISTORY" -type f -name '*.csv' | wc -l
printf "Existing adjusted candidate CSVs: "
find "$CORPUS/corpus_reconciliation/adjusted_candidates_research_only" \
  -type f -name '*.adjusted_candidate.csv' 2>/dev/null | wc -l
df -h "$DATA"

echo "===== Stage 1/3: one whole-corpus v0.2.5 run ====="
python3 -u "$ADJ" \
  --input "$CORPUS" \
  --out-dir "$V025_ROOT" \
  --history-dir "$HISTORY" \
  --events-dir "$RAW" \
  --share-events-dir "$RAW"

PRIOR_RUN="$(
  find "$V025_ROOT" -type f -name 'instrument_decisions.csv' -printf '%T@ %h\n' \
    | sort -nr | head -n 1 | sed 's/^[^ ]* //'
)"
if [ -z "$PRIOR_RUN" ] || [ ! -s "$PRIOR_RUN/instrument_decisions.csv" ] || [ ! -s "$PRIOR_RUN/event_reconciliation.csv" ]; then
  echo "ERROR: v0.2.5 did not produce the decision/event files required for downstream reuse."
  echo "Inspect this run's log before changing arguments; do not rerun automatically."
  find "$V025_ROOT" -maxdepth 4 -type f -printf '%p\n' | head -n 100
  exit 20
fi
echo "v0.2.5 prior run selected: $PRIOR_RUN"

echo "===== Stage 2/3: forensic-v3 + candidate builder v1.1 ====="
python3 -u "$PIPELINE" \
  --repo "$REPO" \
  --phase all \
  --prior-run "$PRIOR_RUN" \
  --forensic-script "$FORENSIC" \
  --candidate-script "$BUILDER" \
  --output-root "$PIPE_ROOT"

echo "===== Stage 3/3: final candidate-suite QA (once) ====="
python3 -u "$QA" --output-root "$PIPE_ROOT"

echo "===== Build final inventory summary ====="
python3 - "$RUN_ROOT" "$CORPUS" "$ADJ" "$FORENSIC" "$BUILDER" "$PIPELINE" "$QA" <<'PY'
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

run_root = Path(sys.argv[1]).resolve()
corpus = Path(sys.argv[2]).resolve()
script_paths = [Path(x).resolve() for x in sys.argv[3:]]
result = {
    "status": "COMPLETED_RESEARCH_CANDIDATE_PIPELINE",
    "run_root": str(run_root),
    "corpus_root": str(corpus),
    "market_data_network_requests": False,
    "raw_inputs_overwritten": False,
    "production_scoring_enabled": False,
    "backtest_approved": False,
    "strategy_backtest_run": False,
    "scripts": {},
    "artifacts": {},
}

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

for script in script_paths:
    if script.is_file():
        result["scripts"][str(script)] = sha256(script)

for path in sorted(run_root.rglob("*")):
    if not path.is_file() or path.name == "finalization_summary.json":
        continue
    relative = path.relative_to(run_root).as_posix()
    entry = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            entry["columns"] = reader.fieldnames or []
            row_count = 0
            status_counts = Counter()
            for row in reader:
                row_count += 1
                status = row.get("decision_status") or row.get("pipeline_status") or ""
                if status:
                    status_counts[status] += 1
            entry["rows"] = row_count
            if status_counts:
                entry["status_counts"] = dict(status_counts)
    elif path.suffix.lower() == ".json":
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                entry["top_level_keys"] = list(obj)[:80]
                for key in (
                    "run_id", "status", "instrument_count", "decision_counts",
                    "research_eligible_count", "candidate_feature_rows",
                    "candidate_forward_labels_available", "research_feature_rows",
                    "forward_label_rows", "source_approved",
                    "investment_scoring_enabled", "approved_for_backtest_any_instrument",
                ):
                    if key in obj:
                        entry[key] = obj[key]
        except Exception:
            entry["json_parse"] = "failed"
    result["artifacts"][relative] = entry

# Separate candidate totals by the actual output column names used by this pipeline.
summary_csvs = [
    p for p in run_root.rglob("*.csv")
    if p.name in {"research_features.csv", "forward_labels_6m.csv",
                  "candidate_features.csv", "candidate_forward_labels.csv"}
]
result["key_csv_row_counts"] = {}
for p in summary_csvs:
    with p.open(encoding="utf-8-sig", newline="") as f:
        result["key_csv_row_counts"][p.relative_to(run_root).as_posix()] = sum(1 for _ in csv.DictReader(f))

summary_path = run_root / "finalization_summary.json"
summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("FINAL_SUMMARY:", summary_path)
print("ARTIFACT_FILES:", len(result["artifacts"]))
print("KEY_CSV_ROW_COUNTS:", json.dumps(result["key_csv_row_counts"], ensure_ascii=False))
print("SCORING_ENABLED:", result["production_scoring_enabled"])
print("BACKTEST_APPROVED:", result["backtest_approved"])
print("BACKTEST_RUN:", result["strategy_backtest_run"])
PY

echo "TSETMC finalization finished at $(date -Is)"
echo "FINAL RUN ROOT: $RUN_ROOT"
echo "FINAL SUMMARY: $RUN_ROOT/finalization_summary.json"
