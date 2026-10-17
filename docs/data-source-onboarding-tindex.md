# Tindex public API connector (free-tier onboarding)

## Scope and safety

This opt-in, read-only connector targets only the currently enabled Tindex public API surfaces: currency rates, public boards/categories, indicator movers, and indicator history/candles. The provider's current dashboard notice takes precedence over older documentation: Iranian equities/TSE, news/articles, inflation/macroeconomics, housing, calendar, and indicators in disabled categories are unavailable (410 Gone).

The connector:
- uses a Bearer token from environment variables; no token is committed or printed;
- requires the API origin from the current Tindex developer dashboard and HTTPS;
- exposes named endpoint methods rather than arbitrary URLs;
- locally limits a process to 3 requests/minute and does not automatically retry 401/403/410/429;
- treats 410 as disabled, not as empty data or permission to scrape another route;
- is not wired into scoring or a point-in-time store. Production scoring remains fail-closed.

The local minute limiter is per process; the provider quota remains authoritative, particularly with multiple workers. The currently supplied provider quota says 300 successful requests/day and one active token. Cache responses before recurring pulls.

## Confirmed currency-rates response shape

A real authenticated request to `/api/public/currency-rates` returned HTTP 200 with an object containing `success` (boolean) and `data` (list). The observed records contained `key` (string), `name` (string), `rate` (integer or float), and `decimals` (integer). This is a shape observation, not a semantic data dictionary.

`user/analysis-engine/tindex_normalizer.py` validates this envelope and those primitive types. It converts `rate` to `Decimal` for precision and keeps the provider's `decimals` as metadata. It intentionally leaves `unit`, `market_definition`, `observed_at`, and `retrieved_at` unknown and sets `eligible_for_scoring=False`. It rejects malformed values and duplicate instrument keys. This does **not** establish whether a quote is Rial or Toman, official or free-market, or what `decimals` means operationally.

## Local setup

1. Create a token in the Tindex developer dashboard. Do not send it in chat or commit it.
2. Copy the API origin (scheme + hostname, without `/api/public`) from current API documentation.
3. Set environment variables in your local shell:

   ```bash
   export TINDEX_API_BASE_URL='https://<API-origin-from-current-docs>'
   export TINDEX_API_TOKEN='<token-created-in-dashboard>'
   ```

4. From `user/analysis-engine`, install development dependencies and run the focused offline suite:

   ```bash
   pip install -r requirements.txt
   python -m pytest -q tests/test_tindex_provider.py tests/test_tindex_normalizer.py
   ```

5. The one-request probe is optional and only for connectivity diagnostics:

   ```bash
   python scripts/probe_tindex.py
   ```

   It calls only `/api/public/currency-rates`, prints shape metadata only, and consumes a successful daily request. Do not repeatedly run it; a live request has already confirmed the response envelope.

## What a successful request proves—and does not prove

HTTP 200 plus valid JSON proves only that the configured token could read the endpoint at that moment. It does not establish historical depth, completeness, publication timestamps, Rial/Toman units, official/free-market definition, corrections, licensing, redistribution, commercial use, or model-training permission. Do not infer that “currency rates” necessarily means free-market Iranian FX.

## Acceptance gates before ingestion/backtests

1. Written terms/permission for automated collection, durable storage, backtesting, AI/model training, and commercial display/use.
2. Sanitized fixture/schema tests for each data family intended for use.
3. Verified instrument identity, market definition, currency and quote convention.
4. Verified observation/publication timestamps, retrieval timestamps, timezone, revisions, missing intervals, history depth, and freshness checks.
5. Reconciliation against an independent source and immutable raw response/checksum retention.
6. Point-in-time replay tests proving no future publication or later revision leaks into earlier decisions.
7. Separate source-registry review and explicit production approval. Until then, Tindex remains research-only and cannot feed live scores.

## Current quotas and caching

The current supplied dashboard text says 3 requests/minute, 300 successful requests/day, and at most one active token on the free tier. Avoid polling every symbol separately. Do not assume history endpoints are full-history exports; the docs describe history as chart-oriented and candles as resampled daily/weekly/monthly data.
