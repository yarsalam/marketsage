# Iranian market data integration status

MarketSage is being extended toward a single release with independent data adapters
for Iranian equities, gold/coins, FX and crypto. A common release does **not** mean
mixing raw price series or applying one model to every asset class.

## Current implementation

- `iran_market_data.py` defines the provider readiness catalog and a fail-closed
  data contract: market, symbol, observation date, price, currency, price unit,
  source, retrieval timestamp, adjustment flag and optional volume.
- `GET /iran-market/providers` exposes provider readiness and candidate source
  information for UI/admin diagnostics.
- Unit and provenance checks reject non-positive/non-finite prices, duplicate
  daily observations, unknown units, naive retrieval timestamps, future observations
  and stale rows. Missing observations are not filled.
- Iranian instruments remain **disabled for scoring** until their source payloads,
  historical coverage, licensing/usage permissions, unit conventions, corporate
  actions and production-network availability are verified.
- TSETMC URLs in the catalog are discovery candidates based on community
  documentation, not a promise of a stable or officially supported API.

## Release gates per provider

1. Confirm terms/permission and availability from the actual production host.
2. Capture representative responses and build a parser against versioned fixtures.
3. Reconcile symbols and at least several historical observations against an
   independent reference; explicitly test adjusted prices, suspensions and gaps.
4. Validate freshness, timezone, Rial/Toman convention, instrument multipliers and
   corporate actions.
5. Run automated tests and a period-by-period historical data-quality report.
6. Enable scoring only after review; otherwise expose `not_configured` /
   `candidate_requires_validation` and no fabricated quote or score.

Gold/coin, FX and local crypto sources are intentionally not selected in this change:
their source, rights, history depth and units need verification before a production
choice. Existing global-proxy/crypto research behavior is unchanged.
