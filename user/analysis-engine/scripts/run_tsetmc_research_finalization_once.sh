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
HISTORY="$CORPUS/normalized"
RAW="$CORPUS/raw"
DETAILS="$REPO/data/source_snapshots/tsetmc_history_pipeline/corpus_reconciliation_v2/instrument_details.jsonl"
if [ ! -s "$DETAILS" ]; then
  DETAILS="$REPO/data/source_snapshots/tsetmc_history_pipeline/corpus_reconciliation/instrument_details.jsonl"
fi

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
INDEX_PATH="$DATA/registry/local_data_index.json"
mkdir -p "$V025_ROOT" "$PIPE_ROOT" "$(dirname "$INDEX_PATH")"

index_run_state() {
  python3 - "$INDEX_PATH" "$RUN_ROOT" "$1" "$2" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path
idx_path, run_root, status, message = sys.argv[1:]
idx_path = Path(idx_path)
idx_path.parent.mkdir(parents=True, exist_ok=True)
try:
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {}
except Exception:
    index = {}
runs = index.setdefault("existing_runs", {})
previous = runs.get("tsetmc_research_finalization")
if status == "RUNNING" and previous and previous.get("run_root") != run_root:
    history = index.setdefault("tsetmc_research_finalization_history", [])
    history.append(previous)
    index["tsetmc_research_finalization_history"] = history[-20:]
runs["tsetmc_research_finalization"] = {
    "status": status,
    "run_root": run_root,
    "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    "message": message,
    "market_data_network_requests": False,
    "raw_inputs_overwritten": False,
    "production_scoring_enabled": False,
    "backtest_approved": False,
}
tmp = idx_path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
tmp.replace(idx_path)
PY
}

index_run_state "RUNNING" "full-corpus TSETMC candidate finalization started"
on_exit() {
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    index_run_state "BLOCKED_OR_FAILED" "finalization exited with status $rc; inspect this run's log/report before deciding next action" || true
  fi
}
trap on_exit EXIT

echo "TSETMC finalization started at $(date -Is)"
echo "Run root: $RUN_ROOT"
echo "Repository: $REPO"
echo "Corpus: $CORPUS"
echo "Normalized histories: $HISTORY"
echo "Raw histories/events: $RAW"
echo "Identity crosswalk: $DETAILS"
echo "Crosswalk is read from repository root; explicit history/event paths still point to canonical data root."
echo "Market-data network requests: none expected"

for p in "$REPO" "$CORPUS" "$HISTORY" "$RAW"; do
  if [ ! -d "$p" ]; then
    echo "ERROR: required directory missing: $p"
    exit 10
  fi
done
if [ ! -s "$DETAILS" ]; then
  echo "ERROR: required identity crosswalk file missing or empty: $DETAILS"
  exit 10
fi
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
RAW_COUNT="$(find "$RAW" -mindepth 2 -maxdepth 2 -type f -name 'history_archive.json' | wc -l | tr -d '[:space:]')"
HISTORY_COUNT="$(find "$HISTORY" -maxdepth 1 -type f -name '*.history.csv' | wc -l | tr -d '[:space:]')"
echo "History archives: $RAW_COUNT"
echo "Normalized history CSVs (*.history.csv): $HISTORY_COUNT"
if [ "$HISTORY_COUNT" -lt 1000 ] || [ "$HISTORY_COUNT" -ne "$RAW_COUNT" ]; then
  echo "ERROR: history preflight rejected this run. Expected the known full corpus (~1,220 normalized histories) and matching raw archive coverage."
  echo "Resolved history directory: $HISTORY"
  echo "Normalized history files: $HISTORY_COUNT; raw archive files: $RAW_COUNT"
  echo "No processing stages were started; do not rerun with guessed paths."
  exit 13
fi
python3 - "$DETAILS" <<'PY'
import json, re, sys
from pathlib import Path
path = Path(sys.argv[1])
pairs = {}
conflicts = set()
for line in path.read_text(encoding="utf-8-sig").splitlines():
    if not line.strip():
        continue
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        continue
    isin = str(row.get("isin") or "").strip().upper()
    code = str(row.get("inscode") or "").strip()
    if re.fullmatch(r"IR[A-Z0-9]{8,}", isin) and re.fullmatch(r"\d{6,24}", code):
        if isin in pairs and pairs[isin] != code:
            conflicts.add(isin)
        else:
            pairs[isin] = code
valid = set(pairs) - conflicts
print(f"Authoritative identity crosswalk: valid ISIN mappings={len(valid)}, conflicts={len(conflicts)}")
if len(valid) < 1000:
    print("ERROR: the repository crosswalk does not contain enough valid ISIN→insCode mappings.")
    print("No processing stages were started.")
    raise SystemExit(14)
PY
printf "Existing adjusted candidate CSVs: "
find "$CORPUS/corpus_reconciliation/adjusted_candidates_research_only" \
  -type f -name '*.adjusted_candidate.csv' 2>/dev/null | wc -l
df -h "$DATA"

echo "===== Stage 1/3: one whole-corpus v0.2.5 run ====="
python3 -u "$ADJ" \
  --input "$REPO" \
  --out-dir "$V025_ROOT" \
  --history-dir "$HISTORY" \
  --events-dir "$RAW" \
  --share-events-dir "$RAW" 2>&1 | tee "$RUN_ROOT/v025.log"

