# Deployment checklist

This runbook prepares the **user stack** for controlled deployment. It does not claim the full application is production-approved.

## 1. Before the server

- Use a supported Ubuntu LTS server, configure SSH keys, restrict SSH, and allow only SSH plus HTTP/HTTPS at the firewall.
- Install Docker Engine and the Docker Compose plugin.
- Point the user-facing DNS name to the server and issue TLS certificates.
- Never store production secrets in Git.
- Plan off-server backups before introducing persistent user data. The `market_data` Docker volume contains first-seen daily market-data snapshots and manifests; include it in backup/retention policy, but do not treat it as a substitute for user-data backups.

## 2. Fetch and inspect

```bash
git clone https://github.com/yarsalam/marketsage.git
cd marketsage
git checkout deploy/production-readiness
cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production
docker compose --env-file .env.production -f docker-compose.production.yml config
```

Set `CORS_ORIGINS` to the exact HTTPS origin(s) of the frontend. Leave `NEXT_PUBLIC_API_URL` empty when the reverse proxy serves the frontend and proxies `/api/` to the user backend on the same origin. This variable is compiled into the frontend image, so changing it requires rebuilding the frontend image.

## 3. Test and build

On a development checkout, run the analysis tests with the development dependencies:

```bash
cd user/analysis-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
cd ../..
docker compose --env-file .env.production -f docker-compose.production.yml build
```

The production Python image intentionally installs runtime dependencies only. Run frontend and backend builds and tests before starting services as well.

## 4. Start the user stack

```bash
docker compose --env-file .env.production -f docker-compose.production.yml up -d
docker compose --env-file .env.production -f docker-compose.production.yml ps
docker compose --env-file .env.production -f docker-compose.production.yml logs --tail=100
curl -fsS http://127.0.0.1:4500/health
curl -fsS 'http://127.0.0.1:4500/api/decision?horizon=1M'
curl -fsS 'http://127.0.0.1:4500/api/markets'
curl -fsS 'http://127.0.0.1:4500/api/markets/scores'
# The backtest may return HTTP 503 if the provider lacks enough complete common history:
curl -i 'http://127.0.0.1:4500/api/markets/backtest'
```

The analysis service has no published host port. Backend and frontend bind to loopback only, so a host Nginx/Caddy reverse proxy can reach them without exposing them directly to the public network. The analysis service persists the first successful price snapshot per UTC day under the named `market_data` volume, with a JSON manifest containing retrieval time, source, symbols, and SHA-256 checksum.

## 5. Reverse proxy routing

Configure the TLS virtual host so:
- `/` proxies to `http://127.0.0.1:3000`.
- `/api/` proxies to `http://127.0.0.1:4500/api/` without stripping the `/api` prefix.
- Forward `Host`, `X-Real-IP`, and `X-Forwarded-For`; set suitable request timeouts.
- Do not publish the analysis service port.

Validate proxy config and HTTPS before opening public access. Domain names and certificate paths depend on the actual host setup.

## 6. Checks after deployment

- Backend `GET /health` returns 200.
- `GET /api/decision?horizon=1M` returns a valid response or a clear 503 if market data is unavailable; it must not fabricate a portfolio.
- `GET /api/markets/scores` returns completed-month momentum scores and separates the signal date from the latest provider observation.
- `GET /api/markets/backtest` returns full-history descriptive metrics plus a chronological 70/30 holdout and benchmark comparisons, or a clear 503 if there is not enough complete data.
- Browser requests use the public same-origin `/api` path. The backend routes market metadata, momentum scores, and backtest output under `/api/markets`.
- Verify builds, Python tests, CORS, health checks, and TLS.
- Ensure logs contain no tokens, passwords, or environment dumps.
- Add monitoring, log rotation, OS updates, and off-server backups before storing user data.

Never run `docker compose down -v` on a server unless deleting every attached named volume is intentional.

## 7. Explicit launch blockers

- The admin frontend source is not tracked here; `admin-panel/apps/web` is an embedded Git repository pointer.
- The admin NestJS server is a starter skeleton. Do not expose it as a functioning admin service.
- The analysis service is a global-proxy research prototype, not an Iran-market engine. Do not claim calibrated probabilities, minimum risk, or verified outperformance.
- Daily snapshots are first-seen immutable provider snapshots, not certified exchange data; verify source licensing, symbol coverage, and snapshot retention/backups.
- Deployment has not been run or validated by these changes. Review generated Compose configuration and test on the target environment before production.
