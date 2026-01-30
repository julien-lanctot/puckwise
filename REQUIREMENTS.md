# Hockey Fantasy Analytics - Project Requirements

## Project Overview

Build a predictive analytics platform for fantasy hockey that helps with drafting and trading decisions. The tool predicts player point progression throughout the season based on historical data, team performance, injuries, and advanced statistics.

## Target Users

- Personal use (single user initially)
- Fantasy hockey players looking for data-driven draft and trade decisions

## Core Features

### 1. Player Projections

#### Season Projections (for Drafting)
- Predict full-season point totals for all NHL skaters and goalies
- Provide confidence intervals (e.g., 10th/90th percentile outcomes)
- Factor in:
  - Historical point production (1yr, 3yr, 5yr rolling averages)
  - Age curves (players peak ~24-28, decline after)
  - Games played percentage (durability/injury history)
  - Team context (projected team goal scoring)
  - Line combinations and power play usage
  - Advanced metrics (xG, Corsi, shooting percentage regression)

#### Rolling Projections (for Trading)
- Short-term predictions (next 2 weeks, next month)
- Identify hot/cold streaks vs sustainable performance
- Factor in schedule strength and recent form

### 2. Regression Detection

#### Buy-Low Candidates
- Players with shooting percentage significantly below career average
- Players with PDO (on-ice shooting% + save%) below 1.0
- Players with goals below expected goals (xG)
- Players returning from injury with depressed stats

#### Sell-High Candidates
- Players with unsustainably high shooting percentage
- Players with PDO significantly above 1.0
- Players with goals above expected goals
- Players benefiting from temporary line/PP promotions

### 3. Roster Management

#### My Team Tracking
- Import/manually add my fantasy roster
- Track projected vs actual performance
- Identify weak positions needing upgrades

#### League Scouting
- Add other managers' rosters from my league
- Identify favorable trade targets on each team
- Find players other managers might undervalue

### 4. Trade Analyzer

#### Trade Evaluation
- Calculate "team improvement score" for proposed trades
- Consider positional scarcity (VORP - Value Over Replacement Player)
- Account for category balance (for category leagues)
- Factor in schedule considerations (games remaining, playoff schedule)

#### Trade Finder
- Given my roster, suggest trades that improve my team
- Identify win-win trades where both teams benefit
- Rank trade targets by improvement potential

### 5. Draft Tools

#### Draft Rankings
- Custom rankings based on league scoring settings
- Support both category leagues and points leagues
- Positional scarcity adjustments
- ADP (Average Draft Position) comparison to identify value

#### Draft Companion (Future)
- Real-time draft tracker
- Recommend best available player
- Track positional needs as draft progresses

---

## Data Sources

### Primary: NHL API

**Base URLs:**
- Web API: `https://api-web.nhle.com/v1`
- Stats API: `https://api.nhle.com/stats/rest/en`

**Key Endpoints:**
- `/player/{id}/landing` - Player bio and career info
- `/player/{id}/game-log/{season}/{gameType}` - Game-by-game stats
- `/roster/{team}/{season}` - Team rosters
- `/standings/now` - Current standings with team info
- `/skater/summary` (Stats API) - Season totals with pagination
- `/goalie/summary` (Stats API) - Goalie season totals

**Data Available:**
- Game logs back to ~2008-2009 season
- Basic stats: G, A, P, +/-, PIM, PPP, SHP, SOG, TOI
- Game context: home/away, opponent, date

### Secondary: MoneyPuck

**Base URL:** `https://moneypuck.com/moneypuck/playerData`

**Key Data Files:**
- `seasonSummary/{year}/regular/skaters.csv` - Skater advanced stats
- `seasonSummary/{year}/regular/goalies.csv` - Goalie advanced stats
- `seasonSummary/{year}/regular/teams.csv` - Team advanced stats
- `seasonSummary/{year}/regular/lines.csv` - Line combination stats
- `playerBios/allPlayersLookup.csv` - Player biographical data
- Shot data (zipped CSVs) - Individual shot-level data with xG

