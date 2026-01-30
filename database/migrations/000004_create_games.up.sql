-- Games table: NHL game schedule and results
CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    nhl_game_id BIGINT UNIQUE NOT NULL,
    season_id VARCHAR(8) NOT NULL REFERENCES seasons(season_id),
    game_date DATE NOT NULL,
    game_type INTEGER NOT NULL DEFAULT 2, -- 1=preseason, 2=regular, 3=playoffs
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    game_state VARCHAR(20), -- FINAL, LIVE, FUT, etc.
    period INTEGER,
    is_overtime BOOLEAN DEFAULT false,
    is_shootout BOOLEAN DEFAULT false,
    venue VARCHAR(150),
    start_time_utc TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_games_nhl_game_id ON games(nhl_game_id);
CREATE INDEX idx_games_season_id ON games(season_id);
CREATE INDEX idx_games_game_date ON games(game_date);
CREATE INDEX idx_games_home_team ON games(home_team_id);
CREATE INDEX idx_games_away_team ON games(away_team_id);
CREATE INDEX idx_games_season_date ON games(season_id, game_date);
CREATE INDEX idx_games_game_type ON games(game_type);

COMMENT ON TABLE games IS 'NHL game schedule and results';
