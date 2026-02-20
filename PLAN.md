# PuckWise - Development Plan

## Status Overview

| Phase | Description | Status |
|---|---|---|
| 1 | Database schema + migrations | ✅ Done |
| 2 | ETL pipeline | ✅ Done |
| 3 | Initial data load (2008–2025) | ✅ Done |
| 4 | ML baseline models | ✅ Done |
| 5 | Auth & multi-tenancy | 🔲 Next |
| 6 | Platform integrations (Yahoo/ESPN/Fantrax) | 🔲 |
| 7 | Billing (Stripe) | 🔲 |
| 8 | Enhanced ETL + ML | 🔲 |
| 9 | Personalized features | 🔲 |
| 10 | Alerts & notifications | 🔲 |
| 11 | Frontend | 🔲 |
| 12 | Production deployment | 🔲 |

---

## Completed Work

### Phase 1: Database ✅
- PostgreSQL 15 + TimescaleDB, 11 migrations
- Hypertables: `skater_game_logs`, `goalie_game_logs`
- Tables: players, teams, seasons, games, skater/goalie stats, advanced stats, projections, fantasy tables

### Phase 2: ETL ✅
- `etl/src/extract/nhl_api.py` — game logs, rosters, schedules
- `etl/src/extract/nhl_stats_api.py` — season stats
- `etl/src/extract/moneypuck.py` — advanced stats CSV
- Transform pipelines + upsert loaders with conflict handling
- `etl/src/jobs/initial_load.py`, `daily_update.py`

### Phase 3: Initial Load ✅
- 2008–2025 fully loaded
- ~9,753 player-seasons of training data
- Advanced stats: xG, Corsi, PDO, WAR from MoneyPuck

### Phase 4: ML ✅
- `ml/src/features/skater_features.py` — PPG rolling, age curves, durability, regression signals
- Ridge: MAE 9.69 pts, R² 0.640
- XGBoost: MAE 9.86 pts, R² 0.619
- 721 projections generated
- Top features: ppg_1yr (30%), ppg_3yr (25%), ppg_5yr (11%)

---

## Pending Phases

### Phase 5: Auth & Multi-Tenancy
**Goal:** Support multiple users with scoped data and subscription tiers.

**Database migrations:**
- [ ] `users` table (id, email, password_hash, email_verified, created_at)
- [ ] `subscriptions` table (user_id, stripe_customer_id, tier, status, current_period_end)

**Backend:**
- [ ] `backend/internal/auth/` — JWT generation, validation, refresh token rotation
- [ ] Registration endpoint with email verification flow
- [ ] Login endpoint
- [ ] JWT middleware — attach user context to all requests
- [ ] Tier-gating middleware — enforce feature access by subscription tier
- [ ] Password reset flow

**Decisions:**
- Access token TTL: 15 minutes
- Refresh token TTL: 30 days, rotated on use
- Algorithm: HS256 (simpler) or RS256 (better for future service split)

---

### Phase 6: Platform Integrations
**Goal:** Import user's actual roster and league settings from Yahoo, ESPN, Fantrax.

**Database migrations:**
- [ ] `platform_connections` table
- [ ] `user_leagues` table (with `scoring_settings jsonb`, `roster_positions jsonb`)
- [ ] `user_teams` table
- [ ] `user_rosters` table

**Backend — Yahoo (do first, largest user base):**
- [ ] `backend/internal/integrations/yahoo/` — OAuth 2.0 PKCE flow
- [ ] Fetch user's leagues + scoring settings
- [ ] Fetch team roster + map to internal player IDs
- [ ] Background sync job via River (daily)
- [ ] Manual sync trigger endpoint

**Backend — ESPN:**
- [ ] `backend/internal/integrations/espn/` — unofficial API (cookie-based or public endpoints)
- [ ] Same sync pattern as Yahoo

**Backend — Fantrax:**
- [ ] `backend/internal/integrations/fantrax/` — unofficial API
- [ ] Same sync pattern

