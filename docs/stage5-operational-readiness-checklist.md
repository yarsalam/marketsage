# Stage 5 — Operational Readiness Checklist

**Status:** started as a readiness workstream; not approved for production or deployment.  
**Branch:** `feat/tindex-free-data-connector`  
**Release posture:** research-only; source scoring and investment ranking remain disabled.

Stage 5 is not complete merely because the code builds or a historical simulation completes. This checklist tracks operational evidence separately from Stage 2 source acceptance and Stage 4 empirical evaluation.

## A. Current guardrails

- [x] Feature branch / PR remains separate from the deployment branch.
- [x] Backtest and evaluation outputs explicitly identify research-only purpose.
- [x] Evaluation report records dataset SHA-256 and declares investment ranking/source scoring disabled.
- [x] Added a report validator and tests for fail-closed flags, holdout boundaries, required baselines, hash shape, and cost scenarios; local execution still pending.
- [x] Unknown source semantics and unapproved providers remain outside scoring.
- [ ] Verify current source registry and every API path remain fail-closed in CI and local tests.
- [ ] Verify live-data failures cannot silently substitute synthetic, stale, or incompatible data.
- [ ] Verify logs and errors contain no tokens, credentials, or raw provider payloads.

## B. Health, readiness, and failure behaviour

- [ ] Define separate liveness and readiness checks; readiness must fail when mandatory dependencies/configuration are missing.
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

## Current decision

**Stage 5 started; release gate not passed.** Outstanding prerequisites include local execution of the report validator and its tests on the newest commit, full-suite confirmation after the newest validator addition, Stage 2 source rights/semantics/coverage review, point-in-time and survivorship assessment, operational failure-mode tests, and explicit staging/release approval. Investment ranking must remain disabled until the applicable gates are approved.
