-- Seasons table: NHL season reference data
CREATE TABLE seasons (
    id SERIAL PRIMARY KEY,
    season_id VARCHAR(8) UNIQUE NOT NULL, -- e.g., "20232024"
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    regular_season_start DATE,
    regular_season_end DATE,
    playoffs_start DATE,
    playoffs_end DATE,
    games_in_season INTEGER DEFAULT 82,
    is_current BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_season_years CHECK (end_year = start_year + 1)
);

-- Index for lookups
CREATE INDEX idx_seasons_season_id ON seasons(season_id);
CREATE INDEX idx_seasons_current ON seasons(is_current) WHERE is_current = true;
CREATE INDEX idx_seasons_years ON seasons(start_year, end_year);

COMMENT ON TABLE seasons IS 'NHL season reference data with schedule dates';
