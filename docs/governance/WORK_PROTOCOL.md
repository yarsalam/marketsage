# MarketSage — Mandatory Work Protocol

**Canonical authority:** this file plus `PROJECT_STATE.md`, `execution_policy.json`, `ARTIFACT_REGISTRY.jsonl`, and `RUN_LEDGER.jsonl`. GitHub Issue #49 is the acceptance gate. Chat history, handoff notes, attachments and memory are not authority when they conflict with these records.

## Mandatory start-of-session sequence

1. Read this file, `PROJECT_EXECUTION_CONSTITUTION.md`, and the current `PROJECT_STATE.md` from the active integration branch.
2. Read the latest owner instructions/comments on the relevant issue and PR. Check the live PR state, base/head SHA, branch, latest commit, and exact-head checks. Never inherit check results from an earlier SHA.
3. Read `execution_policy.json`. If the scope is locked, stop every action outside the allowed scope.
4. Inspect the artifact registry and run ledger before any search, download, calculation, test, or provider request. Search registered archive roots for unresolved artifacts before proposing a new acquisition.
5. Find the existing work item and latest run. Resume it; do not create a parallel plan, duplicate issue/PR, report, acquisition or test. If no work item exists, create one canonical ID and record its inputs, prerequisites, output, acceptance test, owner authority and status before execution.
6. Confirm that the exact code SHA, input hashes, parameters and environment have not already been tested. Reuse a valid result. A retry requires a material change and a recorded reason; never retry an identical failed run merely to seek a green result.

## Work-type procedures

### Data acquisition / source discovery
- Require an unlocked research scope, an explicitly authorized work item, source-specific terms/rights review, exact provider/request parameters, and an artifact identity/request fingerprint.
- Run the common preflight before network access. Search registry, local/archive roots and backups first. Existing/equivalent request means reuse; unresolved path means `PATH_UNRESOLVED` and `RECOVERY_REQUIRED`, not re-download.
- Save provider payloads as new immutable raw versions. Never overwrite raw files. Record SHA-256, byte size, provider, request parameters, instrument IDs as strings, dates, frequency, units, acquisition UTC, storage location, run ID, code SHA, restrictions and backup status.
- Never hide network access inside ordinary unit tests or routine CI.

### Corporate-action adjustment / total-return construction
- Start from registered immutable raw inputs and verified instrument identity. Preserve raw snapshots and hashes.
- Build a separate versioned event ledger. For each event, require primary terms, ex/effective dates, share/cash/rights terms, units and source lineage. Do not infer a factor from a chart discontinuity alone.
- Calculate a new derived artifact; never edit raw data or overwrite an accepted derived artifact. Record formula/version, inputs, event IDs, code SHA, parameters and output hash.
- Reconcile independently against an authoritative adjusted reference over shared dates and record unexplained residuals. Unknown or unresolved events block acceptance.
- No adjustment output becomes investment eligible merely because the script or reconciliation test passes.

### Audit / calculation / test
- Compute the run fingerprint from code SHA, sorted input artifact hashes, parameters and relevant environment/dependency versions.
- Consult the ledger first. If identical run exists (success or failure), do not repeat. A materially changed input/code/parameter/environment requires a new run ID and a written change reason.
- Store stdout/stderr summaries, exit status, exact commit, input hashes and result artifact hashes. Do not expose private paths or data in public logs.
- A test result is valid only for its exact tested SHA and environment.

### Backup / restore
- Never treat Git history, one local disk, chat attachments or Actions artifacts as durable independent backups.
- Require at least three copies across two independent media, including one offline/isolated copy. Checksum each copy.
- A backup is not verified until a restore drill recreates the selected files and confirms exact hashes. Record location class, media/failure domain, timestamp, hash manifest, restore set and result. No deletion/migration without a verified restore.

### Engineering / infrastructure
- Use the existing canonical issue/PR/branch; do not create duplicates.
- Synthetic fixtures only while research is locked. No provider calls, real dataset reads, local workflow dispatch, paid resources, secrets, deploys or merges unless separately authorized.
- Add deterministic tests for new controls. Do not claim tests passed unless the exact test command and exit code are recorded.
- Keep GitHub commits sanitized: no private/local absolute paths, credentials, raw data or operational personal details.

## Mandatory technical preflight

All acquisition/research entry points must be gated before network access, dataset reads, output inspection or computation. Python entry points call `infra.control_plane.safety_gate.preflight` directly. GitHub Actions entry points use `python -m infra.control_plane.preflight_cli --action research` from the checked-out workflow source before any research/data step. The CLI is a side-effect-free adapter; a locked scope exits non-zero. The three existing local TSETMC workflows (offline acceptance, integrated acceptance and sanitized diagnostics) now place this gate before their data/output step. New acquisition/research workflows must add the same gate and a contract test; they must not bypass it through an alternate wrapper.

The common preflight checks policy validity and scope, active work-item authorization (including `IN_PROGRESS`), registered input identity and hashes, request idempotency, run idempotency, and output-path separation. It accepts the actual 40-character Git commit SHA and computes a separate SHA-256 run fingerprint. Immutable registered inputs are re-hashed immediately before use; missing/corrupt policy, work item, registry or ledger fails closed. The preflight itself never performs acquisition.

A CI integration must validate policy, work-item metadata, registry schema/duplicate IDs/hashes/fingerprints, run-ledger integrity and synthetic tests before research can reopen. A check on a different SHA is not evidence.

The canonical validator is `python -m infra.control_plane.validate_governance`. It validates `schemas/governance-records-v1.schema.json`, the active execution policy and work item, every artifact/run JSONL record, and cross-record idempotency/authorization invariants. The infrastructure CI job must run this command, `python -m unittest discover -s tests/infra -p 'test_safety_gate.py' -v`, `python -m unittest discover -s tests/infra -p 'test_preflight_cli.py' -v`, and `python -m unittest discover -s tests/infra -p 'test_governance_validation.py' -v`. These commands being wired into CI is not proof they have passed; record exact-head evidence only after an authorized run.

## End-of-task sequence

1. Append the run record and terminal work status (`DONE`, `BLOCKED`, or `REJECTED`) with exact commit, inputs, parameters, environment, result and evidence IDs.
2. Update `PROJECT_STATE.md`, the artifact registry and run ledger; preserve prior records append-only.
3. State the single next permitted action and every owner gate. Never mark a control active until exact implementation and acceptance evidence exist.
4. If a path is missing, record `PATH_UNRESOLVED`; inspect registered archives/backups before any replacement.
5. Leave the research lock in place until Issue #49 is accepted and the owner explicitly reopens research.

## Current bounded work item

- ID: `MS-20261116-CONTINUITY-001`
- Scope: implement and test continuity, immutable-artifact, duplicate-acquisition/run and fail-closed preflight primitives on the existing infrastructure branch.
- Inputs: existing provider-neutral control-plane code; no real datasets or provider access.
- Acceptance: deterministic synthetic unit tests; JSONL registry/ledger validation; explicit scope-lock behavior; read-back of every changed file; exact-head CI only after separate owner authorization.
- Prohibited: research, data downloads, corporate-action calculations, workflow dispatch/rerun, merge, deploy, secrets, spend, visibility changes.
- Status: `IN_PROGRESS` until tests and exact-head validation are legitimately completed.
