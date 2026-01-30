# CLAUDE.md - Hockey Fantasy Analytics

## Project Summary

Fantasy hockey analytics platform for predicting player performance to assist with drafting and trading decisions. Single-user, self-hosted application.

## Tech Stack

- **Database:** PostgreSQL 15+ with TimescaleDB extension
- **ETL/ML:** Python 3.11+ (pandas, scikit-learn, XGBoost)
- **API:** Go 1.22+ with Chi router
- **Frontend:** React 18+ with Vite, TypeScript, Tailwind, Recharts
- **Deployment:** Docker Compose on Hetzner/OVH VPS

## Data Sources

### NHL API (Primary)
- Base: `https://api-web.nhle.com/v1`
- Stats: `https://api.nhle.com/stats/rest/en`
- Data: Game logs, rosters, schedules, season stats
- Coverage: 2008-present

### MoneyPuck (Advanced Stats)
- Base: `https://moneypuck.com/moneypuck/playerData`
- Data: xG, Corsi, Fenwick, PDO, WAR, shot data
- Format: CSV downloads
- Coverage: 2007-present

## Core Entities

```
players (nhl_id, name, position, birth_date, height, weight)
teams (nhl_id, abbreviation, name, conference, division)
seasons (season_id like "20232024", start_year, end_year)
games (nhl_game_id, season_id, date, home/away teams, score)
skater_game_logs (player_id, game_id, G, A, P, +/-, PIM, SOG, TOI, PPP) -- TimescaleDB hypertable
goalie_game_logs (player_id, game_id, W/L, GA, SV, SV%, TOI)
skater_season_stats (aggregated from game logs)
skater_advanced_stats (from MoneyPuck: xG, CF%, PDO, etc.)
player_projections (ML outputs: projected_points, confidence intervals, regression_flag)
fantasy_leagues (league settings, scoring type)
fantasy_teams (teams in a league)
fantasy_rosters (player assignments)
```

## Key Features

1. **Season Projections** - Full-year point predictions for drafting
2. **Rolling Projections** - Short-term predictions for trading
3. **Regression Detection** - Buy-low (unlucky) / sell-high (lucky) candidates using shooting%, PDO, xG
4. **Roster Management** - Track my roster + other managers' rosters
5. **Trade Analyzer** - Evaluate trades with positional scarcity (VORP)
6. **Draft Rankings** - Configurable for points or category leagues

## ML Model

**Target:** Season total points (goals, assists)

**Key Features:**
- Historical production (1yr, 3yr, 5yr rolling PPG)
- Age (peak 24-28, decline after)
- Games played % (durability)
- Team context (projected team GF, line assignment, PP unit)
- xG vs actual goals (regression signal)
- Shooting % z-score (regression signal)
- PDO deviation from 1.0 (luck indicator)

**Approach:** Start with Ridge regression baseline, then XGBoost with full features.

## API Endpoints

```
GET  /api/players              - List players (paginated, filterable)
GET  /api/players/:id          - Player detail + projections
GET  /api/players/:id/game-log - Game history
GET  /api/projections/rankings - Draft rankings
GET  /api/projections/regression - Buy-low/sell-high candidates
POST /api/trades/analyze       - Evaluate proposed trade
GET  /api/leagues              - My fantasy leagues
POST /api/leagues/:id/teams    - Add team to league
GET  /api/teams/:id/roster     - Team roster
POST /api/teams/:id/roster     - Add player to roster
```

## Project Structure

```
hockey-analytics/
├── backend/           # Go API
│   ├── cmd/api/
│   └── internal/{api,models,repository,service}/
├── etl/               # Python data pipeline
│   └── src/{extract,transform,load,jobs}/
├── ml/                # Python ML models  
│   └── src/{features,models,train,predict}/
├── frontend/          # React app
│   └── src/{components,pages,hooks,api}/
├── database/
│   └── migrations/
└── docker-compose.yml
```

## Development Order

1. **Database** - Schema with TimescaleDB, migrations
2. **ETL** - NHL API client, MoneyPuck downloader, loaders
3. **Initial Load** - Historical data 2008-present
4. **ML** - Feature engineering, baseline model, XGBoost
5. **API** - Go endpoints for players, projections, rosters
6. **Frontend** - Dashboard, player browser, trade analyzer
7. **Deploy** - Docker, VPS setup

## Fantasy Scoring (Configurable)

**Points League Example:**
- Goals: 3 pts, Assists: 2 pts, +/-: 0.5 pts
- PPP: 1 pt bonus, SOG: 0.3 pts, Hits/Blocks: 0.2 pts
- Wins: 5 pts, Saves: 0.2 pts, GA: -1 pt, SO: 3 pts

**Category League:** G, A, +/-, PIM, PPP, SOG, Hits, Blocks | W, GAA, SV%, SO

## Key Algorithms

**VORP (Value Over Replacement):**
- Calculate baseline stats by position (replacement level)
- Player value = stats - replacement level
- Accounts for positional scarcity (60pt C < 55pt RW)

**Regression Detection:**
- Shooting% z-score > 2: sell-high candidate
- Shooting% z-score < -2: buy-low candidate
- PDO > 1.02: sell-high (lucky)
- PDO < 0.98: buy-low (unlucky)
- Goals >> xG: sell-high
- Goals << xG: buy-low

## Commands Reference

```bash
# ETL
python -m etl.src.jobs.initial_load    # Load all historical data
python -m etl.src.jobs.daily_update    # Daily refresh

# ML
python -m ml.src.train.train           # Train models
python -m ml.src.predict.predict       # Generate projections

# API
cd backend && go run cmd/api/main.go

# Frontend
cd frontend && npm run dev

# Docker
docker-compose up -d
```

## Environment Variables

```
DATABASE_URL=postgresql://user:pass@localhost:5432/hockey_analytics
NHL_API_BASE_URL=https://api-web.nhle.com/v1
MONEYPUCK_BASE_URL=https://moneypuck.com/moneypuck/playerData
API_PORT=8080
```
