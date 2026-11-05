# MarketSage staging deployment runbook

**Scope:** private staging only. This is not a production-release procedure.
Investment ranking and production source scoring must remain disabled.

## Before running the stack

1. Select and review one exact release-candidate commit. Confirm its GitHub Actions jobs passed. Do not combine PR #6 and PR #13 implicitly; they target different base branches.
2. Make sure the staging host has Docker Engine and the Docker Compose plugin. Set a DNS A/AAAA record for the chosen staging hostname to the server IP. Configure the firewall to allow only TCP 80/443 (and UDP 443 if HTTP/3 is wanted). Do not expose ports 3000 or 4500 directly.
3. **VPN reminder:** the base images and Caddy image may be fetched from external registries. Before asking the user to pull/build images from a network that requires it, explicitly tell the user to turn VPN on. This instruction concerns container-image downloads, not the Iranian source probes (TSETMC/CODAL/Tindex use VPN off).
4. Copy `.env.staging.example` to an untracked `.env.staging`, set a real DNS hostname, and generate a strong staging password hash. Keep the file private with restrictive permissions (for example `chmod 600 .env.staging`). Do not put the password or environment file in Git or chat.
5. For Caddy Basic Auth, use the documented command below in an interactive secure shell; enter the password when prompted, then place only the generated hash into `STAGING_BASIC_AUTH_HASH`:
   ```bash
   docker run --rm -it caddy:2.11.7-alpine caddy hash-password
   ```
   The example hash placeholder in `.env.staging.example` is intentionally invalid and must be replaced.

## Validate before startup

From the repository root:

```bash
git status --short --branch
docker compose --env-file .env.staging -f docker-compose.production.yml -f docker-compose.staging.yml config -q
```

Review the rendered configuration locally without publishing environment values. Only then start the private staging stack:

```bash
docker compose --env-file .env.staging -f docker-compose.production.yml -f docker-compose.staging.yml up -d --build
docker compose --env-file .env.staging -f docker-compose.production.yml -f docker-compose.staging.yml ps
```

Caddy terminates HTTPS for `STAGING_DOMAIN`, applies Basic Auth to the whole site/API, proxies `/api/*` to `user-backend:4500`, and proxies other paths to `user-frontend:3000`. The Compose file retains loopback bindings on backend/frontend host ports. Caddy needs working DNS and inbound port 80/443 for automatic certificate management. A valid TLS certificate must be confirmed before sending credentials.

## Smoke tests

1. Unauthenticated `GET /` must receive HTTP 401.
2. Authenticated `GET /` must return the frontend.
3. Authenticated `GET /api/markets` and `GET /api/markets/data-status` must return sanitized, expected API responses.
4. Open the research page and run the fixture-backed Research Snapshot. Confirm future records are excluded and `investment_ranking` is null/disabled.
5. Test service health/readiness; induce no live provider requests just to test the fixture flow.
6. Check the explicit unavailable/not-rankable state, stale-data failure behavior, provider outage handling and recovery.
7. Inspect logs for secret/raw payload leakage; store only sanitized status/results. Confirm all ranking/source-scoring flags stay disabled.

## Important boundary

The current NestJS market routes do not have application-level authorization guards. The reverse-proxy Basic Auth gate limits this temporary staging deployment; it is not a substitute for application auth if APIs are ever exposed outside the controlled staging environment. Keep staging behind this gate/IP restrictions and TLS until auth, rate/size limits, and security review are completed.

Do not merge a PR or deploy to production merely because staging starts. Merge only after the exact tested commit has CI-green results, staging smoke evidence is reviewed, source-specific acceptance remains properly fail-closed, and the user explicitly authorizes the merge/release.
