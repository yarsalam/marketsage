#!/usr/bin/env bash
set -uo pipefail

# One-command, free-access dataset discovery and acceptance evidence pack.
# Full offline tests run first. Live probes are bounded and never approve scoring.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd -- "${ENGINE_DIR}/../.." && pwd)"
cd "$ENGINE_DIR"

if [[ -x "$ENGINE_DIR/.venv/bin/python" ]]; then
  PYTHON="$ENGINE_DIR/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

REPORT_DIR="${MARKETSAGE_FREE_DATASET_DIR:-/tmp/marketsage-free-dataset-acceptance}"
OFFLINE_ONLY=0
INCLUDE_GDELT=0
TSETMC_QUERY_ARGS=()

while (($#)); do
  case "$1" in
    --offline-only)
      OFFLINE_ONLY=1
      shift
      ;;
    --include-gdelt)
      INCLUDE_GDELT=1
      shift
      ;;
    --tsetmc-query)
      if (($# < 2)); then echo "Missing value for --tsetmc-query" >&2; exit 2; fi
      TSETMC_QUERY_ARGS+=(--tsetmc-query "$2")
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      echo "Usage: bash scripts/run_free_dataset_acceptance_pack.sh [--offline-only] [--include-gdelt] [--tsetmc-query NAME ...]" >&2
      exit 2
      ;;
  esac
done

mkdir -p "$REPORT_DIR"
SUMMARY="$REPORT_DIR/summary.txt"
: > "$SUMMARY"
record() { printf '%s\n' "$*" | tee -a "$SUMMARY"; }

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
record "PASS: catalog JSON and full offline analysis-engine tests"
record ""

record "== 2/5 Generate source inventory without network requests =="
if ! "$PYTHON" scripts/discover_free_datasets.py --mode inventory \
    --output "$REPORT_DIR/source-inventory.json" > "$REPORT_DIR/source-inventory.stdout.json"; then
  record "FAIL: inventory generation failed."
  exit 1
fi
record "PASS: inventory written to $REPORT_DIR/source-inventory.json"
record ""

if [[ "$OFFLINE_ONLY" == "1" ]]; then
  record "== Live probes skipped by --offline-only =="
  record "Run completed; no network requests were made by the discovery pack."
  record "Templates and CSV audits are optional local commands documented in docs/free-dataset-discovery-and-acceptance.md."
  record "Summary: $SUMMARY"
  exit 0
fi

record "== 3/5 Probe unauthenticated public-access candidates (bounded) =="
LIVE_ARGS=(--mode probe --source iran.tsetmc --source iran.codal \
  --source global.world_bank_indicators --source global.binance_spot_public \
  --export-dir "$REPORT_DIR/candidate-exports" --output "$REPORT_DIR/public-live-probes.json")
LIVE_ARGS+=("${TSETMC_QUERY_ARGS[@]}")
if "$PYTHON" scripts/discover_free_datasets.py "${LIVE_ARGS[@]}" > "$REPORT_DIR/public-live-probes.stdout.json"; then
  record "Public probe batch completed."
else
  record "WARN: one or more public probes failed; inspect the sanitized report."
fi
record "Public report: $REPORT_DIR/public-live-probes.json"
record ""

record "== 4/5 Probe optional free-tier/keyed APIs only when credentials already exist =="
OPTIONAL_ARGS=(--mode probe --output "$REPORT_DIR/optional-live-probes.json" \
  --export-dir "$REPORT_DIR/candidate-exports")
OPTIONAL_SELECTED=0
if [[ -n "${TINDEX_API_BASE_URL:-}" && -n "${TINDEX_API_TOKEN:-}" ]]; then
  OPTIONAL_ARGS+=(--source iran.tindex.candles)
  OPTIONAL_SELECTED=1
  record "Tindex: configured; at most three documented candle slugs will be probed."
else
  record "Tindex skipped: token/origin not configured in this shell; no credential prompt."
fi
if [[ -n "${FRED_API_KEY:-}" ]]; then
  OPTIONAL_ARGS+=(--source us.fred.alfred)
  OPTIONAL_SELECTED=1
  record "FRED/ALFRED: configured; one series request will be attempted."
else
  record "FRED/ALFRED skipped: FRED_API_KEY not configured in this shell."
fi
if [[ "$OPTIONAL_SELECTED" == "1" ]]; then
  if "$PYTHON" scripts/discover_free_datasets.py "${OPTIONAL_ARGS[@]}" > "$REPORT_DIR/optional-live-probes.stdout.json"; then
    record "Optional probe batch completed."
  else
    record "WARN: an optional API probe failed; inspect the sanitized report."
  fi
else
  printf '%s\n' '{"status":"skipped_missing_credentials","production_approved":false}' \
    > "$REPORT_DIR/optional-live-probes.json"
fi
record "Optional report: $REPORT_DIR/optional-live-probes.json"
record ""

record "== 5/5 GDELT is excluded from the default run =="
if [[ "$INCLUDE_GDELT" == "1" ]]; then
  record "GDELT explicit opt-in: making one tiny request; previous probes saw HTTP 429."
  if "$PYTHON" scripts/discover_free_datasets.py --mode probe \
      --source global.gdelt_doc_api --output "$REPORT_DIR/gdelt-probe.json" \
      > "$REPORT_DIR/gdelt-probe.stdout.json"; then
    record "GDELT probe completed."
  else
    record "WARN: GDELT probe failed; do not immediately retry after HTTP 429."
  fi
else
  record "GDELT not contacted. To opt in once, rerun with --include-gdelt."
fi

record ""
record "Generated artifacts (outside the repository):"
record "$REPORT_DIR/source-inventory.json"
record "$REPORT_DIR/public-live-probes.json"
record "$REPORT_DIR/optional-live-probes.json"
record "$REPORT_DIR/candidate-exports/"
record "$SUMMARY"
record ""
record "Next: run scripts/audit_candidate_dataset.py on candidate CSVs and complete a source evidence template."
record "Access success != complete history != legal reuse != production scoring approval."
