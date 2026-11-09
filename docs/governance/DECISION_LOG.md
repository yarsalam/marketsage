# MarketSage — Decision Log

All decisions below are durable records. New decisions must be appended; do not rewrite history silently.

## 2026-11-02 — Adopt a governed execution model

**Decision authority:** Owner  
**Status:** Approved in conversation; repository adoption pending merge.

**Decision**
- MarketSage is an internal investment-decision system for the owner's own capital, not primarily an academic research project or public SaaS.
- The nine rules in `PROJECT_EXECUTION_CONSTITUTION.md` govern all project work.
- The owner delegates routine engineering implementation, PR merging, and software deployment to the execution lead when the change remains within the approved strategy and passes required checks.
- Any change to product strategy, investment horizon/universe principles, fundamental modeling direction, or material capital risk must be presented to the owner for explicit approval.
- Real-money trades, broker orders, and portfolio allocation changes are not authorized by this delegation.
- All significant work must be recorded in Git; repeated work must be prevented through state, manifest, hash, and decision records.

**Repository privacy**
- Owner instructed that `yarsalam/marketsage` be changed from Public to Private.
- Completed by the owner on 2026-11-02; repository metadata now reports `visibility: private`.
- A subsequent rulesets API read returned HTTP 403 with GitHub's message to upgrade to Pro or make the repository public. Private branch-protection/ruleset support is therefore a plan-level blocker in the current account. Do not register a self-hosted runner until branch and trusted-workflow controls are resolved.

**Runner principle**
- Owner has authorized provision of access needed for the runner and execution lead.
- Access must be least-privilege and scoped to the MarketSage repository and designated data directories; blanket laptop or personal-account access is not required.
- Runner must execute only trusted reviewed workflows, not untrusted fork or arbitrary PR code.

## 2026-11-04 — Approve a manual-only local Runner trust-model exception

