-- Skater season stats: Aggregated stats per season
CREATE TABLE skater_season_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id VARCHAR(8) NOT NULL REFERENCES seasons(season_id),
    team_id INTEGER REFERENCES teams(id), -- Primary team for the season

    -- Games
    games_played INTEGER DEFAULT 0,

    -- Scoring
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    plus_minus INTEGER DEFAULT 0,
    pim INTEGER DEFAULT 0,

    -- Per-game rates
    goals_per_game DECIMAL(5,3),
    assists_per_game DECIMAL(5,3),
    points_per_game DECIMAL(5,3),

    -- Shooting
    shots INTEGER DEFAULT 0,
    shooting_pct DECIMAL(5,2),

    -- Time on ice (in seconds, totals)
    toi_total_seconds INTEGER DEFAULT 0,
    toi_per_game_seconds INTEGER DEFAULT 0,
    toi_even_seconds INTEGER DEFAULT 0,
    toi_pp_seconds INTEGER DEFAULT 0,
    toi_sh_seconds INTEGER DEFAULT 0,

    -- Special teams
    pp_goals INTEGER DEFAULT 0,
    pp_assists INTEGER DEFAULT 0,
    pp_points INTEGER DEFAULT 0,
    sh_goals INTEGER DEFAULT 0,
    sh_assists INTEGER DEFAULT 0,
    sh_points INTEGER DEFAULT 0,

    -- Other
    hits INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    giveaways INTEGER DEFAULT 0,
    takeaways INTEGER DEFAULT 0,
    faceoff_wins INTEGER DEFAULT 0,
    faceoff_losses INTEGER DEFAULT 0,
    faceoff_pct DECIMAL(5,2),

    -- Game winning goals
    game_winning_goals INTEGER DEFAULT 0,
    overtime_goals INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id, season_id)
);

-- Indexes
CREATE INDEX idx_skater_season_player ON skater_season_stats(player_id);
CREATE INDEX idx_skater_season_season ON skater_season_stats(season_id);
CREATE INDEX idx_skater_season_team ON skater_season_stats(team_id);
CREATE INDEX idx_skater_season_points ON skater_season_stats(points DESC);

-- Goalie season stats: Aggregated stats per season
CREATE TABLE goalie_season_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id VARCHAR(8) NOT NULL REFERENCES seasons(season_id),
    team_id INTEGER REFERENCES teams(id),

    -- Games
    games_played INTEGER DEFAULT 0,
    games_started INTEGER DEFAULT 0,

    -- Record
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ot_losses INTEGER DEFAULT 0,

    -- Core stats
    goals_against INTEGER DEFAULT 0,
    saves INTEGER DEFAULT 0,
    shots_against INTEGER DEFAULT 0,
    save_pct DECIMAL(5,3),
    goals_against_avg DECIMAL(4,2),
    shutouts INTEGER DEFAULT 0,

    -- Time on ice
    toi_total_seconds INTEGER DEFAULT 0,

    -- Quality starts (future enhancement)
    quality_starts INTEGER DEFAULT 0,

    -- Goalie points (rare)
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    pim INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id, season_id)
);

-- Indexes
CREATE INDEX idx_goalie_season_player ON goalie_season_stats(player_id);
CREATE INDEX idx_goalie_season_season ON goalie_season_stats(season_id);
CREATE INDEX idx_goalie_season_team ON goalie_season_stats(team_id);
CREATE INDEX idx_goalie_season_wins ON goalie_season_stats(wins DESC);

COMMENT ON TABLE skater_season_stats IS 'Aggregated season totals for NHL skaters';
COMMENT ON TABLE goalie_season_stats IS 'Aggregated season totals for NHL goalies';
