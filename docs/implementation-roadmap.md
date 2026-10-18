# MarketSage Implementation Roadmap

**Status date:** 2026-10-18  
**Working branch:** `feat/tindex-free-data-connector`  
**Current milestone:** Stage 3 — end-to-end prototype (first fixture-backed slice added)  
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
   - Expose the prototype through versioned research endpoints and show source freshness, data coverage, model/version, risk metrics, and explanation.
   - Keep unsupported dashboard sections visibly unavailable instead of filling them with fabricated estimates.

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

1. Run the new fixture-backed pipeline tests and then the full analysis-engine suite from `user/analysis-engine`.
2. Review the CI run associated with the latest feature-branch commit once it finishes; the local result and CI result must be reported separately.
3. Inspect and fix any failures before wiring this research-only function into an API or UI.
4. Keep source scoring disabled; the new pipeline is an auditable prototype, not a validated investment signal.

## Project status report (copy-ready)

- **Stage 1 — code and existing tests:** local full suite reported 188 passed, 7 warnings, 8.83s on 2026-10-18; GitHub Actions previously had a successful run, and a newer run is queued for the latest commit.
- **Stage 2 — source acceptance:** in progress; TSETMC, CODAL, Tindex, and FRED/ALFRED had bounded live responses, but data semantics/licensing/coverage are not fully approved; GDELT previously returned HTTP 429.
- **Stage 3 — end-to-end prototype:** started. Added `research_pipeline.py` and `tests/test_research_pipeline.py` on the feature branch. The function combines fixture/provided article metadata, transparent headline labels, and descriptive price metrics; excludes future-dated rows, flags unknown units/source approval, and hard-disables investment ranking.
- **Stage 4 — model/backtest:** not started for this integrated pipeline; needs labelled NLP/event evaluation, point-in-time validation, chronological holdout/walk-forward, costs/liquidity and drawdown/risk reporting.
- **Stage 5 — operational/release:** not started; monitoring, failure handling, security, staging deployment, and release review remain.
- **Not verified:** tests for the newly added pipeline until the user runs them; CI status for latest commit until queued workflow completes; licensing, data correctness, and real-world predictive performance.
- **Exact next step:** run `python -m pytest -q tests/test_research_pipeline.py`, then run `python -m pytest -q` if focused tests pass.
- **Release posture:** research-only; no production investment scoring or ranking enabled.