**Notes:**
- Yahoo's OAuth is well-documented and the API is stable — start here
- ESPN's API is unofficial but widely reverse-engineered; use cookie-based auth for private leagues
- Map platform player IDs to internal `players.nhl_id` — maintain a mapping table

---

### Phase 7: Billing
**Goal:** Stripe subscription management with tier enforcement.

**Backend:**
- [ ] `backend/internal/billing/` — Stripe client wrapper
- [ ] `POST /api/billing/subscribe` — create Stripe customer + subscription
- [ ] `POST /api/billing/cancel` — schedule cancellation at period end
- [ ] `POST /api/billing/webhook` — handle: `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
- [ ] On subscription event: update `subscriptions` table, adjust tier in middleware
- [ ] Graceful downgrade: don't cut off access mid-period; downgrade at `current_period_end`

**Stripe setup required:**
- [ ] Create products: Free, Pro ($49/yr), Elite ($99/yr)
- [ ] Set up webhook endpoint in Stripe dashboard
- [ ] Configure billing portal for self-serve management

---

### Phase 8: Enhanced ETL & ML
**Goal:** Close the gap from MAE 9.7 to below 8.5. Add per-category projections and real-time data.

**ETL additions:**
- [ ] `etl/src/extract/lines.py` — scrape line combinations (line number, PP unit) daily
- [ ] `etl/src/jobs/intraday_update.py` — runs 4–6pm EST: injuries, scratches, lineup changes
- [ ] `etl/src/load/` — loaders for `line_combinations`, `player_injury_history`
- [ ] Database migrations for `line_combinations`, `player_injury_history`

**ML additions:**
- [ ] Extend `skater_features.py` with: injury history features, schedule density features, line context features, recent form delta
- [ ] Add per-category outputs (G, A, SOG, hits, blocks) — use multi-output XGBoost or separate models
- [ ] `ml/src/models/ensemble.py` — blend Ridge + XGBoost + EWM recent-form component
- [ ] `ml/src/train/train.py` — add monthly in-season retrain support with early/late season weighting
- [ ] Re-evaluate: target MAE < 8.5 before shipping projections as a paid feature

**Validation:**
- [ ] Backtest on 2022–23 and 2023–24 seasons (held out) to measure improvement
- [ ] Track MAE per position (F vs D) separately

---

### Phase 9: Personalized Features
**Goal:** Ship the features that justify payment.

**Waiver wire optimizer:**
- [ ] `backend/internal/service/waiver.go` — VORP calculation per user's scoring + schedule bonus
- [ ] Pre-compute nightly for all active users (River job)
- [ ] `GET /api/leagues/:id/waiver-wire` — return ranked pickups with reasoning
- [ ] Filter out already-rostered players (check all teams in the league)

**Trade analyzer (personalized):**
- [ ] `backend/internal/service/trade.go` — VORP delta + roster fit + category impact
- [ ] `POST /api/trades/analyze` — accepts player IDs in/out, returns analysis
- [ ] `GET /api/trades/suggestions` — proactive trade targets based on roster gaps

**Category optimizer:**
- [ ] `backend/internal/service/category.go` — project both teams' week stat totals
- [ ] Identify target/concede categories based on projected gap vs variance
- [ ] `GET /api/leagues/:id/category-optimizer` — weekly strategy

**Playoff planner:**
- [ ] `backend/internal/service/schedule.go` — games-played calendar for date range
- [ ] `GET /api/schedule/analysis?from=&to=` — GP count, back-to-backs, matchups
- [ ] `GET /api/leagues/:id/playoff-planner` — applies to user's roster

---

### Phase 10: Alerts & Notifications
**Goal:** Intraday injury/scratch alerts delivered within 30min.

**Database migration:**
- [ ] `alert_preferences` table
- [ ] `alert_events` table

**Backend:**
- [ ] Intraday ETL job detects changes by diffing against last known state
- [ ] `backend/internal/notifications/email.go` — Resend client
- [ ] `backend/internal/notifications/push.go` — Web Push (VAPID)
- [ ] River job: fan out alerts to affected users when injury/scratch detected
- [ ] `GET /api/alerts` — unread alerts for user
- [ ] `POST /api/alerts/preferences` — set per-player preferences
- [ ] `PATCH /api/alerts/:id/read`

---

### Phase 11: Frontend
**Goal:** Mobile-first UI covering all core features.

**Stack:** React 18, Vite, TypeScript, Tailwind, Recharts

**Pages (in build order):**
- [ ] Auth: Login, Register, Email verification, Forgot password
- [ ] Billing: Subscribe page, Plan comparison, Billing management
- [ ] Platform connect: OAuth initiation, league selection, sync status
- [ ] Dashboard: Roster health summary, top alerts, top 3 waiver pickups
- [ ] Rankings: Full player list, filterable, configurable scoring, export to CSV
- [ ] Player detail: Stats, projections, injury history, trade value chart
- [ ] Waiver wire: Ranked pickups with reasoning
- [ ] Trade analyzer: Player picker, analysis output
- [ ] Category optimizer: Weekly matchup view, strategy panel
- [ ] Playoff planner: Calendar view with GP counts
- [ ] Alerts: Notification center
- [ ] Dynasty tools (Elite): Prospects, keeper analysis

**Mobile-first priorities:**
- Waiver wire and alerts are the most-used features on mobile — design those first
- Dashboard must be usable one-handed
- Trade analyzer input needs a good mobile player-search UX

---

### Phase 12: Production Deployment
**Goal:** Stable, monitored production environment.

- [ ] Docker Compose: all services (Go API, Python ETL, ML, Redis, PostgreSQL+TimescaleDB)
- [ ] Caddy reverse proxy with automatic SSL (Let's Encrypt)
- [ ] Staging environment (identical to prod, separate DB)
- [ ] Structured logging in Go (slog), Python (structlog)
- [ ] Health check endpoints: `GET /health`, `GET /ready`
- [ ] ETL failure alerting (email operator on job failure)
- [ ] PostgreSQL backups: daily pg_dump to object storage (Hetzner Object Storage or Backblaze B2)
- [ ] Uptime monitoring (UptimeRobot or similar)
- [ ] DB connection pooling (PgBouncer or pgx pool settings)
- [ ] Redis persistence config (AOF for alert deduplication safety)

---

## Key Dependencies Between Phases

```
Phase 5 (Auth) must complete before:
  → Phase 6 (Integrations) — needs user identity
  → Phase 7 (Billing) — needs user identity
  → Phase 9 (Personalized features) — needs user scoping

