-- Enable trigram extension for fuzzy search (if not exists)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Players table: Player biographical information
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    nhl_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(150) NOT NULL,
    first_name VARCHAR(75),
    last_name VARCHAR(75),
    position VARCHAR(5) NOT NULL, -- C, LW, RW, D, G
    position_type VARCHAR(20), -- Forward, Defenseman, Goalie
    birth_date DATE,
    birth_city VARCHAR(100),
    birth_country VARCHAR(50),
    nationality VARCHAR(50),
    height_cm INTEGER,
    weight_kg INTEGER,
    shoots VARCHAR(1), -- L, R
    current_team_id INTEGER REFERENCES teams(id),
    is_active BOOLEAN DEFAULT true,
    nhl_debut_date DATE,
    headshot_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_players_nhl_id ON players(nhl_id);
CREATE INDEX idx_players_name ON players(name);
CREATE INDEX idx_players_name_trgm ON players USING gin(name gin_trgm_ops);
CREATE INDEX idx_players_position ON players(position);
CREATE INDEX idx_players_current_team ON players(current_team_id);
CREATE INDEX idx_players_active ON players(is_active) WHERE is_active = true;

COMMENT ON TABLE players IS 'NHL player biographical and reference data';
