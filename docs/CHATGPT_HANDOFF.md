# MarketSage — ChatGPT handoff / resume note

**Last updated:** 2026-10-20  
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
- Stage 3: **fixture-backed local UI/API demonstration passed the current acceptance checks**. User confirmed the Persian `ResearchSnapshot` UI rendered and showed the API output. On 2026-10-18, the new acceptance pack ran twice: `tests/test_research_pipeline.py` + `tests/test_research_backtest.py`: **24 passed** (4.00s and 3.92s). With `RUN_API_SMOKE=1`, local API contract smoke also passed: **HTTP 201**, one future article excluded, snapshot last observation date `2026-10-17`, descriptive return `5.00%`, `investment_ranking=null`, ranking status `disabled_until_source_and_model_acceptance`, and market not eligible for scoring. HTTP 201 is valid for this NestJS POST; do not require only HTTP 200 unless the contract is intentionally changed.
- Stage 3 may be treated as **complete for the fixture-backed local path only**. This does not close Stage 2, approve live sources, prove model predictiveness, or establish production readiness.
- **Next action: begin Stage 4 — evaluation and backtesting.** First write the evaluation scope and data audit; then define time-ordered train/validation/holdout windows, baselines, transaction costs/slippage and risk metrics before running or interpreting model comparisons. Keep Stage 2 source acceptance separate. Fixture-only tests require no VPN; do not probe external providers as part of this pack.
- Stage 4 requires a written evaluation scope and careful time-series evaluation. Stage 2 source acceptance remains a separate gate and must not be falsely marked complete.
- Do not merge PR #6, deploy, enable source scoring, or claim production readiness without the user's explicit authorization and evidence.

## Repeatable test pack (current next action)

Update the local branch to fetch the test-pack commit, preserving local changes. Then run:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
git pull --ff-only origin feat/tindex-free-data-connector
cd user/analysis-engine
bash scripts/run_research_acceptance.sh
```

The default pack uses synthetic fixtures and requires no VPN. To also test the local NestJS → FastAPI API hop, first ensure FastAPI is listening on `127.0.0.1:8000` and NestJS on `127.0.0.1:4500`, then run:

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
RUN_API_SMOKE=1 bash scripts/run_research_acceptance.sh
```

The API smoke accepts HTTP 200 or 201 and asserts: one future article excluded; only prices through 2026-10-17 used; return approximately 5%; ranking remains null; ranking status stays disabled; market is not eligible for scoring. User has already confirmed the UI demo is visible and the expected result appears after it was run; the browser button should be clicked again if the local checkout is updated.

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
- HTTP 200 or 201 (NestJS may return 201 for a successful POST).
- `news.future_articles_excluded == 1`.
- First/only market metric `last_observation_date == "2026-10-17"`; the 2026-10-18 price must not leak into the snapshot.
- `investment_ranking == null`, `investment_ranking_status == "disabled_until_source_and_model_acceptance"`, and market `eligible_for_scoring == false`.
- Visit http://127.0.0.1:3000, navigate to the research tab/demo, click its run button, and confirm the same behavior through the UI.

Send back health results, HTTP status/JSON from the POST (no secrets), and whether the UI demo rendered. If successful, record Stage 3 runtime acceptance and then plan Stage 4. If it fails, debug only the failing hop.

## Stage 4 — evaluation and backtesting (current stage)

Stage 3 fixture-backed local acceptance passed on 2026-10-18. Begin Stage 4 with a design/specification and data audit before treating any model metrics as evidence. Keep the following gates explicit:

1. Define evaluation scope before modelling: markets/instruments, horizon (~6 months), decision frequency, baseline(s), transaction costs/slippage, and risk metrics.
2. Audit data for point-in-time availability, revisions, missingness, units, timezone and survivorship/selection bias.
3. Create time-ordered train/validation/holdout periods and walk-forward evaluation; never random-split time series.
4. Compare against simple baselines and buy-and-hold; include fees/slippage, turnover, drawdown, volatility/Sharpe where appropriate.
5. Calibrate probabilities only with out-of-sample evidence; report uncertainty and failure cases.
6. Keep ranking disabled until source and model acceptance gates pass. No target return (e.g. 50%) should be presented as promised/validated.

