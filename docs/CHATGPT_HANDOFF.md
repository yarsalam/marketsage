# MarketSage — ChatGPT handoff / resume note

**Last updated:** 2026-10-18  
**Repository:** https://github.com/yarsalam/marketsage  
**Working branch:** `feat/tindex-free-data-connector`  
**Base branch:** `deploy/production-readiness`  
**PR:** [#6 — open, not merged](https://github.com/yarsalam/marketsage/pull/6)  
**Latest code commit known before this handoff update:** `b565ed3efcfc1978d2ff616e41482f54bd17d892`. Docs-only follow-up commits may advance the branch; check the live PR head before changing code.

## Five-stage roadmap (keep these exact names)

1. **اصلاح کد و تست‌های فعلی**
2. **پذیرش فنی منابع داده**
3. **ساخت نمونهٔ انتهابه‌انتها**
4. **ارزیابی مدل و بک‌تست**
5. **آزمون عملیاتی و تصمیم انتشار**

## Current status

- Stage 1: latest owner-reported full Analysis Engine test suite: **205 passed, 7 warnings in 8.76s** (command: `.venv/bin/python -m pytest -q`). Warnings are deprecations from Starlette/httpx and pandas/NumPy timedelta; not test failures.
- Stage 2: **still open**. VPN OFF live smoke run for `iran.tsetmc` and `iran.codal`: 2 probes attempted, 2 reachable, 0 failed. TSETMC response shape includes `instrumentSearch: list`; CODAL `publication_timestamp` was null. Both `eligible_for_scoring=false`. This only confirms reachability/shape, not data accuracy, units, history, release-time semantics, licensing or model suitability.
- Tindex was not selected in the latest Iran report; only probe separately if credentials are configured, VPN OFF, respecting 3 requests/minute and 300 successful requests/day.
- FRED/ALFRED probe was skipped because `FRED_API_KEY` is not configured; when tested, VPN ON.
- GDELT previously returned HTTP 429; VPN ON if retried, but do not repeat until cooldown/request budget is deliberately chosen.
- Stage 3 code exists: fixture-backed `POST /research/snapshot` in FastAPI, proxied via NestJS `POST /api/markets/research-snapshot`, with Persian `ResearchSnapshot` UI demo. It uses synthetic fixture data and deliberately keeps `investment_ranking=null` and source scoring disabled.
- **Next action is Stage 3 local runtime/E2E validation**, not Stage 4 yet. No VPN is needed for the local fixture demo. Do not probe external providers in this test.
- Stage 4 is gated on demonstrated UI → NestJS → FastAPI path plus clear data/evaluation scope. Stage 2 source acceptance remains a separate gate and must not be falsely marked complete.
- Do not merge PR #6, deploy, enable source scoring, or claim production readiness without the user's explicit authorization and evidence.

## Local runtime acceptance (Stage 3)

First check the local checkout and ensure it contains the PR branch changes; don't discard any local work:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
git log -1 --oneline
```

No VPN is needed for the following local fixture-only test. Start each service in a separate terminal.

**Terminal 1 — Analysis Engine (FastAPI):**

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
source .venv/bin/activate
uvicorn price_service:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — User Backend (NestJS):**

```bash
cd ~/projects/marketsage-acceptance/user/user-backend
ANALYSIS_ENGINE_URL=http://127.0.0.1:8000 PORT=4500 CORS_ORIGINS=http://localhost:3000 pnpm start:dev
```

**Terminal 3 — User Frontend (Next.js):**

```bash
cd ~/projects/marketsage-acceptance/user/user-frontend
NEXT_PUBLIC_API_URL=http://localhost:4500 pnpm dev -- --hostname 127.0.0.1
```

If dependencies are missing or any service fails to start, stop there and share the exact error; do not install/upgrade dependencies or alter lockfiles without reviewing the cause.

**Terminal 4 — health and API checks:**

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:4500/health
curl -sS -i -X POST http://127.0.0.1:4500/api/markets/research-snapshot \
  -H 'Content-Type: application/json' \
  --data-binary @- <<'JSON'
{
  "as_of_date": "2026-10-17",
  "articles": [
    {
      "source_id": "fixture.news",
      "url": "https://example.test/markets/central-bank-demo",
      "title": "بانک مرکزی از رشد و توافق خبر داد",
      "first_seen_date": "2026-10-16"
    },
    {
      "source_id": "fixture.news",
      "url": "https://example.test/markets/future-demo",
      "title": "Markets surge after agreement",
      "first_seen_date": "2026-10-19"
    }
  ],
  "market_series": [
    {
      "symbol": "DEMO",
      "source_id": "fixture.market",
      "unit": "USD per unit",
      "currency": "USD",
      "unit_confirmed": true,
      "currency_confirmed": true,
      "observations": [
        {"date": "2026-10-15", "close": 100},
        {"date": "2026-10-16", "close": 110},
        {"date": "2026-10-17", "close": 105},
        {"date": "2026-10-18", "close": 1000}
      ]
    }
  ]
}
JSON
```

Expected API acceptance:
- HTTP 200.
- `news.future_articles_excluded == 1`.
- First/only market metric `last_observation_date == "2026-10-17"`; the 2026-10-18 price must not leak into the snapshot.
- `investment_ranking == null`, `investment_ranking_status == "disabled_until_source_and_model_acceptance"`, and market `eligible_for_scoring == false`.
- Visit http://127.0.0.1:3000, navigate to the research tab/demo, click its run button, and confirm the same behavior through the UI.

Send back health results, HTTP status/JSON from the POST (no secrets), and whether the UI demo rendered. If successful, record Stage 3 runtime acceptance and then plan Stage 4. If it fails, debug only the failing hop.

## Stage 4 plan after Stage 3 passes

1. Define evaluation scope before modelling: markets/instruments, horizon (~6 months), decision frequency, baseline(s), transaction costs/slippage, and risk metrics.
2. Audit data for point-in-time availability, revisions, missingness, units, timezone and survivorship/selection bias.
3. Create time-ordered train/validation/holdout periods and walk-forward evaluation; never random-split time series.
4. Compare against simple baselines and buy-and-hold; include fees/slippage, turnover, drawdown, volatility/Sharpe where appropriate.
5. Calibrate probabilities only with out-of-sample evidence; report uncertainty and failure cases.
6. Keep ranking disabled until source and model acceptance gates pass. No target return (e.g. 50%) should be presented as promised/validated.

## VPN rule for every source test

- Iran sources TSETMC/CODAL/Tindex: **VPN OFF**.
- External sources FRED/ALFRED and GDELT: **VPN ON**.
- Mention the VPN state explicitly before asking the user to run any live-source test.
- FRED needs `FRED_API_KEY`; GDELT must respect cooldown after HTTP 429.

## Suggested prompt for a new ChatGPT conversation

“Continue MarketSage from `docs/CHATGPT_HANDOFF.md` and `docs/implementation-roadmap.md` in https://github.com/yarsalam/marketsage. First check the current PR #6 head/CI and read those two docs. Do not assume earlier chat state is complete. The five stages are exactly: (1) اصلاح کد و تست‌های فعلی, (2) پذیرش فنی منابع داده, (3) ساخت نمونهٔ انتهابه‌انتها, (4) ارزیابی مدل و بک‌تست, (5) آزمون عملیاتی و تصمیم انتشار. Current owner-reported Analysis Engine tests: 205 passed, 7 warnings. Iran TSETMC/CODAL reachability succeeded with VPN OFF, but both remain ineligible for scoring; FRED key missing; GDELT previously returned 429. Continue Stage 3 local UI → NestJS → FastAPI fixture E2E using the commands in the handoff. Ask me to run commands only where local machine access is required. Never merge/deploy or enable investment ranking without explicit permission. Keep all scoring fail-closed and clearly distinguish evidence from assumptions.” 
