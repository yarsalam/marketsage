# MarketSage Implementation Roadmap

**Status date:** 2026-10-18  
**Working branch:** `feat/tindex-free-data-connector`  
**Current milestone:** Stage 2 — connector technical acceptance in progress; Stage 3 fixture-backed research API/UI implemented, runtime acceptance pending  
**Release posture:** research-only; source scoring remains fail-closed

This roadmap separates implementation progress from evidence that a data source or model is safe to use. Passing unit tests proves the tested code paths behave as expected on fixtures; it does not prove live-data quality, legal permission, predictive performance, or production readiness.

## 1. Current stage and evidence

### Stage 2 — Connector technical acceptance (in progress)

Local evidence reported by the project owner on 2026-10-18:

- Full analysis-engine test suite: **188 passed, 7 warnings, 8.83 seconds**.
- The warnings are deprecations from Starlette/httpx and pandas/NumPy timedelta handling; they did not fail the suite.
- Controlled, single-request live probes previously received responses from:
  - TSETMC instrument search
  - CODAL disclosure search
  - Tindex public currency-rates endpoint
  - FRED/ALFRED `FEDFUNDS` observations
- GDELT previously encountered HTTP 429. Do not repeat live requests until a retry window and request budget are deliberately chosen.
- Live probe reports are shape/reachability checks only. Raw payloads are not saved, and every source remains `eligible_for_scoring=false`.

The reported 188-test result is local evidence from the project owner; do not label it as a GitHub Actions/CI result unless a workflow run confirms it.

### Stage 2 exit criteria

1. Confirm the full suite is reproducible from the intended branch and record the exact commit and test result.
2. Review and resolve (or explicitly accept with an issue) the deprecation warnings.
3. For each source, record endpoint/contract, fields, units and quote conventions, observation vs publication vs retrieval time, timezone, revisions/corrections, missing data, history depth, rate limits, and permission/licensing.
4. Add sanitized, deterministic fixtures for real response shapes and error cases; never commit API keys or sensitive raw payloads.
5. Reconcile data with an independent reference where legally permitted.
6. Test that unknown units/timestamps, unavailable sources, stale observations, and unapproved sources cannot enter scoring.
7. Keep the source registry fail-closed until an explicit review approves a source for a narrowly defined use.

**Stage 2 decision:** Do not block prototype development on every external source being approved. Stage 3 can proceed with deterministic fixtures and clearly labelled research-only data, while Stage 1 acceptance gaps remain open.

## 3. Stage 3 — End-to-end research prototype

**Goal:** demonstrate one auditable path from inputs to an explainable, risk-aware comparison without claiming production predictive ability.

### Implementation sequence

1. **Canonical data contracts**
   - Define common schemas for instruments, observations, news articles, source metadata, timestamps, units, currency, and quality flags.
   - Preserve source identity and retrieval metadata; do not infer publication times or quote units.
   - Reject invalid, stale, ambiguous, or non-point-in-time records rather than silently repairing them.

2. **Ingestion and normalization**
   - Implement bounded source clients, deduplication, retry/backoff only where appropriate, cache/rate-limit handling, and sanitized operational errors.
   - Store raw responses only when terms permit; otherwise retain approved normalized fields and integrity metadata.
   - Separate observation time, publisher release time, first-seen time, and retrieval time.

3. **News/event pipeline**
   - Build article normalization, canonical URL deduplication, language detection, and timestamp-aware storage.
   - Keep sentiment and event category as separate outputs, with evidence spans and an abstain/unknown state.
   - Create a manually labelled Persian/English benchmark before describing sentiment/event outputs as validated.
   - GDELT is discovery-only until its live reliability, coverage, and applicable terms are reviewed; do not repeatedly probe during HTTP 429.

4. **Market and macro feature layer**
   - Join news/event features to market observations only when timestamps prove the information was available at the decision time.
   - Track missingness, freshness, currency/unit conventions, liquidity, and source quality explicitly.
   - Keep unavailable Iranian-market series disabled rather than substituting unrelated proxies without a visible label.

