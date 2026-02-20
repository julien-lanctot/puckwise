# PuckWise - Product Requirements

## Product Overview

PuckWise is a paid SaaS platform for fantasy hockey analytics. It targets serious players — single-season, keeper, and dynasty — who want a genuine edge beyond what free tools offer.

**Core differentiator:** Personalized, roster-aware recommendations. Generic rankings exist everywhere for free. PuckWise connects to a user's actual league (Yahoo, ESPN, Fantrax), imports their roster and scoring settings, and produces advice specific to *their* situation: who to pick up off waivers, which trade improves *their* team, how to win *their* category matchup this week.

---

## Target Users

- **Primary:** Serious single-season H2H or points league players. Multiple leagues. Play to win. Willing to pay $40-80/season.
- **Secondary:** Keeper and dynasty players with longer time horizons. Higher engagement, higher willingness to pay ($80-120/season).
- **Not targeted:** Casual players (won't pay), DFS players (different product entirely).

---

## Subscription Tiers

| Feature | Free | Pro ($49/season) | Elite ($99/season) |
|---|---|---|---|
| Player rankings (top 100) | ✅ | ✅ | ✅ |
| Full player database | ❌ | ✅ | ✅ |
| Platform roster import | ❌ | ✅ | ✅ |
| Waiver wire optimizer | ❌ | ✅ | ✅ |
| Trade analyzer | Limited | ✅ | ✅ |
| Category league support | ❌ | ✅ | ✅ |
| Playoff schedule planner | ❌ | ✅ | ✅ |
| Injury/scratch alerts | ❌ | ✅ | ✅ |
| Multi-league support | 1 | 3 | Unlimited |
| Dynasty/keeper tools | ❌ | ❌ | ✅ |
| Trade value history | ❌ | ❌ | ✅ |
| Rolling projections | ❌ | ✅ | ✅ |

---

## Data Sources

### NHL API (Primary)
- Web API: `https://api-web.nhle.com/v1`
- Stats API: `https://api.nhle.com/stats/rest/en`
- Data: Game logs, rosters, schedules, season stats, injuries
- Coverage: 2008–present
- **Intraday pull:** Injuries and scratches at 4–6pm EST daily

### MoneyPuck (Advanced Stats)
- Base: `https://moneypuck.com/moneypuck/playerData`
- Files: `seasonSummary/{year}/regular/skaters.csv`, `lines.csv`, `teams.csv`
- Data: xG, Corsi, Fenwick, PDO, WAR, zone starts, quality of competition
- Coverage: 2007–present

### Line Combinations
- Source: Daily Face-Off scrape or community-maintained feed
- Data: Line number (1–4), PP unit (PP1/PP2/none), updated daily
- Critical for: context-aware projections and waiver wire recommendations

### Platform APIs (User Roster Import)
- **Yahoo Fantasy API** (OAuth 2.0): leagues, rosters, scoring settings, waiver wire
- **ESPN Fantasy API** (unofficial): leagues, rosters, scoring settings
- **Fantrax API** (unofficial): leagues, rosters, scoring settings

---

## Core Features

### Priority 1 — Required Before Launch

#### 1. Auth & Multi-Tenancy
- Email/password registration with email verification
- JWT access tokens (15min) + refresh tokens (30 days)
- All data scoped to authenticated user
- Feature gating by subscription tier at middleware level

#### 2. Platform Roster Import
- Connect Yahoo (OAuth 2.0), ESPN, Fantrax
- Auto-import: league settings, scoring weights, roster positions, roster itself
- Daily background sync to keep rosters current
- Manual sync trigger via UI
- *This is table stakes. Without it, everything else is generic.*

#### 3. Waiver Wire Optimizer
Personalized pickup recommendations ranked for the user's specific situation.

**Score formula:**
```
pickup_score = VORP(pickup) - VORP(drop) + schedule_bonus(next_14_days) - roster_redundancy_penalty
```

- Filters by user's roster construction (don't recommend a 4th center if already stacked at C)
- Respects user's league's waiver rules (FAAB budget if applicable)
- Ranks separately for points leagues vs category leagues
- Shows reasoning: "Picks up 2 extra games this week, 3rd-best RW available"

#### 4. Injury & Scratch Alerts
- Intraday ETL job (4–6pm EST) detects new injuries and lineup scratches
- Alert delivered by email (Resend) and web push within 30min of confirmation
- User sets alert preferences per player or for all rostered players
- Alert types: injury (with severity), lineup scratch, lineup promotion

