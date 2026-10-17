# Market data source onboarding

This document tracks integration status and acceptance gates for the currently implemented adapters. Registry presence is not production approval; source scoring remains fail-closed until explicit review.

## Tindex public API (free-tier)

The Tindex connector is opt-in and read-only. It uses an HTTPS origin and Bearer token from environment variables, limits requests locally to 3/minute, does not automatically retry 401/403/410/429, and treats HTTP 410 as a disabled endpoint. The provider's current dashboard notice disables Iranian equities/TSE, news/articles, inflation/macroeconomics, housing, calendar, and indicators in disabled categories. Do not bypass this by scraping alternate routes.

A real authenticated request to `/api/public/currency-rates` returned HTTP 200 with `success` (boolean) and `data` (list); observed records contained `key` (string), `name` (string), `rate` (integer or float), and `decimals` (integer). `tindex_normalizer.py` validates these types and preserves `rate` as Decimal. It deliberately leaves units, market definition, observation/retrieval times unknown and `eligible_for_scoring=False`. This does not prove Rial/Toman, official/free-market meaning, history depth, licensing or model-training permission.

Provider quota supplied by the project owner: 3 requests/minute, 300 successful requests/day, one active token. Cache responses and avoid repeated live probes.

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