Stage 2 source acceptance remains open and separate. Stage 4 analysis may begin using only datasets whose provenance and limitations are explicit; synthetic fixtures validate plumbing, not predictive performance.

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

“Continue MarketSage from `docs/CHATGPT_HANDOFF.md` and `docs/implementation-roadmap.md` in https://github.com/yarsalam/marketsage. First check the current PR #6 head/CI and read those two docs. Do not assume earlier chat state is complete. The five stages are exactly: (1) اصلاح کد و تست‌های فعلی, (2) پذیرش فنی منابع داده, (3) ساخت نمونهٔ انتهابه‌انتها, (4) ارزیابی مدل و بک‌تست, (5) آزمون عملیاتی و تصمیم انتشار. Current owner-reported Analysis Engine tests: 205 passed, 7 warnings. Iran TSETMC/CODAL reachability succeeded with VPN OFF, but both remain ineligible for scoring; FRED key missing; GDELT previously returned 429. The Stage 3 UI fixture demo has rendered and shown the expected output; run `user/analysis-engine/scripts/run_research_acceptance.sh` and optionally `RUN_API_SMOKE=1 bash scripts/run_research_acceptance.sh` with local services running. If the pack passes, begin Stage 4 planning/evaluation while keeping Stage 2 source acceptance separate. Ask me to run commands only where local machine access is required. Never merge/deploy or enable investment ranking without explicit permission. Keep all scoring fail-closed and clearly distinguish evidence from assumptions.” 


## Latest handoff update — 2026-10-20 (free-source discovery and CSV audit)

This section is the current source-discovery checkpoint. Older sections above describe earlier states and should not override the evidence here.

### Branches and PRs — keep the workstreams distinct

- **PR #6** — [conservative Tindex connector](https://github.com/yarsalam/marketsage/pull/6), head branch `feat/tindex-free-data-connector`, base `deploy/production-readiness`. Still open; do not merge or deploy without explicit authorization.
- **PR #13** — [free dataset discovery and acceptance workflow](https://github.com/yarsalam/marketsage/pull/13), head branch `feature/free-dataset-discovery-acceptance`, base `feature/iran-live-data-dashboard`. Last inspected: open and mergeable, head `ef5183c8d800efa1e729939c3966839ec541dd58`. A current Actions run for that head was not confirmed by the workflow lookup; do not describe it as CI-green without checking GitHub Actions.
- These are separate branches and PRs. The local acceptance-pack results below came from `~/projects/marketsage-acceptance` on the free-dataset-discovery workstream; they must not be attributed to PR #6 without verifying the matching commit/files.
- The acceptance pack completed locally: **265 tests passed in 17.19 seconds**, with 9 warnings. Catalog validation, shell syntax, offline tests, inventory and evidence-template generation passed. This is owner-reported local evidence, not CI evidence.

### Latest sanitized live-source results

Report directory: `/tmp/marketsage-free-dataset-acceptance`.

- `iran.tsetmc`: `reachable_response_received`.
- `iran.codal`: `reachable_response_received`.
- `global.world_bank_indicators`: schema-validated candidate with **26 annual Iran CPI inflation observations, 2000–2025**.
- `global.binance_spot_public`: probe failed with `BinancePublicError` / `HTTPStatusError`. The sanitized report does not establish whether the cause was VPN/network routing, provider response, or another HTTP-level issue. Diagnose only with a deliberate, bounded retry.
- Summary: 3 of 4 public probes received responses; **production approval remains false**. Reachability/schema validation is not proof of historical completeness, permission to reuse, or investment suitability.
- Tindex was skipped because `TINDEX_API_BASE_URL` and `TINDEX_API_TOKEN` were not configured in that shell. FRED/ALFRED was skipped because `FRED_API_KEY` was absent. GDELT was not contacted by design. Do not ask the user to paste secrets into chat.

