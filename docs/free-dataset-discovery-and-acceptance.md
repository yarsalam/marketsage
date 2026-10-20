# MarketSage — free-access dataset discovery and acceptance

This workflow turns source discovery into repeatable evidence. It is designed to
prefer sources that do not require purchasing a dataset or subscription while
keeping access cost, legal/data-use rights, data quality, historical coverage, and
predictive value as separate decisions.

**No source in this pack is approved for production scoring.** An HTTP 200, parser
pass, CSV export, green CI run, or complete evidence template does not enable
investment ranking. This workflow never changes `source_registry.py` approval flags.

## Free-access policy

"Free" in this document means no dataset purchase or paid subscription is needed
to make the documented discovery request. It does **not** automatically mean
permission for commercial display, durable storage, redistribution, AI training,
or derived products. Those terms must be reviewed source by source.

Current source catalog: [`free_dataset_source_catalog.json`](free_dataset_source_catalog.json).

### Sources prioritized by this pack

| Source | Free-access path | Useful for | Present caveat |
| --- | --- | --- | --- |
| TSETMC | Public candidate endpoints | Iranian equity/fund search and daily history | Endpoints are reverse-engineered; complete instrument universe, adjusted data, units, access and terms remain unapproved |
| CODAL | Public disclosure search | Financial filings and corporate-event candidates | Retrieval time is not publication time; amendment links and historical coverage need validation |
| World Bank Indicators API | Public API; the current official documentation says API keys are not required | Annual Iranian/global macro series, long historical spans | Annual period is not release timestamp; some series may be missing/revised and are not daily market prices |
| Binance Spot public market data | Public klines endpoint, no API key for public market-data routes | Venue-specific crypto OHLCV | A BTCUSDT candle is not a USD quote or a universal crypto-market price; terms/geographic access remain to be reviewed |
| Tindex | Free-tier account, environment token/origin required | Current currency snapshot and some indicator candles | Account scope and usage rights remain unverified; documented candle history is capped at about 100 days |
| FRED/ALFRED | Free API key | US macro, rates and historical vintages | Observation period is not exact release time; series-specific vintage behavior matters |
| Yahoo Finance / yfinance | Existing no-subscription research path | Global proxies and selected crypto history | Unofficial client/terms and reuse rights need review; not a certified exchange feed |
| GDELT DOC | Public API candidate | News discovery metadata | Earlier request returned HTTP 429; intentionally not part of the default live run |
| Iran Central Bank / Statistical Center | Public portals | Iranian inflation, liquidity and macro releases | No machine-readable end-to-end feed has yet passed acceptance |
| TGJU | Public page candidate only | Gold, coin and free-market FX discovery | No automated scraper is enabled until access/terms, schema and history are verified |

The seller-provided StreamData exports are **not a free source** and are excluded from
the default discovery batch. Their CSV files must stay local unless the vendor
contract explicitly permits the intended storage and use. The existing audit
continues to flag, not repair, the known AYAR OHLC inconsistency.

## Run the pack safely (offline by default)

From the repository root, inspect local changes first and preserve any untracked reports/files:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
```

The default command runs the complete offline test suite, validates the catalog, writes the source inventory and pending evidence templates, and audits only explicitly supplied local CSVs. **It does not contact any provider.**

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
bash scripts/run_free_dataset_acceptance_pack.sh
```

You can also state the offline intent explicitly with `--offline-only`. All generated reports stay outside Git under `/tmp/marketsage-free-dataset-acceptance/`. The pack never turns on source approval, investment ranking, or scoring.

### Iranian provider run — VPN OFF

**Before this live run, turn the VPN off.** The script asks for the exact confirmation `VPN-OFF` before the first network request. If the confirmation is absent/wrong or the terminal is non-interactive, it stops without probing. The script cannot independently verify your VPN state.

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
bash scripts/run_free_dataset_acceptance_pack.sh --live-iran
```

This run probes only TSETMC and CODAL. To explicitly add Tindex candles, only when its token and HTTPS origin are already set securely in environment variables, add `--include-tindex`:

```bash
bash scripts/run_free_dataset_acceptance_pack.sh --live-iran --include-tindex
```

The Tindex candle probe is limited to three slugs/requests in a run. Its quota is shared across endpoints; do not add an additional Tindex currency-rate call to the same batch. Never paste tokens into chat, command arguments, output reports, or Git.

### Foreign/international provider run — VPN ON

**Before this live run, turn the VPN on.** This group includes foreign sites and APIs (World Bank, Binance, and optionally FRED/ALFRED or GDELT). The script asks for the exact confirmation `VPN-ON` before the first network request. If the confirmation is absent/wrong or the terminal is non-interactive, it stops without probing. The script cannot independently verify your VPN state.

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
bash scripts/run_free_dataset_acceptance_pack.sh --live-foreign
```