**Advanced Stats Available:**
- Expected Goals (xG) - individual and on-ice
- Corsi/Fenwick (shot attempt metrics)
- PDO (luck indicator)
- Zone starts (offensive/defensive)
- Quality of competition/teammates
- WAR (Wins Above Replacement)
- Per-60 rates for all counting stats

**Historical Coverage:** 2007-2008 to present

### Data Refresh Strategy

- **Daily refresh** during NHL season (overnight batch)
- **Initial load** of all historical data (2008-present)
- Store raw data locally, transform into analytics-ready format

---

## Technical Architecture

### Database: PostgreSQL + TimescaleDB

**Why TimescaleDB:**
- Time-series optimization for game logs (millions of rows)
- Automatic partitioning by time
- Compression for historical data
- Standard PostgreSQL compatibility

**Core Tables:**
1. `teams` - NHL team reference data
2. `players` - Player biographical info
3. `seasons` - Season metadata
4. `games` - Game schedule and results
5. `skater_game_logs` - Game-by-game skater stats (hypertable)
6. `goalie_game_logs` - Game-by-game goalie stats (hypertable)
7. `skater_season_stats` - Aggregated season totals
8. `goalie_season_stats` - Aggregated goalie season totals
9. `skater_advanced_stats` - MoneyPuck advanced metrics
10. `team_season_stats` - Team-level stats
11. `injuries` - Injury history
12. `player_projections` - ML model outputs
13. `fantasy_leagues` - League configuration
14. `fantasy_teams` - Teams in a league
15. `fantasy_rosters` - Player assignments to fantasy teams
16. `etl_runs` - ETL job tracking

### Backend: Python (ETL + ML) + Go (API)

**Python Components:**
- Data extraction from NHL API and MoneyPuck
- Data transformation and cleaning
- Feature engineering for ML
- Model training (scikit-learn, XGBoost/LightGBM)
- Prediction generation

**Go Components:**
- REST API serving predictions and data
- Roster management endpoints
- Trade analysis logic
- Authentication (future)

**Why Split:**
- Python excels at data science workloads
- Go provides fast, type-safe API with low resource usage
- ML models trained offline, predictions pre-computed daily
- Go API just reads from database (simple, fast)

### Frontend: React

**Key Views:**
1. **Dashboard** - Overview of my team, recent projections, alerts
2. **Player Browser** - Search/filter all players, view projections
3. **Player Detail** - Deep dive on single player (stats, charts, projections)
4. **My Roster** - Current fantasy roster with projections
5. **Trade Analyzer** - Input trades, see evaluation
6. **Draft Board** - Pre-draft rankings and tools
7. **League View** - All teams in my league for scouting

**Charting:** Recharts or Tremor for data visualization

### Deployment: Self-Hosted (Hetzner/OVH)

