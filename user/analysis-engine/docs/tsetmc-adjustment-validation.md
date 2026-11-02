# TSETMC adjusted-history reconciliation (فولاد)

This is a bounded, read-only investigation of historical-price anomalies. TSETMC
adjusted-chart data is retained as a provider-supplied candidate series; this does
**not** enable TSETMC in scoring.

## Validate source payloads

From the repository root, with the analysis-engine environment active:

```bash
python user/analysis-engine/scripts/validate_tsetmc_adjustments.py \
  --symbol "فولاد" \
  --instrument-code "46348559193224090" \
  --out-dir /tmp/marketsage-tsetmc-adjustments
```

The probe requests exact instrument identity, daily history, adjustment events,
and the legacy chart with adjustment disabled/enabled. It writes the raw payloads
and date-level comparisons:
- `tsetmc_adjustment_validation_report.json`
- `anomaly_date_comparison.json`
- `chart_adjustment_differences.csv`
- `daily_history_raw.json`, `price_adjustments_raw.json`,
  `chart_unadjusted_raw.json`, `chart_adjusted_raw.json`

## Build the adjusted-price candidate dataset

Once the files above exist, build a reproducible CSV directly from the saved
daily history and provider's adjusted chart. No price-adjustment factor is
estimated from the event table.

```bash
python user/analysis-engine/scripts/build_tsetmc_adjusted_dataset.py \
  --data-dir /tmp/marketsage-tsetmc-adjustments \
  --instrument-code "46348559193224090" \
  --out-csv /tmp/foulad_adjusted.csv \
  --out-report /tmp/foulad_adjustment_quality_report.json
```

The CSV preserves the raw daily fields and maps the adjusted chart into
`open_adj`, `high_adj`, `low_adj`, `last_adj`, `close_adj` and
`chart_volume`. A missing adjusted-chart date is retained as a blank adjusted
price, not replaced with a raw price or interpolated. The report states coverage,
date range and the adjusted/raw close ratio distribution for scale checking.

The current observations previously collected for فولاد contained 4,664 raw daily
rows and 4,249 adjusted chart rows. Those figures describe that saved capture only,
not a guaranteed future endpoint coverage contract.

## Explicit live ingestion into the point-in-time store

```bash
python user/analysis-engine/scripts/ingest_tsetmc_adjusted_history.py \
  --instrument-code "46348559193224090" \
  --store-path /tmp/marketsage-temporal.sqlite3
```

This is opt-in and is not scheduled automatically. Both daily history and adjusted
chart requests must succeed and parse before the adjusted series is appended. The
store preserves a distinct `daily_ohlcv_adjusted_candidate` series with raw prices
kept under `raw_*` fields. `close_candidate` is the provider-adjusted close only;
it is null when the adjusted chart lacks that date. Original source publication
time remains unknown.

## Reconciliation and decision rules

Do not assume an anomaly is explained just because an adjustment event exists
nearby. Inspect whether:
- the chart endpoint returns both series for an anomalous date;
- the unadjusted chart agrees with raw daily fields where both are available;
- adjusted price changes and volume behavior are internally consistent;
- relevant events and pre/post-event prices are plausible;
- the same pattern holds for old and recent dates.

The legacy chart endpoint's positional fields are not a stable official schema.
The empirical mapping (high, low, open, last-traded price, volume, close) is used
only as a candidate contract; it is preserved in code and must be rechecked if the
provider response changes.

Even successful price reconciliation does not approve collection/redistribution
rights, units, corporate-action completeness, suspensions, historical depth, or
point-in-time availability. TSETMC remains blocked from production scoring by the
source registry.
