# MarketSage — Product Roadmap
**Snapshot:** 2026-11-09  
**Rule:** Parallelize independent work; integrate only after dependencies and acceptance criteria are met.

## Stage 0 — Operating controls
**Outcome:** every active initiative has a contract, evidence and a stop condition.
- Strategy charter, register, decision policy, evidence ledger and release gates are versioned.
- A read-only validator checks the records on PR/push and on a bounded daily schedule.
- Existing strategy/PR/state records are reconciled; stale plans are explicitly superseded, not silently trusted.

## Stage 1 — First real user workflow
**Outcome:** user can inspect a selected market's coverage and understand whether a research answer is possible.
- Market/asset-family selection.
- Source and instrument catalogue with candidate/approved/quarantined/unavailable states.
- Data quality, time coverage, freshness, units and provenance.
- Research-only empty states that explain the missing evidence and the next required validation.
- One reproducible end-to-end browser/API scenario.
**Current related implementation:** draft PR #73 (coverage/registry) and draft PR #77 (research-only output gates and truthful helper). Both remain unmerged and do not yet count as user value.

## Stage 2 — Trustworthy account and operations
**Outcome:** user data and operator controls are protected.
- Backend login/session/authentication and route protection.
- API authorization on private research routes.
- Admin UI and API with role enforcement, audit trail and read-only health/source operations first.
- Deployment topology includes only reviewed components; no admin exposure before its security gate passes.

## Stage 3 — Data breadth and point-in-time integrity
**Outcome:** each target asset family has a defensible, reproducible dataset.
- Keep Iran and global asset-family discovery active in parallel.
- Evaluate source rights, identity, units, calendars, history depth, revisions, corporate actions and independent reconciliation separately.
- Store provenance and source/retrieval/availability timestamps.
- Keep unaccepted sources quarantined from investment analytics.

## Stage 4 — Research dossier and contextual intelligence
**Outcome:** a user receives a source-linked dossier with observations, scenarios, uncertainty and missing evidence.
- Market history and cross-market comparisons only where input data passed its own gate.
- Macro publication vintages, news/event timestamps and asset attribution.
- Separate observed facts from interpretation and model outputs.
- No ranking or probability claims by default.

## Stage 5 — Empirical strategy validation
**Outcome:** a locked, reproducible evaluation supports or rejects the agreed six-month methodology.
- Pre-register universe, benchmark, target, costs, liquidity constraints and risk metrics.
- Point-in-time replay, chronological holdout and walk-forward tests.
- Attribute outliers and compare realistic costs/taxes/FX/market impact.
- Keep final holdout sealed; no parameter tuning against it.
- A failed result is a valid stop/reject decision, not a reason to loosen gates.

## Stage 6 — Release decision
**Outcome:** release only a useful, secure, supportable research product.
- Complete end-to-end user journey.
- Authentication and authorization; no critical security findings.
- Source/licensing posture and UI claims verified.
- Health/backup/rollback/support runbook.
- Separate owner approval for enabling investment outputs or any capital-risk function.

## Parallel execution and integration

Current independent streams are recorded in `WORK_REGISTER.json`. PR #73 and PR #77 are independent in intent but both change the user landing-page path; reconcile their changes into one reviewed integration before merge. PR #74 is a separate infrastructure foundation. PR #71 and PR #61 are based on PR #74 and therefore remain dependent, not independently mergeable. PR #6 remains separately protected by explicit owner approval.
