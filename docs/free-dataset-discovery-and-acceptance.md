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
| Tindex | Free-tier account, environment token/origin required | Current currency snapshot and some indicator candles | Current public docs state 1 request/minute and 100 successful requests/day, indicator history up to 100 days, and Toman values since 2026-07-20; account payload, unit semantics and usage rights still require reconciliation |
| Nerkhsanj rates archive | Publisher-announced no-key JSON candidate (not yet live-verified) | Potential daily Iranian free-market FX, gold and coin history | Publisher announcement claims selected series back to 2010 and Toman values; actual schema, lineage, rights, attribution and history coverage are not yet verified |
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

The current public Tindex Free-plan docs state 1 request/minute and 100 successful requests/day, shared by account. The local in-memory guard is process-wide but not persistent or account-wide across other processes/hosts. The guarded runner now supports one optional slug, for example `--live-iran --include-tindex --tindex-slug "USD-EXCHANGE-RATE"`; do not poll a second slug until at least 60 seconds have elapsed. Never paste tokens into chat, command arguments, output reports, or Git. Tindex docs also describe currency-rate values as Toman per quoted unit; the project keeps units unconfirmed until the current account payload and an independent reference reconcile.

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

**VPN must be OFF before this live request.** Tindex is an Iran-provider flow in the guarded runner and requires the exact interactive `VPN-OFF` confirmation. The current public Free tier permits **one request/minute and 100 successful requests/day**. Probe only one slug per invocation:

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
bash scripts/run_free_dataset_acceptance_pack.sh \
  --live-iran --include-tindex --tindex-slug "GOLD-18K"
```

After at least 60 seconds, repeat only for another required slug, for example `USD-EXCHANGE-RATE` or `btc`. Do not run concurrent Tindex clients/jobs; the local guard is process-memory only and cannot see other machines sharing the account quota.

A disabled slug, 403/410 response, 429, or missing series remains a failure—not an empty price or a reason to switch to another route. The public developer docs say currency rates are quoted in Toman and that Markets & Indicators values are in Toman since 2026-07-20; keep the normalized unit unknown until the actual enabled-account payload and a lawful independent reference reconcile. The documented history window is only about 100 days, so this source alone cannot validate a six-month strategy. Never pass tokens as CLI arguments.

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


## Additional Iranian rate-history candidate: Nerkhsanj (discovery only)

The publisher's October 2026 announcement describes a no-key API at `https://nerkh.jahankhahan.shop` with `/data/live.json`, `/data/rates.json` and `/data/intraday.json`, claiming daily archive coverage since 2010 for selected FX/gold/coin/crypto series. It also describes Toman values and Jalali dates and asks for Nerkhsanj attribution/link. Source lineage, endpoint availability/schema, the series inventory, daily coverage, revision behavior, and the legal/commercial rights are **not independently verified**. It is registered as a candidate only; no live request was made in this update.

Before a bounded live request to this external host, **turn VPN ON first**. Start with a single request to the announced rates archive; do not request `/calc` once per date or instrument. Capture only sanitized schema metadata. Build a typed parser only after an observed response is reviewed and committed as a sanitized fixture. Do not store raw rows, infer source licensing, or allow the candidate into scoring.