**Decision authority:** Owner  
**Status:** Approved by explicit owner authorization; the dedicated manual-only workflow is merged to `main` in PR #27. This decision log is being adopted through a clean documentation-only PR based on the current `main`.  
**Related record:** [Issue #25](https://github.com/yarsalam/marketsage/issues/25), including the owner-authorization comment dated 2026-11-04.

**Question**

The repository is private and the current GitHub Free plan does not provide branch protection/rulesets for private repositories. Should local research Runner activation remain blocked pending a paid plan, or proceed using compensating controls and an explicitly accepted residual risk?

**Decision**

- Select Option 2 in Issue #25: proceed with a revised, manual-only local research Runner trust model.
- Do not purchase a GitHub plan upgrade solely for this gate, make the repository public, or move it to a Free Organization on the assumption that this would provide private-repository branch protection.
- This is a documented exception to the protected-branch enforcement requirement only. It is **not equivalent** to GitHub protected branches or rulesets and must never be represented as such.
- The owner authorizes the execution lead to complete the necessary documentation, workflow review, host hardening and repository-scoped Runner setup within the controls below.

**Mandatory compensating controls**

1. Keep ordinary CI on GitHub-hosted runners. No existing PR workflow may target the local Runner.
2. The local-data workflow must be a separate workflow with `workflow_dispatch` as its only trigger. It must not have `push`, `pull_request`, `pull_request_target`, `issue`, `issue_comment`, `schedule`, `workflow_run`, `repository_dispatch`, or fork-related triggers.
3. Dispatch only after an owner-side review of the exact workflow source and commit to be run. The run record must identify the exact triggering commit SHA. Reject unexpected refs and events. Manual dispatch is an operational approval step, not a substitute for branch protection.
4. Use a repository-scoped Runner with a unique research label; do not use an organization-wide or catch-all runner.
5. Use a dedicated unprivileged OS account with no sudo, Docker, LXD, or other privileged-group membership. Expose only the approved read-only dataset and separate output directory. Never expose the general home directory, browser data, SSH keys, credential stores, broker accounts, or unrelated project directories.
6. Use `permissions: contents: read` only unless a separately documented need is approved. Do not expose repository, organization, or environment secrets to the local job. Third-party actions must be pinned to reviewed immutable commit SHAs.
7. Keep raw local data and raw rows on the laptop. Publish only reviewed, sanitized manifests, counts, date ranges, reason codes, hashes and aggregate metrics; do not upload raw files or raw rows as artifacts.
8. Serialize local jobs, use a dedicated workspace, preserve input hashes and write outputs to a unique run directory. The initial workload is offline/read-only and must not change VPN settings or probe providers.
9. Do not enable source approval, backtest approval, investment ranking/scoring, production deployment, broker access or real-money trading through this authorization.

**Accepted residual risk**

Without private-repository branch protection/rulesets, GitHub does not technically enforce that the workflow and default-branch content remain owner-reviewed before manual dispatch. A person with sufficient repository write/Actions permissions, or a compromised owner account, could alter executable workflow content. Manual dispatch, exact-commit review, read-only permissions, absence of secrets, repository scoping and OS isolation reduce the exposure but do not eliminate it. Code executing as the Runner can read the staged research dataset and may attempt network exfiltration; that is why only reviewed code may run. This residual risk is accepted for the limited local research workload, not for secrets or personal data.

**Evidence at decision time**

- The host audit reports `marketsage-runner` as UID 110/GID 119, `nologin`, member only of its own group and not in `sudo`, `docker`, `lxd` or `adm`.
- An earlier host note recorded the Runner files as installed under `/opt/actions-runner/marketsage`; the latest owner terminal output corrects that interpretation. See the 2026-11-04 package-location correction below. No active Runner process or systemd Runner service was found in the latest terminal output.
- The staged dataset at `/srv/marketsage/data/tsetmc_history_20261022` contains 8,801 source files plus `SHA256SUMS` and `STAGING_README.txt`. All 8,801 source-file SHA-256 values were verified. Adjusted research-only candidates were excluded.
- The Runner account successfully read representative raw, normalized, report, manifest, reconciliation and acceptance files; representative hashes and JSON/CSV parsing passed.
- Attempts to write to the dataset root and normalized source data were denied. A create/delete test in `/srv/marketsage/output` passed.
- These are owner-supplied terminal results. They do not prove GitHub workflow security or eliminate OS/kernel/network vulnerabilities.

**Scope and impact**

This resolves the owner-decision blocker in Issue #25. PR #27's separate manual-only workflow is merged to `main` and its five required CI jobs passed. This does not authorize arbitrary workflow execution. Final host installation/isolation checks and a fresh local-only registration token are still required before registration/activation. The previously exposed registration token remains invalid for use and must never be reused.

**Supersedes**

The 2026-11-02 instruction to block registration pending protected-branch enforcement is superseded only by this narrowly scoped manual-only exception. All other least-privilege and untrusted-PR prohibitions remain in force.

## 2026-11-04 — Correct Runner package-location evidence

**Authority:** latest owner-provided terminal output in the current conversation.  
**Related record:** [Issue #25 — owner action required](https://github.com/yarsalam/marketsage/issues/25).

The latest terminal output supersedes the earlier installation-location note:

- The full 228,071,396-byte v2.338.2 archive is in `/home/nima/actions-runner`.
- Extracted `config.sh`, `run.sh`, `bin` and `externals` also exist there, but the extracted files show 2026-10-26 timestamps; their version/correspondence to the 2026-11-04 archive has not been verified.
- `/opt/actions-runner/marketsage` contains only a 9,719,808-byte partial archive and no extracted `config.sh`/`run.sh`. The designated installation is incomplete.
- The personal directory contains `.env`, `.path` and `_diag`; these must not be copied into the dedicated Runner directory. The full archive's SHA-256 must be checked before a fresh extraction.
- No active Runner process or installed service was found in the latest terminal output. Runner is not registered or online. The token previously exposed in chat remains compromised and must never be reused.

The GitHub-side workflow gate is now implemented separately: PR #27 merged to `main` at `7e669749d2615bc0f2a9d6f557bb99f8e7bd0767`; all five required CI jobs passed on its exact PR head. This workflow only validates the staged file inventory and hashes. It does not register/start the Runner or run the full PR #14 integrated pipeline. The owner must review the exact current `main` SHA before manual dispatch.

**Decision effect:** the Option 2 manual-only model and accepted residual risk remain unchanged. The Runner must stay offline until the full archive is verified and freshly extracted in the designated path, service/workspace isolation is applied, a final local audit passes, and a fresh repository registration token is entered locally. Issue #25 now records the exact owner action, effect and acceptance criteria.

## Decision template

### YYYY-MM-DD — Title

**Decision authority:** Owner / Delegated execution  
**Status:** Proposed / Approved / Rejected / Superseded

**Question:**  
**Decision:**  
**Reason/evidence:**  
**Scope affected:**  
**Capital-risk impact:**  
**Implementation PR/commit:**  
**Supersedes:** (if any)


## 2026-11-05 — Local Runner activated and staged TSETMC corpus validated

**Decision authority:** Owner-approved manual-only compensating-control model (Issue #25, 2026-11-04); routine host hardening and bounded research execution delegated under the project constitution.  
**Status:** Implemented for the Runner activation and first offline validator only.

**Evidence**
- Registered the repository-level Runner marketsage-local-01 for yarsalam/marketsage, with the custom labels marketsage-local and marketsage-research.
- Installed and enabled actions.runner.yarsalam-marketsage.marketsage-local-01.service under the unprivileged marketsage-runner account.
- Retained ProtectHome=true, ProtectSystem=strict, PrivateTmp=true, NoNewPrivileges=true, kernel/module/control-group protections, read-only staged data and restricted write paths.
- Removed only RestrictSUIDSGID after an observed GNU tar 1.35 Function not implemented checkout failure. A nested tar extraction test passed inside a hardened systemd sandbox before restarting the Runner.
- The first manual local validator run [41906518123](https://github.com/yarsalam/marketsage/actions/runs/41906518123), attempt 2, completed successfully. It verified all 8,801 staged source SHA-256 entries and 1,268,527,673 source bytes; inventoried 2,493 instrument-universe rows; made zero provider/network requests; and did not modify the dataset.
- The validator retained eligible_for_scoring=false and approved_for_backtest=false.

**Decision effect**
- Issue #25's Runner installation/registration and first-validator acceptance criteria are complete.
- A separate, reviewed manual workflow is being prepared for the PR #14 integrated offline TSETMC candidate pipeline. Its pipeline code is pinned to integration commit 819f8b4028469cb0d498098fec88545a18ebacc6; PR #6 itself remains open and must not be merged into main without separate owner approval.
- The integrated pipeline run, source rights, raw/adjusted semantics, corporate-action completeness, independent reconciliation, point-in-time validity, Stage 4 attribution and investment strategy acceptance remain pending.
- No source approval, backtest approval, investment ranking/scoring, production deployment, broker access, portfolio allocation or real-money trading is authorized by this decision.

**Capital-risk impact:** None. This is an engineering/data-integrity milestone, not an investment decision.


## 2026-11-05 — Integrated local TSETMC candidate workflow merged

**Decision authority:** Routine engineering execution delegated under the adopted project constitution; owner retains source-acceptance and capital-risk authority.  
**Status:** Workflow merged; local data execution awaiting owner dispatch.

**Evidence**
- PR #32 merged to main at `11f9de85c13f3ee8bd61e6eb7aea64992a7271d4`.
- Exact PR head `2df9e5fc523307a08894c8077210e8584aa4adcb` passed all five required CI jobs in run [41911051358](https://github.com/yarsalam/marketsage/actions/runs/41911051358); the analysis test suite reported 107 passed and 7 warnings.
- Workflow `.github/workflows/local-tsetmc-integrated-acceptance.yml` is `workflow_dispatch` only, owner/main/input gated, contents-read only, uses full-SHA-pinned checkout actions, and checks out PR #6's integration implementation at immutable commit `819f8b4028469cb0d498098fec88545a18ebacc6`.
- The wrapper checks local data boundaries, symlinks, path containment, file count/size, available RAM and free disk, hashes all produced local report files, and emits only aggregate reason/semantics/identity counts.
- Candidate-level CSVs, source hashes and absolute paths remain on the laptop under the Runner-only output directory. No artifacts are uploaded and no provider/network requests are made.

**Next owner action**
- Review the current workflow and pinned implementation on main.
- Manually dispatch from GitHub Actions on branch `main`, setting `confirm_integrated_acceptance=true`.
- Review the sanitized results; detailed candidate CSVs remain local.

**Decision effect**
- PR #6 remains open and must not be merged into main without separate explicit owner approval.
- The integrated run does not approve source rights, adjusted-price semantics, corporate-action correctness, independent reconciliation, point-in-time validity, strategy/backtest or scoring.
- No investment ranking/scoring, production release, broker access, portfolio allocation or real-money trading is authorized.

**Capital-risk impact:** None. This is an offline candidate-audit workflow only.


## 2026-11-05 — Integrated TSETMC first dispatch blocked by static RAM gate; bounded-batch correction

**Authority:** Routine engineering correction within the existing owner-approved local research scope.  
**Status:** Correction implemented and merged to `main` in PR #34 at `554fe2200ccb3a523442b0e241e81a748becfa44`.

**Observed run**
- Local workflow run [41912248800](https://github.com/yarsalam/marketsage/actions/runs/41912248800) reached Runner `marketsage-local-01`.
- Both `actions/checkout` steps succeeded, including the exact pipeline source commit `819f8b4028469cb0d498098fec88545a18ebacc6`.
- The analysis wrapper stopped at preflight with `insufficient_available_memory`, because the initial hard-coded minimum was 16 GiB. The integrated pipeline itself did not start; no candidate batch ran.
- No source data was written or changed, no provider request was made, and no scoring/backtest flag was enabled.

**Correction in PR #34**
- Replace the 16 GiB static gate with a 4 GiB effective-available-memory floor measured against both host `MemAvailable` and applicable cgroup limits.
- Process at most 32 candidates and 32 MiB of unique selected input files per batch; refuse a single candidate whose selected inputs exceed that batch budget.
- Recheck memory and disk before each batch, garbage-collect batch-local objects, keep each batch's detailed outputs under the private output root, and write mode-0600 aggregate progress after each completed batch.
- Preserve the 3 GiB overall input cap, 8 GiB free-disk floor, read-only input, no-network, output hash verification, no-artifact-upload, no-scoring and no-backtest controls.
- Emit resource measurements and sanitized batch counts only; do not emit symbols, instrument codes, row data or local paths.

**Decision effect**
- The previous failed run is not treated as a data-quality result and must not be used to accept or reject TSETMC.
- PR #34 passed all five required exact-head CI jobs in run `41913385729` (analysis: 109 passed, 7 warnings) and was merged. The remaining action is owner review and a manual re-dispatch on `main`.
- PR #6 remains open; no source acceptance, scoring, backtest approval, production, broker or trading authorization changes.

**Capital-risk impact:** None. This remains an offline data-audit workload.


## 2026-11-09 — Owner-directed parallel execution and product-value gate

**Authority:** Explicit owner instruction in the conversation on 2026-11-09.  
**Decision:** CONTINUE the MarketSage mission using parallel, bounded workstreams; do not keep the former infrastructure-only sequence as a blanket block on product execution.

**Reason**
- The owner explicitly directed that the strategy be documented in GitHub and that parallel execution begin, with strict adherence to the project constitution.
- The previous Copilot prompt imposed an infrastructure-only sequence that prevented independent product work. This narrow execution-policy conflict is superseded by the owner's current instruction.
- The original six-month, Iranian-and-global investment research mission remains unchanged. No asset-universe narrowing, source approval or capital-risk authorization is implied.

**Execution effect**
- Product, data-quality, backend/security, admin/operations, research-methodology and engineering-infrastructure streams may proceed in parallel only when dependencies and file ownership are isolated.
- PR #73 and #77 remain open drafts and must be reconciled because they both modify the user landing-page/Sidebar paths.
- PR #74 is a separate infrastructure stream. PR #71 and #61 remain dependent on #74.
- A product task cannot be accepted from a branch CI result. It requires integration and a reproducible real user/API flow.
- The owner receives no routine progress narration; report only an evidenced project decision or a user-value capability that resolves a real user problem.

**Non-changes**
- PR #6 must not be merged without separate explicit owner approval.
- No self-hosted/laptop Runner dispatch, paid resources, production deployment, source approval, investment scoring/ranking, probability calibration, backtest approval, broker, trading or capital allocation is authorized.

**Evidence:** `STRATEGY_CHARTER.md`, `PRODUCT_ROADMAP.md`, `WORK_REGISTER.json`, `DECISION_POLICY.json`, `RELEASE_GATES.json`, `EVIDENCE_LEDGER.json` and `PROJECT_STATE.json` on branch `strategy/project-operating-system-parallel-2026-11`.
