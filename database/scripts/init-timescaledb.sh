#!/bin/bash
set -e

# Enable TimescaleDB extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    CREATE EXTENSION IF NOT EXISTS pg_trgm;

    -- Verify extensions are installed
    SELECT extname, extversion FROM pg_extension WHERE extname IN ('timescaledb', 'pg_trgm');
EOSQL

echo "TimescaleDB extension enabled successfully"