5. **Risk/return and explainable ranking**
   - Produce baseline returns, volatility, drawdown, and appropriate risk measures from validated historical series.
   - Show assumptions, horizon, evidence, uncertainty, and reasons for each rank; do not present uncalibrated scores as probabilities.
   - Include a clear “insufficient data / not rankable” result.

6. **API/UI integration**
   - Implemented `POST /research/snapshot` in the FastAPI analysis engine and `POST /api/markets/research-snapshot` through the NestJS backend.
   - Added a Persian UI demo in the existing News tab. It submits deterministic fixture data, displays headline labels and descriptive metrics, and shows future-record exclusion plus disabled scoring.
   - The API forces `source_approved=false` for caller-supplied market series; it never accepts client input as production approval.
   - Updated the analysis-engine Dockerfile to copy local modules required by the service and research pipeline.
   - Remaining: run focused/full Python tests, NestJS tests/build, frontend build, and production image build in CI; inspect API behaviour in the deployed staging environment only after explicit deployment approval.

### Stage 3 acceptance evidence

- Deterministic end-to-end tests with frozen fixtures.
- Tests for duplicate news, corrected disclosures, missing values, unit mismatches, stale data, unavailable providers, and timestamp leakage.
- At least one fully traceable example from source record to final rank, including rejected records and explanation.
- No live investment scoring from unapproved sources.

## 4. Stage 4 — Model and strategy validation

1. Build time-stamped, independently labelled Persian/English sentiment and event evaluation data; publish class-wise precision, recall, F1, confusion matrices, and error analysis.
2. Define the investment universe, benchmark, decision cadence, horizon, costs, slippage, liquidity constraints, and portfolio rules before evaluating strategies.
3. Use chronological splits and walk-forward/out-of-sample testing; prevent look-ahead, survivorship, revision, and publication-time leakage.
4. Compare against simple baselines and buy-and-hold/appropriate asset benchmarks.
5. Report net returns, volatility, maximum drawdown, Sharpe/Sortino where appropriate, VaR/expected shortfall with assumptions, turnover, and performance by regime.
6. Test sensitivity to transaction costs, missing/stale data, source outages, model changes, and alternative parameter choices.
7. Calibrate probabilities on held-out data before exposing confidence estimates; document calibration and uncertainty.
8. Version datasets, source contracts, features, models, configuration, and every generated decision so results can be replayed.

**Exit gate:** results are reproducible out of sample, limitations are documented, and a reviewer can replay a historical decision using only information available at that time. Passing this gate still does not guarantee future returns.

## 5. Stage 5 — Operational readiness and controlled release

- Add structured metrics/logging without secrets, health/readiness checks, bounded timeouts, provider-specific rate limits, cache policies, and safe degradation.
- Add data-quality alerts for staleness, schema drift, missing intervals, unexpected unit/scale changes, and abnormal duplicate rates.
- Ensure provider failures cannot silently fall back to fabricated or incompatible data.
- Secure secrets through environment/secret management; review access control, dependency security, backups, retention, and permitted data storage.
- Run API, integration, and deployment smoke tests in a staging environment; verify DNS/TLS, reverse proxy, firewall, resource limits, and rollback procedures before any release.
- Provide source lineage, methodology notes, risk disclosures, model/version identifiers, and an auditable decision history.
- Do not claim the entire product is production-ready while admin/auth/deployment blockers listed in the repository README remain unresolved.

**Exit gate:** a documented release review explicitly approves the supported scope, with rollback and monitoring in place. Approval of one data source or one API endpoint does not approve the whole investment product.


### Source-by-source approval gate (applies across Stages 2–5)

Approve sources individually and only for the purposes actually reviewed. Maintain registry states such as `candidate`, `reachable_only`, `research_only`, `approved_for_specific_fields`, and `disabled`.

