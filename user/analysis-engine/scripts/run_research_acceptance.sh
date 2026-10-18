#!/usr/bin/env bash
set -euo pipefail

# MarketSage research acceptance pack.
# Default: deterministic unit/regression tests; no network or VPN required.
# Optional live local API check:
#   RUN_API_SMOKE=1 ./scripts/run_research_acceptance.sh
# Requires FastAPI (8000) and NestJS (4500) to be running for API smoke.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "$ENGINE_DIR"

if [[ -x "$ENGINE_DIR/.venv/bin/python" ]]; then
  PYTHON="$ENGINE_DIR/.venv/bin/python"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "== MarketSage research acceptance pack =="
echo "Engine: $ENGINE_DIR"
echo "Python: $PYTHON"
echo
echo "== 1/2 Deterministic pipeline and backtest tests =="
"$PYTHON" -m pytest -q \
  tests/test_research_pipeline.py \
  tests/test_research_backtest.py

if [[ "${RUN_API_SMOKE:-0}" != "1" ]]; then
  echo
  echo "Unit/regression pack passed. API smoke was skipped."
  echo "To also test the local UI -> NestJS -> FastAPI API hop, start both APIs and run:"
  echo "  RUN_API_SMOKE=1 ./scripts/run_research_acceptance.sh"
  exit 0
fi

echo
echo "== 2/2 Local API contract smoke test =="
API_URL="${MARKETSAGE_API_URL:-http://127.0.0.1:4500/api/markets/research-snapshot}" \
"$PYTHON" - <<'PY'
import json
import os
import sys
import urllib.error
import urllib.request

url = os.environ["API_URL"]
payload = {
    "as_of_date": "2026-10-17",
    "articles": [
        {
            "source_id": "fixture.news",
            "url": "https://example.test/markets/central-bank-demo",
            "title": "Central bank announces agreement and growth",
            "first_seen_date": "2026-10-16",
        },
        {
            "source_id": "fixture.news",
            "url": "https://example.test/markets/future-demo",
            "title": "Markets surge after agreement",
            "first_seen_date": "2026-10-19",
        },
    ],
    "market_series": [
        {
            "symbol": "DEMO",
            "source_id": "fixture.market",
            "unit": "USD per unit",
            "currency": "USD",
            "unit_confirmed": True,
            "currency_confirmed": True,
            "observations": [
                {"date": "2026-10-15", "close": 100},
                {"date": "2026-10-16", "close": 110},
                {"date": "2026-10-17", "close": 105},
                {"date": "2026-10-18", "close": 1000},
            ],
        }
    ],
}

request = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Accept": "application/json", "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=15) as response:
        status = response.status
        body = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    print(f"FAIL: API returned HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')}")
    sys.exit(1)
except Exception as exc:
    print(f"FAIL: could not reach API at {url}: {exc}")
    sys.exit(1)

assert status in (200, 201), f"unexpected HTTP status: {status}"
assert body.get("news", {}).get("future_articles_excluded") == 1, "future article was not excluded"
assert body.get("news", {}).get("articles_analyzed") == 1, "expected exactly one analyzed article"
markets = body.get("markets") or []
assert markets, "response has no market metrics"
market = markets[0]
metrics = market.get("metrics", {})
assert metrics.get("last_observation_date") == "2026-10-17", "future price leaked into snapshot"
assert metrics.get("total_return") is not None and abs(metrics["total_return"] - 0.05) < 1e-9, "unexpected descriptive return"
assert body.get("investment_ranking") is None, "investment ranking must remain disabled"
assert body.get("investment_ranking_status") == "disabled_until_source_and_model_acceptance", "ranking gate status changed"
assert market.get("eligible_for_scoring") is False, "unapproved fixture must not be eligible for scoring"
print(f"PASS: HTTP {status}")
print("PASS: future article excluded; future price excluded from 2026-10-17 snapshot")
print("PASS: descriptive return is 5%; investment ranking remains disabled")
PY

echo
echo "All requested research acceptance checks passed."
