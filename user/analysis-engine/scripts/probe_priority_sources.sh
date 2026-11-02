#!/usr/bin/env bash
set -uo pipefail

# Focused acceptance run for GDELT, FRED/ALFRED and Tindex only.
# Runs targeted mocked tests, then at most one live request per selected source.
# Reports contain sanitized metadata only; credentials are never written to disk.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "$ENGINE_DIR"

if [[ -x "$ENGINE_DIR/.venv/bin/python" ]]; then
  PYTHON="$ENGINE_DIR/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

REPORT_DIR="${MARKETSAGE_ACCEPTANCE_DIR:-/tmp/marketsage-acceptance}"
mkdir -p "$REPORT_DIR"
SUMMARY="$REPORT_DIR/priority-sources-summary.txt"
: > "$SUMMARY"
record() { printf '%s\n' "$*" | tee -a "$SUMMARY"; }

record "MarketSage priority-source acceptance"
record "UTC started: $(date -u +%FT%TZ)"
record "Reports: $REPORT_DIR"
record "Production scoring: remains disabled"
record ""

record "== 1/3 Targeted offline tests =="
if ! "$PYTHON" -m pytest -q \
  tests/test_gdelt_news_provider.py \
  tests/test_fred_alfred_provider.py \
  tests/test_tindex_provider.py \
  tests/test_source_acceptance_probe.py; then
  record "FAIL: targeted tests failed; no live requests were made."
  exit 1
fi
record "PASS: targeted offline tests"
record ""

record "== 2/3 Tindex (VPN OFF; one request maximum) =="
if [[ -z "${TINDEX_API_TOKEN:-}" ]]; then
  read -r -s -p "Tindex developer API token (Enter to skip; input hidden): " TINDEX_TOKEN
  echo
  if [[ -n "$TINDEX_TOKEN" ]]; then export TINDEX_API_TOKEN="$TINDEX_TOKEN"; fi
  unset TINDEX_TOKEN
fi
export TINDEX_API_BASE_URL="${TINDEX_API_BASE_URL:-https://tindex.app}"
if [[ -n "${TINDEX_API_TOKEN:-}" ]]; then
  if "$PYTHON" scripts/probe_source_acceptance_pack.py --source iran.tindex.public_api > "$REPORT_DIR/tindex-probe.json"; then
    record "Tindex probe completed without reported failures."
  else
    record "Tindex probe failed; sanitized report saved."
  fi
else
  printf '%s\n' '{"sources":{"iran.tindex.public_api":{"status":"skipped_missing_credentials"}},"production_approved":false}' > "$REPORT_DIR/tindex-probe.json"
  record "Tindex skipped: no token supplied."
fi
unset TINDEX_API_TOKEN TINDEX_API_BASE_URL
record "Tindex report: $REPORT_DIR/tindex-probe.json"
record ""

record "== 3/3 GDELT + FRED (VPN ON; one request each maximum) =="
read -r -p "Turn VPN ON, then press Enter (Ctrl-C to stop): " _
if [[ -z "${FRED_API_KEY:-}" ]]; then
  read -r -s -p "FRED API key (Enter to skip; input hidden): " FRED_TOKEN
  echo
  if [[ -n "$FRED_TOKEN" ]]; then export FRED_API_KEY="$FRED_TOKEN"; fi
  unset FRED_TOKEN
fi
if "$PYTHON" scripts/probe_source_acceptance_pack.py \
  --source global.gdelt_doc_api --source us.fred.alfred \
  > "$REPORT_DIR/gdelt-fred-probes.json"; then
  record "GDELT/FRED probes completed without reported failures."
else
  record "At least one GDELT/FRED probe failed or was unavailable; report saved."
fi
unset FRED_API_KEY
record "GDELT/FRED report: $REPORT_DIR/gdelt-fred-probes.json"
record ""
record "No raw payloads or credentials were written by this script."
record "Inspect JSON statuses and error_type/safe_error_detail only."
record "A successful probe is not production approval."
