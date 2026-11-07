# MarketSage infrastructure-branch CI operations

This file documents the CI boundary on the provider-neutral integration branch.

## Triggers
- Pushes to main, deploy/**, research/**, ci/**, and infra/**.
- Pull requests targeting main, deploy/**, and infra/**.
- Scheduled full CI at 03:17 UTC and manual workflow_dispatch.

## CI jobs
- analysis, user-backend, user-frontend, admin-workspace, and production-images: existing application/research validations.
- infra-control-plane-tests: installs only requirements-infra.txt and discovers every test_*.py module under infra/control_plane. New provider-neutral tests are included automatically.
- Test CI automation helpers: offline tests for the sanitized failure notice utility.
- Post sanitized failure notice: emits job names and the run link only; it is not a runner-pool health monitor.

All external Actions in the workflow are pinned to immutable 40-character commit SHAs. Workflow permissions remain read-only except the separate failure-notification job, which receives issues:write only for its narrow Issue #49 comment.

## Safety and cost
- Standard GitHub-hosted runners only; the repository is public and no paid or larger runner is used.
- No raw market dataset, provider credential, production credential, broker access, or user-private file is available to these jobs.
- The owner laptop runner remains manual-only and must not receive untrusted PR code.
- No automated merge, deployment, billing, source collection, scoring, backtest approval, trading, or capital allocation.

## Completion boundary
A passing CI job validates code in this runner environment only. It does not prove the local worker is online, that a provider is reachable, that a data source is investment-eligible, or that the control plane provides 24/7 service. Scheduled reliability, direct-main-update detection, independent health observation, and dual-backend failover remain separate acceptance requirements.
