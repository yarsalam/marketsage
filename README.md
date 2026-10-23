# MarketSage

MarketSage is an early-stage investment research application with a Next.js frontend, NestJS API, and Python analysis service.

## Current implementation scope

- The analysis service ranks a small set of **global-market proxies and crypto assets** using trailing monthly prices.
- It does **not** yet ingest Tehran Stock Exchange prices, Iranian FX rates, Iranian gold/coin prices, news, political events, or macroeconomic publication-time data.
- The Iranian-market dashboard now has an opt-in Tindex currency-rate refresh and persistent raw/normalized storage. Public display is disabled by default; enable it only if the vendor agreement allows redistribution. The dashboard does not yet score Iranian opportunities; it reports blockers until data semantics and commercial rights are accepted.
- The probability model is not production-validated. The API reports confidence as unavailable until probabilities are calibrated out-of-sample.
- Rankings are research output, not personalized recommendations, guaranteed returns, or a minimum-risk portfolio.

## Repository layout

- `user/user-frontend`: Next.js user interface.
- `user/user-backend`: NestJS API gateway.
- `user/analysis-engine`: Python/FastAPI analysis service and research/backtest scripts.
- `admin-panel/apps/web`: tracked Next.js admin UI source.
- `admin-panel/apps/server`: tracked NestJS admin API starter.

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

For research methodology, input requirements, limitations, and the leakage-aware backtest baseline, read [the research protocol](user/analysis-engine/research/README.md). The user API exposes `/api/markets/scores` and `/api/markets/backtest` for the current data-backed momentum ranking and historical research simulation. The remaining regime/news/macro/AI-analysis tabs intentionally show their unavailable state until real sources and validation exist. For the separate ML research scripts that use scikit-learn or XGBoost, also install `pip install -r requirements-research.txt`. Those heavier libraries are not included in the production API image.

### User backend and frontend

Install dependencies from each project using its committed lockfile, then run `pnpm start:dev` in `user/user-backend` and `pnpm dev` in `user/user-frontend`. For local frontend-to-API requests, set `NEXT_PUBLIC_API_URL=http://localhost:4500` before starting/building the frontend.

### Admin workspace

The admin UI source is tracked in this repository, but the admin NestJS server currently contains only a starter controller/module. The UI and API are **not approved for public production use** until authentication, authorization, audit logging, persistence, admin operations, and end-to-end API contracts are implemented and tested. CI build/test coverage does not imply those product/security requirements are complete.

## Production Compose

Review [DEPLOYMENT.md](DEPLOYMENT.md) before deployment. The current production Compose file covers only the user-facing research stack; it does not deploy the admin UI or admin API.

```bash
cp .env.production.example .env.production
chmod 600 .env.production
docker compose --env-file .env.production -f docker-compose.production.yml config
docker compose --env-file .env.production -f docker-compose.production.yml build
```

Do not start production services until config output, builds, tests, DNS, TLS, reverse-proxy routes, and firewall settings have been reviewed.

## Known blockers before a full production launch

1. The admin UI is tracked, but the admin server is a starter skeleton and is not integrated into production Compose.
2. Authentication, authorization, audit logging, admin operations, and persistence for the admin service are not implemented in the visible server source.
3. The analysis universe and data ingestion are not Iran-market ready. A separate draft PR defines fail-closed contracts for Iranian provider onboarding but does not add a live feed.
4. Historical backtests and synthetic comparisons are research artifacts, not verified live performance.
5. News, political-event and sentiment ingestion are not implemented as production data pipelines.
6. No full end-to-end test or target-server deployment has been run from this repository.