FRED/ALFRED is **not** contacted unless you explicitly add `--include-fred`; `FRED_API_KEY` must already be configured securely in the environment. GDELT is also explicit opt-in only; add `--include-gdelt` only after choosing a deliberate cooldown/request budget because a previous probe returned HTTP 429.

Do not combine `--live-iran` and `--live-foreign`; the runner refuses mixed groups so that VPN state is unambiguous. Offline tests run before either group. The runner writes separate `iran-live-probes.json` and `foreign-live-probes.json` reports under the local report directory.

The low-level inventory command itself is network-free:

```bash
python scripts/discover_free_datasets.py --mode inventory \
  --output /tmp/marketsage-free-dataset-acceptance/source-inventory.json
```

### Probe a broader TSETMC seed list

Search one exact name per request; exact matches are reported as counts and numeric
instrument-ID availability, not as raw company data. Start with a small seed list,
inspect the report, then expand deliberately:

```bash
python scripts/discover_free_datasets.py --mode probe \
  --source iran.tsetmc \
  --tsetmc-query "فولاد" \
  --tsetmc-query "فملی" \
  --tsetmc-query "فارس" \
  --tsetmc-query "شپنا" \
  --tsetmc-query "شبندر" \
  --tsetmc-query "خودرو" \
  --tsetmc-query "خساپا" \
  --tsetmc-query "شستا" \
  --tsetmc-query "وبملت" \
  --tsetmc-query "وتجارت" \
  --tsetmc-query "وبصادر" \
  --output /tmp/marketsage-free-dataset-acceptance/tsetmc-seed-discovery.json
```

This is a seed-symbol discovery pass, **not** a complete TSETMC instrument master.
The endpoint may return similar instruments, so a discovered numeric `insCode` must
be reconciled with the instrument name/type before collecting history. The existing
TSETMC ingestion/audit scripts remain the history and adjusted-price workflow.

### Probe actual Tindex candles

The shell batch uses the following defaults only if the token/origin are configured:
`GOLD-18K`, `USD-EXCHANGE-RATE`, and `btc`. Each response is handled independently.
A disabled slug, a 410 response or a missing series must remain a failure—not an
empty price or a reason to use yesterday's value.

To test only one known slug:

```bash
python scripts/discover_free_datasets.py --mode probe \
  --source iran.tindex.candles \
  --tindex-slug "GOLD-18K" \
  --output /tmp/marketsage-free-dataset-acceptance/tindex-gold18.json
```

Never pass tokens as CLI arguments; the provider reads them from environment
variables. Historical candle collection already has a dedicated, opt-in persistence
path in `scripts/ingest_tindex_candles.py`; the discovery export is only a small
candidate sample.

## CSV acceptance audit

Use the generic metadata-only auditor on local, candidate CSVs. It recognizes
angle-bracket headers such as `<DTYYYYMMDD>`, `<OPEN>`, `<HIGH>`, `<LOW>`, `<CLOSE>`
and `<VOL>`, reports row/date coverage, duplicate dates, ordering inversions,
missing/non-numeric values and OHLC violations. It never changes source files or
prints raw prices.

```bash
python scripts/audit_candidate_dataset.py \
  /tmp/marketsage-free-dataset-acceptance/candidate-exports/binance_BTCUSDT_1d_candidate.csv \
  /tmp/marketsage-free-dataset-acceptance/candidate-exports/world_bank_IRN_FP.CPI.TOTL.ZG_candidate.csv \
  --out-report /tmp/marketsage-free-dataset-acceptance/csv-quality-report.json
```

The World Bank series is annual and intentionally has no OHLC columns, so the
report will mark OHLC checks as unavailable for that file. That is expected.
World Bank records must not be merged directly into daily prices without a
publication-time/point-in-time policy. For local StreamData files, point the same
auditor at the original CSVs to get a fresh metadata-only report. The auditor does
not validate vendor permission or resolve price-unit ambiguity.