For each source, record the owner/reviewer and date; terms/licensing and permitted use; endpoint/schema version and fixture provenance; unit, currency, timestamp, revision and coverage validation; independent reconciliation; rate limits and outage behaviour; exact approved fields/use cases and exclusions.

TGJU, unsupported Tindex categories, and any source with unresolved rights or semantics remain disabled. Never bypass a provider's disabled endpoint or access restrictions.

## Immediate next action

1. Pull `feat/tindex-free-data-connector` and run `python -m pytest -q` from `user/analysis-engine`; the owner previously reported 203 passed, 7 warnings after adding the API endpoint tests, but that latest result must be confirmed locally.
2. Run the backend checks from `user/user-backend`: `pnpm install --frozen-lockfile`, `pnpm build`, and `pnpm exec jest --runInBand`.
3. Run the frontend checks from `user/user-frontend`: `pnpm install --frozen-lockfile` and `pnpm build`.
4. Confirm the production image build includes `research_pipeline.py`, `headline_signal_engine.py`, `source_registry.py`, and `temporal_data.py`; check CI separately from local evidence.
5. Keep the PR open and do not merge or deploy without explicit permission. Keep source scoring disabled; this endpoint uses caller-supplied demo data and is not a production feed.

## Project status report (copy-ready)

- **Stage 1 — code and existing tests:** local full suite reported 188 passed, 7 warnings, 8.83s on 2026-10-18; GitHub Actions previously had a successful run, and a newer run is queued for the latest commit.
- **Stage 2 — source acceptance:** in progress; TSETMC, CODAL, Tindex, and FRED/ALFRED had bounded live responses, but data semantics/licensing/coverage are not fully approved; GDELT previously returned HTTP 429.
- **Stage 3 — end-to-end prototype:** API/UI wiring added on the feature branch. The fixture-backed `research_pipeline.py` is exposed via FastAPI `POST /research/snapshot`, proxied by NestJS `POST /api/markets/research-snapshot`, and called from a Persian demo panel in the existing News tab. Added API tests and updated Docker module copies. Latest API/UI commits still require CI and local validation.
- **Stage 4 — model/backtest:** not started for this integrated pipeline; needs labelled NLP/event evaluation, point-in-time validation, chronological holdout/walk-forward, costs/liquidity and drawdown/risk reporting.
- **Stage 5 — operational/release:** not started; monitoring, failure handling, security, staging deployment, and release review remain.
- **Not verified:** latest API endpoint tests, NestJS build/tests, Next.js build, production image build, and CI status for the newest commits; licensing, data correctness, and real-world predictive performance.
- **Exact next step:** run the Python suite, backend build/tests, and frontend build using the commands above.
- **Release posture:** research-only; no production investment scoring or ranking enabled.


## Execution update — 2026-10-18

This update supersedes older test counts and CI-status notes above where they conflict.