**Infrastructure:**
- Single VPS (4 vCPU, 8GB RAM recommended)
- Docker Compose for all services
- Coolify or manual Docker management
- PostgreSQL with TimescaleDB in container
- Nginx reverse proxy with SSL (Let's Encrypt)

**Services:**
```
┌─────────────────────────────────────────┐
│              Nginx (SSL)                │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│   React App   │   │    Go API     │
│   (static)    │   │   :8080       │
└───────────────┘   └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  PostgreSQL   │
                    │  + TimescaleDB│
                    └───────────────┘
                            ▲
                            │
                    ┌───────────────┐
                    │  Python ETL   │
                    │  (cron jobs)  │
                    └───────────────┘
```

---

## ML Model Requirements

### Target Variables

1. **Season Total Points** - Primary prediction target
2. **Season Total Goals** - Secondary
3. **Season Total Assists** - Secondary
4. **Games Played** - For injury adjustment

### Feature Categories

#### Player Historical Features
- Points per game (1yr, 3yr, 5yr rolling)
- Goals per game (1yr, 3yr, 5yr)
- Assists per game (1yr, 3yr, 5yr)
- Games played per season (durability)
- Shooting percentage (career, recent)
- Power play points percentage
- Age at start of season

#### Team Context Features
- Projected team goals for (based on roster)
- Team power play efficiency
- Line assignment (1st, 2nd, 3rd, 4th)
- Power play unit (PP1, PP2, none)
- Teammate quality (avg linemate points)

#### Advanced Metrics (from MoneyPuck)
- Expected goals (xG) vs actual goals
- Corsi for percentage (CF%)
- PDO (luck indicator)
- Zone start percentage
- Quality of competition

#### Regression Indicators
- Shooting % vs career average (z-score)
- PDO deviation from 1.0
- Goals above/below expected
- On-ice shooting % vs league average

### Model Approach

**Phase 1: Baseline**
- Linear regression with regularization (Ridge/Lasso)
- Simple feature set (historical stats + age)
- Establish baseline performance

**Phase 2: Gradient Boosting**
- XGBoost or LightGBM
- Full feature set including advanced metrics
- Hyperparameter tuning with cross-validation

**Phase 3: Ensemble (Future)**
- Combine multiple models
- Separate models for different player archetypes
- Position-specific models (F vs D vs G)

### Evaluation Metrics

- MAE (Mean Absolute Error) for point predictions
- RMSE for overall accuracy
- Correlation with actual results
- Ranking accuracy (Spearman correlation for draft rankings)

---

## Fantasy Scoring Systems to Support

### Category Leagues (Head-to-Head)

**Standard Skater Categories:**
- Goals (G)
- Assists (A)
- Plus/Minus (+/-)
- Penalty Minutes (PIM)
- Power Play Points (PPP)
- Shots on Goal (SOG)
- Hits (HIT) - optional
- Blocked Shots (BLK) - optional

**Standard Goalie Categories:**
- Wins (W)
- Goals Against Average (GAA)
- Save Percentage (SV%)
- Shutouts (SO)

### Points Leagues

**Example Scoring (Yahoo Default):**
- Goals: 3 points
- Assists: 2 points
- Plus/Minus: 0.5 points
- PIM: 0.25 points
- PPP: 1 point bonus
- SOG: 0.3 points
- Wins: 5 points
- GA: -1 point
- Saves: 0.2 points
- Shutouts: 3 points

**Configuration:**
- Allow custom scoring weights
- Store league settings in database
- Calculate fantasy value using configured weights

---

## API Endpoints (Go)

### Players
- `GET /api/players` - List all players (paginated, filterable)
- `GET /api/players/:id` - Player detail with projections
- `GET /api/players/:id/game-log` - Player game history
- `GET /api/players/:id/projections` - All projections for player
- `GET /api/players/search?q=` - Search players by name

### Projections
- `GET /api/projections/current` - Current season projections
- `GET /api/projections/rankings` - Draft rankings
- `GET /api/projections/regression` - Buy-low/sell-high candidates

### Fantasy
- `GET /api/leagues` - List my leagues
- `POST /api/leagues` - Create a league
- `GET /api/leagues/:id/teams` - Teams in a league
- `POST /api/leagues/:id/teams` - Add a team
- `GET /api/teams/:id/roster` - Team roster
- `POST /api/teams/:id/roster` - Add player to roster
- `DELETE /api/teams/:id/roster/:playerId` - Remove player

### Trades
- `POST /api/trades/analyze` - Analyze a proposed trade
- `GET /api/trades/suggestions` - Get trade suggestions for my team

### Teams (NHL)
- `GET /api/nhl/teams` - List NHL teams
- `GET /api/nhl/teams/:id/roster` - Current NHL roster
- `GET /api/nhl/teams/:id/schedule` - Team schedule

---

## Project Structure

```
hockey-analytics/
├── README.md
├── REQUIREMENTS.md          # This file
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── cmd/
│   │   └── api/
│   │       └── main.go      # API entrypoint
│   ├── internal/
│   │   ├── api/             # HTTP handlers
│   │   ├── models/          # Data models
│   │   ├── repository/      # Database access
│   │   ├── service/         # Business logic
│   │   └── config/          # Configuration
│   ├── go.mod
│   └── go.sum
│
├── etl/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── extract/         # Data extraction
│   │   │   ├── nhl_api.py
│   │   │   └── moneypuck.py
│   │   ├── transform/       # Data transformation
│   │   │   └── transform.py
│   │   ├── load/            # Database loading
│   │   │   └── loader.py
│   │   └── jobs/            # Scheduled jobs
│   │       ├── initial_load.py
│   │       └── daily_update.py
│   ├── requirements.txt
│   └── pyproject.toml
│
├── ml/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── features/        # Feature engineering
│   │   │   └── features.py
│   │   ├── models/          # ML models
│   │   │   ├── baseline.py
│   │   │   └── xgboost_model.py
│   │   ├── train/           # Training pipelines
│   │   │   └── train.py
│   │   └── predict/         # Prediction generation
│   │       └── predict.py
│   ├── notebooks/           # Jupyter notebooks for exploration
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── api/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── database/
│   ├── migrations/          # SQL migrations
│   │   └── 001_initial.sql
│   └── seeds/               # Seed data
│
└── scripts/
    ├── setup.sh             # Initial setup script
    └── deploy.sh            # Deployment script
```

---

## Development Phases

### Phase 1: Data Pipeline (Week 1-2)
- [ ] Set up PostgreSQL + TimescaleDB
- [ ] Implement NHL API client
- [ ] Implement MoneyPuck downloader
- [ ] Create database schema
- [ ] Build initial data load script
- [ ] Build daily update script
- [ ] Load historical data (2008-present)

### Phase 2: ML Model (Week 3-4)
- [ ] Exploratory data analysis in Jupyter
- [ ] Feature engineering pipeline
- [ ] Baseline linear regression model
- [ ] XGBoost model with full features
- [ ] Model evaluation and tuning
- [ ] Prediction generation pipeline
- [ ] Regression candidate detection

### Phase 3: API (Week 5-6)
- [ ] Go project setup
- [ ] Database repository layer
- [ ] Player endpoints
- [ ] Projection endpoints
- [ ] Fantasy roster endpoints
- [ ] Trade analysis endpoint

### Phase 4: Frontend (Week 7-8)
- [ ] React project setup with Vite
- [ ] Dashboard page
- [ ] Player browser and detail pages
- [ ] Roster management
- [ ] Trade analyzer UI
- [ ] Draft board

### Phase 5: Polish & Deploy (Week 9-10)
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Deploy to VPS
- [ ] Monitoring and logging
- [ ] Documentation

---

## Non-Functional Requirements

### Performance
- Dashboard load time < 2 seconds
- Player search results < 500ms
- Trade analysis < 1 second
- Support 17 years of historical data (~1M+ game log records)

### Reliability
- Daily ETL job completes successfully
- Graceful handling of NHL API rate limits
- Retry logic for failed requests
- ETL job tracking and alerting on failure

### Security
- Environment variables for secrets
- No API keys in code
- HTTPS only in production
- Database not exposed publicly

### Maintainability
- Type hints in Python code
- Go interfaces for testability
- Database migrations for schema changes
- Comprehensive logging

---

## Open Questions / Future Considerations

1. **Real-time updates during games?** - Currently scoped as daily only
2. **Mobile app?** - Could add React Native or Flutter later
3. **Multi-user support?** - Currently single user, could add auth later
4. **Paid data sources?** - Elite Prospects, Evolving Hockey have more data
5. **Goalie projections?** - More volatile, may need different approach
6. **Prospect projections?** - Limited NHL data, would need junior stats
7. **Playoff projections?** - Different dynamics than regular season
8. **Integration with fantasy platforms?** - Yahoo/ESPN APIs for roster sync
