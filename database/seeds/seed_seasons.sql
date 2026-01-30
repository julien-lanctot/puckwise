-- Seed NHL Seasons (2007-2008 through 2025-2026)
-- Includes approximate regular season dates

INSERT INTO seasons (season_id, start_year, end_year, regular_season_start, regular_season_end, games_in_season, is_current) VALUES
-- Historical seasons
('20072008', 2007, 2008, '2007-09-29', '2008-04-06', 82, false),
('20082009', 2008, 2009, '2008-10-04', '2009-04-12', 82, false),
('20092010', 2009, 2010, '2009-10-01', '2010-04-11', 82, false),
('20102011', 2010, 2011, '2010-10-07', '2011-04-10', 82, false),
('20112012', 2011, 2012, '2011-10-06', '2012-04-07', 82, false),
('20122013', 2012, 2013, '2013-01-19', '2013-04-28', 48, false), -- Lockout shortened season
('20132014', 2013, 2014, '2013-10-01', '2014-04-13', 82, false),
('20142015', 2014, 2015, '2014-10-08', '2015-04-11', 82, false),
('20152016', 2015, 2016, '2015-10-07', '2016-04-10', 82, false),
('20162017', 2016, 2017, '2016-10-12', '2017-04-09', 82, false),
('20172018', 2017, 2018, '2017-10-04', '2018-04-08', 82, false),
('20182019', 2018, 2019, '2018-10-03', '2019-04-06', 82, false),
('20192020', 2019, 2020, '2019-10-02', '2020-03-11', 71, false), -- COVID shortened, varies by team (69-71 games)
('20202021', 2020, 2021, '2021-01-13', '2021-05-19', 56, false), -- COVID shortened season
('20212022', 2021, 2022, '2021-10-12', '2022-04-29', 82, false),
('20222023', 2022, 2023, '2022-10-07', '2023-04-14', 82, false),
('20232024', 2023, 2024, '2023-10-10', '2024-04-18', 82, false),

-- Current season
('20242025', 2024, 2025, '2024-10-08', '2025-04-17', 82, true),

-- Future season placeholder
('20252026', 2025, 2026, '2025-10-08', '2026-04-17', 82, false)

ON CONFLICT (season_id) DO UPDATE SET
    regular_season_start = EXCLUDED.regular_season_start,
    regular_season_end = EXCLUDED.regular_season_end,
    games_in_season = EXCLUDED.games_in_season,
    is_current = EXCLUDED.is_current,
    updated_at = NOW();

-- Update current season flag (ensure only one is current)
UPDATE seasons SET is_current = false WHERE season_id != '20242025';
UPDATE seasons SET is_current = true WHERE season_id = '20242025';
