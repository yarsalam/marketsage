# Market data source onboarding

This document tracks integration status and acceptance gates for the currently implemented adapters. Registry presence is not production approval; source scoring remains fail-closed until explicit review.

## Tindex public API (free-tier)

The Tindex connector is opt-in and read-only. It uses an HTTPS origin and Bearer token from environment variables, enforces the current documented free-tier ceiling of 1 request/minute and 100 successful requests/day with a process-memory guard, does not automatically retry 401/403/410/429, and treats HTTP 410 as a disabled endpoint. The local daily guard is not persistent and cannot account for other processes/hosts using the same token; provider-side quota remains authoritative. The provider's current dashboard notice disables Iranian equities/TSE, news/articles, inflation/macroeconomics, housing, calendar, and indicators in disabled categories. Do not bypass this by scraping alternate routes.

A real authenticated request to `/api/public/currency-rates` previously returned HTTP 200 with `success` (boolean) and `data` (list); observed records contained `key` (string), `name` (string), `rate` (integer or float), and `decimals` (integer). `tindex_normalizer.py` validates these types and preserves `rate` as Decimal. The current public Tindex docs now state that currency-rate `rate` values are expressed in Toman per quoted unit, and that since 2026-07-20 values in Markets & Indicators are returned in Toman. However, until the user's currently enabled account payload and a second lawful reference are reconciled, the normalized `unit` must remain unknown and `eligible_for_scoring=False`. Official/free-market meaning, history completeness, licensing, and model-training permission remain unapproved.

**Current public-docs quota update (2026-10-20):** Free tier documents 1 request/minute and 100 successful requests/day, with one active token. This supersedes the earlier 3/minute and 300/day values recorded in older project notes. Cache responses and avoid repeated live probes. The local process-memory guard cannot enforce account-wide quotas across machines or processes.

Focused test command from `user/analysis-engine`:

```bash
python -m pytest -q tests/test_tindex_provider.py tests/test_tindex_normalizer.py
```

## FRED/ALFRED observations adapter (new, not scheduled)

`fred_alfred_provider.py` provides a read-only adapter for FRED series observations and their realtime/vintage metadata. Configure `FRED_API_KEY` in the runtime environment; never commit the key or include it in logs. The adapter uses the official `/fred/series/observations` endpoint, validates date filters and pagination, normalizes numeric values to Decimal, and represents FRED's `.` missing-value marker as null.

Important temporal distinction:
- `observation_date` is the period the value describes, not its release time.
- `realtime_start` / `realtime_end` are FRED vintage boundaries, not exact publication timestamps.
- `vintage_available_at` is a conservative day-end UTC boundary derived from the vintage date; it is not a claim about the actual release time.
- `publication_timestamp` remains null and `eligible_for_scoring` remains false.

Offline tests use HTTP mocks; they do not consume API quota or contact FRED:

```bash
python -m pytest -q tests/test_fred_alfred_provider.py
```

Before scheduling or scoring, verify each series' release calendar, vintage semantics, key/API limits, units, missing-value patterns, and independent reconciliation. Do not treat a macro observation period date as the time it became known to investors.

## Shared production acceptance gates

For every source, verify:
1. Terms and permission for automated collection, durable storage, backtesting, AI/model training, redistribution, and commercial display/use.
2. Instrument/series identity, units, currency and quote convention.
3. Observation/publication timestamps versus retrieval timestamps, timezone, revisions, missing intervals, history depth, and freshness.
4. Independent reconciliation and immutable raw response/checksum retention where permitted.
5. Point-in-time replay proving that future publications and later revisions cannot leak into earlier decisions.
6. Explicit source-registry review and production approval.

Until these gates pass, new adapters are research-only and must not affect live investment rankings.


## Iranian equity disclosures: TSETMC and CODAL (candidate adapters)

`tsetmc_provider.py` adds a read-only client for instrument search and daily history on the TSETMC CDN JSON surface, plus a conservative history normalizer. The endpoints are reverse-engineered and may change or block non-Iranian IPs. Price units, adjustment methodology, suspensions, trading calendar, legal collection rights and history completeness are not approved. Every normalized row has unknown unit/timestamps and `eligible_for_scoring=False`.

`codal_provider.py` adds a read-only client for the CODAL search endpoint. It preserves the provider-native payload rather than guessing the disclosure schema. Exact publication time, amended/corrected filing linkage, search filters, and historical coverage need sanitized fixtures and reconciliation. Retrieval time is not publication time; scoring remains disabled.

Mocked tests:

```bash
python -m pytest -q tests/test_tsetmc_provider.py tests/test_codal_provider.py
```

## Iranian gold and free-market FX: TGJU candidate, not enabled

TGJU is listed as a candidate source for gold, coin and free-market FX discovery. A verified public API contract and automated-collection/license permission have not been established, so **no live TGJU scraper is enabled**. Do not silently scrape or parse unstable page markup. The source must first pass terms/access review, then fixed sanitized fixtures must confirm series identity, free-vs-official market convention, Rial-vs-Toman unit, update/correction semantics and historical coverage. Keep 18k gram gold, each coin type, USD free-market FX, and official FX as separate series. Tindex may expose currency/precious-metal families, but its current payload semantics are not enough to identify or score these series yet.


## News discovery: GDELT DOC 2.0

`gdelt_news_provider.py` implements a read-only client for the GDELT DOC 2.0 Article List API (`https://api.gdeltproject.org/api/v2/doc/doc`). It supports keyword queries, a bounded result count (1–250), and optional start/end timestamps within the API's supported search window. It canonicalizes article URLs and deduplicates them.

