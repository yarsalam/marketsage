# Tindex historical candle candidate ingestion

Tindex documents `GET /api/public/indicators/{slug}/candles` as a columnar OHLC
series. Its response fields `t,o,h,l,c,partial` are parallel arrays. The `t`
array is integer days since 1970-01-01, delta-encoded after the first element.
The provider's `unit` field is preserved without converting or guessing it.

The current Tindex developer documentation says supported candle windows are
`1m` and `3m`, intervals are `daily` or `weekly`, and longer history is
clamped to at most 100 days. This is a charting feed, not evidence of a complete
long-term total-return history. It cannot by itself validate a six-month strategy.
See the official reference: https://tindex.app/en/developers/

## Explicit, single-slug ingestion

The client requires the user's own environment configuration. Never paste a token
into the command line, source file, log or GitHub. Each invocation fetches one slug
and respects the local request cooldown.

```bash
cd ~/projects/marketsage-acceptance || exit 1
source user/analysis-engine/.venv/bin/activate

read -r -p "Tindex API origin (HTTPS origin only): " TINDEX_API_BASE_URL
export TINDEX_API_BASE_URL
read -r -s -p "Tindex token: " TINDEX_API_TOKEN
echo
export TINDEX_API_TOKEN

python user/analysis-engine/scripts/ingest_tindex_candles.py \
  --slug "GOLD-18K" \
  --range 3m \
  --interval daily \
  --out-csv "$HOME/marketsage-free-source-audit/tindex-gold18-candidate.csv"
```

Run separate invocations for other confirmed slugs, for example `USD-EXCHANGE-RATE`
or `btc`, allowing the configured local cooldown between calls. Do not assume that
a documented slug is enabled for the user's token; HTTP 410 means disabled and is
preserved as a failed attempt, never as an empty series.

## Stored representation

- The raw response is stored separately and hashed.
- The table `iran_candle_observations` stores decoded dates, OHLC values, reported
  provider unit, interval and the provider's `partial` flag.
- Retrieval time is recorded, but the original publication time is not invented.
- Malformed lengths, non-monotone dates, mismatched count/range/interval, and OHLC
  invariant violations fail closed.
- The ingestion is opt-in and is not scheduled automatically.
- All rows are `eligible_for_scoring = false`; this helper is not a public-display
  endpoint.

## Limits before market use

Even if the endpoint works, data acceptance still requires confirmation of the
account's enabled scopes, seller/provider contract, internal research and derived-data
rights, instrument and venue identity, unit meaning, source timestamp semantics,
revision policy, and independent reconciliation. Historical depth is at most 100
days in the documented candles interface, which is insufficient alone for long
historical validation of a six-month strategy. Do not concatenate Tindex series with
seller-provided CSVs until symbol/venue/price definition, timezone, price unit and
overlapping date values have been reconciled.
