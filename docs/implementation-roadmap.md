# MarketSage Implementation Roadmap

**Status date:** 2026-10-20  
**Working branch:** `feat/tindex-free-data-connector`  
**Current milestone:** Stage 4 — empirical review documented, acceptance still open; Stage 5 operational hardening in progress; Stage 2 source acceptance remains open  
**Release posture:** research-only; investment ranking and source scoring remain disabled

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
- Implemented in the current work branch: provider-refresh logs now emit exception type only, and stale cached market prices may be served only up to configurable `MAX_STALE_CACHE_AGE_SECONDS` (default 86,400 seconds); older cache fails closed with HTTP 503. Regression tests cover the age boundary and log redaction; fresh CI/local confirmation remains required.
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

## Current evidence update (2026-10-18)

- Project owner reports the Analysis Engine suite passed **229 tests with 14 warnings** and the Stage 4 report validator passed. This is local evidence; it must not be labelled as CI evidence.
- Stage 4 exploratory report: 78 monthly rows, 11 global proxy/crypto assets, data end 2026-09-30, holdout 2025-10 through 2026-09. Momentum net holdout return was 30.57%, versus 6.41% monthly-rebalanced equal weight and 1.34% equal-weight buy-and-hold. Full-period momentum maximum drawdown was -40.15%, and its Sharpe (0.77) was below monthly-rebalanced equal weight (0.86).
- The six-month fold from 2023-10 through 2024-03 reported 240.89% momentum return. Asset attribution and data/weight sanity checks are required before Stage 4 acceptance; the annualized number for that short fold is not a forecast.
- See [Stage 4 empirical review](stage4-empirical-review-2026-10.md) and [Stage 5 readiness checklist](stage5-operational-readiness-checklist.md).
- Latest Stage 5 code changes add a bounded stale-cache age and sanitized refresh logging. CI run [#246](https://github.com/yarsalam/marketsage/actions/runs/39128372381) reports **233 Analysis Engine tests passed (14 warnings)** and the frontend, backend, and admin workspace jobs passed; the production-image build was still running at the last status check. The project owner still needs to pull the latest branch and confirm the local test run.

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


## Stage 4 execution update — evaluation protocol and local inventory

- Added [`docs/stage4-evaluation-protocol.md`](stage4-evaluation-protocol.md), defining the evaluation scope before results are inspected: approximate six-month target horizon, monthly decision cadence, current monthly momentum strategy as a baseline only, chronological validation, baselines, costs, risk metrics, and exit criteria.
- Added `user/analysis-engine/scripts/audit_research_data.py`, a read-only local inventory utility. It reports file metadata, candidate schemas/date ranges, missingness, and heuristic price-field checks without printing sample rows or raw cell values. It does not access the network and does not approve sources.
- The known Yahoo Finance universe (BTC-USD, ETH-USD, SOL-USD, GLD, SPY, QQQ, TLT, UUP, USO, XLF, XLE) is a mixed US-listed fund/equity and crypto sample; it must not be represented as an Iranian-market evaluation.
- **Not yet evidenced:** the user's current local data inventory, data provenance/licensing, adjusted-price semantics, point-in-time correctness, and any out-of-sample strategy result. Do not report backtest performance until these are audited.
- Stage 3 remains complete for the fixture-backed local demo only. Stage 2 source acceptance remains separate and open.

### First Stage 4 command

Run from the local checkout after reviewing `git status` and updating the feature branch without discarding local changes:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
git pull --ff-only origin feat/tindex-free-data-connector
python user/analysis-engine/scripts/audit_research_data.py --root user/analysis-engine --output /tmp/marketsage-data-audit.json
```

Review the summary and the generated JSON locally. Do not commit the generated report or local smoke reports automatically. Keep PR #6 open, do not deploy, and keep ranking disabled.


## Superseding update — Stage 4 implementation and Stage 5 kickoff (2026-10-18)

This section supersedes earlier handoff notes that Stage 4 had not started. Work was added to the existing feature branch / PR #6:

- Updated `research/backtest.py`: annual risk-free-rate assumption is explicit in Sharpe reporting; transaction costs, slippage, and total costs are reported separately; the legacy aggregate cost key now sums all charged costs.
- Added `research/evaluation.py`: fixed-parameter comparison against a zero-return cash reference and an equal-weight monthly-rebalanced reference; full-period and final 12-month holdout metrics; six-month chronological folds before the holdout; six-month forward-label inventory only.
- Added `scripts/run_stage4_evaluation.py`: repeatable JSON report with input dataset SHA-256 and configurable holdout, fold, cost, and risk-free assumptions.
- Added `tests/test_research_evaluation.py` and extended `tests/test_research_backtest.py` for these contracts.
- Extended `docs/stage4-evaluation-protocol.md` with command and interpretation constraints.
- Added `docs/stage5-operational-readiness-checklist.md`; Stage 5 has started as a checklist/readiness workstream, not as production release approval.

**Important: implementation is not the same as acceptance.** These new changes have not yet been run on the owner's local checkout in this conversation. Wait for the exact PR-head GitHub Actions result and local focused/full Python test results. Review any failures and fix them before interpreting the generated report. Do not mark Stage 4 complete until the runner/report is reproduced and reviewed, data provenance/permissions and point-in-time/survivorship gaps are resolved or explicitly bounded, and the locked holdout is not used for tuning.

**Stage 5 remains open.** No staging deployment was performed, no production readiness claim is made, PR #6 remains unmerged, and investment ranking/source scoring must remain disabled.


## Local evidence update — 2026-10-18

The owner reports the Stage 4 runner completed locally against the monthly panel with SHA-256 `1e71d898b18b4a6db74aba4826c86a4982efad934ee30aa82ff354883f01d878`, 78 rows, 11 assets, data range 2020-04-30 through 2026-09-30, 12-month holdout 2025-10-31 through 2026-09-30, and 7 walk-forward folds. The focused tests passed 16/16 and the full Analysis Engine suite passed 225/225 on the checkout before the report-validator addition. These are user-provided local results, not independently executed by this maintainer.

Stage 5 work added `scripts/validate_stage4_report.py` and `tests/test_stage4_report_validator.py`. They validate research-only/disabled-ranking flags, SHA-256 shape, baseline presence, holdout separation, and cost scenario presence. **The validator tests and full suite must be rerun after this newest change.** The metric values from the generated report have not yet been reviewed, so Stage 4 is not accepted. CI for the newest changes is pending; PR #6 remains unmerged and no deployment has been performed.


## Latest source-discovery checkpoint — 2026-10-20

This checkpoint records the free-dataset acceptance work on a separate workstream; it does not supersede or merge the Tindex connector branch.

### Branch / CI distinction

- PR #6: `feat/tindex-free-data-connector` → `deploy/production-readiness`; still open.
- PR #13: `feature/free-dataset-discovery-acceptance` → `feature/iran-live-data-dashboard`; last inspected open and mergeable, head `ef5183c8d800efa1e729939c3966839ec541dd58`.
- Local acceptance-pack result for the PR #13 workstream: **265 tests passed in 17.19 seconds; 9 warnings**. Offline tests, catalog and shell syntax passed. This is local evidence; the current GitHub Actions result for the exact head has not been confirmed here.
- Keep the two PRs distinct. Do not merge, deploy, or enable ranking as part of the data-discovery checkpoint.

### Free-source discovery results

Report path on the user's machine: `/tmp/marketsage-free-dataset-acceptance/public-live-probes.json`.

| Source | Latest result | Interpretation |
|---|---|---|
| TSETMC | `reachable_response_received` | Reachability only; VPN off |
| CODAL | `reachable_response_received` | Reachability only; VPN off |
| World Bank Indicators | `reachable_schema_validated_candidate`, 26 annual Iran CPI observations for 2000–2025 | Candidate only; VPN on before any future foreign-source request |
| Binance Spot public data | `probe_failed`, sanitized error class `HTTPStatusError` | Cause not established; do not infer provider outage or code defect without a bounded diagnosis |

Three of four public probes returned a response. The report explicitly states `production_approved=false`; this is not source acceptance. Tindex was skipped because `TINDEX_API_BASE_URL`/`TINDEX_API_TOKEN` were absent in the shell; FRED/ALFRED was skipped because `FRED_API_KEY` was absent; GDELT was not contacted. Do not ask for secrets in chat or repeat the entire acceptance pack merely to diagnose Binance.

### Seller CSV audit — outside the free-source batch

Metadata-only report: `/tmp/marketsage-free-dataset-acceptance/vendor-streamdata-quality-report.json`. The four seller-provided files were all parseable candidates; no raw values were emitted and none was production-approved.

| Dataset | Rows | Date range | Audit note |
|---|---:|---|---|
| AYAR gold fund daily | 123 | 2026-04-19 – 2026-10-18 | 1 OHLC invariant violation |
| BTCUSDT daily | 184 | 2026-04-19 – 2026-10-19 | No detected structural issue |
| Gold18 daily | 184 | 2026-04-19 – 2026-10-19 | No detected structural issue |
| US Dollar daily | 176 | 2026-04-19 – 2026-10-19 | No detected structural issue |

All four reports showed zero invalid/missing/duplicate dates and zero source-order inversions. Investigate the AYAR OHLC violation using the user's local copy and vendor documentation; quarantine the affected observation until corrected by evidence. These are seller-provided exports, not free/open datasets. Confirm contract, usage and redistribution/training rights, units, timezone/session rules and adjustment semantics before research use. Never put these CSV files or raw price rows into GitHub. Their approximately six-month history does not by itself support robust six-month-horizon strategy validation.

### VPN rule (owner requirement — must be stated before any live command)

Before asking the user to execute a live request to any foreign/international provider, explicitly tell them to turn VPN on first. This specifically includes **FRED/ALFRED, Binance, World Bank, GDELT and other foreign sites**. Do not mix foreign and Iranian probes in one batch with ambiguous VPN state.

- TSETMC, CODAL, Tindex: VPN **off**.
- FRED/ALFRED: VPN **on**, and only if `FRED_API_KEY` is already configured securely.
- Binance, World Bank and GDELT: VPN **on** before a live request.
- GDELT had previously returned HTTP 429; do not retry before an intentional cooldown and bounded request budget.
- Tindex: if credentials are configured, probe separately with VPN off; enforce 3 requests/minute and 300 successful requests/day. Never print or share tokens.

### Updated immediate next actions

1. Inspect PR #13's current head and GitHub Actions status, and preserve local modifications/untracked files (`git status --short --branch`); no destructive reset/clean.
2. Diagnose the single Binance HTTP-level failure with at most one bounded retry after telling the user to enable VPN; separate network/provider diagnosis from source-quality acceptance.
3. Inspect and quarantine the AYAR OHLC anomaly locally; do not silently repair it or use the four vendor CSVs as “free data.”
4. Continue provenance/permission, units, timestamp, history-depth and independent-reconciliation checks for each source. Keep the World Bank data as an annual macro candidate; do not treat response-schema success as approval.
5. Keep Stage 2 source acceptance open; scoring/ranking disabled. Stage 4 may use only appropriately labelled research data, with point-in-time limitations explicit. Do not merge either PR or deploy without explicit authorization.

**Next-session starting point:** no more full-suite rerun is required just to read these reports. Start with branch/PR/CI state, the sanitized Binance error and local AYAR anomaly. When any foreign-source probe is proposed, announce VPN-on first.


## Latest execution checkpoint — 2026-10-20 (source gates and staging decision)

### CI and branches

- PR #6, feat/tindex-free-data-connector → deploy/production-readiness, remains open/unmerged. Latest inspected head 496cb9bc9785442b43ba1d31ee1f44ed30f0913d; [CI run #39389606760](https://github.com/yarsalam/marketsage/actions/runs/39389606760) passed all five jobs.
- PR #13, feature/free-dataset-discovery-acceptance → feature/iran-live-data-dashboard, remains open/unmerged. Latest inspected head 8d330c460bf2cd89ff2bb4a59e7a07523e6dfb1f; [CI run #39392008358](https://github.com/yarsalam/marketsage/actions/runs/39392008358) passed all five jobs.
- These branches target different bases and must be reviewed separately. CI success verifies the checked code/build contracts; it does not approve a live data source or authorize deployment.

### VPN-isolated source acceptance tooling

PR #13 changes the free-dataset acceptance runner so the default run is offline and creates inventory/evidence templates without provider calls. Live probes require exactly one source group per invocation:

- Iranian providers: --live-iran, with VPN OFF; optional Tindex candle probe only via --include-tindex. The runner requires a terminal confirmation VPN-OFF.
- Foreign providers: --live-foreign, with VPN ON; optional FRED via --include-fred and GDELT via --include-gdelt. The runner requires a terminal confirmation VPN-ON.
- Mixed groups and invalid option combinations exit before any live provider request. The script cannot detect the real VPN state, so the user is explicitly warned and must confirm it.
- New shell-contract tests cover the mixed-group refusal and option guards. The latest CI run on the exact PR #13 head passed all five jobs.

Before suggesting any live foreign-source command, explicitly tell the user to turn VPN on. GDELT is still under cooldown/low-retry discipline after the previous HTTP 429.

### Updated cross-market data maturity matrix

| Market/data family | Current status | Remaining acceptance work |
|---|---|---|
| Iranian stocks/funds | TSETMC and CODAL bounded probes returned responses; candidate adapters exist | Full symbol master, symbol identity, historical depth, adjusted-price methodology, dividends/capital actions, delisted/suspended instruments, licensing and independent reconciliation |
| Gold/coins | Tindex and vendor StreamData are candidates; TGJU automated path is not approved | Verify unit (Rial/Toman), quote convention, instrument/coin identity, timestamp, history overlap and rights. Investigate and quarantine the single AYAR OHLC violation |
| Free-market FX | Prior Tindex snapshot is candidate; latest Tindex batch skipped for missing configuration | Precisely define free vs official quote, preserve units/times and validate historical coverage against an independent lawful reference |
| Crypto | Yahoo Finance research proxies; vendor BTCUSDT file; latest Binance public probe failed at HTTP-status level | Diagnose Binance once with a bounded request after VPN-on reminder; validate pair/venue, OHLCV, full six-month coverage, fees/slippage and terms |
| Fixed income | No accepted provider or series | Find an accessible lawful series with consistent yield convention, maturity/duration metadata, dates and history; otherwise mark unavailable |
| Iran macro/inflation | World Bank schema-valid candidate: 26 annual Iran CPI observations, 2000–2025; official Iranian feeds not automated/accepted | Preserve annual period rather than invent daily timestamps; acquire publication/revision dates and validate Central Bank/Statistical Center series |
| CODAL corporate events | Search adapter candidate | Link amendments/corrections, distinguish publication time from retrieval time, map filings to structured event schema and point-in-time availability |
| News/geopolitics | GDELT discovery adapter exists; previous 429 | Validate coverage/reliability, preserve first-seen separately from publication time, build event labels and avoid look-ahead |
| Sentiment/social | Not production-validated or connected to ranking | Choose permitted sources, manually label a representative Persian/English benchmark, report out-of-sample class-wise metrics and drift; abstain when uncertain |

Seller StreamData is explicitly non-free/vendor-provided. None of its four exports is approved for public commits or production training; its latest audit found one AYAR OHLC anomaly. A data-quality pass is not proof of usage rights, and roughly six months of rows do not by themselves prove a six-month investment strategy.

### Staging versus complete source acceptance

Decision: Continue application completion and prepare staging in parallel with source acceptance. Do not block fixture-backed service/UI smoke tests while every market awaits historical/legal acceptance. A staging prototype may use synthetic and explicitly labelled research-only data; any unapproved market must return an explicit unavailable/not-rankable state. The live investment ranking/source scoring must remain disabled.

The currently inspected production Compose defines only analysis-engine, user-backend, and user-frontend. CI builds the admin workspace, but that admin service is not included in the production Compose file. Before staging, decide whether admin is outside the first staging scope or requires its own reviewed deployment service. The Compose file also relies on externally managed DNS/TLS/reverse proxy, firewall and production environment values.

### Staging exit checklist

1. Do not merge either PR or deploy until the user explicitly authorizes it.
2. Select a single reviewed release-candidate commit after checking current branch heads and CI status; do not deploy the PR #13 branch accidentally, as it targets another feature branch.
3. Prepare the server's .env.production privately with restrictive permissions, validate Compose configuration, build immutable images and record the exact commit/image digests.
4. Verify DNS/TLS/reverse proxy, firewall/exposure, secret handling, backups and a tested rollback.
5. Smoke-test health and API/UI paths for fixture-backed success, not-rankable response, stale data, provider failure and recovery. Keep sanitized evidence only.
6. Keep all unaccepted source IDs out of scoring; staging success is not source, model or production acceptance.

### Immediate next action

Review both open PRs and local branch status. If the user is ready to authorize staging, ask for the target server/environment details then prepare a deployment-specific plan; until that authorization, continue on feature branches only. For foreign live data probes, remind the user to enable VPN before giving the command; for TSETMC/CODAL/Tindex, specify VPN off. Do not repeat the entire 265-test pack just to revisit the already-read reports.


## Latest operational increment — 2026-10-20 (readiness endpoint)

- Implemented distinct endpoint contracts: /health reports only process liveness; /ready reports research-only readiness after verifying that the source registry is non-empty, its reported counts match the entries, and the research-snapshot callable is loaded.
- /ready returns HTTP 503 with a sanitized reason if critical local registry/pipeline prerequisites are invalid. It does not contact TSETMC, CODAL, Tindex, FRED, Binance, World Bank, GDELT or any other provider.
- The Analysis Engine Dockerfile and docker-compose.production.yml now use /ready for the container health check. This makes the Compose dependency check meaningful for local app readiness while leaving provider/data approvals as separate gates.
- Added tests for /health liveness, /ready research-only semantics/disabled ranking, and an invalid/empty registry returning 503.
- CI run [#39393823453](https://github.com/yarsalam/marketsage/actions/runs/39393823453) passed all five jobs on exact PR #6 head 37c6e85dea37b02543df7150d359d8f72c5be511, including production-images. This is a code/build test, not server staging evidence.
- Remaining Stage 5 gates still include source outage/staleness failure tests across all paths, auth/access-control review, secret and dependency security checks, network exposure/TLS, backups/restore, staging smoke tests and rehearsed rollback. No deployment was performed.


## Staging exposure review — 2026-10-20

Static review of the current feature branch found a concrete access-control gap:

- The NestJS MarketsController exposes GET markets/scores/backtest/data-status and POST research-snapshot without a controller/route authentication guard. main.ts configures CORS, but CORS is not authentication.
- The research snapshot endpoint processes a caller-supplied payload. Keep it private during staging; review payload-size and request-rate limits before public exposure.
- The frontend calls same-origin /api/markets/research-snapshot when NEXT_PUBLIC_API_URL is empty. next.config.ts has no /api rewrite, and the production Compose file does not define a reverse-proxy service. A server-managed reverse proxy is therefore required to route /api/ to the user backend and other paths to the frontend.
- Keep the Compose host ports bound to loopback. For staging, put an IP allowlist or strong authentication at the reverse proxy and use TLS; do not expose 3000/4500 directly. CORS is not an access-control substitute.
- Before public exposure, implement app-level auth/authorization and request-rate/size controls with regression tests. This was a static code review; no server was contacted and no deployment was performed.
