# Iranian market data integration status

MarketSage is being extended toward a single release with independent data adapters
for Iranian equities, gold/coins, FX and crypto. A common release does **not** mean
mixing raw price series or applying one model to every asset class.

## Current implementation

- `iran_market_data.py` defines the provider readiness catalog and a fail-closed
  data contract: market, symbol, observation date, price, currency, price unit,
  source, retrieval timestamp, adjustment flag and optional volume.
- `GET /iran-market/providers` exposes provider readiness and candidate source
  information for UI/admin diagnostics.
- Unit and provenance checks reject non-positive/non-finite prices, duplicate
  daily observations, unknown units, naive retrieval timestamps, future observations
  and stale rows. Missing observations are not filled.
- `tsetmc_adapter.py` now has a separate adjusted-series parser and explicit
  `ingest_adjusted_history()` entry point. It joins raw daily history to the TSETMC
  legacy chart with `a=1`, stores raw values alongside adjusted candidates, and
  marks the series `daily_ohlcv_adjusted_candidate`.
- `scripts/build_tsetmc_adjusted_dataset.py` rebuilds a CSV and coverage report from
  the saved raw validation payloads. `scripts/ingest_tsetmc_adjusted_history.py`
  is the manual opt-in path for saving the candidate series in the point-in-time
  SQLite store.
- Missing adjusted-chart dates are retained as rows with null adjusted prices.
  There is deliberately no fallback to raw daily prices and no forward-fill.
- TSETMC candidates remain **disabled for production scoring**. The adjusted
  chart is a legacy positional endpoint; the field mapping is empirically compared
  to the raw daily history but is not a stable official schema contract. Rights,
  Rial/Toman convention, historical completeness, suspensions and original
  publication timestamps remain unverified.

## Rebuild the saved فولاد dataset

From the repository root, after running the validation probe and preserving its
raw response files:

```bash
python user/analysis-engine/scripts/build_tsetmc_adjusted_dataset.py \
  --data-dir /tmp/marketsage-tsetmc-adjustments \
  --instrument-code 46348559193224090 \
  --out-csv /tmp/foulad_adjusted.csv \
  --out-report /tmp/foulad_adjustment_quality_report.json
```

## Explicit live candidate ingestion

This command makes read-only requests to TSETMC and writes a quarantined candidate
series to a local SQLite point-in-time store. It is not started by the API service
or scheduled automatically.

```bash
python user/analysis-engine/scripts/ingest_tsetmc_adjusted_history.py \
  --instrument-code 46348559193224090 \
  --store-path /tmp/marketsage-temporal.sqlite3
```

Only run collection where permitted by the applicable source terms. A successful
ingestion result means that payloads were captured; it does **not** grant
production-scoring approval.

## Seller-provided StreamData CSV exports

- `vendor.streamdata_export` is registered as a separate candidate source.
- `scripts/audit_streamdata_vendor_exports.py` reads the seller's CSVs from a local
  directory, writes candidate-normalized copies and a JSON QA report, and emits
  SHA-256 hashes. It does not copy proprietary source CSVs into Git or infer units,
  currency, timezone, or price-adjustment status.
- The export capture currently has an AYAR OHLC inconsistency (close exceeds high on
  2026-10-14) and varying source-time values for AYAR. The other series also require
  confirmation of source/venue identity, price units, timezone and raw/adjusted
  semantics. See `docs/vendor-streamdata-csv-acceptance.md`.
- These feeds are not wired to portfolio allocation, research scoring, or automatic
  scheduled ingestion; `eligible_for_scoring` remains false until seller terms and
  data conventions are confirmed and independent reconciliation is complete.

## Release gates per provider

1. Confirm terms/permission and availability from the actual production host.
2. Capture representative responses and build a parser against versioned fixtures.
3. Reconcile symbols and historical observations against an independent reference;
   explicitly test adjusted prices, suspensions, actions and missing dates.
4. Validate freshness, timezone, Rial/Toman convention, instrument multipliers and
   corporate actions.
5. Run automated tests and a period-by-period historical data-quality report.
6. Enable scoring only after review; otherwise expose `not_configured` /
   `candidate_requires_validation` and no fabricated quote or score.

Gold/coin, FX and local crypto sources are intentionally not selected in this change:
their source, rights, history depth and units need verification before a production
choice. Existing global-proxy/crypto research behavior is unchanged.
