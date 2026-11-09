# MarketSage — Strategy Charter
**Version:** 1.0  
**Effective date:** 2026-11-09  
**Authority:** Owner-directed execution under `PROJECT_EXECUTION_CONSTITUTION.md`

## 1. Mission

Build an evidence-led research and decision-support system for the owner's investment decisions, with an approximately six-month decision horizon. It must compare relevant Iranian and global asset classes and explain opportunities, downside scenarios, liquidity, macroeconomic context, corporate actions, news and geopolitical/social conditions using evidence available at the decision time.

The product is not an indicator dashboard and is not a promise of return. The strategy must not be silently narrowed to the easiest data provider, current prototype universe, or one market.

## 2. Product outcome

The user must be able to complete a real workflow that helps answer: **what is known, what is uncertain, what evidence supports each scenario, and what additional evidence is required before a decision can be made?**

The minimum useful workflow is:
1. Select a market or asset family.
2. See whether the asset universe and data coverage exist.
3. Inspect source identity, units, time coverage, freshness, quality and known gaps.
4. Read an evidence-linked research brief that separates observed facts, interpretation, uncertainty and unavailable analysis.
5. Understand why the product can or cannot answer the intended six-month question.
6. Revisit the same dossier and see what changed, with provenance.

The first release may expose a narrower *working path* to prove usability, but that is sequencing, not a permanent change to the strategy or target asset universe.

## 3. Non-negotiable boundaries

- Research-only. No broker, trading, capital movement or automatic allocation.
- No investment ranking, recommendation, success probability, calibrated confidence or approved backtest until its own data, methodology and out-of-sample gates pass and the owner explicitly approves activation.
- Unapproved, stale, mismatched or unlicensed data must be quarantined from analytical outputs.
- Unknown is not pass. Missing evidence must be displayed as unknown or unavailable.
- No fabricated/demo prices, metrics, confidence values, provider health or AI responses.
- No paid infrastructure, paid model/API, paid agent, or resource provisioning without explicit owner approval. Prefer free GitHub-hosted CI and bounded workloads.
- The owner's laptop Runner is not assumed online and must not be dispatched by routine automation. Local-only work remains manual and explicitly owner-gated.
- PR #6 remains unmerged unless the owner gives separate explicit approval.
- Do not weaken branch protection, rulesets, approval requirements or security settings to make automation pass.

## 4. Execution strategy: parallel, bounded workstreams

Run independent streams in parallel when code ownership, branch scope, inputs and acceptance criteria are isolated:
- Product workflow and user experience.
- Data inventory, provenance and source-quality contracts.
- Backend, authentication, security and API integration.
- Admin operations and observability.
- Engineering automation, CI reliability and release controls.
- Research methodology and evidence standards.

A dependency blocks only the dependent task, never unrelated streams. Do not stack dependent PRs as if they were independent. Maintain one integration order for dependent changes.

Every stream must deliver either:
- a user-observable capability that solves a named user problem; or
- a verified reduction of a release/security/data-integrity blocker that is directly required for such a capability.

Tests, documentation, PRs, architecture diagrams and passing builds alone are not product outcomes.

## 5. Product-first delivery

For every proposed feature, state the user, the task they need to perform, the friction or risk removed, the actual screen/API path, and a reproducible acceptance scenario. Build vertical slices across UI, API and data contracts; do not build disconnected layers indefinitely.

The first user-facing vertical slice must be useful without pretending that unavailable market analysis exists. A truthful market/data coverage and evidence workflow is acceptable as a first slice only when it is integrated and demonstrated end-to-end. It must visibly distinguish available, candidate, quarantined and unavailable data.

## 6. Task contract

Each work item in `WORK_REGISTER.json` must have a unique ID, objective, user problem or blocker, track, owner, status, bounded timebox, dependencies, deliverables, measurable acceptance criteria, stop conditions and evidence references.

No open-ended task. No duplicate issue/PR for the same outcome. Reuse existing work where it already meets the contract. An item is not complete merely because its branch CI passed.

## 7. Completion levels

- **Activity:** code, tests or documents were produced.
- **Engineering delivery:** code is reviewed, integrated into the canonical branch and passes exact-head validation.
- **User value:** the real user flow is executable end-to-end and demonstrably resolves the stated user problem.
- **Research approval:** source and methodology gates pass independently; this does not follow automatically from user value.

Only User value counts as product progress. Only explicit Research approval can unlock investment outputs. A workflow may be technically complete while product release remains not ready.

## 8. Decision vocabulary

At the initiative/project level record exactly one of:
- `CONTINUE`: mission remains worthwhile; execute the next evidenced milestone.
- `PIVOT`: change the execution approach or product scope; explain what changes and what remains fixed.
- `HOLD`: pause a bounded initiative pending an external dependency or owner action.
- `STOP`: stop the current approach because value, feasibility, safety or evidence failed.
- `ARCHIVE`: remove an initiative from active work while preserving its code and evidence.

The execution lead may stop or archive a task within delegated scope. A decision to abandon the whole MarketSage mission or materially change its investment objective remains with the owner.

## 9. Stop rules

- No measurable acceptance criteria: do not start.
- No user-problem connection and no release-blocker connection: reject.
- Two bounded attempts fail on the same root cause: stop that approach and record the failure; do not loop retries.
- A dependency is blocked: mark only dependent items blocked and continue independent work.
- No user-observable outcome after two execution cycles: stop expanding scope and re-cut to the smallest end-to-end slice.
- Security breach, data-rights uncertainty, source-integrity failure or fabricated output: fail closed.
- No evidence of user value: do not call the product an MVP or release-ready.

## 10. Reporting contract

The owner receives only two classes of report:
1. The initiative decision: Continue, Pivot, Hold, Stop or Archive.
2. A confirmed user-value result: the specific capability and the real user problem it solves.

Do not send routine activity updates, PR counts, test counts, architecture notes or progress narration. Escalate only an unavoidable owner action that blocks a safe continuation, using one concrete action.

## 11. Relationship to the existing constitution

This charter supplements and does not weaken the binding project constitution. The owner has directly instructed parallel execution, replacing the former infrastructure-only sequencing in the Copilot run prompt. This does not authorize changes to the product mission, data/source acceptance, capital-risk controls, local Runner boundary, PR #6 restriction, security controls or repository protection.