Important limitations:
- GDELT `seendate` is stored as `first_seen_at`, not asserted to be the publisher's original publication timestamp.
- Article titles/metadata are discovery signals, not verified article truth or the full article body.
- Sentiment and political-event type intentionally remain null in this adapter. This avoids manufacturing a signal before a separately tested classifier and labeled evaluation set exist.
- Results are not scheduled and are not eligible for investment scoring. Publisher terms, language/country recall, historical coverage, and real network behavior still require acceptance testing.

The provider's endpoint and query controls are described by the [GDELT DOC 2.0 API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/). The automated tests use HTTP mocks and do not make live requests.

```bash
python -m pytest -q tests/test_gdelt_news_provider.py
```


## Headline sentiment and event-category smoke baseline

`headline_signal_engine.py` provides a transparent Persian/English keyword baseline for headline sentiment and broad category candidates (politics, conflict, sanctions, macro/monetary). It returns the exact matching lexical evidence and abstains with `unknown` where no sentiment terms match. It deliberately does **not** emit a probability, claim a validated model, or permit investment scoring.

The mocked GDELT tests and headline fixtures verify API request construction, response validation, URL deduplication, metadata/timestamp conservatism, known keyword cases, abstention, and auditable evidence. These tests establish code behavior on fixtures only; they do not establish recall/precision on real news or correctness of political-event attribution.

Before this can be called a proven news/sentiment/event engine, build a time-stamped Persian/English benchmark with independently annotated sentiment and event labels, report class-wise precision/recall/F1 and calibration where applicable, check source/language bias and duplicates, and evaluate point-in-time replay. Keep the source gate closed until that evaluation passes.


## Batched source acceptance pack

Run the entire offline analysis-engine test suite from the analysis-engine directory in one command (CI runs the same suite):

```bash
python -m pytest -q
```

The new `tests/test_acceptance_pack.py` adds deterministic batch invariants in a single pytest test invocation:
- 2,000 generated Persian/English headline variants: output shape, evidence/score consistency, and the hard scoring gate.
- 1,000 GDELT URL variants: canonicalization and deduplication, with publication time and sentiment left unknown.
- One registry-wide gate check for FRED/ALFRED, TSETMC, CODAL, Tindex, GDELT, and the headline baseline.

These are regression/robustness checks, not 3,000 independent examples of real-world accuracy. They make no network calls and require no API credentials. The CI result must be reported separately from controlled live smoke checks. For the live stage, run a bounded probe per provider from the intended runtime/network, save sanitized status/schema/latency metadata (never tokens or full sensitive payloads), and do not turn a network response into production approval automatically.


## VPN-aware live source smoke pack

The probe script accepts repeatable `--source SOURCE_ID` arguments. **Do not run the default all-source pack when providers require different VPN states.** Run the Iranian and external probes separately.

All commands below run from `user/analysis-engine`. Use the project's virtualenv interpreter so the command works even when the shell does not provide a `python` alias:

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
PYTHON="$PWD/.venv/bin/python"
```

### Iranian providers — VPN OFF

TSETMC and CODAL make one bounded request each:

```bash
"$PYTHON" scripts/probe_source_acceptance_pack.py \
  --source iran.tsetmc \
  --source iran.codal > source-smoke-iran.json
```

Tindex is optional and must only be included if its environment credentials are configured. Check presence without printing the values:

```bash
if [ -n "${TINDEX_API_BASE_URL:-}" ] && [ -n "${TINDEX_API_TOKEN:-}" ]; then
  "$PYTHON" scripts/probe_source_acceptance_pack.py \
    --source iran.tindex.public_api > source-smoke-tindex.json
else
  echo "Tindex skipped: credentials are not configured in this shell."
fi
```

The Tindex probe calls only the currency-rates endpoint; respect the current provider docs' 1 request/minute and 100 successful requests/day limits.

### External providers — VPN ON

FRED/ALFRED is optional and must only be probed when `FRED_API_KEY` is configured:

```bash
if [ -n "${FRED_API_KEY:-}" ]; then
  "$PYTHON" scripts/probe_source_acceptance_pack.py \
    --source us.fred.alfred > source-smoke-fred.json
else
  echo "FRED skipped: FRED_API_KEY is not configured in this shell."
fi
```

**Do not probe GDELT again immediately:** its previous live request returned HTTP 429. Wait for a deliberate cooldown, then make at most one bounded attempt with VPN on:

```bash
"$PYTHON" scripts/probe_source_acceptance_pack.py \
  --source global.gdelt_doc_api > source-smoke-gdelt.json
```

Do not run the GDELT command until the cooldown/request budget is intentionally chosen. Repeated requests will not improve acceptance evidence and may trigger further rate limiting.

### Interpreting the reports

- `reachable_response_received` means only that a response arrived and its shape was summarized.
- `probe_failed` can indicate connectivity, rate limiting, provider changes, authentication, or a real client defect; classify the cause before changing code.
- `skipped_missing_credentials` is not a failed test.
- Non-zero exit status means at least one selected, attempted probe failed; it does not by itself identify whether the cause was network or code.
- Reports omit raw payloads and credentials, but review them for environment-specific metadata before sharing. Keep generated reports local unless reviewed.
- Live probes never enable scoring. Production eligibility still requires source rights, unit/time semantics, coverage, reconciliation and point-in-time acceptance.
