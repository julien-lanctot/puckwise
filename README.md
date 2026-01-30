# Puckwise - Hockey Fantasy Analytics

Fantasy hockey analytics platform — player projections, regression detection, and trade analysis powered by NHL data and machine learning.

## Tech Stack

- **Database:** PostgreSQL 15 + TimescaleDB
- **ETL/ML:** Python 3.11+ (pandas, scikit-learn, XGBoost)
- **API:** Go 1.22+ with Chi router
- **Frontend:** React 18+ with Vite, TypeScript, Tailwind

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Go 1.22+
- Python 3.11+
- Node.js 20+
- golang-migrate CLI

### 1. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings (defaults work for local dev)
```

### 2. Start Database

```bash
# Start TimescaleDB
docker-compose up -d

# Verify it's running
docker-compose ps
```

### 3. Run Migrations

```bash
# Install golang-migrate if needed
# macOS: brew install golang-migrate
# Windows: scoop install migrate
# Go: go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Run all migrations
./database/scripts/run-migrations.sh up

# Load seed data (teams + seasons)
./database/scripts/run-migrations.sh seed
```

### 4. Verify Setup

```bash
# Connect to database
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics

# Check tables
\dt

# Check TimescaleDB hypertables
SELECT * FROM timescaledb_information.hypertables;

# Check seed data
SELECT COUNT(*) FROM teams;
SELECT COUNT(*) FROM seasons;
```

## Project Structure

```
puckwise/
├── database/
│   ├── migrations/     # SQL migration files
│   ├── seeds/          # Seed data (teams, seasons)
│   └── scripts/        # Database utilities
├── etl/                # Python ETL pipeline
├── ml/                 # Python ML models
├── backend/            # Go API
├── frontend/           # React app
├── docker-compose.yml
├── REQUIREMENTS.md     # Full requirements spec
└── CLAUDE.md           # Project context for AI
```

## Database Schema

### Core Tables

| Table | Description |
|-------|-------------|
| `teams` | NHL team reference data |
| `players` | Player biographical info |
| `seasons` | Season metadata |
| `games` | Game schedule and results |
| `skater_game_logs` | Game-by-game skater stats (hypertable) |
| `goalie_game_logs` | Game-by-game goalie stats (hypertable) |
| `skater_season_stats` | Aggregated season stats |
| `goalie_season_stats` | Aggregated goalie stats |
| `skater_advanced_stats` | MoneyPuck advanced metrics |
| `player_projections` | ML model predictions |
| `fantasy_leagues` | League configurations |
| `fantasy_teams` | Teams in leagues |
| `fantasy_rosters` | Player assignments |
| `etl_runs` | ETL job tracking |

### TimescaleDB Features

- Game logs use hypertables partitioned by `game_date`
- Automatic compression after 1 year
- Optimized for time-series queries

## Migration Commands

```bash
# Run all pending migrations
./database/scripts/run-migrations.sh up

# Roll back last migration
./database/scripts/run-migrations.sh down 1

# Check current version
./database/scripts/run-migrations.sh version

# Create new migration
./database/scripts/run-migrations.sh create add_new_feature

# Reset database (destructive!)
./database/scripts/run-migrations.sh reset

# Load seed data
./database/scripts/run-migrations.sh seed
```

## Development Status

- [x] Phase 1: Database & Infrastructure
- [ ] Phase 2: ETL Pipeline (Python)
- [ ] Phase 3: ML Pipeline (Python)
- [ ] Phase 4: API (Go)
- [ ] Phase 5: Frontend (React)
- [ ] Phase 6: Deployment

## Data Sources

- **NHL API:** Player data, game logs, rosters (2008-present)
- **MoneyPuck:** Advanced stats (xG, Corsi, WAR, etc.)

## License

Private - Personal use only
