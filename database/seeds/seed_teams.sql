-- Seed NHL Teams (all 32 current teams + historical teams)
-- NHL team IDs from NHL API

INSERT INTO teams (nhl_id, abbreviation, name, full_name, conference, division, active) VALUES
-- Eastern Conference - Atlantic Division
(1, 'NJD', 'Devils', 'New Jersey Devils', 'Eastern', 'Atlantic', true),
(2, 'NYI', 'Islanders', 'New York Islanders', 'Eastern', 'Metropolitan', true),
(3, 'NYR', 'Rangers', 'New York Rangers', 'Eastern', 'Metropolitan', true),
(4, 'PHI', 'Flyers', 'Philadelphia Flyers', 'Eastern', 'Metropolitan', true),
(5, 'PIT', 'Penguins', 'Pittsburgh Penguins', 'Eastern', 'Metropolitan', true),
(6, 'BOS', 'Bruins', 'Boston Bruins', 'Eastern', 'Atlantic', true),
(7, 'BUF', 'Sabres', 'Buffalo Sabres', 'Eastern', 'Atlantic', true),
(8, 'MTL', 'Canadiens', 'Montreal Canadiens', 'Eastern', 'Atlantic', true),
(9, 'OTT', 'Senators', 'Ottawa Senators', 'Eastern', 'Atlantic', true),
(10, 'TOR', 'Maple Leafs', 'Toronto Maple Leafs', 'Eastern', 'Atlantic', true),

-- Eastern Conference - Metropolitan Division
(12, 'CAR', 'Hurricanes', 'Carolina Hurricanes', 'Eastern', 'Metropolitan', true),
(13, 'FLA', 'Panthers', 'Florida Panthers', 'Eastern', 'Atlantic', true),
(14, 'TBL', 'Lightning', 'Tampa Bay Lightning', 'Eastern', 'Atlantic', true),
(15, 'WSH', 'Capitals', 'Washington Capitals', 'Eastern', 'Metropolitan', true),
(16, 'CHI', 'Blackhawks', 'Chicago Blackhawks', 'Western', 'Central', true),
(17, 'DET', 'Red Wings', 'Detroit Red Wings', 'Eastern', 'Atlantic', true),
(18, 'NSH', 'Predators', 'Nashville Predators', 'Western', 'Central', true),
(19, 'STL', 'Blues', 'St. Louis Blues', 'Western', 'Central', true),

-- Western Conference - Central Division
(20, 'CGY', 'Flames', 'Calgary Flames', 'Western', 'Pacific', true),
(21, 'COL', 'Avalanche', 'Colorado Avalanche', 'Western', 'Central', true),
(22, 'EDM', 'Oilers', 'Edmonton Oilers', 'Western', 'Pacific', true),
(23, 'VAN', 'Canucks', 'Vancouver Canucks', 'Western', 'Pacific', true),
(24, 'ANA', 'Ducks', 'Anaheim Ducks', 'Western', 'Pacific', true),
(25, 'DAL', 'Stars', 'Dallas Stars', 'Western', 'Central', true),
(26, 'LAK', 'Kings', 'Los Angeles Kings', 'Western', 'Pacific', true),
(28, 'SJS', 'Sharks', 'San Jose Sharks', 'Western', 'Pacific', true),
(29, 'CBJ', 'Blue Jackets', 'Columbus Blue Jackets', 'Eastern', 'Metropolitan', true),
(30, 'MIN', 'Wild', 'Minnesota Wild', 'Western', 'Central', true),

-- Western Conference - Pacific Division
(52, 'WPG', 'Jets', 'Winnipeg Jets', 'Western', 'Central', true),
(53, 'ARI', 'Coyotes', 'Arizona Coyotes', 'Western', 'Central', true), -- Now Utah
(54, 'VGK', 'Golden Knights', 'Vegas Golden Knights', 'Western', 'Pacific', true),
(55, 'SEA', 'Kraken', 'Seattle Kraken', 'Western', 'Pacific', true),

-- Utah Hockey Club (new 2024-25, formerly Arizona)
(59, 'UTA', 'Utah HC', 'Utah Hockey Club', 'Western', 'Central', true)

ON CONFLICT (nhl_id) DO UPDATE SET
    abbreviation = EXCLUDED.abbreviation,
    name = EXCLUDED.name,
    full_name = EXCLUDED.full_name,
    conference = EXCLUDED.conference,
    division = EXCLUDED.division,
    active = EXCLUDED.active,
    updated_at = NOW();

-- Historical team entries (for tracking relocated/renamed teams)
-- Atlanta Thrashers (became Winnipeg Jets in 2011)
INSERT INTO teams (nhl_id, abbreviation, name, full_name, conference, division, active) VALUES
(11, 'ATL', 'Thrashers', 'Atlanta Thrashers', 'Eastern', 'Southeast', false)
ON CONFLICT (nhl_id) DO UPDATE SET active = false, updated_at = NOW();

-- Phoenix Coyotes (renamed to Arizona in 2014)
-- Note: Using same nhl_id (53) as Arizona since it's the same franchise
