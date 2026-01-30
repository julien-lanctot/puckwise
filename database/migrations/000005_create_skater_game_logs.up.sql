-- Skater game logs: Game-by-game stats for skaters (TimescaleDB hypertable)
CREATE TABLE skater_game_logs (
    id BIGSERIAL,
    player_id INTEGER NOT NULL REFERENCES players(id),
    game_id INTEGER NOT NULL REFERENCES games(id),
    game_date DATE NOT NULL, -- Denormalized for TimescaleDB partitioning
    team_id INTEGER NOT NULL REFERENCES teams(id),

    -- Basic stats
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    pim INTEGER DEFAULT 0, -- Penalty minutes

    -- Shooting
    shots INTEGER DEFAULT 0,
    shooting_pct DECIMAL(5,2),

    -- Time on ice (in seconds)
    toi_seconds INTEGER DEFAULT 0,
    toi_even_seconds INTEGER DEFAULT 0,
    toi_pp_seconds INTEGER DEFAULT 0,
    toi_sh_seconds INTEGER DEFAULT 0,

    -- Special teams
    pp_goals INTEGER DEFAULT 0,
    pp_assists INTEGER DEFAULT 0,
    sh_goals INTEGER DEFAULT 0,
    sh_assists INTEGER DEFAULT 0,

    -- Other counting stats
    hits INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    giveaways INTEGER DEFAULT 0,
    takeaways INTEGER DEFAULT 0,
    faceoff_wins INTEGER DEFAULT 0,
    faceoff_losses INTEGER DEFAULT 0,

    -- Game context
    is_home BOOLEAN NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (id, game_date)
);

-- Convert to TimescaleDB hypertable partitioned by game_date
SELECT create_hypertable('skater_game_logs', 'game_date', chunk_time_interval => INTERVAL '1 year');

-- Indexes for common queries
CREATE INDEX idx_skater_logs_player_date ON skater_game_logs(player_id, game_date DESC);
CREATE INDEX idx_skater_logs_game ON skater_game_logs(game_id);
CREATE INDEX idx_skater_logs_team ON skater_game_logs(team_id);
CREATE INDEX idx_skater_logs_player_game ON skater_game_logs(player_id, game_id);

-- Unique constraint (no duplicate entries)
CREATE UNIQUE INDEX idx_skater_logs_unique ON skater_game_logs(player_id, game_id);

-- Enable compression for older data (after 1 year)
ALTER TABLE skater_game_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'player_id'
);

SELECT add_compression_policy('skater_game_logs', INTERVAL '1 year');

COMMENT ON TABLE skater_game_logs IS 'Game-by-game statistics for NHL skaters (TimescaleDB hypertable)';