### Required VPN reminder — owner instruction

**Before asking the user to run any live request to a foreign/international website or provider, first explicitly tell them to turn the VPN on. Do not silently start or recommend a foreign-source probe without this reminder.** This includes FRED/ALFRED, Binance, World Bank, GDELT, and other foreign providers. When a batch mixes Iran and foreign providers, split it into separate runs so the VPN state is unambiguous.

- Iranian providers TSETMC, CODAL, and Tindex: VPN **off**.
- Foreign/international providers (including FRED/ALFRED, Binance, World Bank, and GDELT): tell the user VPN **on before the request**.
- GDELT previously returned HTTP 429; do not retry until a deliberate cooldown and request budget are chosen.
- Never put API tokens in a command transcript that may be shared, logs, reports, or Git.

### Seller-provided StreamData CSV audit (metadata only)

The user separately audited four files under `~/Downloads/Telegram Desktop/4_Symbols_Data_StreamData`. The report is `/tmp/marketsage-free-dataset-acceptance/vendor-streamdata-quality-report.json`; it emitted no raw cell values and does **not** approve any source for production.

| File | Rows | Date range | Structural findings |
|---|---:|---|---|
| `Ayar_Gold_Fund_1D_StreamData.csv` | 123 | 2026-04-19 to 2026-10-18 | 1 OHLC invariant violation |
| `BTCUSDT_1D_StreamData.csv` | 184 | 2026-04-19 to 2026-10-19 | No date/duplicate/order/OHLC issue detected |
| `Gold18_1D_StreamData.csv` | 184 | 2026-04-19 to 2026-10-19 | No date/duplicate/order/OHLC issue detected |
| `US_Dollar_1D_StreamData.csv` | 176 | 2026-04-19 to 2026-10-19 | No date/duplicate/order/OHLC issue detected |

All four had zero invalid dates, missing dates, duplicate dates, and source-order inversions. The AYAR OHLC violation must be inspected locally and resolved against the vendor/source before use; do not silently alter the record. These are seller-provided exports, not free/open datasets: confirm licence, contract, redistribution/training rights, units, timezone/session conventions, and adjustment semantics. Do not commit the vendor CSVs, raw rows, or reports containing sensitive commercial details. The roughly six-month coverage is not enough to establish robust six-month-horizon out-of-sample performance on its own.

### Next actions for the next ChatGPT session

1. Start by checking `git status --short --branch` and current heads for PR #6 and PR #13; preserve the user's local changes and untracked files. Do not reset/clean the checkout or conflate branch histories.
2. Do **not** rerun the whole acceptance pack by default. Inspect the sanitized Binance error first. If another live Binance/foreign-source request is needed, tell the user to turn VPN on before providing the bounded command.
3. Inspect the AYAR OHLC anomaly locally (report only whether it is resolved and the date/field metadata, not all vendor prices); keep that observation quarantined until verified.
4. If validating Tindex, use a separate run with VPN off and already-configured credentials; respect the provider limit of 3 requests/minute and 300 successful requests/day. Never echo the token.
5. FRED requires `FRED_API_KEY` and VPN on. GDELT remains opt-in and must respect cooldown after HTTP 429.
6. Keep source acceptance open, ranking/scoring disabled, and both PRs unmerged unless the user explicitly authorizes a merge/release. Do not commit local candidate exports, evidence reports, vendor files, API keys, or raw payloads.

