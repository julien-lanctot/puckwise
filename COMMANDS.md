# Puckwise Commands Reference

## Prerequisites

- Docker installed and running
- WSL (Windows Subsystem for Linux)
- Python 3.11+ with venv

## Docker

```bash
# Navigate to project (from WSL)
cd /mnt/c/Users/Julien/Desktop/MobileProjects/puckwise

# Start database container
docker compose up -d

# Check container status
docker ps

# View database tables
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics -c "\dt"

# Connect to database interactively
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics

# Stop containers
docker compose down
```

## Python Virtual Environment

```bash
# Create venv (first time only)
python3 -m venv etl/.venv

# Activate venv
source etl/.venv/bin/activate

# Install dependencies
pip install --upgrade pip && pip install -r etl/requirements.txt

# Verify venv is active
which pip
# Should show: /mnt/c/.../puckwise/etl/.venv/bin/pip
```

## ETL Pipeline

```bash
# Activate venv first
source etl/.venv/bin/activate

# Test database connection
python -c 'from etl.src.db import get_connection; conn = get_connection(); print("Connected")'

# Run initial load (all historical data from 2008)
python -m etl.src.jobs.initial_load

# Run initial load for specific years
python -m etl.src.jobs.initial_load --start-year 2023 --end-year 2024

# Run daily update (once initial load is complete)
python -m etl.src.jobs.daily_update
```

## Database Migrations

```bash
# Migrations are in database/migrations/
# They run automatically via Docker init scripts

# To manually check migration status
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics -c "SELECT * FROM schema_migrations"
```

## Useful Queries

```bash
# Count players
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics -c "SELECT COUNT(*) FROM players"

# Check ETL run history
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics -c "SELECT * FROM etl_runs ORDER BY started_at DESC LIMIT 5"

# View seasons
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics -c "SELECT * FROM seasons"

# View teams
docker exec -it puckwise_db psql -U puckwise -d hockey_analytics -c "SELECT abbreviation, name FROM teams ORDER BY abbreviation"
```
