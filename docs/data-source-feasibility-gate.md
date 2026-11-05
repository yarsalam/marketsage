# MarketSage — comprehensive data-source feasibility gate

## Decision this audit must answer

Before paying for a server tier, data subscription, or enabling investment ranking, determine whether the target markets can be covered with enough **valid, historical, timestamped, comparable, and legally usable data** to evaluate the financial objective: identify opportunities with attractive expected return for a defined risk budget.

This is a discovery gate, not a marketing checklist. A source is not useful merely because its homepage responds or it advertises many markets.

## Target coverage

Run the one-pass smoke audit across all source families:

- Iran listed equities, ETFs/gold funds, fixed-income instruments and market indices.
- Iran free-market FX, gold, coins and (where available) housing/vehicle indicators.
- Global crypto, gold, silver, oil, USD index, volatility and interest-rate/bond proxies.
- Iran macroeconomic series and global macro drivers.
- News/events as candidate explanatory features only, not a separate product objective.
- Source costs, API quotas, historical depth, reliability and terms of use.

The candidate list deliberately includes free and commercial possibilities. Some are only website reachability checks, and some endpoints are unofficial. They must not be treated as accepted providers without deeper validation.

## Run locally

From the repository root:

\`\`\`bash
cd ~/projects/marketsage-acceptance

# First verify the audit logic without network access.
python3 user/analysis-engine/scripts/probe_market_sources.py --self-test

# Optional: provide Tindex credentials only in this shell; never put them in a file or Git.
read -r -p "Tindex API origin (Enter to skip): " TINDEX_API_BASE_URL
export TINDEX_API_BASE_URL
if [ -n "$TINDEX_API_BASE_URL" ]; then
  read -r -s -p "Tindex API token: " TINDEX_API_TOKEN
  echo
  export TINDEX_API_TOKEN
fi

# One pass across the complete candidate list. It makes one small request per configured source.
python3 user/analysis-engine/scripts/probe_market_sources.py \
  --output /tmp/marketsage-data-feasibility.json

# Show only aggregate results and source status; no raw payloads or credentials.
python3 - <<'PY'
import json
from pathlib import Path
p = Path("/tmp/marketsage-data-feasibility.json")
r = json.loads(p.read_text())
print("PURPOSE:", r["purpose"])
print("SUMMARY:", json.dumps(r["summary"], ensure_ascii=False))
for s in r["sources"]:
    print(
        f'{s["id"]:34} status={s.get("status")} '
        f'http={s.get("http_status", "-")} '
        f'shape={s.get("shape_valid", "-")} '
        f'rows={s.get("row_count", "-")} '
        f'ms={s.get("elapsed_ms", "-")}'
    )
PY

unset TINDEX_API_BASE_URL TINDEX_API_TOKEN
\`\`\`

If the script is located under a different working directory in the current checkout, adjust only the path to the script; keep the report in /tmp. Do not commit the generated JSON or include any token in bug reports.

## Interpret the smoke report correctly

- http_ok + valid shape means only that a small response could be read.
- not_configured for Tindex is expected when credentials were intentionally skipped.
- http_error, network_error, or invalid shape may reflect a temporary outage, regional blocking, endpoint changes, rate limiting, or an incorrect candidate endpoint. Repeat only the affected source after checking its official documentation.
- HTML homepage success does **not** mean a usable API or historical dataset exists.
- A public endpoint does **not** imply permission for commercial reuse, persistent storage, model training, or redistribution.
- Never put secrets in reports, screenshots, logs, commits, or CI output.

## Stage 2 acceptance: evidence required for each source

After the one-pass probe, only the reachable and relevant candidates advance. For each one, capture:

1. Exact series/instrument identifiers and market coverage.
2. History start/end, frequency, missingness, duplicate timestamps and update delay.
3. Units and conventions (IRR vs toman, adjusted vs unadjusted prices, local time zone/calendar, currency and contract rolls).
4. Survivorship, corporate actions, symbol changes, suspensions and delistings.
5. Whether timestamps mean event time, publication time, observation period, or retrieval time.
6. Documented quota, latency, failure rate, and recovery behavior.
7. Written terms: storage, commercial use, model training, derived outputs, caching and redistribution.
8. Measured acquisition/maintenance cost.

A candidate is **not accepted** until these are documented and checked with representative samples. A source smoke report must not change the production scoring flags.

## Stage 3/4: does each variable pay for itself?

Do not assign permanent weights because a variable sounds important. Build a time-aligned feature table and compare the same investment universe and walk-forward splits:

- Baseline: market prices/returns, liquidity, volatility and transaction costs.
- Add macro variables.
- Add FX/gold/cross-market features.
- Add news/event/sentiment features.
- Add other features only when the data is timely and lawful to use.

For each addition, compare net out-of-sample return, drawdown, tail risk, turnover, stability across regimes, and the cost of acquiring and maintaining the feature. Use ablation tests and purged/chronological splits; keep all data point-in-time to avoid look-ahead leakage. Weights may vary over time, but only through a predeclared training/validation process. If an expensive feature does not deliver a robust incremental benefit after costs, exclude it.

No result from the smoke audit is evidence of predictive value. No strategy should be ranked for users until independent evaluation and governance gates pass.

## Current limitations / vendor outreach

- Tindex has been contacted, but no reply has been received yet. The audit can test the configured public API token; it cannot determine a vendor's commercial offer or grant permissions. Ask specifically for historical endpoint coverage, API quotas, commercial terms, model-training/storage rights, a trial, and pricing.
- Terminal subscription pricing is not automatically API pricing. Keep these as separate questions.
- TSETMC public endpoints and third-party wrappers are discovery candidates, not a promise of official commercial access.
- Classified property/vehicle listings are not transaction records. Do not build a price index from scraped listings unless lawful access, deduplication and methodology are established.
- Iran's macro series may be low-frequency, revised, or published with delays. The model must use the value known at the decision time, not a later revised value.

## Release decision rule

Do not decide that the app is server-ready from a passing smoke test alone. The gate should produce one of:

- **Proceed with a limited release**: core price data are accepted, licensed, monitored and sufficient for the advertised features; no unvalidated investment ranking is exposed.
- **Proceed with a narrower product**: some market families have sufficient evidence, others are explicitly disabled.
- **Pause paid infrastructure / paid data**: data coverage, history, legal rights or strategy feasibility is not yet demonstrated.

This audit is intentionally conservative: the cheapest useful dataset is preferable to the largest dataset, provided it improves the financial decision robustly after costs.


## One-command batched acceptance run

From the repository root, after updating the current PR branch without discarding local work:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
git pull --ff-only origin feat/tindex-free-data-connector
cd user/analysis-engine
bash scripts/run_data_acceptance_pack.sh
```

