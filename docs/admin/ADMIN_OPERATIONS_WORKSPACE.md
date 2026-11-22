# Admin operations workspace — first read-only slice

**Status:** implementation candidate on branch `admin/read-only-operations-workspace-2026-11`; not deployed and not approved for public exposure.

## What the operator can do

- Open the operations page and request a current health check.
- See the user API and analysis engine as `healthy`, `unavailable`, `not_configured` or `disabled`.
- See when the check was performed.
- Distinguish a disabled monitor from an unavailable service.
- Avoid seeing internal URLs, stack traces, exception strings or guessed statuses.

The server performs bounded GET requests to each configured service's `/health` endpoint. Each probe has a five-second timeout. It does not read market data, change settings, enqueue work or perform administrative mutations.

## Configuration

- `MARKETSAGE_ADMIN_OPS_ENABLED=true` enables probes.
- `MARKETSAGE_USER_API_URL` is the internal base URL of the user backend.
- `ANALYSIS_ENGINE_URL` is the internal base URL of the analysis engine.
- `NEXT_PUBLIC_ADMIN_API_URL` configures the admin browser API base URL.

Without the enable flag, the service returns `disabled` and performs no network probe. Missing URLs return `not_configured`.

## Security and release boundary

This slice intentionally does not claim to be a complete admin system. Admin authentication, role authorization and durable audit logging are not implemented here. The operations endpoint only returns coarse health states and no internal targets, but the admin UI/API must remain out of public production routing until the admin security task passes. The production Compose file remains unchanged and does not deploy this workspace.

## Acceptance evidence still required

- CI build and unit tests on the exact PR head.
- A local, isolated smoke test with synthetic health endpoints.
- Authentication/authorization and audit logging before any public exposure.
- A later deployment/rollback check after the admin release gate is approved.
