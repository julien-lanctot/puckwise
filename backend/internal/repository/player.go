package repository

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

type PlayerRepo struct {
	pool *pgxpool.Pool
}

// ListPlayers returns a paginated, filterable list of players.
// Filters: position, team_id, search (name), is_active.
func (r *PlayerRepo) ListPlayers(ctx context.Context, p Pagination, position, search string, teamID int, activeOnly bool) ([]Player, int, error) {
	where := "WHERE 1=1"
	args := []any{}
	argIdx := 1

	if position != "" {
		where += fmt.Sprintf(" AND p.position = $%d", argIdx)
		args = append(args, position)
		argIdx++
	}
	if teamID > 0 {
		where += fmt.Sprintf(" AND p.current_team_id = $%d", argIdx)
		args = append(args, teamID)
		argIdx++
	}
	if search != "" {
		where += fmt.Sprintf(" AND p.name ILIKE $%d", argIdx)
		args = append(args, "%"+search+"%")
		argIdx++
	}
	if activeOnly {
		where += " AND p.is_active = true"
	}

	// Count total matching rows.
	countQuery := "SELECT COUNT(*) FROM players p " + where
	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("counting players: %w", err)
	}

	// Fetch page.
	query := `
		SELECT p.id, p.nhl_id, p.name, p.first_name, p.last_name,
		       p.position, p.position_type, p.birth_date, p.birth_country,
		       p.height_cm, p.weight_kg, p.shoots, p.current_team_id,
		       p.is_active, p.headshot_url, p.created_at, p.updated_at,
		       t.name, t.abbreviation
		FROM players p
		LEFT JOIN teams t ON t.id = p.current_team_id
		` + where + `
		ORDER BY p.name ASC
		LIMIT $` + fmt.Sprintf("%d", argIdx) + ` OFFSET $` + fmt.Sprintf("%d", argIdx+1)

	args = append(args, p.PerPage, p.Offset())

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("querying players: %w", err)
	}
	defer rows.Close()

	players := make([]Player, 0, p.PerPage)
	for rows.Next() {
		var pl Player
		if err := rows.Scan(
			&pl.ID, &pl.NhlID, &pl.Name, &pl.FirstName, &pl.LastName,
			&pl.Position, &pl.PositionType, &pl.BirthDate, &pl.BirthCountry,
			&pl.HeightCM, &pl.WeightKG, &pl.Shoots, &pl.CurrentTeamID,
			&pl.IsActive, &pl.HeadshotURL, &pl.CreatedAt, &pl.UpdatedAt,
			&pl.TeamName, &pl.TeamAbbrev,
		); err != nil {
			return nil, 0, fmt.Errorf("scanning player: %w", err)
		}
		players = append(players, pl)
	}
	if err := rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("iterating players: %w", err)
	}

	return players, total, nil
}