#### 5. Stripe Billing
- Subscription management (subscribe, upgrade, downgrade, cancel)
- Webhook handler for subscription lifecycle events
- Graceful tier downgrade (don't hard-block access mid-billing period)
- Free tier available without payment info

### Priority 2 — Core Differentiators

#### 6. Personalized Trade Analyzer
Different from generic trade analyzers: evaluates trades relative to *this user's roster* and *their league's scoring*.

- Input: players offered vs players received
- Output: net VORP impact for both sides, roster fit analysis, category impact
- Flags if the trade makes both teams better (win-win) or one-sided
- Shows what need the trade fills ("you're weak at C, this helps")
- Trade suggestions: given user's roster, proactively surface favorable trade targets

#### 7. Category League H2H Optimizer
For H2H categories leagues (most popular format, most underserved by analytics tools).

- Project both teams' stat totals for the current week based on remaining games
- Identify categories within reach (1 SD) vs categories to concede (too far ahead/behind)
- Recommend streaming adds by target category
- Weekly strategy brief: "Target SOG and PPP this week. Concede hits."

#### 8. Playoff Schedule Planner
Critical for H2H leagues in the stretch run.

- For any date range (e.g., fantasy playoff weeks), compute games-played per player
- Flag players with 4-game weeks, back-to-backs, favorable opponents
- Recommend streaming adds specifically for schedule advantage
- Show full team GP calendar for the playoff window

#### 9. Season Projections
- Full-year point total predictions per player
- Confidence intervals (10th / 50th / 90th percentile)
- Per-category projections (G, A, SOG, hits, blocks) for category league users
- Regression detection: buy-low / sell-high candidates based on PDO, xG, shooting%
- Draft rankings configurable by league scoring type

#### 10. Rolling Projections (2-Week)
- Short-term predictions factoring schedule, recent form, opponent
- Identifies hot/cold streaks vs sustainable performance
- Powers the waiver wire optimizer's schedule component

### Priority 3 — Elite Tier / Retention

#### 11. Dynasty & Keeper Tools
- Prospect rankings with NHL ETA and upside tier
- Aging curve projections (multi-year expected production)
- Keeper cost analysis (is this player worth the cap hit or round cost?)
- Dynasty trade analyzer with multi-year value weighting
- Contract status and term (years of team control)

#### 12. Trade Value Tracker
- 30/60/90-day value trend per player
- Shows how a player's perceived trade value has moved
- Context: "Value up 15% since line promotion 3 weeks ago"

---

## ML Model

### Current State (Phase 4 Complete)
- Ridge regression: MAE 9.69 pts, R² 0.640
- XGBoost: MAE 9.86 pts, R² 0.619
- 721 projections, trained on 9,753 player-seasons (2008–2025)
- Top features: ppg_1yr (30%), ppg_3yr (25%), ppg_5yr (11%)

### Required Improvements for Paid Product

**Target MAE: below 8.5 points** (required to be competitive with professional tools)

**New features to add:**
- `games_missed_per_season_avg` — injury history (1yr, 3yr)
- `injury_type_risk` — encoded severity category from injury history
- `games_in_next_14_days` — schedule density for rolling projections
- `home_away_ratio_next_14` — travel context
- `back_to_backs_next_14` — fatigue factor
- `line_number` — 1st/2nd/3rd line encoding
- `pp_unit` — PP1/PP2/none encoding
- `avg_linemate_ppg_1yr` — teammate quality on current line
- `last_14_day_ppg` — recent form vs season average
- `recent_form_delta` — divergence from projection (hot/cold signal)

**Per-category outputs:**
Current model outputs points only. Need separate projections for G, A, SOG, hits, blocks to support category leagues. Options:
- Multi-output regression (single model, multiple targets)
- Separate models per stat category

**In-season retraining:**
- Monthly retrain October–April using actual season data
- Early-season prior weighted toward historical (first 20 games: 70% historical / 30% current)
- After 40 games: weight shifts to 40/60; after 60 games: 20/80

**Ensemble:**
Blend Ridge + XGBoost + recent-form time-series component (exponential weighted moving average of last 14 days).

### Regression Detection Logic
- Shooting% z-score > 2.0: sell-high
- Shooting% z-score < -2.0: buy-low
- PDO > 1.02: sell-high (lucky)
- PDO < 0.98: buy-low (unlucky)
- Goals > xG by 1.5 SD: sell-high
- Goals < xG by 1.5 SD: buy-low

---

## Database Schema (Additions to Existing)

### Existing (Phase 1, complete)
```
players, teams, seasons, games
skater_game_logs (hypertable), goalie_game_logs (hypertable)
skater_season_stats, goalie_season_stats
skater_advanced_stats
player_projections
fantasy_leagues, fantasy_teams, fantasy_rosters
etl_runs
```

### New Tables Required
```sql
-- Auth & billing
users (id, email, password_hash, email_verified, created_at)
subscriptions (user_id, stripe_customer_id, stripe_subscription_id, tier, status, current_period_end)

-- Platform integrations
platform_connections (user_id, platform, access_token, refresh_token, token_expires_at, platform_user_id)
user_leagues (user_id, platform, platform_league_id, name, scoring_type, scoring_settings jsonb, roster_positions jsonb)
user_teams (user_id, user_league_id, platform_team_id, name)
user_rosters (user_team_id, player_id, acquired_at, is_keeper)

-- Real-time data
line_combinations (team_id, player_id, date, line_number, pp_unit, recorded_at)
player_injury_history (player_id, season_id, games_missed, injury_type, start_date, end_date)

-- Alerts
alert_preferences (user_id, player_id, alert_types text[])
alert_events (user_id, player_id, type, message, sent_at, read_at)

-- Trade value
trade_value_history (player_id, date, value_score)
```

---

## API Endpoints

### Auth
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
POST /api/auth/verify-email
POST /api/auth/forgot-password
POST /api/auth/reset-password
```

### Billing
```
GET  /api/billing/status
POST /api/billing/subscribe
POST /api/billing/cancel
POST /api/billing/webhook           (Stripe webhook)
```

### Platform Integrations
```
GET    /api/integrations
POST   /api/integrations/yahoo/connect
GET    /api/integrations/yahoo/callback
POST   /api/integrations/yahoo/sync
POST   /api/integrations/espn/connect
POST   /api/integrations/fantrax/connect
DELETE /api/integrations/:platform
```

### Players & Projections
```
GET /api/players                        (paginated, filterable; top-100 for free tier)
GET /api/players/:id                    (detail + projections + injury history)
GET /api/players/:id/game-log
GET /api/players/:id/trade-value        (Elite)
GET /api/players/search?q=
GET /api/projections/rankings           (configurable scoring; exportable)
GET /api/projections/regression         (buy-low / sell-high)
GET /api/schedule/analysis?from=&to=    (games-played calendar)
```

### Personalized (requires platform connection)
```
GET  /api/leagues
GET  /api/leagues/:id/waiver-wire       (personalized pickups)
GET  /api/leagues/:id/category-optimizer
GET  /api/leagues/:id/playoff-planner
GET  /api/teams/:id/roster
POST /api/trades/analyze
GET  /api/trades/suggestions            (proactive trade targets)
```

### Alerts
```
GET   /api/alerts
POST  /api/alerts/preferences
PATCH /api/alerts/:id/read
```

### Dynasty (Elite)
```
GET /api/prospects
GET /api/players/:id/dynasty-value
```

### NHL Reference
```
GET /api/nhl/teams
GET /api/nhl/teams/:id/roster
GET /api/nhl/teams/:id/schedule
```

---

## Non-Functional Requirements

### Performance
- Dashboard load: < 2s
- Player search: < 500ms
- Waiver wire recommendations: < 2s (pre-computed nightly, personalized on request)
- Trade analysis: < 1s
- Rankings page: served from Redis cache, < 200ms

### Reliability
- Intraday ETL (4–6pm EST) must complete before 5:30pm — scratches post-deadline matter
- Daily ETL must complete before 8am — before users check morning waiver wire
- Alert delivery: injury/scratch alerts within 30min of source confirmation
- ETL failure → PagerDuty/email alert to operator
- Retry logic with exponential backoff on NHL API rate limits

### Security
- Passwords: bcrypt, min cost 12
- JWT: RS256, short-lived access tokens
- OAuth tokens: encrypted at rest
- HTTPS only in production (Caddy handles cert)
- DB not publicly exposed
- Stripe webhooks: verified by signature
- Rate limiting on auth endpoints

### Scalability
- Single VPS (4 vCPU, 8GB RAM) sufficient for initial launch
- Redis caches projection rankings, VORP calculations
- TimescaleDB handles historical query load
- Background jobs via River (Postgres-backed queue, no extra infra)

### Maintainability
- Go: interfaces for testability, structured logging (slog)
- Python: type hints throughout, pytest for ETL and ML
- DB: all schema changes via numbered migrations
- ETL runs tracked in `etl_runs` table with status and error logs

---

## Out of Scope

- **Real-time in-game updates** — daily and intraday (4–6pm) is sufficient
- **Mobile app** — mobile-first web; native app is future consideration
- **Building fantasy league management** — do not compete with Yahoo/Fantrax on roster/waiver/trade infrastructure; integrate with them
- **DFS tools** — different product, different user
- **Goalie projections (v1)** — more volatile; ship skater projections first
- **Prospect junior stats** — limited NHL data; use ETA estimates and prospect rankings from public sources initially
- **Paid data sources** — Elite Prospects, Evolving Hockey are future upgrades if free sources prove insufficient
