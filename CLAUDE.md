# CLAUDE.md - PuckWise

## Project Summary

Multi-tenant SaaS for fantasy hockey analytics. Personalized waiver wire, trade analysis, category league support, and playoff planning — driven by the user's actual roster imported from Yahoo/ESPN/Fantrax. Stripe-billed subscription tiers.

See `REQUIREMENTS.md` for full product spec and `PLAN.md` for development roadmap.

## Tech Stack

- **Database:** PostgreSQL 15+ with TimescaleDB
- **Cache:** Redis
- **ETL/ML:** Python 3.11+ (pandas, scikit-learn, XGBoost)
- **Job Queue:** River (Go, Postgres-backed)
- **API:** Go 1.22+ with Chi router
- **Auth:** JWT with refresh tokens; OAuth 2.0 for platform integrations
- **Billing:** Stripe
- **Notifications:** Resend (email) + Web Push
- **Frontend:** React 18+, Vite, TypeScript, Tailwind, Recharts — mobile-first
- **Deployment:** Docker Compose, Caddy reverse proxy, Hetzner/OVH VPS

## Project Structure

```
puckwise/
├── backend/
│   ├── cmd/api/
│   └── internal/
│       ├── api/            # Route handlers
│       ├── auth/           # JWT middleware
│       ├── billing/        # Stripe client + webhook
│       ├── integrations/   # Yahoo/ESPN/Fantrax OAuth + sync
│       ├── notifications/  # Email + web push
│       ├── models/
│       ├── repository/
│       └── service/
├── etl/
│   └── src/
│       ├── extract/        # nhl_api.py, moneypuck.py, lines.py
│       ├── transform/
│       ├── load/
│       └── jobs/
│           ├── initial_load.py
│           ├── daily_update.py      # midnight: stats + projections
│           └── intraday_update.py   # 4-6pm EST: injuries, scratches, lines
├── ml/
│   └── src/
│       ├── features/       # skater_features.py
│       ├── models/         # ridge.py, xgboost_model.py, ensemble.py
│       ├── train/
│       └── predict/        # outputs points + per-category projections
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── api/
├── database/
│   └── migrations/
├── REQUIREMENTS.md
├── PLAN.md
└── docker-compose.yml
```

## Progress Log

### Phase 1: Database ✅
- PostgreSQL 15 + TimescaleDB, 11 migrations
- Hypertables: skater_game_logs, goalie_game_logs

### Phase 2: ETL ✅
- `etl/src/extract/nhl_api.py`, `nhl_stats_api.py`, `moneypuck.py`
- Transform + upsert loaders

### Phase 3: Initial Load ✅
- 2008–2025 loaded, ~9,753 player-seasons

### Phase 4: ML ✅
- `ml/src/features/skater_features.py`
- Ridge: MAE 9.69, R² 0.640 | XGBoost: MAE 9.86, R² 0.619
- 721 projections generated

### Phase 5–12: Pending
See `PLAN.md`.

## Commands Reference

```bash
# ETL
python -m etl.src.jobs.initial_load
python -m etl.src.jobs.daily_update
python -m etl.src.jobs.intraday_update

# ML
python -m ml.src.train.train
python -m ml.src.predict.predict

# API
cd backend && go run cmd/api/main.go

# Frontend
cd frontend && npm run dev

# Docker
docker-compose up -d
```

## Environment Variables

```
DATABASE_URL=postgresql://user:pass@localhost:5432/puckwise
REDIS_URL=redis://localhost:6379

NHL_API_BASE_URL=https://api-web.nhle.com/v1
MONEYPUCK_BASE_URL=https://moneypuck.com/moneypuck/playerData

JWT_SECRET=...
JWT_REFRESH_SECRET=...

STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
STRIPE_PRO_PRICE_ID=...
STRIPE_ELITE_PRICE_ID=...

RESEND_API_KEY=...
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...

YAHOO_CLIENT_ID=...
YAHOO_CLIENT_SECRET=...
ESPN_CLIENT_ID=...
FANTRAX_CLIENT_ID=...

API_PORT=8080
APP_ENV=development
```
