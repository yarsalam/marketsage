#!/usr/bin/env bash
set -uo pipefail

# One batched MarketSage data-acceptance run.
# Start with VPN OFF; this script pauses once so external probes can run with VPN ON.
# No credentials or raw provider payloads are written to the repository.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd -- "${ENGINE_DIR}/../.." && pwd)"
cd "$ENGINE_DIR"

if [[ -x "$ENGINE_DIR/.venv/bin/python" ]]; then
  PYTHON="$ENGINE_DIR/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

REPORT_DIR="${MARKETSAGE_ACCEPTANCE_DIR:-/tmp/marketsage-acceptance}"
mkdir -p "$REPORT_DIR"
SUMMARY="$REPORT_DIR/run-summary.txt"
: > "$SUMMARY"

record() { printf '%s\n' "$*" | tee -a "$SUMMARY"; }

record "MarketSage batched data acceptance"
record "UTC started: $(date -u +%FT%TZ)"
record "Engine: $ENGINE_DIR"
record "Reports: $REPORT_DIR"
record "Ranking/scoring approval: NEVER changed by this script"
record ""

record "== 1/4 Offline regression tests (no VPN/network required) =="
if ! "$PYTHON" -m pytest -q; then
  record "FAIL: full pytest suite failed; stopping before live probes."
  exit 1
fi
record "PASS: full pytest suite"
record ""

record "== 2/4 TSETMC history quality audit (VPN OFF) =="
FIXTURE="/tmp/marketsage-tsetmc-foolad-history.json"
if [[ -f "$FIXTURE" ]]; then
  if ! "$PYTHON" scripts/audit_tsetmc_history.py --input "$FIXTURE" \
      --ins-code 46348559193224090 --output "$REPORT_DIR/tsetmc-history-audit.json"; then
    record "FAIL: TSETMC fixture audit failed."
    exit 1
  fi
else
  record "No saved TSETMC fixture found; fetching one full Foolad history now."
  if ! "$PYTHON" scripts/audit_tsetmc_history.py \
      --ins-code 46348559193224090 --output "$REPORT_DIR/tsetmc-history-audit.json"; then
    record "FAIL: TSETMC history audit/fetch failed (error details redacted)."
    exit 1
  fi
fi
record "PASS: TSETMC history audit; report contains metadata/flags only."
record ""

record "== 3/4 Iran source probes (VPN OFF) =="
record "Sources: TSETMC instrument search, CODAL disclosure search, Tindex currency rates."
if [[ -z "${TINDEX_API_BASE_URL:-}" || -z "${TINDEX_API_TOKEN:-}" ]]; then
  read -r -p "Tindex API origin (Enter to skip): " TINDEX_ORIGIN
  if [[ -n "$TINDEX_ORIGIN" ]]; then
    export TINDEX_API_BASE_URL="$TINDEX_ORIGIN"
    if [[ -z "${TINDEX_API_TOKEN:-}" ]]; then
      read -r -s -p "Tindex API token (input hidden): " TINDEX_TOKEN
      echo
      export TINDEX_API_TOKEN="$TINDEX_TOKEN"
      unset TINDEX_TOKEN
    fi
  fi
fi
if "$PYTHON" scripts/probe_source_acceptance_pack.py \
    --source iran.tsetmc --source iran.codal --source iran.tindex.public_api \
    > "$REPORT_DIR/iran-source-probes.json"; then
  record "Probe pack completed without reported failures."
else
  record "Some Iran probes failed; the sanitized report was still saved."
fi
record "Iran probe report: $REPORT_DIR/iran-source-probes.json"
record ""

record "== 4/4 External source probes (VPN ON) =="
record "Please turn VPN ON now."
read -r -p "When VPN is ON, press Enter to continue (Ctrl-C to stop): " _
if [[ -z "${FRED_API_KEY:-}" ]]; then
  read -r -s -p "FRED API key (Enter to skip; input hidden): " FRED_TOKEN
  echo
  if [[ -n "$FRED_TOKEN" ]]; then export FRED_API_KEY="$FRED_TOKEN"; fi
  unset FRED_TOKEN
fi
if "$PYTHON" scripts/probe_source_acceptance_pack.py \
    --source global.gdelt_doc_api --source us.fred.alfred \
    > "$REPORT_DIR/external-source-probes.json"; then
  record "External probe pack completed without reported failures."
else
  record "Some external probes failed; the sanitized report was still saved."
fi
record "External probe report: $REPORT_DIR/external-source-probes.json"
record ""

record "== Result files =="
record "$REPORT_DIR/tsetmc-history-audit.json"
record "$REPORT_DIR/iran-source-probes.json"
record "$REPORT_DIR/external-source-probes.json"
record "$SUMMARY"
record ""
record "Interpretation: reachability/history flags are evidence for review only."
record "Commercial rights, units, adjustments, point-in-time timestamps and predictive value remain separate gates."
record "Production scoring and investment ranking remain disabled."
