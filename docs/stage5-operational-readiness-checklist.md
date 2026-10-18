# Stage 5 — Operational Readiness Checklist

**Status:** active; bounded stale-cache fallback and regression tests added. CI run #246 passed all jobs on code commit `21e4b2e5db74972f510fa88833f99e510984a2c1`; local confirmation and deployment gates remain open. Not approved for production or deployment.  
**Branch:** `feat/tindex-free-data-connector`  
**Release posture:** research-only; source scoring and investment ranking remain disabled.

Stage 5 is not complete merely because the code builds or a historical simulation completes. This checklist tracks operational evidence separately from Stage 2 source acceptance and Stage 4 empirical evaluation.

## A. Current guardrails

- [x] Feature branch / PR remains separate from the deployment branch.
- [x] Backtest and evaluation outputs explicitly identify research-only purpose.
- [x] Evaluation report records dataset SHA-256 and declares investment ranking/source scoring disabled.
- [x] Added a report validator and tests for fail-closed flags, holdout boundaries, required baselines, hash shape, and cost scenarios; project owner reports the validator passed and the full suite passed on the local checkout.
- [x] Unknown source semantics and unapproved providers remain outside scoring.
- [ ] Verify current source registry and every API path remain fail-closed in CI and local tests.
- [x] Bound stale-cache fallback with `MAX_STALE_CACHE_AGE_SECONDS` (default 24 hours); cache older than the limit fails with HTTP 503 instead of returning a decision.
- [x] Added regression tests for bounded stale fallback, explicit stale status, fail-closed 503 after the age limit, and provider exception-message redaction.
- [ ] Verify live-data failures cannot silently substitute synthetic or incompatible data across all source/API paths.
- [ ] Verify logs and errors contain no tokens, credentials, or raw provider payloads. The price-refresh path now logs exception type only; wider log review remains open.

## B. Health, readiness, and failure behaviour

- [ ] Define and verify separate liveness and readiness semantics; `/health` and `/ready` currently exist but both return unconditional success.
- [ ] Bound network timeouts and retries per provider; never automatically retry GDELT during a provider cooldown/HTTP 429.
- [ ] Verify per-provider rate limits and caching; Tindex limits remain enforced.
- [ ] Test source timeout, HTTP error, malformed schema, missing timestamp, unknown currency/unit, stale response, duplicate observations, and empty history.
- [ ] Verify an unavailable or unapproved source yields an explicit unavailable/not-rankable state, not a fallback recommendation.
- [ ] Verify partial dependency failures are visible in health/metrics without leaking sensitive response bodies.

## C. Observability and auditability

- [ ] Structured logs include request/correlation ID, provider ID, operation, latency, result class, and sanitized error code.
- [ ] Metrics cover request count/latency/error rate, rate-limit responses, data freshness, missing intervals, schema drift, and rejected records.
- [ ] Alerts have documented thresholds, owner, and response procedure.
- [ ] Every generated research decision records code/model version, configuration, source lineage, data cut-off, and artifact/dataset hashes.
- [ ] Logs do not contain credentials, personal data, or unlicensed raw payloads.

## D. Security and deployment safety

- [ ] Confirm all secrets are environment/secret-manager supplied and absent from Git history, logs, images, and artifacts.
- [ ] Review dependency vulnerabilities and supported runtime versions.
- [ ] Verify authentication/authorization boundaries for research endpoints and admin functions.
- [ ] Review network exposure, TLS, reverse proxy, firewall, container resource limits, and least-privilege permissions.
- [ ] Verify backups and restore procedure for persistent state; document retention/deletion policy.
- [ ] Build immutable images from the reviewed commit; record image digests and SBOM where supported.
- [ ] Perform staging-only smoke tests after explicit deployment approval; production deployment is a separate approval.

## E. Release and rollback

- [ ] Stage 2 source-specific acceptance records are reviewed and approved for narrowly defined fields/use cases.
- [ ] Stage 4 report is reproducible from a pinned dataset and commit; holdout was not used for tuning.
- [ ] API, integration, frontend, backend, and image CI jobs pass on the exact release candidate.
- [ ] Staging smoke test covers normal response, not-rankable response, stale data, provider outage, and recovery.
- [ ] Release notes explain supported markets, excluded data, cost assumptions, risk limitations, and non-guarantee of returns.
- [ ] Rollback trigger, rollback command/procedure, and post-rollback verification are documented and rehearsed.
- [ ] Named reviewer explicitly approves the exact supported release scope.

## F. Required local/CI evidence

Run only against the intended branch and retain sanitized summaries:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
git log -1 --oneline
cd user/analysis-engine
.venv/bin/python -m pytest -q tests/test_research_backtest.py tests/test_research_evaluation.py
.venv/bin/python -m pytest -q
```

Then run the Stage 4 evaluation command documented in `docs/stage4-evaluation-protocol.md`, followed by:

```bash
.venv/bin/python scripts/validate_stage4_report.py /tmp/marketsage-stage4-evaluation.json
.venv/bin/python -m pytest -q tests/test_stage4_report_validator.py
```

Confirm its dataset hash and output dates before interpreting any metrics. Do not commit local reports, tokens, or raw licensed data.

## Work completed in this Stage 5 increment

- Bounded stale market-cache fallback with a configurable maximum age (default 86,400 seconds / 24 hours); expired cached data returns HTTP 503 and cannot generate a decision.
- Sanitized provider-refresh logging to record exception type without logging exception text or provider response details.
- Added regression coverage for stale-cache use within the limit, explicit stale metadata, rejection after the limit, and log redaction.
- Added `MAX_STALE_CACHE_AGE_SECONDS` to the production Compose environment and `.env.production.example`.
- Added `docs/stage4-empirical-review-2026-10.md` with the observed results, the extreme 2023-10–2024-03 fold, and outstanding attribution/data-quality checks.

## Current decision

**Stage 5 is in progress; release gate not passed.** CI run [#246](https://github.com/yarsalam/marketsage/actions/runs/39128372381) passed all jobs, including 233 Analysis Engine tests and production-image build, on code commit `21e4b2e5db74972f510fa88833f99e510984a2c1`. The project owner still needs to pull the latest branch and confirm the local test run. Separate readiness semantics, provider/schema/staleness failure tests across all source paths, source rights/semantics review, point-in-time and survivorship assessment, security/dependency review, backup/restore rehearsal, staging smoke tests, rollback rehearsal, and explicit release approval remain open. Investment ranking and source scoring must remain disabled.