You can pass local files to the one-command runner with repeated `--audit-csv`
options; this only performs a technical audit and does not reclassify vendor-provided
data as free. To audit the four already-supplied local exports without live requests:

```bash
bash scripts/run_free_dataset_acceptance_pack.sh --offline-only \
  --audit-csv "$HOME/Downloads/Telegram Desktop/4_Symbols_Data_StreamData/Ayar_Gold_Fund_1D_StreamData.csv" \
  --audit-csv "$HOME/Downloads/Telegram Desktop/4_Symbols_Data_StreamData/BTCUSDT_1D_StreamData.csv" \
  --audit-csv "$HOME/Downloads/Telegram Desktop/4_Symbols_Data_StreamData/Gold18_1D_StreamData.csv" \
  --audit-csv "$HOME/Downloads/Telegram Desktop/4_Symbols_Data_StreamData/US_Dollar_1D_StreamData.csv"
```

## Source acceptance evidence

Create a pending checklist for every registered provider:

```bash
python scripts/create_source_evidence_templates.py --all \
  --output-dir /tmp/marketsage-source-evidence-templates
```

Each template includes all required checks from the registry. It deliberately
marks every check `pending`; fill reviewer identity, timezone-aware review time,
status and traceable evidence links after verification.

Evaluate one completed evidence file with the existing gate:

```bash
python source_acceptance.py /path/to/completed-source.evidence.json
```

The evaluator can report missing or failed evidence. It cannot register unknown
sources, override the independent registry, or enable scoring. Rights evidence
should separately cover automated collection, durable storage, historical
backtesting, model training, derivative metrics, commercial display and redistribution.

## What "accepted" requires

For every source and series, complete all stages below. An endpoint passing one
stage cannot skip the next:

1. **Discovery:** provider, exact asset/series ID, market/venue, contract/pair,
   and a source-specific contact/documentation URL.
2. **Access test:** actual network from the intended runtime, auth state, HTTP status,
   quota/rate limits and behavior for disabled/missing symbols.
3. **Schema contract:** sanitized/versioned fixtures, field mapping, decimals,
   null/malformed handling and regression tests.
4. **Identity and units:** currency, quote convention, Rial/Toman, instrument multiplier,
   volume meaning, exchange/venue and raw versus adjusted semantics.
5. **Time model:** market timezone/calendar, observation vs publication vs retrieval
   time, candle open/close, revision timing and whether the value was known at a
   historical decision cutoff.
6. **History coverage:** first/last observation, frequency, missing sessions,
   duplicate/out-of-order records, stale spans, suspensions, delistings and corporate
   actions. A 100-day series alone cannot validate a six-month strategy.
7. **Independent reconciliation:** compare a sample of overlapping dates and corporate
   actions against a second lawful source; investigate every material mismatch.
8. **Rights and retention:** record written or official applicable terms for API
   use, caching, database retention, commercial use, model training, derivative metrics
   and redistribution. Public webpage access alone does not resolve this.
9. **Operational reliability:** rate-limit budget, retries/backoff policy, failure
   alerts, checkpointing, checksums, corrections and backup/restore.
10. **Research acceptance:** build a point-in-time dataset, freeze the universe at
    each historical date, then compare baseline strategies with realistic costs in
    chronological walk-forward and holdout tests. Report drawdown, turnover, tail
    risk, calibration and stability—not only total return.
11. **Feature ablation:** add FX/gold, macro, liquidity, news or sentiment one family
    at a time. Keep a feature only if it improves robust out-of-sample outcomes after
    costs and missingness; do not choose weights based only on intuition.
12. **Explicit production review:** only a human-reviewed change to the source registry
    can change a source's approval status. No script in this pack does so.

## Links to official provider documentation

- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api) — the current documentation states that API keys are no longer required.
- [Binance Spot REST API overview](https://developers.binance.com/en/docs/products/spot/rest-api) — public market-data endpoints and IP-based limits; back off on HTTP 429.
- [FRED API](https://fred.stlouisfed.org/docs/api/fred/) — API key, observation and vintage endpoints.
- [Tindex developer docs](https://tindex.app/en/developers/) — current free-tier/API limits and history/candle constraints.
- [GDELT DOC 2.0](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) — article discovery, not a validated sentiment label source.
