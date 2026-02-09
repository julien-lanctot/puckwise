package repository

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

type ProjectionRepo struct {
	pool *pgxpool.Pool
}

// GetRankings returns paginated draft rankings from latest projections.
// Filters: position, projection_type.
func (r *ProjectionRepo) GetRankings(ctx context.Context, p Pagination, position, projType string) ([]PlayerProjection, int, error) {
	if projType == "" {
		projType = "season"
	}

	where := "WHERE lp.projection_type = $1"
	args := []any{projType}
	argIdx := 2

	if position != "" {
		where += fmt.Sprintf(" AND pl.position = $%d", argIdx)
		args = append(args, position)
		argIdx++
	}

	countQuery := `
		SELECT COUNT(*)
		FROM latest_projections lp
		JOIN players pl ON pl.id = lp.player_id
		` + where
	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("counting rankings: %w", err)
	}

	query := `
		SELECT lp.id, lp.player_id, lp.season_id, lp.projection_date, lp.projection_type,
		       lp.projected_games, lp.projected_goals, lp.projected_assists, lp.projected_points,
		       lp.projected_ppp, lp.projected_shots,
		       lp.confidence_low, lp.confidence_high,
		       lp.fantasy_points, lp.fantasy_rank,
		       lp.regression_flag, lp.regression_score, lp.regression_reasons,
		       lp.model_version, lp.model_type,
		       pl.name, pl.position, t.abbreviation
		FROM latest_projections lp
		JOIN players pl ON pl.id = lp.player_id
		LEFT JOIN teams t ON t.id = pl.current_team_id
		` + where + `
		ORDER BY lp.fantasy_points DESC NULLS LAST
		LIMIT $` + fmt.Sprintf("%d", argIdx) + ` OFFSET $` + fmt.Sprintf("%d", argIdx+1)

	args = append(args, p.PerPage, p.Offset())

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, fmt.Errorf("querying rankings: %w", err)
	}
	defer rows.Close()

	rankings := make([]PlayerProjection, 0, p.PerPage)
	for rows.Next() {
		var proj PlayerProjection
		if err := rows.Scan(
			&proj.ID, &proj.PlayerID, &proj.SeasonID, &proj.ProjectionDate, &proj.ProjectionType,
			&proj.ProjectedGames, &proj.ProjectedGoals, &proj.ProjectedAssists, &proj.ProjectedPoints,
			&proj.ProjectedPPP, &proj.ProjectedShots,
			&proj.ConfidenceLow, &proj.ConfidenceHigh,
			&proj.FantasyPoints, &proj.FantasyRank,
			&proj.RegressionFlag, &proj.RegressionScore, &proj.RegressionReason,
			&proj.ModelVersion, &proj.ModelType,
			&proj.PlayerName, &proj.Position, &proj.TeamAbbrev,
		); err != nil {
			return nil, 0, fmt.Errorf("scanning ranking: %w", err)
		}
		rankings = append(rankings, proj)
	}
	if err := rows.Err(); err != nil {
		return nil, 0, fmt.Errorf("iterating rankings: %w", err)
	}

	return rankings, total, nil
}

// GetRegressionCandidates returns players flagged as buy-low or sell-high.
func (r *ProjectionRepo) GetRegressionCandidates(ctx context.Context, flag string) ([]RegressionCandidate, error) {
	where := "WHERE lp.regression_flag IS NOT NULL"
	args := []any{}
	argIdx := 1

	if flag == "buy_low" || flag == "sell_high" {
		where = fmt.Sprintf("WHERE lp.regression_flag = $%d", argIdx)
		args = append(args, flag)
		argIdx++
	}

	// Join current season stats for context.
	query := `
		SELECT lp.player_id, pl.name, pl.position, t.abbreviation,
		       lp.regression_flag, lp.regression_score, lp.regression_reasons,
		       lp.projected_points, lp.fantasy_points,
		       ss.points, ss.games_played
		FROM latest_projections lp
		JOIN players pl ON pl.id = lp.player_id
		LEFT JOIN teams t ON t.id = pl.current_team_id
		LEFT JOIN skater_season_stats ss ON ss.player_id = lp.player_id
		    AND ss.season_id = lp.season_id
		` + where + `
		  AND lp.projection_type = $` + fmt.Sprintf("%d", argIdx) + `
		ORDER BY ABS(COALESCE(lp.regression_score, 0)) DESC`

	args = append(args, "season")

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("querying regression candidates: %w", err)
	}
	defer rows.Close()

	candidates := make([]RegressionCandidate, 0, 50)
	for rows.Next() {
		var c RegressionCandidate
		if err := rows.Scan(
			&c.PlayerID, &c.PlayerName, &c.Position, &c.TeamAbbrev,
			&c.RegressionFlag, &c.RegressionScore, &c.RegressionReason,
			&c.ProjectedPoints, &c.FantasyPoints,
			&c.CurrentPoints, &c.CurrentGames,
		); err != nil {
			return nil, fmt.Errorf("scanning regression candidate: %w", err)
		}
		candidates = append(candidates, c)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating regression candidates: %w", err)
	}

	return candidates, nil
}

// GetTradePlayerValues returns projection data for a set of player IDs.
func (r *ProjectionRepo) GetTradePlayerValues(ctx context.Context, playerIDs []int) ([]TradePlayerValue, error) {
	if len(playerIDs) == 0 {
		return make([]TradePlayerValue, 0), nil
	}

	query := `
		SELECT pl.id, pl.name, pl.position, t.abbreviation,
		       lp.projected_points, lp.fantasy_points
		FROM players pl
		LEFT JOIN teams t ON t.id = pl.current_team_id
		LEFT JOIN latest_projections lp ON lp.player_id = pl.id
		    AND lp.projection_type = 'season'
		WHERE pl.id = ANY($1)`

	rows, err := r.pool.Query(ctx, query, playerIDs)
	if err != nil {
		return nil, fmt.Errorf("querying trade player values: %w", err)
	}
	defer rows.Close()

	values := make([]TradePlayerValue, 0, len(playerIDs))
	for rows.Next() {
		var v TradePlayerValue
		if err := rows.Scan(
			&v.PlayerID, &v.PlayerName, &v.Position, &v.TeamAbbrev,
			&v.ProjectedPoints, &v.FantasyPoints,
		); err != nil {
			return nil, fmt.Errorf("scanning trade player: %w", err)
		}
		values = append(values, v)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating trade players: %w", err)
	}

	return values, nil
}

// GetReplacementLevel returns average fantasy points by position for VORP.
// Uses the bottom third of rostered-caliber players as replacement level.
func (r *ProjectionRepo) GetReplacementLevel(ctx context.Context) (map[string]float64, error) {
	query := `
		SELECT pl.position, AVG(lp.fantasy_points)
		FROM latest_projections lp
		JOIN players pl ON pl.id = lp.player_id
		WHERE lp.projection_type = 'season'
		  AND lp.fantasy_points IS NOT NULL
		  AND lp.fantasy_rank IS NOT NULL
		GROUP BY pl.position`

	rows, err := r.pool.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("querying replacement levels: %w", err)
	}
	defer rows.Close()

	levels := make(map[string]float64)
	for rows.Next() {
		var pos string
		var avg float64
		if err := rows.Scan(&pos, &avg); err != nil {
			return nil, fmt.Errorf("scanning replacement level: %w", err)
		}
		levels[pos] = avg
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating replacement levels: %w", err)
	}

	return levels, nil
}
