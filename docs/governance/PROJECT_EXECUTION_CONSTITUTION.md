# MarketSage — Project Execution Constitution

**Version:** 1.0  
**Status:** Proposed for adoption; binding after this PR is merged  
**Owner:** Project owner  
**Execution lead:** ChatGPT within the connected GitHub and approved local-runner capabilities  
**Purpose:** Prevent strategic drift, repeated work, lost context, and untraceable changes.

This document governs how MarketSage is built and operated. It is not a research paper, product brochure, or technical backlog. No implementation task may override these rules.

## Product objective

MarketSage is an internal investment-decision system for the owner's own capital. Its purpose is to compare investment opportunities across relevant Iranian and global asset classes and improve capital-allocation decisions, with a core decision horizon of approximately six months.

It is not being built primarily as an academic research project, a public SaaS product, a charting application, or an indicator-only signal generator. External commercialization may be considered later only by an explicit strategy decision.

The product must help answer, using evidence available at the decision time:
- Which assets or markets offer the more attractive risk-adjusted opportunity?
- What return and loss scenarios are plausible over the decision horizon?
- Which observable conditions support or invalidate each scenario?
- How do liquidity, inflation, rates, macroeconomic conditions, corporate actions, news and geopolitical/social events change the comparison?
- What is the opportunity cost versus cash, lower-risk instruments, and alternative assets?

The system must not present a forecast as a promise or turn unverified data into investment certainty.

## The nine binding execution rules

### Rule 1 — One source of truth and complete traceability

The GitHub repository `yarsalam/marketsage` is the canonical source for code, strategy, project state, decisions, operating instructions, and sanitized evidence indexes.

- No material script, configuration, report, or decision may exist only in Downloads, a temporary folder, or a chat.
- Every code or workflow change must be represented by a branch, commit, and pull request.
- Raw datasets, credentials, API tokens, private account data, and large local captures must remain outside Git unless explicitly reviewed and approved for storage.
- Every local dataset used by a task must have a manifest with source, retrieval time, time range, semantics/units where known, file hash, and storage location.
- A result must point to the exact commit, data manifest, and run identifier that produced it.

### Rule 2 — Strategy is fixed; asset selection is evidence-led

The product objective above is the baseline strategy. It must not be silently narrowed to a fixed list of five assets, one provider, one market, or one modeling technique.

- Candidate sources and asset families are screened broadly before deep investment in any one of them.
- The shortlist is selected using the same comparison criteria: strategic relevance, history depth, data quality, adjustment/total-return correctness, independent reconciliation, point-in-time availability, access reliability, cost/effort, and terms of use.
- Ease of downloading data alone is not a reason to choose an asset.
- A candidate may be deferred or rejected only with a recorded reason and, where useful, a replacement candidate.
- The candidate universe may be expanded or reduced only through a recorded strategy decision.

### Rule 3 — Every task must produce a strategic outcome

A task is admissible only when it answers a named investment or data question that affects a strategy decision.

Examples of strategic outcomes:
- a dataset accepted, rejected, or explicitly blocked against pre-defined quality criteria;
- a verified adjustment or total-return series with reconciled corporate actions;
- a quantified data-coverage or integrity assessment;
- a time-aligned macro/event feature with documented publication-time semantics;
- a measured risk, cost, liquidity, or drawdown result;
- an out-of-sample comparison showing whether a strategy improves on an agreed benchmark.

UI pages, API endpoints, passing unit tests, dashboards, CI success, and helper scripts are engineering outputs. They are not strategic progress by themselves.

### Rule 4 — Evidence and acceptance criteria come before implementation

Before implementation begins, the task record must state:
1. the question being answered;
2. the input data and its provenance;
3. the acceptance criteria and the reason for each;
4. the bounded execution plan;
5. the expected artifact or decision;
6. the stop condition and fallback if the input cannot pass.

Connectivity, a valid response schema, a mock test, or a successful parser is not proof of historical completeness, correct units, correct corporate-action treatment, point-in-time integrity, independent accuracy, or predictive value.

Data acceptance must consider, as applicable:
- instrument identity and venue/market convention;
- currency and price/volume units;
- timestamps, timezone, trading calendar, publication time and revisions;
- gaps, duplicates, stale values, outliers and OHLC consistency;
- dividends, splits, rights issues, capital increases, delistings and other corporate actions;
- adjusted price versus total return semantics;
- cross-source or official-reference reconciliation;
- reproducible provenance and content hashes.

Unknown is not pass. A failed or unverified data gate must remain visible and must not silently feed investment scoring.

### Rule 5 — One ordered integration path; independent work may proceed in parallel

