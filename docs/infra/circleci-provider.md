# CircleCI second CI provider

**Status:** configuration committed; account/project activation and a real CircleCI run are still pending.

## What is configured

`.circleci/config.yml` runs the exact provider-neutral control-plane conformance suite used by GitHub Actions:

```bash
python -m unittest discover -s infra/control_plane -p 'test_*.py' -v
```

The workflow is restricted to `main` and `infra/**` branches. It uses the small Linux Docker resource class, Python 3.12.11, bounded dependency-install/test commands, and no CircleCI contexts, secrets, deployment credentials, provider credentials, or write tokens.

This is an independent CI execution adapter, not a persistent worker host. CircleCI's hosted Docker executor will be separate from the GitHub-hosted runner pool, but it does not provide a continuously running MarketSage daemon or a durable coordinator host.

## Free-plan boundary (verify at activation)

The official CircleCI pricing page currently advertises the Free plan at $0/month, no credit card required, up to five active users, 30,000 credits/month, and up to 6,000 build minutes when using the small Docker resource class. Credits are usage-dependent, expire monthly, and personal builds are blocked when the balance reaches zero. The free-plan documentation describes the personal/non-open-source allowance as 30,000 credits/month.

Sources:
- https://circleci.com/pricing/
- https://circleci.com/docs/guides/plans-pricing/credits/

Operational rules:
- Do not enable paid refills, Performance, or any paid add-on.
- Do not assume the open-source allowance applies; use only the personal Free allowance unless eligibility is verified.
- Stop treating CircleCI as available when its quota is exhausted or account/project authorization is missing.
- Do not route a failed test to another provider. Cross-provider retry is permitted only after the prior attempt is known terminal/no-effect and idempotency is verified.
- A CircleCI green run is a second CI-provider signal; it is not proof of multi-host worker availability, uptime, or 24/7 operations.

## One-time owner activation

1. Sign in to CircleCI using the GitHub account that owns `yarsalam/marketsage`.
2. Authorize the CircleCI GitHub integration for this repository only.
3. Select the repository/project and allow the first VCS build to run.
4. Verify the build's commit SHA equals the exact MarketSage PR head under test and that the job `provider-neutral-control-plane` passes.
5. Verify the Free-plan credit balance and disable any paid upgrade/refill. Do not share credentials or tokens in chat or GitHub Issues.

No CircleCI account was created, no OAuth consent was granted, and no external provider was activated by this change.

## Acceptance state

- [x] CircleCI adapter configuration added to the integration branch.
- [x] Test command matches the GitHub provider-neutral conformance suite.
- [x] No contexts, secrets, deploy, merge, release, or write permission required by this pipeline.
- [ ] CircleCI account connected by the owner.
- [ ] Exact same PR head executes successfully on CircleCI and GitHub Actions.
- [ ] Quota exhaustion and provider outage are reported as unavailable, not silently treated as a passing test.
- [ ] Provider-router integration demonstrates safe no-duplicate failover before any task is automatically retried across these providers.
