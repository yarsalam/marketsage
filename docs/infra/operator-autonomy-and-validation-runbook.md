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


## 6. Mirror-probe review — 2026-11-06

The candidate mirror probe was reviewed and hardened before asking for a network run:
- HTTPS-to-HTTP redirects are rejected; default certificate verification is retained.
- Requests are GET-only, carry no credentials, read at most 2,048 bytes, and have a 12-second per-request timeout.
- Transport exception text and response bodies are not emitted.
- Nine offline regression tests cover the request contract, redirect policy, status handling, redaction and exit behavior. They passed in an isolated temporary harness, but have not yet run from the owner's clean detached checkout.

**Owner-only network gate:** [Issue #52](https://github.com/yarsalam/marketsage/issues/52) tracks running the probe on the actual worker network. No mirror can be selected from desk research or this assistant's network. After a successful mirror probe, verify compatible wheels and install the unchanged dependency set in a clean isolated environment; only then run the manifest/lifecycle tests. Do not start durable storage implementation before those existing tests pass from the clean checkout.

GitHub Actions remains at a zero-dollar usage/budget stop. Do not dispatch or rerun hosted workflows until included quota is verified to have reset or the owner separately authorizes spend. No paid provider, Oracle workaround, production VPS worker or private-code export is authorized.


## 7. Isolated lifecycle-fixture execution — 2026-11-06

The existing standard-library-only `infra/control_plane/lifecycle.py` and `test_lifecycle.py` were copied unchanged into a temporary isolated harness and executed with `python -m unittest`: **9 tests passed**. This provides an initial result for the in-memory fixture only. It is not a clean checkout, not a repository CI run, and not proof of persistence, process restart, distributed locking or provider failover.

The `test_manifest` module still depends on `jsonschema` and remains unexecuted from a clean checkout because dependency bootstrap failed before test discovery. The exact-network mirror probe remains the next owner gate in Issue #52. Do not proceed to durable storage implementation until the prescribed clean-checkout manifest/lifecycle test batch passes.

The PR #50 failure-notification job shares the same GitHub Actions runner pool as the jobs it observes. Run [42176190919](https://github.com/yarsalam/marketsage/actions/runs/42176190919) shows that the notifier also failed before steps during runner allocation. Therefore an external observer on a genuinely independent execution path is required; an Actions job cannot prove or report the health of the Actions runner pool when that pool cannot start jobs.


### Probe request bound — 2026-11-06

The probe rejects non-HTTPS initial URLs and user-info URLs, rejects HTTPS-to-HTTP redirects, and permits at most one HTTPS redirect per package page. It makes 12 initial package-page GETs and at most 24 total GETs including redirects, with a 12-second timeout per request. The nine offline probe tests passed in an isolated temporary harness only; the owner-network probe remains pending Issue #52.


## 8. GitHub Actions quota handoff

[Issue #53](https://github.com/yarsalam/marketsage/issues/53) tracks the account-only check required before another hosted run. The latest exact-head attempt and its single bounded retry failed before any job step started (runner ID 0, zero steps). This is not a code-level test result and does not prove billing as the cause. The owner must inspect included-minute balance/reset and account/repository Actions restrictions while leaving the USD 0 spending cap unchanged. Until that evidence is returned, do not dispatch or rerun hosted Actions. Continue zero-cost repository-side work only.