Announcement references (publisher-authored, not independent proof of accuracy):
- [WebNuz announcement](https://www.webnuz.com/article/2026-10-06/A%20free%2C%20keyless%20JSON%20API%20for%20Iran%27s%20free-market%20exchange%20rates%20%28with%20a%20daily%20archive%20since%202010%29)
- [DEV.to announcement](https://dev.to/hamidjh80arch/a-free-keyless-json-api-for-irans-free-market-exchange-rates-with-a-daily-archive-since-2010-k6f)

## Owner-run multi-asset collection snapshot (2026-10-22; discovery only)

The project owner reported one local run of an exploratory multi-asset collector. Only the aggregate console summary is available in this repository; no raw responses, price rows, headline text, or credentials are copied here.

| Reported measure | Result |
|---|---:|
| Source endpoints attempted | 17 |
| HTTP-accessible sources | 13 |
| Failed sources | 4 |
| Normalized market rows | 7,637 |
| Price series with rows | 8 |
| RSS source-items | 180 |
| RSS unique items | 180 |

Reported failures:
- Binance Spot `BTCUSDT`, `ETHUSDT`, and `SOLUSDT`: HTTP 451. Treat this as an access/legal restriction and leave these requests blocked. Do not try alternate hosts or routes to bypass the response; use a separately reviewed source only if it is available under its own terms.
- Tasnim RSS: DNS/name-resolution failure. This indicates a network resolution problem for that attempt, not that the publisher has no usable data. Do not retry repeatedly without first checking the host/network resolution.

The console summary reported eight price series, but the collector attempted three TGJU pages and six Yahoo chart proxies. Since that implies up to nine candidate series, the console output is insufficient to identify the missing/empty series or determine whether a parser recognized every page. The local run's `source_status.csv`, `collection_quality_report.json`, and `run_manifest.json` must be reviewed together for per-source parsed-row counts, schema status, and coverage. Do not infer which series was missing from the aggregate counts alone.

Important limitations of this exploratory run:
- The collector invoked Iranian page sources, foreign market sources, and RSS publishers in one run. Future runs must use the repository's separated network groups / VPN confirmations; Iranian sources, foreign sources, and Persian RSS should be run in distinct invocations.
- The initial standalone collector labeled TGJU quotes with IRR-like unit identifiers even though the actual quote convention has not been independently confirmed. Treat those unit labels as provisional and do not use the series in cross-asset returns or ranking until the unit is reconciled. Future collector revisions must preserve the unit as unknown/unconfirmed until verified.
- Public accessibility, row count, a parsable chart, or the weak Persian keyword sentiment output do not prove collection rights, commercial reuse, accurate publication times, correct units, predictive value, or eligibility for scoring.
- All data remains discovery/research-only. This run changes no registry approval flags; production scoring, investment ranking, and backtest approval stay disabled.

Next action is a source-by-source review of the local summary metadata—not another identical collection run. Resolve the eight-versus-nine series discrepancy, unit semantics, price-series coverage, RSS publication-time completeness, and the two distinct failure classes. Then carry forward only the series with explicit source/asset/unit/time contracts into the common research data layer.

## Owner-run controlled foreign probe snapshot (2026-10-22; VPN reported enabled)

The project owner shared the aggregate console output from a bounded foreign-source probe. The run attempted nine source requests: three Binance Spot pairs and six Yahoo chart symbols. The console summary reported eight accessible results, one failure, 18 market rows across eight series, and no news requests. The log specifically identified one failure: `yahoo.chart.EURUSD=X`, a TLS handshake timeout.

Interpretation:
- The BTCUSDT, ETHUSDT and SOLUSDT probe attempts emitted no individual failure lines in the shared log. Treat them as probe-level reachability evidence only; this does not establish multi-year history coverage, uninterrupted daily candles, exact venue/quote semantics, or usage rights.
- Five of the six Yahoo chart symbol requests emitted no individual failure line. EURUSD=X timed out during TLS; this is a connection failure for that attempt, not evidence that EUR/USD data is unavailable. Reuse the already captured five-year series from the earlier collection rather than redownloading it merely to repeat the same probe.
- Only 18 market rows were reported in this run, so this was not a new five-year ingestion.
- Do not retry all nine sources as a batch. Investigate EURUSD=X only if this series is needed and the failure persists during a later scheduled refresh; first review the detailed status report for timeout phase and prior successful history coverage.
- Foreign probes must continue to be performed with VPN enabled and separate from Iran-provider probes. No source approval, scoring permission, or backtest approval follows from this snapshot.

## Owner-run one-shot Nerkhsanj archive probe (2026-10-22)

The project owner ran `scripts/probe_nerkhsanj_archive.py` from the repository commit fetched from `feature/free-dataset-discovery-acceptance`, after explicitly confirming VPN was ON. The single HTTPS request completed and the metadata-only parser reported:

- `status=probe_completed`
- `schema_status=candidate_schema_parsed`
- `series_count=28`
- `raw_values_emitted=false`
- `raw_payload_saved=false`
- `production_approved=false`, `eligible_for_scoring=false`

This is the first successful live schema/series-count evidence for this source. The report and console output shared so far do not enumerate the full per-series summary, so no particular key is yet claimed to be gold, a coin, or free-market FX. The probe performs lexical Jalali date checks only, not full Jalali calendar validation, and it does not establish rate units, upstream lineage, completeness, source accuracy, independent reconciliation, attribution requirements, or commercial/model-use permissions.

Next step: inspect the existing local report `/tmp/marketsage-nerkhsanj-probe.json` for per-series keys, counts, and date bounds. Select only clearly identified target candidates, then reconcile dates/units against a separate lawful source before normalizing them into the shared MarketSage research store. Do not rerun the archive fetch just to list these already captured metadata fields, and do not infer market meaning from a key string alone. No registry or scoring approval changes follow from this probe.