- Keep one canonical integration path for changes that depend on one another. Merge dependent PRs in dependency order; do not merge stacked PRs in parallel.
- Independent research, local-data inventory, source evaluation, documentation, and separately scoped engineering work may proceed in parallel when their inputs and outputs are isolated and they do not compete to modify the same integration branch.
- Each work item must have one owner, one objective, explicit dependencies, a bounded output, and a clear acceptance/stop condition.
- Do not create duplicate PRs for the same objective or leave ambiguous competing implementations.
- A PR must state its strategic objective, scope, files/artifacts produced, evidence, tests actually run, limitations, and follow-up decision.
- A blocked PR does not freeze unrelated work. Record the blocker and continue with independent work that does not rely on it.
- No change is considered complete until the Git record and project-state register are updated.

### Rule 6 — Tests are decision tools, not a work stream

Tests are run only to answer the acceptance question for the current commit and input.

- Reuse a valid prior result when the tested commit, data hash, configuration, environment, and relevant dependencies have not changed.
- Do not rerun a test merely to obtain a new green result.
- Each task has one planned validation run and at most one bounded correction cycle for the same root cause.
- If the second attempt fails, stop. Record the failure as `BLOCKED` or `REJECTED`, identify the external dependency or missing evidence, and evaluate a different path.
- A new test suite is allowed only when it validates a new requirement or closes a demonstrated coverage gap.
- CI success validates software behavior under its test conditions; it does not certify market data or strategy profitability.

### Rule 7 — Local execution is automated, isolated, and least-privilege

The owner's laptop is the execution environment for tasks that require local datasets, a specific VPN/network, or local compute. The owner must not be required to download and run a succession of scripts manually.

- A dedicated self-hosted runner is scoped to this private repository only.
- Runner jobs execute only trusted, reviewed code from the protected integration branch or an explicitly approved execution branch.
- No self-hosted runner job may be triggered by an untrusted fork PR or arbitrary PR code.
- The runner uses a dedicated unprivileged OS account and a dedicated work directory.
- It receives only the minimum read/write access to the designated project-data directories. No unrestricted home-directory, browser-profile, SSH-key, password-store, trading-account, or sudo access.
- Secrets are stored in GitHub/local secret storage and are never pasted into chat or committed.
- Raw data stays local. Sanitized manifests, run summaries, hashes, and decision records are linked back to Git.
- Runner installation, data-directory access, VPN use, and any network restrictions must be documented before the first data job.

### Rule 8 — Decision authority is explicit

The owner has delegated routine engineering execution, PR merging, and software deployment to the execution lead, subject to the rules in this document.

The execution lead may:
- inspect the repository and evidence;
- create branches, commits and PRs;
- implement approved-scope changes;
- run bounded CI and trusted local jobs;
- merge a PR when required checks pass and the change stays within the approved strategy;
- deploy software when deployment is a routine technical step, rollback is available, and no capital-risk boundary is crossed.

The execution lead must ask the owner before:
- changing the product objective, asset-universe strategy, investment horizon, or fundamental modeling approach;
- accepting a material increase in portfolio/capital risk;
- initiating, authorizing, or changing real-money transactions, broker orders, or automated trading;
- using an approach that materially changes the owner's risk exposure;
- accepting an exception to a binding rule in this constitution.

No real-money trade or portfolio allocation change is authorized by a software merge or deployment approval.

### Rule 9 — Continuity is stored in Git, not in chat memory

The repository must maintain:
- `docs/governance/PROJECT_EXECUTION_CONSTITUTION.md` — these nine rules;
- `docs/governance/PROJECT_STATE.md` — current branch, commit, active PR, completed strategic outcomes, blockers, and the single next action;
- `docs/governance/DECISION_LOG.md` — dated decisions, authority, rationale, and consequences;
- `docs/governance/PR_REGISTER.md` — one auditable inventory of open, merged, and closed PRs relevant to the current plan;
- task-specific evidence manifests and run summaries.

At the start of every new chat or work session, the execution lead must re-read these files and inspect the current GitHub state before continuing. Chat summaries are convenience only and never the source of truth.

Every completed task must update the state and decision records in the same PR or in a directly linked follow-up PR. No task may be repeated solely because a chat ended.

## Change control

This constitution cannot be changed implicitly by implementation, test output, a new chat, or an assistant-generated plan.

A proposed change must:
1. identify the exact rule and text to change;
2. explain why the existing rule is insufficient;
3. state the strategic and capital-risk consequences;
4. present the proposed replacement;
5. receive the owner's explicit approval;
6. be recorded in the decision log and merged through a PR.

Until that process completes, the current version remains in force.

## What can and cannot be guaranteed

This constitution and its technical controls can make unauthorized scope drift detectable, make unreviewed code changes difficult to merge, preserve durable context, and prevent routine work from silently crossing into capital-risk decisions.

They cannot guarantee that a market strategy will be profitable, that every external data provider will remain available, or that software has zero defects. A human administrator could also deliberately override repository controls. Therefore the practical adherence target is: no unrecorded strategy change, no untraceable task, no repeated test without a change trigger, no unreviewed code on the trusted runner, and no capital-risk action without the owner's explicit approval.
