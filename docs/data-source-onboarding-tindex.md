# Tindex public API connector (free-tier onboarding)

## Scope and safety

This connector is an opt-in, read-only adapter for the currently enabled Tindex developer API. It supports the documented public endpoint paths for currency rates, public boards/categories, indicator movers, and indicator history/candles. The provider's current dashboard notice takes precedence over older docs: Iranian equities/TSE, news/articles, inflation/macroeconomics, housing, calendar, and indicators from disabled categories are unavailable (410 Gone).

The connector:
- uses a Bearer token from environment variables; no token is committed or printed;
- requires the API origin to be copied from the current Tindex developer documentation (the hostname is deliberately not guessed);
- uses HTTPS only and allows only named endpoint methods, not arbitrary URLs;
- locally limits a process to 3 requests/minute and does not retry 401/403/410/429;
- treats 410 as disabled, not as an empty dataset or an invitation to scrape another route;
- does not infer a schema, unit, timestamp, license, history depth, or production eligibility from HTTP 200;
- is not yet wired to scoring or the point-in-time store. Production scoring remains fail-closed.

The local minute limiter is per process; Tindex's own quota is authoritative, particularly if multiple workers run. Provider documentation currently states 300 successful requests/day and one active token. Cache responses before scheduling recurring pulls.

## Local setup

1. Open the current Tindex developer dashboard and create a token for MarketSage. Do not send the token in chat or commit it.
2. Copy the API origin (scheme + hostname, without `/api/public`) from the current API docs. Do not guess it from the marketing website.
3. In your local shell, set:

   ```bash
   export TINDEX_API_BASE_URL='https://<API-origin-from-current-docs>'
   export TINDEX_API_TOKEN='<token-created-in-dashboard>'
   ```

4. Install the analysis service development dependencies and run tests:

   ```bash
   cd user/analysis-engine
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   pytest -q tests/test_tindex_provider.py
   ```

5. To make a live, one-request connectivity probe, run:

   ```bash
   python scripts/probe_tindex.py
   ```

   This calls only `/api/public/currency-rates`, prints HTTP/shape metadata only, and does not dump market data or credentials. It consumes one successful daily request if the provider returns success. It requires outbound HTTPS from the machine running it.

## What the live probe proves (and does not prove)

- 200 + valid JSON proves only that the configured token can read the currency-rates endpoint at that time.
- 401 means the token is missing/invalid; 403 means the provider may have disabled the account; 410 means the endpoint is disabled; 429 means stop and wait.
- A successful response does not establish history depth, completeness, publication timestamps, Rial/Toman units, corrections, licensing, redistribution, commercial use, or permission to train models.
- Before normalizing values, capture a sanitized sample schema locally and document each field's exact unit, market definition, timestamp semantics, and provider revision behavior. Do not infer that "currency rates" means free-market Iran FX without evidence.
- Do not use Tindex for equities/news/macro/housing after its 410 notice. Do not evade those restrictions by scraping the terminal or undocumented endpoints.

## Acceptance gates before ingestion/backtests

1. Written permission/terms for automated collection, durable storage, backtesting, AI/model training, and commercial display/use.
2. Sanitized payload fixture and schema tests for each intended data family.
3. Verified instrument/series identity and currency/quote convention (Rial vs Toman must be explicit).
4. Observed timestamps, retrieval timestamps, timezone, revisions/corrections, missing intervals, historical depth, and freshness checks.
5. Reconciliation against an independent source and immutable raw response/checksum retention.
6. Point-in-time replay tests proving no future publication or later revisions leak into earlier decisions.
7. Separate source-registry review and explicit production approval. Until then, this connector is research-only and cannot feed live scores.

## Current quotas and caching

The supplied current dashboard text says 3 requests/minute, 300 successful requests/day, and at most one active token on the free tier. Do not poll every symbol separately. First use a single board/rates response where suitable, inspect actual payload shape, and build a cache with explicit expiry and source/retrieval metadata. Do not assume that the history endpoint is a raw full-history export; the docs describe history as chart-oriented and candles as resampled daily/weekly/monthly data.