PRIOR_RUN="$(
  find "$V025_ROOT" -type f -name 'instrument_decisions.csv' -printf '%T@ %h\n' \
    | sort -nr | awk 'NR==1 {sub(/^[^ ]* /, ""); print}'
)"
if [ -z "$PRIOR_RUN" ] || [ ! -s "$PRIOR_RUN/instrument_decisions.csv" ] || [ ! -s "$PRIOR_RUN/event_reconciliation.csv" ]; then
  echo "ERROR: v0.2.5 did not produce the decision/event files required for downstream reuse."
  echo "Inspect this run's log before changing arguments; do not rerun automatically."
  find "$V025_ROOT" -maxdepth 4 -type f -printf '%p\n' | head -n 100
  exit 20
fi
echo "v0.2.5 prior run selected: $PRIOR_RUN"

# Require actual history observations before any downstream forensic/candidate step.
python3 - "$PRIOR_RUN/data_quality_report.json" <<'PY'
import json, sys
from pathlib import Path
p = Path(sys.argv[1])
if not p.is_file():
    print("ERROR: v0.2.5 summary is missing:", p)
    raise SystemExit(21)
d = json.loads(p.read_text(encoding="utf-8"))
hist = int(d.get("history_instruments", 0) or 0)
rows = int(d.get("history_rows_read", 0) or 0)
print(f"v0.2.5 observed history instruments={hist}; history rows={rows}")
if hist < 1000 or rows < 1_000_000:
    print("ERROR: refusing to continue: v0.2.5 did not ingest the known full history corpus.")
    print("This is an input-path/coverage failure, not a successful empty research run.")
    raise SystemExit(22)
PY

echo "===== Stage 2/3: forensic-v3 + candidate builder v1.1 ====="
python3 -u "$PIPELINE" \
  --repo "$REPO" \
  --phase all \
  --prior-run "$PRIOR_RUN" \
  --forensic-script "$FORENSIC" \
  --candidate-script "$BUILDER" \
  --output-root "$PIPE_ROOT"

# Block empty candidate outputs; upstream validation currently allows an empty manifest.
PIPELINE_RUN="$(find "$PIPE_ROOT" -mindepth 2 -maxdepth 2 -type f -name 'pipeline_report.json' -printf '%h\n' | sort | tail -n 1)"
VALIDATION_REPORT="$PIPELINE_RUN/validation_report.json"
if [ -z "$PIPELINE_RUN" ] || [ ! -s "$VALIDATION_REPORT" ]; then
  echo "ERROR: pipeline validation report is missing; final QA was not run."
  exit 30
fi
python3 - "$VALIDATION_REPORT" "$RUN_ROOT/finalization_blocker.json" <<'PY'
import json, sys
from pathlib import Path
report_path, blocker_path = map(Path, sys.argv[1:])
v = json.loads(report_path.read_text(encoding="utf-8"))
counts = v.get("counts", {})
checks = {
    "validation_status_is_passed": v.get("status") == "PASSED",
    "normalized_history_coverage_at_least_1000": int(counts.get("normalized_history_files", 0) or 0) >= 1000,
    "candidate_series_nonempty": int(counts.get("candidate_series", 0) or 0) > 0,
    "feature_rows_nonempty": int(counts.get("feature_rows", 0) or 0) > 0,
    "forward_labels_nonempty": int(counts.get("forward_label_rows", 0) or 0) > 0,
}
print("Pre-QA completeness checks:", json.dumps(checks, ensure_ascii=False))
if not all(checks.values()):
    blocker = {
        "status": "BLOCKED_INCOMPLETE_OR_EMPTY_OUTPUT",
        "validation_report": str(report_path),
        "counts": counts,
        "checks": checks,
        "instruction": "Do not rerun audits individually. Resolve this run's specific pipeline blocker before another full pass.",
    }
    blocker_path.write_text(json.dumps(blocker, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ERROR: final QA not run because the research outputs are empty or incomplete.")
    raise SystemExit(31)
PY

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
                  "candidate_features.csv", "candidate_forward_labels.csv",
                  "research_features_candidate_only.csv",
                  "forward_labels_126obs_candidate_only.csv"}
]
result["key_csv_row_counts"] = {}
for p in summary_csvs:
    with p.open(encoding="utf-8-sig", newline="") as f:
        result["key_csv_row_counts"][p.relative_to(run_root).as_posix()] = sum(1 for _ in csv.DictReader(f))

summary_path = run_root / "finalization_summary.json"
summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Update the local index at the end, so next sessions start from the last run
# rather than asking the owner to rediscover paths and repeat work.
index_path = run_root.parent.parent / "registry" / "local_data_index.json"
try:
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    else:
        index = {"schema_version": 1, "data_root": str(run_root.parent.parent)}
    index.setdefault("existing_runs", {})["tsetmc_research_finalization"] = {
        "status": result["status"],
        "run_root": str(run_root),
        "summary_path": str(summary_path),
        "artifact_file_count": len(result["artifacts"]),
        "market_data_network_requests": False,
        "raw_inputs_overwritten": False,
        "production_scoring_enabled": False,
        "backtest_approved": False,
        "strategy_backtest_run": False,
    }
    temporary_index = index_path.with_suffix(".json.tmp")
    temporary_index.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_index.replace(index_path)
    result["local_data_index_updated"] = str(index_path)
    summary_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
except Exception as exc:
    print("WARNING: local index update failed:", type(exc).__name__, str(exc))
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
