# MarketSage Implementation Roadmap

**Status date:** 2026-10-18  
**Working branch:** `feat/tindex-free-data-connector`  
**Current milestone:** Stage 1 — connector technical acceptance  
**Release posture:** research-only; source scoring remains fail-closed

This roadmap separates implementation progress from evidence that a data source or model is safe to use. Passing unit tests proves the tested code paths behave as expected on fixtures; it does not prove live-data quality, legal permission, predictive performance, or production readiness.

## 1. Current stage and evidence

### Stage 1 — Connector technical acceptance (in progress)

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

### Stage 1 exit criteria

1. Confirm the full suite is reproducible from the intended branch and record the exact commit and test result.
2. Review and resolve (or explicitly accept with an issue) the deprecation warnings.
3. For each source, record endpoint/contract, fields, units and quote conventions, observation vs publication vs retrieval time, timezone, revisions/corrections, missing data, history depth, rate limits, and permission/licensing.
4. Add sanitized, deterministic fixtures for real response shapes and error cases; never commit API keys or sensitive raw payloads.
5. Reconcile data with an independent reference where legally permitted.
6. Test that unknown units/timestamps, unavailable sources, stale observations, and unapproved sources cannot enter scoring.
7. Keep the source registry fail-closed until an explicit review approves a source for a narrowly defined use.

**Stage 1 decision:** Do not block prototype development on every external source being approved. Stage 2 can begin with deterministic fixtures and clearly labelled research-only data, while Stage 1 acceptance gaps remain open.

## 2. Stage 2 — End-to-end research prototype

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

### Stage 2 acceptance evidence

- Deterministic end-to-end tests with frozen fixtures.
- Tests for duplicate news, corrected disclosures, missing values, unit mismatches, stale data, unavailable providers, and timestamp leakage.
- At least one fully traceable example from source record to final rank, including rejected records and explanation.
- No live investment scoring from unapproved sources.

## 3. Stage 3 — Model and strategy validation

1. Build time-stamped, independently labelled Persian/English sentiment and event evaluation data; publish class-wise precision, recall, F1, confusion matrices, and error analysis.
2. Define the investment universe, benchmark, decision cadence, horizon, costs, slippage, liquidity constraints, and portfolio rules before evaluating strategies.
3. Use chronological splits and walk-forward/out-of-sample testing; prevent look-ahead, survivorship, revision, and publication-time leakage.
4. Compare against simple baselines and buy-and-hold/appropriate asset benchmarks.
5. Report net returns, volatility, maximum drawdown, Sharpe/Sortino where appropriate, VaR/expected shortfall with assumptions, turnover, and performance by regime.
6. Test sensitivity to transaction costs, missing/stale data, source outages, model changes, and alternative parameter choices.
7. Calibrate probabilities on held-out data before exposing confidence estimates; document calibration and uncertainty.
8. Version datasets, source contracts, features, models, configuration, and every generated decision so results can be replayed.

**Exit gate:** results are reproducible out of sample, limitations are documented, and a reviewer can replay a historical decision using only information available at that time. Passing this gate still does not guarantee future returns.

## 4. Stage 4 — Operational readiness and controlled release

- Add structured metrics/logging without secrets, health/readiness checks, bounded timeouts, provider-specific rate limits, cache policies, and safe degradation.
- Add data-quality alerts for staleness, schema drift, missing intervals, unexpected unit/scale changes, and abnormal duplicate rates.
- Ensure provider failures cannot silently fall back to fabricated or incompatible data.
- Secure secrets through environment/secret management; review access control, dependency security, backups, retention, and permitted data storage.
- Run API, integration, and deployment smoke tests in a staging environment; verify DNS/TLS, reverse proxy, firewall, resource limits, and rollback procedures before any release.
- Provide source lineage, methodology notes, risk disclosures, model/version identifiers, and an auditable decision history.
- Do not claim the entire product is production-ready while admin/auth/deployment blockers listed in the repository README remain unresolved.

**Exit gate:** a documented release review explicitly approves the supported scope, with rollback and monitoring in place. Approval of one data source or one API endpoint does not approve the whole investment product.

## 5. Stage 5 — Source-by-source approval and expansion

Approve sources individually and only for the purposes actually reviewed. Maintain a registry with states such as `candidate`, `reachable_only`, `research_only`, `approved_for_specific_fields`, and `disabled`.

For each source, the approval record must include:
- owner/reviewer and review date;
- terms/licensing decision and permitted use;
- endpoint/schema version and fixture provenance;
- unit, currency, timestamp, revision and coverage validation;
- independent reconciliation evidence;
- rate limits, outage behaviour and operational owner;
- exact approved fields/use cases and explicit exclusions.

TGJU, unsupported Tindex categories, and any source with unresolved rights or semantics remain disabled. Never bypass a provider's disabled endpoint or access restrictions.

## Immediate next action

1. Keep the passing full-suite result as local evidence: `188 passed, 7 warnings`.
2. Do not run another redundant provider test pack now. The next useful check is to confirm the result against the current feature-branch commit and inspect the warning sources when convenient.
3. Start Stage 2 with canonical schemas and a fixture-backed vertical slice (one market-data series plus a small, manually reviewed news/event fixture set). No additional live provider calls are required to begin.
4. Leave live scoring disabled until the relevant source and model gates pass.

## Project status report (copy-ready)

- **Current stage:** Stage 1 — connector technical acceptance, with Stage 2 prototype work ready to begin using fixtures.
- **Evidence:** local full analysis-engine suite: 188 passed, 7 warnings, 8.83s (reported 2026-10-18); bounded live probes reached TSETMC, CODAL, Tindex, and FRED/ALFRED at least once.
- **Not verified:** CI status for this exact commit; external-data licensing; full schema/units/timestamps/history/revision semantics; independent reconciliation; GDELT reliability after HTTP 429; real-world sentiment/event accuracy; out-of-sample investment performance.
- **Exact next step:** implement the canonical data contract and one deterministic end-to-end, fixture-backed research path. No further broad test pack is required before beginning.
- **Remaining stages:** complete source acceptance; end-to-end research prototype; labelled NLP/event and leakage-aware strategy validation; operational/security readiness; source-by-source release approval.
