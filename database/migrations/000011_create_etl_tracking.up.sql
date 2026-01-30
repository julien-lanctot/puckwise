-- ETL run tracking
CREATE TABLE etl_runs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- 'initial_load', 'daily_update', 'backfill'

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'

    -- Scope
    season_id VARCHAR(8),
    date_from DATE,
    date_to DATE,

    -- Results
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,

    -- Details
    details JSONB, -- Additional job-specific details
    error_message TEXT,
    error_details JSONB,

    -- Environment
    hostname VARCHAR(100),
    worker_id VARCHAR(50),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_etl_runs_job_name ON etl_runs(job_name);
CREATE INDEX idx_etl_runs_status ON etl_runs(status);
CREATE INDEX idx_etl_runs_started ON etl_runs(started_at DESC);
CREATE INDEX idx_etl_runs_job_started ON etl_runs(job_name, started_at DESC);

-- Data source sync tracking
CREATE TABLE data_source_sync (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(50) NOT NULL, -- 'nhl_api', 'moneypuck'
    entity_type VARCHAR(50) NOT NULL, -- 'players', 'game_logs', 'advanced_stats'

    -- Last successful sync
    last_sync_at TIMESTAMPTZ,
    last_sync_season VARCHAR(8),
    last_sync_date DATE,

    -- Incremental sync cursor
    cursor_value VARCHAR(100), -- Could be a date, ID, or other cursor

    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'syncing', 'synced', 'error'
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_name, entity_type)
);

CREATE INDEX idx_data_sync_source ON data_source_sync(source_name);
CREATE INDEX idx_data_sync_status ON data_source_sync(status);

-- Helper function to update ETL run on completion
CREATE OR REPLACE FUNCTION complete_etl_run(
    p_run_id INTEGER,
    p_status VARCHAR(20),
    p_records_processed INTEGER DEFAULT NULL,
    p_records_inserted INTEGER DEFAULT NULL,
    p_records_updated INTEGER DEFAULT NULL,
    p_records_failed INTEGER DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_error_details JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE etl_runs SET
        completed_at = NOW(),
        duration_seconds = EXTRACT(EPOCH FROM (NOW() - started_at))::INTEGER,
        status = p_status,
        records_processed = COALESCE(p_records_processed, records_processed),
        records_inserted = COALESCE(p_records_inserted, records_inserted),
        records_updated = COALESCE(p_records_updated, records_updated),
        records_failed = COALESCE(p_records_failed, records_failed),
        error_message = p_error_message,
        error_details = p_error_details
    WHERE id = p_run_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE etl_runs IS 'Tracks ETL job executions and results';
COMMENT ON TABLE data_source_sync IS 'Tracks sync status with external data sources';
