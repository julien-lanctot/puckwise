-- Goalie game logs: Game-by-game stats for goalies (TimescaleDB hypertable)
CREATE TABLE goalie_game_logs (
    id BIGSERIAL,
    player_id INTEGER NOT NULL REFERENCES players(id),
    game_id INTEGER NOT NULL REFERENCES games(id),
    game_date DATE NOT NULL, -- Denormalized for TimescaleDB partitioning
    team_id INTEGER NOT NULL REFERENCES teams(id),

    -- Game result
    decision VARCHAR(2), -- W, L, O (OT loss)

    -- Core goalie stats
    goals_against INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    shots_against INTEGER DEFAULT 0,
    save_pct DECIMAL(5,3),

    -- Time on ice (in seconds)
    toi_seconds INTEGER DEFAULT 0,

    -- Additional stats
    shutout BOOLEAN DEFAULT false,
    goals INTEGER DEFAULT 0, -- Goalie goals (rare)
    assists INTEGER DEFAULT 0, -- Goalie assists
    pim INTEGER DEFAULT 0,

    -- Game context
    is_home BOOLEAN NOT NULL,
    is_starter BOOLEAN DEFAULT true,

    -- Even strength
    even_saves INTEGER DEFAULT 0,
    even_shots_against INTEGER DEFAULT 0,

    -- Power play (against)
    pp_saves INTEGER DEFAULT 0,
    pp_shots_against INTEGER DEFAULT 0,

    -- Short handed
    sh_saves INTEGER DEFAULT 0,
    sh_shots_against INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (id, game_date)
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('goalie_game_logs', 'game_date', chunk_time_interval => INTERVAL '1 year');

-- Indexes
CREATE INDEX idx_goalie_logs_player_date ON goalie_game_logs(player_id, game_date DESC);
CREATE INDEX idx_goalie_logs_game ON goalie_game_logs(game_id);
CREATE INDEX idx_goalie_logs_team ON goalie_game_logs(team_id);
CREATE UNIQUE INDEX idx_goalie_logs_unique ON goalie_game_logs(player_id, game_id, game_date);

-- Compression policy
ALTER TABLE goalie_game_logs SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'player_id'
);

SELECT add_compression_policy('goalie_game_logs', INTERVAL '1 year');

COMMENT ON TABLE goalie_game_logs IS 'Game-by-game statistics for NHL goalies (TimescaleDB hypertable)';
