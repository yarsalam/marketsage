# MarketSage Project Operating System

This is the operator's index for the project control plane. Canonical machine-readable records:
- `STRATEGY_CHARTER.md`: mission, boundaries and execution strategy.
- `PRODUCT_ROADMAP.md`: stage outcomes and integration order.
- `WORK_REGISTER.json`: every active/parked task with its contract and state.
- `DECISION_POLICY.json`: decision vocabulary, thresholds and authority.
- `RELEASE_GATES.json`: evidence required before user release or investment-output enablement.
- `EVIDENCE_LEDGER.json`: sanitized, immutable evidence references.
- `PROJECT_STATE.json`: current project and release posture.

## Operating cycle

1. Select the highest-value READY work item whose dependencies are satisfied.
2. Work in a dedicated branch; keep independently owned workstreams separate.
3. Update the register when state changes. Never mark work ACCEPTED based only on an open PR or a green test.
4. Validate the exact commit. Reuse prior evidence only if code, input, configuration, environment and dependency identity are unchanged.
5. Before integration, reconcile conflicting paths and inspect the complete diff.
6. After integration, exercise the actual user/API journey. Capture sanitized evidence with commit, run ID, scenario and observed result.
7. Only then mark a user-facing item ACCEPTED and set its user-value evidence.
8. Apply the decision policy. Stop failed approaches; do not keep producing PRs to create the appearance of activity.

## Machine validation

Run locally or in CI:

```bash
python3 .github/scripts/validate_project_operating_system.py
python3 .github/scripts/test_project_operating_system.py
```

The GitHub workflow `.github/workflows/project-operating-system.yml` runs on relevant push/PR changes and once daily. It is read-only, bounded, cancellable and does not run the laptop Runner, deploy, merge, collect market data or call paid services.

## Automation boundary

This is a governance validator, not an autonomous coding agent and not a 24/7 availability guarantee. It validates the work/evidence/decision records. Code-authoring agents are not enabled by this change. No paid credits, API, hosted service or always-on machine are consumed or provisioned.
