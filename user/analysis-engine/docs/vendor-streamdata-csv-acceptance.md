# Seller-provided StreamData CSV exports: acceptance and local normalization

The user received four CSV exports from a data seller. They are not treated as free
public data, and the raw files are deliberately not stored in this public repository.

## Files recognized by the local-only audit

| Candidate series | Filename | Observed rows in the supplied capture |
|---|---|---:|
| AYAR gold fund | `Ayar_Gold_Fund_1D_StreamData.csv` | 123 |
| BTC/USDT | `BTCUSDT_1D_StreamData.csv` | 184 |
| 18K gold | `Gold18_1D_StreamData.csv` | 184 |
| Free-market USD | `US_Dollar_1D_StreamData.csv` | 176 |

These counts apply only to the supplied archive captured on 2026-10-19; they are not
a promise of the feed's normal history depth.

## Run the local audit

Extract the ZIP to a directory without copying the data into Git, then run:

```bash
python user/analysis-engine/scripts/audit_streamdata_vendor_exports.py \
  --data-dir "$HOME/Downloads/Telegram Desktop/4_Symbols_Data_StreamData" \
  --out-dir "$HOME/marketsage-free-source-audit/streamdata"
```

The audit produces:
- a report, `streamdata_validation_report.json`;
- one normalized candidate CSV per input series;
- SHA-256 hashes for provenance checks;
- date range, duplicate/out-of-order rows, time-field variants, invalid prices,
  OHLC consistency anomalies, calendar gaps and close-return diagnostics.

It intentionally does not infer price units, currency, timezone, candle boundary,
adjustment status, venue, or licensing rights. It does not fill missing dates,
repair anomalous rows or enable scoring. OHLC anomalies remain in the candidate CSV
with an explicit false flag rather than being silently modified.

## Initial audit of the delivered capture

The four CSVs have the expected seven-column layout:
`<DTYYYYMMDD>, <TIME>, <OPEN>, <HIGH>, <LOW>, <CLOSE>, <VOL>`.
No duplicate dates or source-order inversions were observed in the supplied capture.
BTCUSDT and Gold18 each contain 184 consecutive calendar-day rows, the USD export
contains 176 rows across the same overall date window, and the AYAR file contains
123 rows. These differences should be interpreted against the actual instrument
calendar and export contract, not automatically classified as missing trading
sessions.

One AYAR row dated 2026-10-14 has `CLOSE=715981` above `HIGH=714820`. It must be
reconciled against the seller's original source before use. AYAR also contains five
different raw `<TIME>` values across the capture, while the other three files use
`033000`; the clock and timezone meaning are not documented in the export.

## Required gates before research or display

1. Obtain the seller/provider identity, invoice/contract, and rights for internal
   analysis, derived metrics, backups, user-facing display and redistribution.
2. Confirm exact instrument/venue identity, currency, price unit (Rial/Toman/other),
   quote/base convention, volume definition and whether rows are raw or adjusted.
3. Confirm timezone, `<TIME>` meaning, candle close boundary and market calendar.
4. Reconcile every anomaly and price level against a permitted independent reference.
5. Confirm corrections, revised history, export versioning, missing intervals and
   supported history depth.
6. After acceptance, add explicit units and source metadata, then run a chronological
   research evaluation with point-in-time and transaction-cost controls.

The registry source `vendor.streamdata_export` is a candidate only. A complete CSV
audit is not source approval and is not proof of predictive value.
