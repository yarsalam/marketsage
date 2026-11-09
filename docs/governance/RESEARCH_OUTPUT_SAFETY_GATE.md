# Research-only output safety gate

**Status:** default closed; no deployment or environment change performed.

## Why the gate exists

The current decision/portfolio path sends a fixed capital amount to the analysis engine and presents ranked instruments and portfolio weights. The current engine is a limited global-proxy prototype; source approval, Iranian instrument identity, six-month methodology, historical point-in-time completeness, costs, liquidity and out-of-sample validation are not complete.

A disclaimer beside an allocation is not an adequate control. The web UI and API must fail closed until the owner separately approves reopening.

## Protected outputs

The following API routes are blocked unless the explicit feature flag is enabled:
- `GET /api/decision` — ranked decision/portfolio allocation.
- `GET /api/markets/scores` — relative instrument scoring/ranking.
- `GET /api/markets/backtest` — historical strategy/backtest and derived risk metrics.

The UI also does not request or display these outputs while disabled:
- Investment decision and capital allocation.
- Momentum scores/ranks.
- Backtest results and derived risk summaries.

Market coverage, source registry, instrument metadata and operational data-quality views remain available.

## Gate behavior

The NestJS API requires:

```text
MARKETSAGE_RESEARCH_OUTPUTS_ENABLED=true
```

When the variable is absent or is any value other than the exact string `true`, the protected routes return HTTP 503 before calling the analysis service.

The flag is intentionally not added to any deployment environment or example environment file. Do not set it merely to make the UI populate. Enabling it requires a separate explicit owner decision after the relevant data and methodology gates have passed.

## Required evidence before reopening

1. Source-specific legal/access rights and publication/update timestamp semantics.
2. Canonical identity, venue, symbol lifecycle, currency and price unit for each instrument.
3. Representative history, corporate-action/correction handling and missing-interval audit.
4. Point-in-time replay without look-ahead; source-vintage and captured-time availability remain distinct.
5. Predeclared six-month method, benchmark and risk/cost/liquidity assumptions.
6. Walk-forward and locked holdout validation on an immutable, permissioned dataset.
7. Independent review of results and explicit owner approval.

A successful CI run, one local dataset check, a current quote or a UI disclaimer is not an approval.

## Validation

Backend tests verify closed-by-default behavior for decision, scores and backtest before downstream analysis is called. The frontend build verifies the guarded UI. All normal CI uses GitHub-hosted runners; no laptop Runner is required.

## Assistant disclosure

The floating chat helper is not a connected language model. It is a fixed product guide and must not return hard-coded prices, rankings, risk statistics, probabilities or claimed explanations for asset selection. The guide explicitly discloses this limitation and routes users to the operational data-status view where relevant. A real evidence-grounded assistant remains a separate product workstream requiring a model API, retrieval over approved evidence, citations and refusal on unsupported claims.
