#!/usr/bin/env bash
set -uo pipefail

# Dataset acceptance pack. Network probes are split by VPN state.
# Default mode is offline only; no provider is contacted unless a live group is selected.
SCRIPT_DIR="$(cd -- "$(dirname -- "$BASH_SOURCE")" && pwd)"
ENGINE_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPO_DIR="$(cd -- "$ENGINE_DIR/../.." && pwd)"
cd "$ENGINE_DIR"

if [[ -x "$ENGINE_DIR/.venv/bin/python" ]]; then
  PYTHON="$ENGINE_DIR/.venv/bin/python"
else
  PYTHON="$(command -v python3)"
fi

REPORT_DIR="/tmp/marketsage-free-dataset-acceptance"
if [[ -n "${MARKETSAGE_FREE_DATASET_DIR:-}" ]]; then REPORT_DIR="$MARKETSAGE_FREE_DATASET_DIR"; fi
OFFLINE_ONLY=0
RUN_IRAN=0
RUN_FOREIGN=0
INCLUDE_TINDEX=0
INCLUDE_FRED=0
INCLUDE_GDELT=0
TSETMC_QUERY_ARGS=()
TINDEX_SLUG_ARGS=()
AUDIT_CSV_ARGS=()

while (($#)); do
  case "$1" in
    --offline-only) OFFLINE_ONLY=1; shift ;;
    --live-iran) RUN_IRAN=1; shift ;;
    --live-foreign) RUN_FOREIGN=1; shift ;;
    --include-tindex) INCLUDE_TINDEX=1; shift ;;
    --include-fred) INCLUDE_FRED=1; shift ;;
    --include-gdelt) INCLUDE_GDELT=1; shift ;;
    --tsetmc-query)
      if (($# < 2)); then echo "Missing value for --tsetmc-query" >&2; exit 2; fi
      TSETMC_QUERY_ARGS+=(--tsetmc-query "$2"); shift 2 ;;
    --tindex-slug)
      if (($# < 2)); then echo "Missing value for --tindex-slug" >&2; exit 2; fi
      TINDEX_SLUG_ARGS+=(--tindex-slug "$2"); shift 2 ;;
    --audit-csv)
      if (($# < 2)); then echo "Missing value for --audit-csv" >&2; exit 2; fi
      AUDIT_CSV_ARGS+=(--audit-csv "$2"); shift 2 ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: bash scripts/run_free_dataset_acceptance_pack.sh [--offline-only] [--live-iran [--include-tindex [--tindex-slug SLUG]]] [--live-foreign [--include-fred] [--include-gdelt]] [--tsetmc-query NAME ...] [--audit-csv FILE ...]" >&2
      exit 2 ;;
  esac
done

if (( RUN_IRAN && RUN_FOREIGN )); then
  echo "Refusing to mix Iranian and foreign providers in one run; VPN state must be unambiguous." >&2
  exit 2
fi
if (( OFFLINE_ONLY && (RUN_IRAN || RUN_FOREIGN) )); then
  echo "--offline-only cannot be combined with a live source group." >&2
  exit 2
fi
if (( INCLUDE_TINDEX && ! RUN_IRAN )); then echo "--include-tindex requires --live-iran." >&2; exit 2; fi
if (( (INCLUDE_FRED || INCLUDE_GDELT) && ! RUN_FOREIGN )); then
  echo "--include-fred and --include-gdelt require --live-foreign." >&2
  exit 2
fi
if [[ "${#TSETMC_QUERY_ARGS[@]}" -gt 0 ]] && (( ! RUN_IRAN )); then
  echo "--tsetmc-query requires --live-iran." >&2
  exit 2
fi
if [[ "${#TINDEX_SLUG_ARGS[@]}" -gt 0 ]] && (( ! INCLUDE_TINDEX )); then
  echo "--tindex-slug requires --include-tindex." >&2
  exit 2
fi
if [[ "${#TINDEX_SLUG_ARGS[@]}" -gt 0 ]] && (( ! RUN_IRAN )); then
  echo "--tindex-slug requires --live-iran." >&2
  exit 2
fi
if [[ "${#TINDEX_SLUG_ARGS[@]}" -gt 1 ]]; then
  echo "Only one Tindex slug is allowed per invocation under the current 1-request/minute free-tier quota." >&2
  exit 2
fi

mkdir -p "$REPORT_DIR"
SUMMARY="$REPORT_DIR/summary.txt"
: > "$SUMMARY"
record() { echo "$*" | tee -a "$SUMMARY"; }

confirm_vpn_state() {
  local expected="$1"
  local prompt="$2"
  local answer
  if [[ ! -t 0 ]]; then
    record "FAIL: VPN confirmation needs an interactive terminal; no live request was made."
    return 2
  fi
  echo "$prompt" | tee -a "$SUMMARY"
  read -r -p "Type $expected to confirm: " answer
  if [[ "$answer" != "$expected" ]]; then
    record "FAIL: VPN confirmation did not match; no live request was made."
    return 2
  fi
  return 0
}

audit_csv_batch() {
  local -a csv_files=()
  local candidate
  local i
  # Only include exported candidates from the current live phase. Explicit CSV
  # paths are always audited, including in offline-only mode.
  if (( RUN_IRAN || RUN_FOREIGN )) && [[ -d "$REPORT_DIR/candidate-exports" ]]; then
    while IFS= read -r candidate; do csv_files+=("$candidate"); done < <(find "$REPORT_DIR/candidate-exports" -maxdepth 1 -type f -name '*.csv' -print | sort)
  fi
  for ((i=0; i<${#AUDIT_CSV_ARGS[@]}; i+=2)); do csv_files+=("${AUDIT_CSV_ARGS[i+1]}"); done
  if (("${#csv_files[@]}" == 0)); then
    record "CSV audit skipped: no exported or explicitly supplied CSV files were selected."
    return 0
  fi
  if "$PYTHON" scripts/audit_candidate_dataset.py "${csv_files[@]}" --out-report "$REPORT_DIR/csv-quality-report.json" > "$REPORT_DIR/csv-quality-report.stdout.json"; then
    record "CSV audit completed: $REPORT_DIR/csv-quality-report.json"
  else
    record "WARN: one or more CSVs could not be audited; see $REPORT_DIR/csv-quality-report.json"
  fi
}

record "MarketSage free-access dataset discovery/acceptance"
record "Started (UTC): $(date -u +%FT%TZ)"
record "Repository: $REPO_DIR"
record "Reports: $REPORT_DIR"
record "The run never enables scoring or ranking."
record ""

record "== 1/5 Validate source catalog and run complete offline test suite =="
if ! "$PYTHON" -m json.tool "$REPO_DIR/docs/free_dataset_source_catalog.json" >/dev/null; then
  record "FAIL: free dataset source catalog is invalid JSON."
  exit 1
fi
if ! "$PYTHON" -m pytest -q tests; then
  record "FAIL: offline test suite failed; live probes were not started."
  exit 1
fi
if ! bash -n scripts/run_free_dataset_acceptance_pack.sh; then
  record "FAIL: bundled acceptance shell script failed bash syntax validation."
  exit 1
fi
record "PASS: catalog JSON, shell syntax and full offline analysis-engine tests"
record ""

record "== 2/5 Generate inventory and pending evidence templates (no network) =="
if ! "$PYTHON" scripts/discover_free_datasets.py --mode inventory --output "$REPORT_DIR/source-inventory.json" > "$REPORT_DIR/source-inventory.stdout.json"; then
  record "FAIL: inventory generation failed."
  exit 1
fi
if ! "$PYTHON" scripts/create_source_evidence_templates.py --all --output-dir "$REPORT_DIR/evidence-templates" > "$REPORT_DIR/evidence-templates.stdout.json"; then
  record "FAIL: source evidence template generation failed."
  exit 1
fi
record "PASS: source inventory and pending evidence templates"
record ""

if (( RUN_IRAN )); then
  if ! confirm_vpn_state "VPN-OFF" "VPN PRECHECK: Iranian providers selected (TSETMC/CODAL; Tindex only if requested). Turn VPN OFF before continuing."; then exit 2; fi
  record "== 3/5 Probe Iranian providers only (VPN OFF) =="
  IRAN_ARGS=(--mode probe --source iran.tsetmc --source iran.codal --export-dir "$REPORT_DIR/candidate-exports" --output "$REPORT_DIR/iran-live-probes.json")
  IRAN_ARGS+=("${TSETMC_QUERY_ARGS[@]}")
  if (( INCLUDE_TINDEX )); then
    IRAN_ARGS+=(--source iran.tindex.candles)
    IRAN_ARGS+=("${TINDEX_SLUG_ARGS[@]}")
    if [[ -n "${TINDEX_API_BASE_URL:-}" && -n "${TINDEX_API_TOKEN:-}" ]]; then
      record "Tindex configured; one candle slug maximum per invocation under the current 1-request/minute quota."
    else
      record "Tindex selected but credentials are absent; provider will be marked skipped, without a prompt."
    fi
  fi
  if "$PYTHON" scripts/discover_free_datasets.py "${IRAN_ARGS[@]}" > "$REPORT_DIR/iran-live-probes.stdout.json"; then
    record "Iranian probe group completed."
  else
    record "WARN: an Iranian provider probe failed; see the sanitized report."
  fi
  record "Iranian report: $REPORT_DIR/iran-live-probes.json"
elif (( RUN_FOREIGN )); then
  if ! confirm_vpn_state "VPN-ON" "VPN PRECHECK: Foreign/international providers selected (World Bank/Binance; FRED/GDELT only if requested). Turn VPN ON before continuing."; then exit 2; fi
  record "== 3/5 Probe foreign providers only (VPN ON) =="
  FOREIGN_ARGS=(--mode probe --source global.world_bank_indicators --source global.binance_spot_public --export-dir "$REPORT_DIR/candidate-exports" --output "$REPORT_DIR/foreign-live-probes.json")
  if (( INCLUDE_FRED )); then
    FOREIGN_ARGS+=(--source us.fred.alfred)
    if [[ -n "${FRED_API_KEY:-}" ]]; then
      record "FRED/ALFRED selected and API key is configured in the environment."
    else
      record "FRED/ALFRED selected but FRED_API_KEY is absent; provider will be marked skipped, without a prompt."
    fi
  fi
  if (( INCLUDE_GDELT )); then
    record "GDELT explicit opt-in: one tiny request only; previous probe returned HTTP 429. Do not retry rapidly."
    FOREIGN_ARGS+=(--source global.gdelt_doc_api)
  fi
  if "$PYTHON" scripts/discover_free_datasets.py "${FOREIGN_ARGS[@]}" > "$REPORT_DIR/foreign-live-probes.stdout.json"; then
    record "Foreign probe group completed."
  else
    record "WARN: a foreign provider probe failed; see the sanitized report."
  fi
  record "Foreign report: $REPORT_DIR/foreign-live-probes.json"
else
  record "== 3/5 Live providers skipped =="
  record "Safe default: no provider network requests. Choose exactly one group per invocation: --live-iran or --live-foreign."
fi
record ""

record "== 4/5 Audit candidate exports and explicitly supplied local CSVs =="
audit_csv_batch
record ""

record "== 5/5 Final safety state =="
record "No source was approved; production scoring and investment ranking remain disabled."
record "Generated local artifacts:"
record "$REPORT_DIR/source-inventory.json"
record "$REPORT_DIR/evidence-templates/"
if (( RUN_IRAN )); then record "$REPORT_DIR/iran-live-probes.json"; fi
if (( RUN_FOREIGN )); then record "$REPORT_DIR/foreign-live-probes.json"; fi
record "$REPORT_DIR/candidate-exports/"
record "$REPORT_DIR/csv-quality-report.json"
record "$SUMMARY"
record ""
record "Access success != complete history != legal reuse != production scoring approval."