// GetPlayer returns full player detail with latest projection, season stats, and advanced stats.
func (r *PlayerRepo) GetPlayer(ctx context.Context, id int) (*PlayerDetail, error) {
	// 1. Base player data.
	var pl Player
	err := r.pool.QueryRow(ctx, `
		SELECT p.id, p.nhl_id, p.name, p.first_name, p.last_name,
		       p.position, p.position_type, p.birth_date, p.birth_country,
		       p.height_cm, p.weight_kg, p.shoots, p.current_team_id,
		       p.is_active, p.headshot_url, p.created_at, p.updated_at,
		       t.name, t.abbreviation
		FROM players p
		LEFT JOIN teams t ON t.id = p.current_team_id
		WHERE p.id = $1`, id,
	).Scan(
		&pl.ID, &pl.NhlID, &pl.Name, &pl.FirstName, &pl.LastName,
		&pl.Position, &pl.PositionType, &pl.BirthDate, &pl.BirthCountry,
		&pl.HeightCM, &pl.WeightKG, &pl.Shoots, &pl.CurrentTeamID,
		&pl.IsActive, &pl.HeadshotURL, &pl.CreatedAt, &pl.UpdatedAt,
		&pl.TeamName, &pl.TeamAbbrev,
	)
	if err != nil {
		return nil, fmt.Errorf("getting player %d: %w", id, err)
	}

	detail := &PlayerDetail{Player: pl}

	// 2. Season stats (last 5 seasons).
	statsRows, err := r.pool.Query(ctx, `
		SELECT ss.id, ss.season_id, ss.games_played, ss.goals, ss.assists,
		       ss.points, ss.plus_minus, ss.pim, ss.shots, ss.pp_points,
		       ss.hits, ss.blocks, ss.toi_per_game_seconds,
		       ss.shooting_pct, ss.points_per_game,
		       t.abbreviation
		FROM skater_season_stats ss
		LEFT JOIN teams t ON t.id = ss.team_id
		WHERE ss.player_id = $1
		ORDER BY ss.season_id DESC
		LIMIT 5`, id)
	if err != nil {
		return nil, fmt.Errorf("getting season stats for player %d: %w", id, err)
	}
	defer statsRows.Close()

	detail.SeasonStats = make([]SkaterSeasonStats, 0, 5)
	for statsRows.Next() {
		var s SkaterSeasonStats
		if err := statsRows.Scan(
			&s.ID, &s.SeasonID, &s.GamesPlayed, &s.Goals, &s.Assists,
			&s.Points, &s.PlusMinus, &s.PIM, &s.Shots, &s.PPPoints,
			&s.Hits, &s.Blocks, &s.TOIPerGameS,
			&s.ShootingPct, &s.PointsPerGP,
			&s.TeamAbbrev,
		); err != nil {
			return nil, fmt.Errorf("scanning season stat: %w", err)
		}
		detail.SeasonStats = append(detail.SeasonStats, s)
	}
	if err := statsRows.Err(); err != nil {
		return nil, fmt.Errorf("iterating season stats: %w", err)
	}

	// 3. Advanced stats (latest season, all situation).
	advRows, err := r.pool.Query(ctx, `
		SELECT id, season_id, situation, games_played,
		       xg, goals_above_expected, cf_pct, ff_pct, pdo,
		       war, offensive_war, defensive_war,
		       shooting_pct, on_ice_shooting_pct, on_ice_save_pct,
		       goals_per_60, assists_per_60, points_per_60, oz_start_pct
		FROM skater_advanced_stats
		WHERE player_id = $1
		ORDER BY season_id DESC, situation
		LIMIT 10`, id)
	if err != nil {
		return nil, fmt.Errorf("getting advanced stats for player %d: %w", id, err)
	}
	defer advRows.Close()

	detail.AdvancedStats = make([]SkaterAdvancedStats, 0, 10)
	for advRows.Next() {
		var a SkaterAdvancedStats
		if err := advRows.Scan(
			&a.ID, &a.SeasonID, &a.Situation, &a.GamesPlayed,
			&a.XG, &a.GoalsAboveExpect, &a.CFPct, &a.FFPct, &a.PDO,
			&a.WAR, &a.OffensiveWAR, &a.DefensiveWAR,
			&a.ShootingPct, &a.OnIceShootingPct, &a.OnIceSavePct,
			&a.GoalsP60, &a.AssistsP60, &a.PointsP60, &a.OZStartPct,
		); err != nil {
			return nil, fmt.Errorf("scanning advanced stat: %w", err)
		}
		detail.AdvancedStats = append(detail.AdvancedStats, a)
	}
	if err := advRows.Err(); err != nil {
		return nil, fmt.Errorf("iterating advanced stats: %w", err)
	}

	// 4. Latest projection.
	var proj PlayerProjection
	err = r.pool.QueryRow(ctx, `
		SELECT id, player_id, season_id, projection_date, projection_type,
		       projected_games, projected_goals, projected_assists, projected_points,
		       projected_ppp, projected_shots,
		       confidence_low, confidence_high,
		       fantasy_points, fantasy_rank,
		       regression_flag, regression_score, regression_reasons,
		       model_version, model_type
		FROM latest_projections
		WHERE player_id = $1 AND projection_type = 'season'
		LIMIT 1`, id,
	).Scan(
		&proj.ID, &proj.PlayerID, &proj.SeasonID, &proj.ProjectionDate, &proj.ProjectionType,
		&proj.ProjectedGames, &proj.ProjectedGoals, &proj.ProjectedAssists, &proj.ProjectedPoints,
		&proj.ProjectedPPP, &proj.ProjectedShots,
		&proj.ConfidenceLow, &proj.ConfidenceHigh,
		&proj.FantasyPoints, &proj.FantasyRank,
		&proj.RegressionFlag, &proj.RegressionScore, &proj.RegressionReason,
		&proj.ModelVersion, &proj.ModelType,
	)
	if err == nil {
		detail.Projection = &proj
	}
	// If no projection found, that's fine — leave nil.

	return detail, nil
}

// GetPlayerGameLog returns paginated game log entries for a player.
func (r *PlayerRepo) GetPlayerGameLog(ctx context.Context, playerID int, p Pagination, seasonID string) ([]SkaterGameLog, int, error) {
	where := "WHERE gl.player_id = $1"
	args := []any{playerID}
	argIdx := 2

	if seasonID != "" {
		where += fmt.Sprintf(" AND g.season_id = $%d", argIdx)
		args = append(args, seasonID)
		argIdx++
	}

	// Count.
	countQuery := `
		SELECT COUNT(*)
		FROM skater_game_logs gl
		JOIN games g ON g.id = gl.game_id
		` + where
	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("counting game logs: %w", err)
	}

	// Fetch.
	query := `
		SELECT gl.id, gl.game_id, gl.game_date,
		       gl.goals, gl.assists, gl.points, gl.plus_minus, gl.pim,
		       gl.shots, gl.toi_seconds,
		       gl.pp_goals, gl.pp_assists,
		       gl.hits, gl.blocks, gl.is_home,
		       t.abbreviation,
		       CASE WHEN gl.is_home THEN at.abbreviation ELSE ht.abbreviation END
		FROM skater_game_logs gl
		JOIN games g ON g.id = gl.game_id
		JOIN teams t ON t.id = gl.team_id
		JOIN teams ht ON ht.id = g.home_team_id
		JOIN teams at ON at.id = g.away_team_id
		` + where + `
		ORDER BY gl.game_date DESC
		LIMIT $` + fmt.Sprintf("%d", argIdx) + ` OFFSET $` + fmt.Sprintf("%d", argIdx+1)

	args = append(args, p.PerPage, p.Offset())

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("querying game logs: %w", err)
	}
	defer rows.Close()

	logs := make([]SkaterGameLog, 0, p.PerPage)
	for rows.Next() {
		var gl SkaterGameLog
		if err := rows.Scan(
			&gl.ID, &gl.GameID, &gl.GameDate,
			&gl.Goals, &gl.Assists, &gl.Points, &gl.PlusMinus, &gl.PIM,
			&gl.Shots, &gl.TOISeconds,
			&gl.PPGoals, &gl.PPAssists,
			&gl.Hits, &gl.Blocks, &gl.IsHome,
			&gl.TeamAbbrev, &gl.OpponentAbbrev,
		); err != nil {
			return nil, 0, fmt.Errorf("scanning game log: %w", err)
		}
		logs = append(logs, gl)
	}
	if err := rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("iterating game logs: %w", err)
	}

	return logs, total, nil
}
