# Iranian Equity Adjustment Orchestrator

Status: Foolad pilot, research-only. The orchestrator coordinates the existing CODAL and TSETMC collectors; it contains no collection logic or adjustment formula.

## Pipeline

```text
Daily scheduler
  -> CODAL collector + TSETMC collector
  -> immutable per-run capture
  -> SHA-256 file fingerprints
  -> daily dEven record comparison
  -> CODAL snapshot / instrument identity review
  -> event-ledger change detection
  -> isolated reconciler
  -> existing adjustment engine
  -> versioned output + run manifest
```

The collectors remain the only downloaders. The adjustment engine remains the only place where price/share adjustment logic lives. The orchestrator decides when work is needed, what changed, whether review is current, and whether a stage can safely continue.

## Foolad pilot

- Symbol: فولاد
- Primary InsCode: `46348559193224090`
- CODAL symbol list: `data/market-research/iran-equities/adjustment-evidence/_shared/orchestrator/codal_symbols.txt`
- Canonical event ledger: `foolad/event-ledger.csv`
- Canonical identity: `foolad/identity.json`

Each invocation writes a unique run under `_shared/orchestrator/runs/<run-id>/`. CODAL may resume under the same run ID according to its own manifest semantics. TSETMC full-history capture is immutable and is never overwritten; an incomplete TSETMC output requires a new run ID.

## Revision rules

The semantic fingerprint covers captured payload files, excluding generated manifests, transport metadata and temporary files. The daily JSON comparator uses `closingPriceDaily[].dEven` and detects:
- new trading dates;
- dates removed from the latest source snapshot;
- corrected fields for an existing date.

A changed CODAL capture, TSETMC capture, canonical event ledger or instrument identity marks recalculation as required. A pending recalculation remains pending across later runs until the adjustment stage succeeds. CODAL snapshot and instrument identity changes require an append-only owner acknowledgement against exact SHA-256 fingerprints.

## Review acknowledgement

No approval file is pre-created. After reviewing the exact snapshot and identity, append a JSON object to:

`data/market-research/iran-equities/adjustment-evidence/_shared/orchestrator/review_approvals.jsonl`

Example (use exact values from the run manifest):

```json
{"reviewer":"owner","reviewed_at":"2026-11-26T19:00:00+03:30","codal_snapshot_sha256":"<source_fingerprints.codal.sha256>","identity_sha256":{"foolad":"<identity_fingerprints.foolad>"}}
```

The newest JSONL record is used. Any new CODAL or identity hash invalidates the previous acknowledgement.

## Adjustment safety gate

The sample config deliberately leaves `reconcile.argv` and `adjustment.argv` empty. Until the local untracked downloader/engine code is committed and their exact artifact contracts are verified, a changed input ends in `BLOCKED_RECONCILIATION_NOT_CONFIGURED`. It never overwrites canonical raw data and never invokes an adjustment against stale inputs.

The reconciler must copy and validate the immutable run snapshots into a new isolated workspace, check the exact primary InsCode, and prepare the existing engine's inputs. It must not edit/accept event-ledger rows or implement adjustment formulas. The adjustment engine must write to a new versioned output directory.

## Commands

From the repository root:

```bash
python3 scripts/research/adjustment_orchestrator.py run --config configs/adjustment_orchestrator.foolad.json --run-id dry-run --dry-run
python3 scripts/research/adjustment_orchestrator.py run --config configs/adjustment_orchestrator.foolad.json
python3 scripts/research/adjustment_orchestrator.py run --config configs/adjustment_orchestrator.foolad.json --run-id 20261126 --resume
python3 scripts/research/adjustment_orchestrator.py status --run-root data/market-research/iran-equities/adjustment-evidence/_shared/orchestrator/runs
```

Do not enable the daily timer until the acquisition scripts are present, a dry-run passes, and the immutable snapshot-to-engine adapter has passed tests.

## Scheduler

The included user-level systemd timer runs daily at 18:15 Asia/Tehran with persistent catch-up. It requires the laptop to be powered on and connected; it is not a 24/7 hosted service.
