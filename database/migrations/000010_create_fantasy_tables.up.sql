-- Fantasy leagues: League configuration
CREATE TABLE fantasy_leagues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    platform VARCHAR(50), -- 'yahoo', 'espn', 'fantrax', 'custom'

    -- League type
    scoring_type VARCHAR(20) NOT NULL DEFAULT 'points', -- 'points', 'category', 'roto'

    -- Scoring settings (for points leagues)
    scoring_settings JSONB DEFAULT '{
        "goals": 3,
        "assists": 2,
        "plus_minus": 0.5,
        "pim": 0.25,
        "ppp": 1,
        "shp": 1,
        "sog": 0.3,
        "hits": 0.2,
        "blocks": 0.3,
        "wins": 5,
        "saves": 0.2,
        "goals_against": -1,
        "shutouts": 3
    }'::jsonb,

    -- Category settings (for category leagues)
    skater_categories JSONB DEFAULT '["G", "A", "+/-", "PIM", "PPP", "SOG", "HIT", "BLK"]'::jsonb,
    goalie_categories JSONB DEFAULT '["W", "GAA", "SV%", "SO"]'::jsonb,

    -- Roster settings
    roster_positions JSONB DEFAULT '{
        "C": 2,
        "LW": 2,
        "RW": 2,
        "D": 4,
        "G": 2,
        "BN": 4,
        "IR": 2
    }'::jsonb,

    -- League settings
    num_teams INTEGER DEFAULT 12,
    season_id VARCHAR(8) REFERENCES seasons(season_id),

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Fantasy teams: Teams within a league
CREATE TABLE fantasy_teams (
    id SERIAL PRIMARY KEY,
    league_id INTEGER NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    owner_name VARCHAR(100),

    -- Is this my team or another manager's?
    is_my_team BOOLEAN DEFAULT false,

    -- External platform ID
    external_id VARCHAR(100),

    -- Standing
    standing_rank INTEGER,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(league_id, name)
);

-- Fantasy rosters: Player assignments to fantasy teams
CREATE TABLE fantasy_rosters (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES fantasy_teams(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id),

    -- Roster position
    position_slot VARCHAR(10), -- 'C', 'LW', 'RW', 'D', 'G', 'BN', 'IR'

    -- Acquisition
    acquired_date DATE DEFAULT CURRENT_DATE,
    acquisition_type VARCHAR(20) DEFAULT 'draft', -- 'draft', 'trade', 'waiver', 'add'
    acquisition_cost INTEGER, -- Draft pick number or FAAB cost

    is_active BOOLEAN DEFAULT true,
    dropped_date DATE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(team_id, player_id, is_active)
);

-- Indexes
CREATE INDEX idx_fantasy_leagues_season ON fantasy_leagues(season_id);
CREATE INDEX idx_fantasy_leagues_active ON fantasy_leagues(is_active) WHERE is_active = true;

CREATE INDEX idx_fantasy_teams_league ON fantasy_teams(league_id);
CREATE INDEX idx_fantasy_teams_my_team ON fantasy_teams(is_my_team) WHERE is_my_team = true;

CREATE INDEX idx_fantasy_rosters_team ON fantasy_rosters(team_id);
CREATE INDEX idx_fantasy_rosters_player ON fantasy_rosters(player_id);
CREATE INDEX idx_fantasy_rosters_active ON fantasy_rosters(is_active) WHERE is_active = true;

-- Trade history
CREATE TABLE fantasy_trades (
    id SERIAL PRIMARY KEY,
    league_id INTEGER NOT NULL REFERENCES fantasy_leagues(id) ON DELETE CASCADE,
    trade_date TIMESTAMPTZ DEFAULT NOW(),

    -- Teams involved
    team_1_id INTEGER NOT NULL REFERENCES fantasy_teams(id),
    team_2_id INTEGER NOT NULL REFERENCES fantasy_teams(id),

    -- Players involved (JSON arrays of player IDs)
    team_1_gives JSONB NOT NULL, -- [player_id, ...]
    team_2_gives JSONB NOT NULL,

    -- Trade analysis at time of trade
    team_1_value_change DECIMAL(6,1),
    team_2_value_change DECIMAL(6,1),
    analysis_notes TEXT,

    status VARCHAR(20) DEFAULT 'completed', -- 'proposed', 'completed', 'rejected'

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fantasy_trades_league ON fantasy_trades(league_id);
CREATE INDEX idx_fantasy_trades_teams ON fantasy_trades(team_1_id, team_2_id);

COMMENT ON TABLE fantasy_leagues IS 'Fantasy hockey league configurations';
COMMENT ON TABLE fantasy_teams IS 'Teams within fantasy leagues';
COMMENT ON TABLE fantasy_rosters IS 'Player assignments to fantasy teams';
COMMENT ON TABLE fantasy_trades IS 'Trade history and analysis';
