-- Teams table: NHL team reference data
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    nhl_id INTEGER UNIQUE NOT NULL,
    abbreviation VARCHAR(3) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    conference VARCHAR(20),
    division VARCHAR(30),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common lookups
CREATE INDEX idx_teams_abbreviation ON teams(abbreviation);
CREATE INDEX idx_teams_nhl_id ON teams(nhl_id);
CREATE INDEX idx_teams_active ON teams(active) WHERE active = true;

-- Comment on table
COMMENT ON TABLE teams IS 'NHL team reference data including historical teams';
