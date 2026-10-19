# TSETMC adjusted-history reconciliation (فولاد)

This is a bounded, read-only investigation of the historical-price anomalies found in the first live smoke test. It does **not** enable TSETMC in scoring.

## Run locally

From the repository root, with the analysis-engine environment activated:

```bash
python user/analysis-engine/scripts/validate_tsetmc_adjustments.py \
  --symbol "فولاد" \
  --instrument-code "46348559193224090" \
  --out-dir /tmp/marketsage-tsetmc-adjustments
```

The script makes a small, sequential set of read-only requests for:
1. exact instrument identity;
2. daily closing-price history;
3. price-adjustment event history;
4. the legacy chart endpoint with `a=0` (unadjusted) and `a=1` (adjusted).

It writes raw responses as well as a compact comparison:
- `tsetmc_adjustment_validation_report.json`: request/coverage summary and conservative decision;
- `anomaly_date_comparison.json`: the previously flagged dates, daily history row, both chart rows, and same-date adjustment events;
- `chart_adjustment_differences.csv`: dates where the two chart responses differ and the raw positional fields;
- `daily_history_raw.json`, `price_adjustments_raw.json`, `chart_unadjusted_raw.json`, `chart_adjusted_raw.json`: source payloads for audit.

## How to decide

Do not assume an anomaly is explained just because an adjustment event exists nearby. Inspect whether:
- the chart endpoint returns both series for the anomalous date;
- `a=0` and `a=1` actually differ at the date and which positional fields change;
- the adjustment-event record's date and values plausibly explain the difference;
- the daily-history values align with the unadjusted chart series;
- the same pattern holds for recent and older anomaly dates.

The legacy chart endpoint is undocumented and the script deliberately preserves positional fields without assigning undocumented meanings. If the report is incomplete or endpoints disagree, keep the source blocked. Even a successful reconciliation of price fields does not approve collection rights, units, suspensions, corporate-action completeness, point-in-time history, or production scoring.

## Source references

The endpoint paths and legacy chart parameters are documented by community-maintained TSETMC clients, not an official stable API contract:
- `/api/ClosingPrice/GetClosingPriceDailyList/{insCode}/0`
- `/api/ClosingPrice/GetPriceAdjustList/{insCode}`
- `/tsev2/chart/data/Financial.aspx?i={insCode}&t=ph&a={0|1}`

This script is a research probe only. `eligible_for_scoring` remains `false`.
