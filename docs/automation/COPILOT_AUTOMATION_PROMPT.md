# MarketSage coding-agent operating prompt — parallel execution

This is an execution policy for a coding agent only when a no-incremental-cost agent is already available and explicitly enabled. Do not provision paid credits, AI/API services, hosted workers or always-on machines.

## Canonical strategy and records

Read these before selecting work:
- `docs/governance/PROJECT_EXECUTION_CONSTITUTION.md`
- `docs/governance/STRATEGY_CHARTER.md`
- `docs/governance/PRODUCT_ROADMAP.md`
- `docs/governance/WORK_REGISTER.json`
- `docs/governance/DECISION_POLICY.json`
- `docs/governance/RELEASE_GATES.json`
- `docs/governance/EVIDENCE_LEDGER.json`
- `docs/governance/PROJECT_STATE.json`
- `docs/governance/PROJECT_STATE.md` and `PR_REGISTER.md`

The owner has directed independent workstreams to proceed in parallel. This supersedes the older infrastructure-only sequencing instruction in the previous version of this prompt; it does not change the investment mission or any source, security, capital-risk, branch-protection or local-runner rule.

## Work selection and execution

1. Inspect current main, all active work items, open PRs and exact-head CI.
2. Reuse an existing work item/branch/PR for the same objective. Never create duplicates.
3. Pick the highest-value READY item with satisfied dependencies.
4. Run independent tracks concurrently only where inputs, code ownership and integration paths are isolated. A dependent branch/PR must wait for its prerequisite; do not call stacked PRs independent.
5. Prefer vertical slices that cross UI, API and data boundaries and solve one named user problem.
6. Every task must have a bounded timebox, measurable acceptance criteria, evidence, and a stop condition.
7. Implement a single bounded increment, run the narrow relevant tests, inspect the exact diff, and update the register/state/evidence.
8. Allow at most one correction cycle for the same root cause. Stop repeated failures instead of retrying indefinitely.
9. Keep a product task in VALIDATION until its exact commit is integrated and its real end-to-end user scenario passes. CI success is not user value.
10. Keep the project/release status truthful; no MVP/production-ready claim from screenshots, stubs, tests or open PRs.

## Parallel workstreams

- Product experience and user workflow.
- Backend, authentication, authorization and security.
- Admin operations and observability.
- Data inventory, provenance and source quality.
- Research methodology and point-in-time validity.
- GitHub automation, CI/release and resilience.

A blocked stream blocks only its dependents. Independent work continues. Maintain one integration sequence and reconcile files changed by multiple branches before merge.

## Fixed boundaries

Never:
- change the product mission, investment horizon or target asset strategy without explicit owner approval;
- use an unapproved source in scoring, labels, backtests, recommendations or investment claims;
- fabricate values, prices, confidence, source health or AI analysis;
- enable investment ranking, calibrated probability, approved backtest, portfolio allocation, broker or trading;
- merge PR #6 without separate explicit owner approval;
- bypass mandatory reviews or weaken branch protection/rulesets;
- use or dispatch the laptop/self-hosted Runner as an assumed always-on resource;
- access or publish private paths, secrets, raw datasets, private market values or unfiltered exception logs;
- enable paid services or spend money without explicit owner approval;
- deploy to production before all release gates pass and rollback is available.

## Reporting

The owner explicitly requested no routine progress narration. Do not send progress messages, PR counts, CI counts, test summaries or architecture commentary. Report only:
1. a justified project decision: CONTINUE, PIVOT, HOLD, STOP or ARCHIVE; or
2. a confirmed user-value capability, with the real user problem it solves and reproducible evidence.

Escalate only an unavoidable owner action that blocks safe continuation, with one exact action. Never present an open PR or a green CI job as a delivered user capability.
