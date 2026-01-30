-- Player projections: ML model outputs
CREATE TABLE player_projections (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season_id VARCHAR(8) NOT NULL REFERENCES seasons(season_id),
    projection_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Projection type
    projection_type VARCHAR(20) NOT NULL DEFAULT 'season', -- 'season', 'rolling_14d', 'rolling_30d'

    -- Projected stats (skaters)
    projected_games INTEGER,
    projected_goals DECIMAL(5,1),
    projected_assists DECIMAL(5,1),
    projected_points DECIMAL(5,1),
    projected_ppp DECIMAL(5,1), -- Power play points
    projected_shots DECIMAL(6,1),
    projected_hits DECIMAL(6,1),
    projected_blocks DECIMAL(6,1),

    -- Projected stats (goalies)
    projected_wins DECIMAL(4,1),
    projected_gaa DECIMAL(4,2),
    projected_save_pct DECIMAL(5,3),
    projected_shutouts DECIMAL(3,1),

    -- Confidence intervals
    confidence_low DECIMAL(5,1), -- 10th percentile for points
    confidence_high DECIMAL(5,1), -- 90th percentile for points

    -- Fantasy value
    fantasy_points DECIMAL(7,1), -- Based on league settings
    fantasy_rank INTEGER, -- Overall rank

    -- Regression indicators
    regression_flag VARCHAR(20), -- 'buy_low', 'sell_high', null
    regression_score DECIMAL(4,1), -- -10 to +10, negative=buy_low, positive=sell_high
    regression_reasons JSONB, -- Array of reasons

    -- Model metadata
    model_version VARCHAR(20),
    model_type VARCHAR(50), -- 'xgboost', 'ridge', 'ensemble'

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(player_id, season_id, projection_date, projection_type)
);

-- Indexes
CREATE INDEX idx_projections_player ON player_projections(player_id);
CREATE INDEX idx_projections_season ON player_projections(season_id);
CREATE INDEX idx_projections_date ON player_projections(projection_date DESC);
CREATE INDEX idx_projections_type ON player_projections(projection_type);
CREATE INDEX idx_projections_rank ON player_projections(fantasy_rank);
CREATE INDEX idx_projections_regression ON player_projections(regression_flag) WHERE regression_flag IS NOT NULL;
CREATE INDEX idx_projections_latest ON player_projections(player_id, season_id, projection_type, projection_date DESC);

-- View for latest projections
CREATE VIEW latest_projections AS
SELECT DISTINCT ON (player_id, season_id, projection_type)
    *
FROM player_projections
ORDER BY player_id, season_id, projection_type, projection_date DESC;

COMMENT ON TABLE player_projections IS 'ML model predictions for player performance';
COMMENT ON VIEW latest_projections IS 'Most recent projection for each player/season/type combination';