- **GitHub Actions:** run [39105077841](https://github.com/yarsalam/marketsage/actions/runs/39105077841) completed successfully on PR #6 head `8d56a1ab3659b234094bebb605dfba272e3ecbb5`. All five jobs passed: analysis, user frontend, user backend, admin workspace, and production images. This is CI evidence for that exact commit, not live-provider acceptance.
- **Owner-reported local tests:** latest full Analysis Engine suite on 2026-10-18: **205 passed, 7 warnings in 8.76 seconds**. Warnings are deprecations from Starlette/httpx and pandas/NumPy timedelta handling. Earlier focused research pipeline/API/source-acceptance suites also passed; these overlap the full suite and must not be added to its total. Focused suites overlap the full suite and must not be summed into a new total. Deprecation warnings remain non-blocking but should be cleaned up separately.
- **Network-aware live validation:** do not run the default all-provider smoke pack while assuming one VPN state fits all providers. Use `--source` to select providers and follow the VPN split documented in `docs/data-source-onboarding-tindex.md`. Do not retry GDELT immediately after HTTP 429; wait for a deliberate cooldown and request budget.
- **Next Stage 3 acceptance task:** run one bounded local API/UI demo against the actual local services; separately probe Iranian providers with VPN off and external providers with VPN on when credentials are available. Record sanitized reports only. Do not commit credentials or local reports, and do not enable source scoring.
- **Still unverified:** end-to-end UI/API behavior in the user's local runtime, data rights/licensing, source semantics/units/history completeness, independent reconciliation, and real-world sentiment quality. No production ranking is approved.

### VPN-aware live-probe checklist

1. Iranian sources — VPN **off**: TSETMC and CODAL. Tindex is optional and should only be probed when its configured credentials are available; respect its quota.
2. External sources — VPN **on**: FRED/ALFRED only when `FRED_API_KEY` is configured. GDELT remains on cooldown after the previously observed HTTP 429; do not include it in the next probe until the retry window is deliberately chosen.
3. A reachability failure is not automatically a code failure. Record provider, VPN state, timestamp, HTTP/error class, and sanitized response-shape metadata; never store tokens or raw payloads in the report.

## Latest execution update — 2026-10-18 (PR #6 head `1943df208705a7266f59999ac7615097acfb3017`)

- **GitHub Actions:** run [39106444216](https://github.com/yarsalam/marketsage/actions/runs/39106444216) completed successfully on the current PR head. All five jobs passed: analysis, user frontend, user backend, admin workspace, and production images.
- **Owner-reported Iranian source smoke report:** `iran.tsetmc` and `iran.codal` each returned `reachable_response_received`; 2 probes attempted, 2 reachable, 0 failed. TSETMC returned an object with an `instrumentSearch` list. CODAL returned a payload object, but `publication_timestamp` was null. The report shows `eligible_for_scoring=false` for both.
- **Scope limitations:** this confirms response reachability and coarse response shape only. It does not validate unit conventions, historical coverage, publication/correction semantics, collection rights, or independent data accuracy. The command output did not itself record the actual VPN state; the required procedure remains VPN off for Iranian providers.
- **FRED/ALFRED:** live probe was skipped because `FRED_API_KEY` is not configured. If run later, VPN must be on. GDELT remains on cooldown after the previously observed HTTP 429; do not repeat it in this batch. Tindex was not selected in this Iranian-only report and needs a separate bounded probe only when its credentials are available (VPN off; honor the 3 requests/minute and 300 successful requests/day limits).
- **Current gate decision:** Stage 2 remains open. The next user-run batch should be local/offline acceptance tests plus a sanitized Tindex probe only if credentials are available. After that, complete the source evidence review (rights, units, timestamps, history, reconciliation) and validate the local API/UI path. Do not merge PR #6, deploy, or enable investment scoring as part of this update.


## Handoff and next execution — 2026-10-18

- **Latest owner-reported test result:** `cd user/analysis-engine && .venv/bin/python -m pytest -q` -> **205 passed, 7 warnings in 8.76s**. This is a local result reported by the owner, not a claim about CI.
- **Next action:** finish Stage 3 runtime acceptance locally using the three services (FastAPI analysis engine on 8000, NestJS user backend on 4500, Next.js frontend on 3000). Use the exact commands in [the ChatGPT handoff note](CHATGPT_HANDOFF.md). This is a local fixture demo; no VPN is required and it must not make external provider requests.
- **Local E2E acceptance gate:** verify engine `/health`, verify backend `/health`, POST a deterministic fixture to `/api/markets/research-snapshot`, then use the frontend's research demo and verify that future-dated article/price data are excluded and investment ranking remains null/disabled.
- **Do not start Stage 4 yet** until the full UI -> NestJS -> FastAPI request path is demonstrated and its output is captured. Stage 2 source-semantic/legal/data-quality gates remain independently open; Stage 3 can use fixtures without treating sources as approved.
- **No merge/deploy:** PR #6 remains open; no production release or scoring activation is authorized by these tests.
