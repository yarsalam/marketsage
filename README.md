# MarketSage

MarketSage is an early-stage investment research application with a Next.js frontend, NestJS API, and Python analysis service.

## Current implementation scope

- The analysis service ranks a small set of **global-market proxies and crypto assets** using trailing monthly prices.
- It does **not** yet ingest Tehran Stock Exchange prices, Iranian FX rates, Iranian gold/coin prices, news, political events, or macroeconomic publication-time data.
- The probability model is not production-validated. The API reports confidence as unavailable until probabilities are calibrated out-of-sample.
- Rankings are research output, not personalized recommendations, guaranteed returns, or a minimum-risk portfolio.

## Repository layout

- `user/user-frontend`: Next.js user interface.
- `user/user-backend`: NestJS API gateway.
- `user/analysis-engine`: Python/FastAPI analysis service and research/backtest scripts.
- `admin-panel`: admin workspace; see the deployment blockers below.

## Local development

### Python analysis service

```bash
cd user/analysis-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn price_service:app --reload --host 127.0.0.1 --port 8000
pytest -q
```

For research methodology, input requirements, limitations, and the new leakage-aware backtest baseline, read [the research protocol](user/analysis-engine/research/README.md). For the separate ML research scripts that use scikit-learn or XGBoost, also install `pip install -r requirements-research.txt`. Those heavier libraries are not included in the production API image.

### User backend and frontend

Install dependencies from each project using its committed lockfile, then run `pnpm start:dev` in `user/user-backend` and `pnpm dev` in `user/user-frontend`. For local frontend-to-API requests, set `NEXT_PUBLIC_API_URL=http://localhost:4500` before starting/building the frontend.

## Production compose

Review `DEPLOYMENT.md` before deployment. The user-facing stack can be built with:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
docker compose --env-file .env.production -f docker-compose.production.yml config
docker compose --env-file .env.production -f docker-compose.production.yml build
```

Do not start production services until config output, builds, tests, DNS, TLS, reverse-proxy routes, and firewall settings have been reviewed.

## Known blockers before a full production launch

1. `admin-panel/apps/web` is represented in this repository as an embedded Git repository pointer, not tracked source files. Add its source to this monorepo or configure a valid submodule before building the admin UI.
2. The tracked admin server is a NestJS starter skeleton; authentication, authorization, audit logging, admin operations, and persistence are not implemented in the visible source.
3. The analysis universe and data ingestion are not Iran-market ready.
4. Historical backtests and synthetic comparisons are research artifacts, not verified live performance.
5. No full end-to-end production test or server deployment has been run from this repository yet.
