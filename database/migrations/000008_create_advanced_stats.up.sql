-- Skater advanced stats: MoneyPuck and other advanced metrics
CREATE TABLE skater_advanced_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id VARCHAR(8) NOT NULL REFERENCES seasons(season_id),

    -- Situation (5v5, all, pp, pk)
    situation VARCHAR(10) DEFAULT 'all',

    -- Games/ice time
    games_played INTEGER DEFAULT 0,
    toi_minutes DECIMAL(8,2) DEFAULT 0,

    -- Expected Goals
    xg DECIMAL(6,2), -- Individual expected goals
    xg_per_60 DECIMAL(5,3),
    goals_above_expected DECIMAL(6,2), -- Goals - xG
    on_ice_xg_for DECIMAL(6,2),
    on_ice_xg_against DECIMAL(6,2),
    xg_diff DECIMAL(6,2), -- On-ice xGF - xGA

    -- Corsi (all shot attempts)
    cf INTEGER, -- Corsi for (shot attempts for when on ice)
    ca INTEGER, -- Corsi against
    cf_pct DECIMAL(5,2), -- CF / (CF + CA)
    cf_pct_rel DECIMAL(6,2), -- Relative to team

    -- Fenwick (unblocked shot attempts)
    ff INTEGER,
    fa INTEGER,
    ff_pct DECIMAL(5,2),
    ff_pct_rel DECIMAL(6,2),

    -- Shooting
    individual_cf INTEGER, -- Player's own shot attempts
    shooting_pct DECIMAL(5,2),
    on_ice_shooting_pct DECIMAL(5,2),
    on_ice_save_pct DECIMAL(5,3),

    -- PDO (luck indicator: on-ice sh% + on-ice sv%)
    pdo DECIMAL(6,3), -- Expected ~1.000

    -- Zone starts
    oz_starts INTEGER, -- Offensive zone faceoffs
    dz_starts INTEGER, -- Defensive zone faceoffs
    nz_starts INTEGER, -- Neutral zone faceoffs
    oz_start_pct DECIMAL(5,2), -- OZ / (OZ + DZ)

    -- Quality metrics
    qoc DECIMAL(6,3), -- Quality of competition (avg opponent CF%)
    qot DECIMAL(6,3), -- Quality of teammates (avg teammate CF%)

    -- Wins Above Replacement
    war DECIMAL(5,2),
    offensive_war DECIMAL(5,2),
    defensive_war DECIMAL(5,2),

    -- Primary points
    primary_assists INTEGER DEFAULT 0,
    secondary_assists INTEGER DEFAULT 0,
    first_goals INTEGER DEFAULT 0, -- First goal of the game

    -- Per 60 rates
    goals_per_60 DECIMAL(5,3),
    assists_per_60 DECIMAL(5,3),
    points_per_60 DECIMAL(5,3),
    shots_per_60 DECIMAL(5,3),

    -- Source tracking
    data_source VARCHAR(50) DEFAULT 'moneypuck',
    source_updated_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id, season_id, situation)
);

-- Indexes
CREATE INDEX idx_advanced_player ON skater_advanced_stats(player_id);
CREATE INDEX idx_advanced_season ON skater_advanced_stats(season_id);
CREATE INDEX idx_advanced_situation ON skater_advanced_stats(situation);
CREATE INDEX idx_advanced_xg ON skater_advanced_stats(xg DESC);
CREATE INDEX idx_advanced_war ON skater_advanced_stats(war DESC);
CREATE INDEX idx_advanced_pdo ON skater_advanced_stats(pdo);

-- Team advanced stats
CREATE TABLE team_advanced_stats (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    season_id VARCHAR(8) NOT NULL REFERENCES seasons(season_id),
    situation VARCHAR(10) DEFAULT 'all',

    games_played INTEGER DEFAULT 0,
    toi_minutes DECIMAL(10,2) DEFAULT 0,

    -- Expected goals
    xg_for DECIMAL(8,2),
    xg_against DECIMAL(8,2),
    xg_diff DECIMAL(8,2),
    xg_for_per_60 DECIMAL(5,3),
    xg_against_per_60 DECIMAL(5,3),

    -- Corsi
    cf INTEGER,
    ca INTEGER,
    cf_pct DECIMAL(5,2),

    -- Fenwick
    ff INTEGER,
    fa INTEGER,
    ff_pct DECIMAL(5,2),

    -- Goals
    goals_for INTEGER,
    goals_against INTEGER,
    goals_for_per_game DECIMAL(4,2),
    goals_against_per_game DECIMAL(4,2),

    -- Shooting
    shooting_pct DECIMAL(5,2),
    save_pct DECIMAL(5,3),
    pdo DECIMAL(6,3),

    data_source VARCHAR(50) DEFAULT 'moneypuck',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(team_id, season_id, situation)
);

CREATE INDEX idx_team_advanced_team ON team_advanced_stats(team_id);
CREATE INDEX idx_team_advanced_season ON team_advanced_stats(season_id);

COMMENT ON TABLE skater_advanced_stats IS 'Advanced analytics for skaters from MoneyPuck';
COMMENT ON TABLE team_advanced_stats IS 'Advanced analytics for teams from MoneyPuck';