The script runs the full offline test suite once, audits the saved Foolad history fixture if present (otherwise fetches one full history), probes TSETMC/CODAL/Tindex with VPN OFF, then pauses once so FRED/GDELT can be probed with VPN ON. It writes sanitized summaries under `/tmp/marketsage-acceptance/`; it does not save raw provider payloads or secrets. FRED is skipped unless `FRED_API_KEY` is already set. Tindex is skipped unless `TINDEX_API_BASE_URL` and `TINDEX_API_TOKEN` are set. A failed live probe is recorded but does not erase other results; the full offline test suite must pass before live requests start.

The TSETMC history audit sorts observations for calculations but reports the original provider ordering. It flags invalid/duplicate dates, instrument mismatches, missing or nonnumeric fields, non-positive prices, candidate OHLC inconsistencies, large close-to-close returns (default absolute 30%), and calendar gaps over four days. Calendar gaps and return jumps are review flags, not automatic rejections: exchange holidays, corporate actions, price limits and field semantics must be checked separately. It never modifies the source registry or enables scoring.

**VPN / rate-limit note:** start the script with VPN OFF. It intentionally pauses before the external probes. GDELT previously returned HTTP 429, so this script makes only one controlled GDELT attempt; if the provider is still rate-limiting, leave it as pending and do not repeatedly retry. Do not paste tokens into chat or commit them. This run is a consolidated evidence-gathering step, not final legal or predictive acceptance.


### Newly checked vendor documentation notes (2026-10-18)

- Tindex's current public developer documentation describes history/candles as limited to the latest 100 days. That is shorter than MarketSage's approximately six-month evaluation horizon, so Tindex alone cannot supply a complete six-month historical backtest from its documented history endpoints. Use it for a short live/rolling window only unless the provider confirms a different licensed archive/API. The docs also say commercial/high-volume use requires bespoke terms; a free API token is not evidence of commercial reuse rights. See https://tindex.app/en/developers/.
- StreamData's current API docs describe token-authenticated history via `/api/chart/v1/{token}/history`, including daily/weekly/monthly resolutions. Its coverage/price claims on the marketing page are not acceptance evidence. The API token, symbol mapping, historical retention, exact price plan, storage/model-use rights and commercial terms still need provider confirmation before the source can be accepted. See https://streamdata.ir/api and https://streamdata.ir/terms.
- These documentation checks are not live authentication tests. The batch runner prompts for Tindex credentials but does not invent a StreamData token or silently switch MarketSage to a paid provider.
