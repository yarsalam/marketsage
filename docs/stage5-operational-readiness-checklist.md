# Stage 5 — Operational Readiness Checklist

**Status:** active; bounded stale-cache fallback and research-only readiness checks have CI-passing implementation. Deployment gates remain open; not approved for production or deployment.  
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
- [x] Point the Analysis Engine Dockerfile and production Compose health checks at `/ready`; the user backend waits for the Analysis Engine container to become healthy. This is local app readiness, not live-source approval.
- [ ] Verify live-data failures cannot silently substitute synthetic or incompatible data across all source/API paths.
- [ ] Verify logs and errors contain no tokens, credentials, or raw provider payloads. The price-refresh path now logs exception type only; wider log review remains open.

## B. Health, readiness, and failure behaviour

- [x] Define distinct semantics: `/health` is process liveness only; `/ready` validates source-registry structure/counts and research-snapshot availability, returns HTTP 503 on empty/inconsistent registry, and makes no external provider requests.
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
- [ ] Access-control blocker confirmed on the current branch: MarketsController exposes markets, scores, backtest, data-status and research-snapshot without an authentication guard; CORS is not authentication. Keep staging behind a private reverse proxy with an IP allowlist or strong authentication, and add application auth/authorization plus request-rate/size controls before public exposure.
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


## Readiness endpoint implementation — 2026-10-20

- Implemented separate liveness and readiness response semantics in the Analysis Engine.
- Readiness verifies the in-memory source registry is non-empty/consistent and the research-snapshot pipeline is callable; failure produces HTTP 503 with a sanitized response.
- Readiness does not make provider requests and does not require a production-approved source, because the allowed staging scope is the research-only fixture path.
- Dockerfile and Compose health checks now target /ready.
- Tests added: tests/test_health_readiness.py.
- CI run [#39393823453](https://github.com/yarsalam/marketsage/actions/runs/39393823453) passed all five jobs on PR #6 head 37c6e85dea37b02543df7150d359d8f72c5be511.
- Still open: source failure/stale data scenarios throughout the API, auth/access-control review, dependency/secret security, TLS/reverse proxy, resource limits, backup/restore, staging smoke test and rollback rehearsal. No server deployment was performed.


## Staging access-control finding — 2026-10-20

The current branch's MarketsController endpoints have no authentication guard; CORS in main.ts does not protect API access. The ResearchSnapshot UI defaults to same-origin /api, but Next.js has no rewrite and the Compose file does not contain a reverse proxy. The server deployment must configure a reverse proxy to route /api/ to the user backend and / to the frontend. Keep host ports bound to loopback and protect staging with an IP allowlist or strong authentication plus TLS. Before public exposure, implement app-level authorization and request-rate/size protections with tests. No server deployment was performed.


## Staging overlay and adjustment-history tests — 2026-10-20

- Added a staging-only Compose overlay and Caddy reverse proxy with HTTPS and a global Basic Auth gate. It proxies `/api/*` to the user backend and remaining paths to the frontend. The env example intentionally uses placeholder domain/hash values and cannot be deployed without private operator configuration.
- GitHub Actions run [#39404768839](https://github.com/yarsalam/marketsage/actions/runs/39404768839) passed all five jobs, including validation of the staging Compose overlay and Caddyfile. This is CI evidence, not a server smoke test.
- No deployment occurred. Server, DNS and authorization-specific prerequisites remain open.
- PR #13 adjustment/history test coverage is now 32 collected fixture test cases across three modules; CI run [#39403875602](https://github.com/yarsalam/marketsage/actions/runs/39403875602) passed on code/test commit `cb557837788e0f805088ac7ad72a9aedc676143c`. The next docs-only matrix commit's CI must be checked separately.
- Live-data acceptance is still open: one previously reported فولاد sample has 4,664 raw rows / 4,249 adjusted / 415 unmatched. Expand with two additional exact-identity instruments selected from actual adjustment-event responses, review event windows and independent reconciliation. Missing adjusted rows must not fall back to raw prices.
