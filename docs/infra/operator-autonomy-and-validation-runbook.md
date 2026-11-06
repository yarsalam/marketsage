# Operator autonomy and zero-cost validation runbook

**Status:** active operating rule for the infrastructure-first phase.
**Scope:** provider-neutral control plane, local validation, runner readiness and recovery.
**Cost ceiling:** zero. No hosted CI dispatch, paid service, plan upgrade, billing activation, VPS purchase, merge or deployment is authorized by this document.

## 1. Execution ownership

The project workflow must not depend on the owner repeatedly asking the assistant to continue, requesting another script, or manually batching routine tests.

For every work cycle, the assistant/operator must:

1. Read the current branch head, working tree state (when available), relevant issues, existing strategy and prior execution evidence before proposing work.
2. Convert the strategy already recorded in GitHub into an ordered, persistent task backlog with acceptance criteria. Do not ask the owner to restate it.
3. Perform repository-only work directly through the available GitHub/repository tools when safe and possible. Batch independent reads and writes, keep changes on the designated infrastructure branch, and verify every write by reading it back.
4. Prepare tests and execution commands as one reproducible batch. Avoid repeated one-command-at-a-time requests and avoid asking the owner to run work that can be performed in an already authorized execution environment.
5. Request owner action only for a genuine boundary that cannot be crossed by available tools: local hardware/network access, interactive login/consent, a required local secret, or explicit authorization. State exactly why it is needed and ask for the smallest useful action.
6. If owner action is required, preserve the exact current state and provide a single diagnostic bundle that captures environment, command output, exit status and logs. Do not assume the terminal is persistent or that a foreground command will survive terminal closure.
7. Record each attempt, evidence, blocker, and next action in this runbook or the infrastructure tracking issue. A failed attempt must not be described as a successful test or runner.

## 2. No repeated manual-script loop

- Do not ask the owner to switch branches in a dirty working tree. Use a detached worktree or another isolated checkout.
- Do not overwrite, reset, clean, stash, or otherwise mutate uncommitted owner changes without explicit approval.
- Prefer an already authorized persistent/background execution environment over interactive terminal sessions. If a background process is used, provide a log path and verify process completion and exit code; process launch alone is not test evidence.
- Before installing dependencies, record Python and pip versions, platform/architecture, configured package index (without credentials), and whether compatible wheels are cached.
- Dependency/network failures must be classified as environment/bootstrap failures, not code/test failures. Preserve complete pip diagnostics. Do not blindly retry the same resolver command.
- Prefer deterministic, pinned and hash-verified dependencies or a prebuilt offline wheelhouse when available. Do not weaken dependency constraints or replace schema validation with an incomplete home-grown validator merely to make a test pass.
- A successful local test run must identify exact commit SHA, interpreter version, dependency set, test command, exit code and test count.

## 3. Runner readiness definition

A runner is **not ready** merely because a process starts, a runner package is installed, a workflow file exists, or a background PID is printed.

Minimum evidence before calling a runner usable:
- a worker registers with the intended coordinator/provider and reports healthy;
- a harmless, allowlisted, zero-network, zero-secret canary task is accepted and reaches a terminal state;
- task identity and idempotency survive duplicate delivery;
- lost/ambiguous dispatch response is reconciled without a second execution;
- lease expiry and fencing reject stale workers/results;
- worker shutdown/restart is recovered safely;
- an actual test failure remains a test failure and is not hidden by failover;
- budget remains zero and no hosted Actions run or external paid resource was triggered.

24/7 readiness additionally requires durable queue/outbox, monitoring, recovery and an end-to-end drill across independent execution capacity. Until proven, report runner status as not ready.

## 4. Current validation incident — 2026-11-06

### What succeeded
- The owner-local repository had seven modified tracked files. A branch checkout was correctly refused by Git to protect those changes.
- A detached worktree was then created successfully at commit `141c288` from `origin/infra/provider-neutral-control-plane-2026-11`.
- The worktree was clean in the captured output.
- A background process was launched, but its PID was only evidence of process creation, not successful execution.

### What failed
- The process stopped during `pip install -r requirements-infra.txt`, before unittest discovery or execution.
- Pip reported a PyPI read timeout while fetching package metadata and then `ResolutionImpossible` involving `jsonschema<5,>=4.23` and its transitive `rpds-py` requirement.
- Neither `test_manifest` nor `test_lifecycle` ran. There is no test pass/fail result.
- This is currently classified as **dependency bootstrap / package-index connectivity or resolver environment**, not a repository test failure.
- The failed attempt did not establish a working local runner, durable background service, or 24/7 execution capability.

### Next diagnostic action
1. Inspect Python version, pip version, OS/architecture, pip configuration/index (redacting credentials), and available cached wheels in the isolated environment.
2. Determine whether the configured package index can provide compatible `rpds-py` and `jsonschema-specifications` wheels for that interpreter/platform.
3. Prefer a deterministic offline wheelhouse if compatible cached artifacts exist; otherwise diagnose network/index access before another install attempt.
4. Once dependencies are available, run the two test modules from the exact detached-worktree commit and record complete output and exit status.
5. Do not proceed to durable storage implementation until the in-memory lifecycle tests have actually run and failures, if any, are resolved.

## 5. Owner approval boundaries remain unchanged

No private code transfer to an external provider, provider registration, billing activation, paid usage, plan upgrade, new VPS, production access, merge, deployment, ranking/scoring activation, or investment action is permitted without the relevant explicit approval. The production Yarsalam server and the owner's laptop are not assumed to be always-on MarketSage workers.