**Resume prompt:** “Continue MarketSage using the latest update in `docs/CHATGPT_HANDOFF.md` and `docs/implementation-roadmap.md`. Check PR #6 and PR #13 as separate branches. Local free-dataset acceptance run: 265 tests passed; TSETMC/CODAL reachable, World Bank schema validated for 26 annual Iran CPI observations (2000–2025), Binance HTTPStatusError; Tindex/FRED skipped for missing configuration; GDELT not contacted. The four seller CSVs have only one reported OHLC issue, in AYAR, and remain unapproved/vendor-restricted candidates. Before any live call to FRED, Binance, World Bank, GDELT, or other foreign provider, explicitly remind me to turn VPN on. For TSETMC/CODAL/Tindex use VPN off. Do not repeat the full test pack, merge, deploy, or enable ranking without evidence and permission.” 


## Latest implementation continuation — 2026-10-20

### VPN-separated acceptance runner

A follow-up change was made on PR #13's separate branch, feature/free-dataset-discovery-acceptance:

- Latest PR #13 head: 8d330c460bf2cd89ff2bb4a59e7a07523e6dfb1f.
- GitHub Actions run [#39392008358](https://github.com/yarsalam/marketsage/actions/runs/39392008358) completed successfully: analysis, user frontend, user backend, admin workspace, and production-images jobs all passed.
- The acceptance runner now defaults to offline-only behavior. Live Iranian and foreign-source probes require separate invocations. It refuses to combine groups and prompts for exact VPN-OFF or VPN-ON confirmation before making network requests. New tests cover mixed-mode refusal and invalid option combinations.
- The default command does not call any provider. These changes do not change source approvals or enable scoring.
- PR #13 remains open and unmerged into feature/iran-live-data-dashboard.

### Latest CI for the Tindex workstream

- PR #6 remains open: feat/tindex-free-data-connector → deploy/production-readiness.
- Latest inspected head: 496cb9bc9785442b43ba1d31ee1f44ed30f0913d.
- GitHub Actions run [#39389606760](https://github.com/yarsalam/marketsage/actions/runs/39389606760) passed all five jobs (analysis, user frontend, user backend, admin workspace, production images).
- These are CI/build results, not data-source acceptance, licence approval, model validation, or deployment evidence. Neither PR was merged, and no server deployment was performed.

### Decision: source discovery and staging can proceed in parallel

Do not wait for all nine market/data families to be fully accepted before completing the deployable prototype. A staging-only run can use synthetic fixtures or explicitly labelled research-only data while production ranking and source scoring stay disabled. It must visibly return “insufficient data / not rankable” for unaccepted markets.

| Area | Current evidence and next gate |
|---|---|
| Iranian equities | TSETMC/CODAL responded to bounded discovery probes. Complete instrument universe, symbol identity, daily coverage, adjusted prices, corporate actions and permission checks remain open. |
| Gold/coin | Tindex and seller exports are candidates. Resolve units, quote conventions, source overlap and usage rights. Keep the AYAR row with the detected OHLC invariant violation quarantined until checked against the vendor. |
| Free-market USD | Tindex has a prior candidate snapshot but its latest discovery probe was skipped for missing environment configuration. Define free vs official rate and validate history independently. |
| Crypto | Existing Yahoo Finance history is a research proxy; seller BTCUSDT is venue-specific and not yet rights-approved. Latest Binance probe returned sanitized HTTPStatusError; cause is not established. |
| Fixed income | No accepted series yet. Keep this asset class unavailable/not-rankable until a source, yield definition and history are accepted. |
| Iran macro | World Bank produced 26 annual Iran CPI observations for 2000–2025. This is a candidate only; publication/revision timing remains unresolved. Central Bank/Statistical Center have no accepted automated pipeline yet. |
| CODAL events | Search adapter exists; publication-vs-retrieval timestamps, corrections/amendments and event normalization remain open. |
| News/geopolitics | GDELT adapter exists, but a prior request returned HTTP 429. Its current live status was not tested in the latest run. |
| Sentiment/social | No production-validated sentiment model or connected scoring path. Build/label a benchmark and report held-out metrics before use. |

The four StreamData files are vendor-provided, not free/open. Their metadata audit found one OHLC issue in AYAR and no detected date/order/OHLC issues in the other three files. None is production-approved; do not commit raw files or infer units/timezone/rights.

### Staging readiness decision

The production Compose file currently contains the Analysis Engine, user backend and user frontend. The admin workspace is built by CI but is not a service in that production Compose file; confirm whether it belongs in this staging scope or needs a separately reviewed deployment definition. The Compose stack expects server-managed DNS/TLS/reverse proxy and environment configuration rather than providing those itself.

Before staging:
1. Review both open PRs and their base/head relationships; do not merge or deploy without explicit user authorization.
2. Choose one reviewed, exact release-candidate commit and ensure all CI jobs passed on that commit. Do not deploy the PR #13 feature-branch head to the server accidentally; it currently targets another feature branch.
3. Configure a private server-side .env.production (permissions such as chmod 600), DNS/TLS/reverse proxy, firewall, and backup/rollback plan. Never place real secrets in Git or chat.
4. Run the service health checks and smoke tests for normal, not-rankable, stale-data, provider outage and recovery paths. Capture sanitized results.
5. Keep live scoring and rankings disabled even if the staging deployment passes.

### Next-session instructions

1. Read this section and the current roadmap, then check current heads/CI for PR #6 and PR #13 separately.
2. Preserve the user's local changes/untracked files. Start with git status --short --branch; never run a destructive reset/clean.
3. From the PR #13 local branch, the default bash scripts/run_free_dataset_acceptance_pack.sh now runs offline tests/inventory/audit only. Do not run foreign live probes without first telling the user to turn VPN ON. For Iranian providers, tell the user VPN must be OFF. The runner then demands the matching confirmation.
4. Do not automatically rerun the full test pack merely to read existing reports. Diagnose the specific failing item, and do not retry GDELT after HTTP 429 without an intentional cooldown.
5. After the user authorizes staging, prepare and run a staging-only checklist; do not treat staging deployment or CI as proof of market-data acceptance or predictive value.

Resume prompt: “Continue MarketSage from the newest docs/CHATGPT_HANDOFF.md and docs/implementation-roadmap.md. PR #6 is open on feat/tindex-free-data-connector; its latest checked CI run #39389606760 passed all five jobs. PR #13 is a separate open PR on feature/free-dataset-discovery-acceptance; latest head 8d330c460bf2cd89ff2bb4a59e7a07523e6dfb1f passed all five CI jobs in run #39392008358. PR #13's acceptance runner now defaults offline and forces separate live runs: VPN OFF for TSETMC/CODAL/Tindex and VPN ON for World Bank/Binance/FRED/GDELT. Source acceptance remains open. Staging may be prepared with fixtures/research-only data and ranking disabled, but do not merge or deploy without my explicit authorization. Check the branch/CI states first and preserve local untracked files.”


## Latest operational increment — 2026-10-20 (liveness/readiness)

- The Analysis Engine now distinguishes /health (process liveness only) from /ready (readiness for the research-only API). The ready check validates source-registry structure/counts and the research snapshot callable. It returns HTTP 503 on an empty/inconsistent registry and logs only the exception class. It makes no live provider requests and does not imply any financial source is approved.
- Analysis Engine Dockerfile and production Compose health checks now target /ready, so Compose's service_healthy dependency gates the user backend on local research readiness.
- Added tests in tests/test_health_readiness.py for liveness, research-only readiness with ranking disabled, and 503 when the source registry is empty.
- Exact current PR #6 head: 37c6e85dea37b02543df7150d359d8f72c5be511. GitHub Actions run [#39393823453](https://github.com/yarsalam/marketsage/actions/runs/39393823453) completed successfully; all five jobs passed, including the production-image build.
- PR #6 and PR #13 remain open; no merge or deployment was performed. Source acceptance, staging access-control/security review, backups/rollback and staging smoke tests remain open.
- Staging decision is unchanged: a research-only staging test can use deterministic fixtures while investment ranking and source scoring remain disabled. Do not treat /ready=ready, a successful build, or a fixture test as market-data/model approval.
