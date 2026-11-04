# MarketSage local-data Runner — trust boundary and activation gate

**Status:** Design only; Runner is not registered and no local data has been read by this session.  
**Scope:** Local TSETMC corpus acceptance and Stage 4 research evaluation.  
**Activation:** Requires owner-side repository settings and host setup. Do not register a Runner before every precondition below is met.

## Why the existing CI workflow must not host local-data jobs

The current `.github/workflows/ci.yml` runs on every `pull_request` and checks out the PR head. It is appropriate for GitHub-hosted ephemeral runners. It is not a trusted execution boundary for a self-hosted machine that can see private local market data.

Never add a self-hosted job to that workflow, and never run arbitrary PR code on the local Runner. A malicious or compromised PR could read every file and credential accessible to the Runner account.

## Required trust boundary

1. **Protected source branch**
   - Protect the exact integration branch used for local research execution.
   - Require pull requests and the required CI checks before changes reach that branch.
   - Block force-pushes and routine bypasses.
   - Do not treat the current open #6 branch as trusted until the protection is active and its head is reviewed.
2. **Repository-scoped Runner**
   - Register a dedicated self-hosted Runner for this private repository only.
   - Restrict the Runner group to this repository and the dedicated research workflow.
   - Prefer an ephemeral Runner that accepts one job and is removed; otherwise use a persistent service with automatic workspace cleanup and a documented update/revocation procedure.
3. **Dedicated operating-system identity**
   - Run as a new unprivileged account with no sudo and no membership in groups that can read other users' private files.
   - Use a dedicated workspace and temporary directory.
   - Grant read-only access only to the explicitly selected research-data roots; grant write access only to a separate output directory.
   - Do not grant access to the general home directory, Downloads, browser profiles, SSH keys, password stores, cloud credentials, GitHub tokens, broker accounts, or unrelated project folders.
4. **Separate trusted workflow**
   - Use a new workflow that is triggered only by `workflow_dispatch` or an explicitly reviewed schedule on the protected integration branch.
   - Reject any event other than the allowed trigger and reject any ref other than the exact protected branch.
   - Do not use `pull_request`, `pull_request_target`, issue, comment, or fork events.
   - Check out the exact triggering SHA; do not fetch or execute a moving PR head.
   - Set the minimum token permissions (normally `contents: read`); pin third-party actions to reviewed immutable commit SHAs.
   - Serialize local jobs so they cannot race over the same corpus or VPN state.
5. **Data handling**
   - Keep raw input files and all intermediate price rows local.
   - Write outputs to a dedicated, non-Git directory with a unique run ID.
   - Return only a sanitized manifest, counts, date ranges, reason codes, file hashes and aggregate metrics. Do not upload raw files or raw rows as workflow artifacts.
   - Review every output field for accidental raw values, credentials or local paths before any report is sent to GitHub.
6. **Network and VPN isolation**
   - Do not let the workflow change VPN settings or inspect browser credentials.
   - Keep Iranian providers and foreign providers in separate jobs with an explicit network-state precondition.
   - A failed provider request must not trigger retries or alternate-route probing unless a new bounded acceptance question is approved.
7. **Research-only execution**
   - The TSETMC acceptance pipeline must not make network requests or modify source inputs.
   - Stage 4 must use only a pinned, permissioned dataset and a predeclared evaluation configuration.
   - No job may enable source approval, investment ranking, scoring, broker access, or trading.

## First allowed workload

After all controls are active, the first job should run only:

- the offline TSETMC integrated acceptance pipeline against the designated local corpus;
- the metadata-only Stage 4 data inventory;
- no network probes, no strategy parameter tuning, no production scoring, and no holdout inspection until the split and run manifest are frozen.

The job must preserve input hashes and produce a unique output directory. If the pipeline finds ambiguous histories, unverified raw/adjusted semantics, long gaps or missing evidence, it must quarantine the instrument rather than repair it.

## Owner-side blocker

The connected GitHub integration cannot configure or verify repository rulesets/branch protection in this private repository (the relevant API calls are denied by GitHub permissions). A separate plan constraint also applies: GitHub's current documentation says branch protection is available on Free only for public repositories (including Free organizations); private repositories require Pro, Team or Enterprise. Rulesets have the same public-Free/private-paid distinction. Therefore, moving this private repository to a GitHub Free Organization alone does **not** satisfy the required protected-branch gate. See [protected-branch plan availability](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) and [ruleset plan availability](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

The current CI workflow also executes arbitrary PR heads on GitHub-hosted runners, so it must remain separate from any local Runner. Do not attach a local Runner to the existing `pull_request` workflow or run unreviewed PR code on the host.

**Required owner decision before activation:** either obtain a plan that supports protected branches/rulesets for this private repository, or explicitly approve a revised trust model that does not claim equivalent branch protection and is reviewed for its residual risk. Only after that decision may the dedicated unprivileged host account, restricted data/output directories, repository-scoped Runner and separate trusted `workflow_dispatch` workflow be provisioned. Enter any Runner registration token directly on the host; never paste it into chat, a repository file, or a workflow log.

Until the protection/trust-model decision and host isolation are verified, local corpus audit and empirical Stage 4 execution remain **BLOCKED**. No claim of local data access or Runner readiness is made.
