#!/bin/bash
set -e

# Enable TimescaleDB extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS timescaledb;

    -- Verify TimescaleDB is installed
    SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';
EOSQL

echo "TimescaleDB extension enabled successfully"