Phase 6 (Integrations) must complete before:
  → Phase 9 (Personalized features) — needs imported roster + scoring settings

Phase 8 (Enhanced ML) must complete before:
  → Phase 9 (Personalized features) — waiver wire uses projections
  → Phase 11 (Frontend) — rankings page needs category projections

Phase 9 (Personalized features) must complete before:
  → Phase 11 (Frontend) — UI needs the endpoints

Phase 10 (Alerts) can run in parallel with Phase 9.
Phase 12 (Deploy) can be set up in parallel; final cutover at the end.
```

---

## Open Questions

1. **Yahoo API rate limits** — Yahoo Fantasy API has usage limits. Need to understand quota for syncing many users' rosters simultaneously. May need to stagger syncs.
2. **ESPN private leagues** — Public ESPN leagues are accessible; private leagues require cookie-based auth which may break without notice.
3. **Line combination source** — Daily Face-Off scraping may violate ToS. Investigate: LeftWingLock API ($), community-maintained GitHub feeds, or HockeyDB.
4. **Goalie projections** — Higher variance than skaters. Include with heavy caveats in v1 or ship skater-only first?
5. **FAAB waiver wire** — Yahoo/ESPN FAAB budgets need to be surfaced in waiver wire optimizer. Requires tracking each user's remaining budget.
6. **Mobile app** — React-first now; native app is future consideration if web engagement proves the concept.
7. **Pricing validation** — Pro at $49/season and Elite at $99/season are assumptions. Should validate against Dobber ($40-80) and target slightly below to enter the market.
