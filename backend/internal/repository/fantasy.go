package repository

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5/pgxpool"
)

type FantasyRepo struct {
	pool *pgxpool.Pool
}

// ListLeagues returns all active fantasy leagues.
func (r *FantasyRepo) ListLeagues(ctx context.Context) ([]FantasyLeague, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, name, platform, scoring_type, scoring_settings,
		       roster_positions, num_teams, season_id,
		       is_active, created_at, updated_at
		FROM fantasy_leagues
		WHERE is_active = true
		ORDER BY created_at DESC`)
	if err != nil {
		return nil, fmt.Errorf("querying leagues: %w", err)
	}
	defer rows.Close()

	leagues := make([]FantasyLeague, 0, 5)
	for rows.Next() {
		var l FantasyLeague
		if err := rows.Scan(
			&l.ID, &l.Name, &l.Platform, &l.ScoringType, &l.ScoringSettings,
			&l.RosterPositions, &l.NumTeams, &l.SeasonID,
			&l.IsActive, &l.CreatedAt, &l.UpdatedAt,
		); err != nil {
			return nil, fmt.Errorf("scanning league: %w", err)
		}
		leagues = append(leagues, l)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating leagues: %w", err)
	}

	return leagues, nil
}

// CreateLeague inserts a new fantasy league and returns it.
func (r *FantasyRepo) CreateLeague(ctx context.Context, req CreateLeagueRequest) (*FantasyLeague, error) {
	var l FantasyLeague
	err := r.pool.QueryRow(ctx, `
		INSERT INTO fantasy_leagues (name, platform, scoring_type, scoring_settings,
		                             roster_positions, num_teams, season_id)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id, name, platform, scoring_type, scoring_settings,
		          roster_positions, num_teams, season_id,
		          is_active, created_at, updated_at`,
		req.Name, req.Platform, req.ScoringType, req.ScoringSettings,
		req.RosterPositions, req.NumTeams, req.SeasonID,
	).Scan(
		&l.ID, &l.Name, &l.Platform, &l.ScoringType, &l.ScoringSettings,
		&l.RosterPositions, &l.NumTeams, &l.SeasonID,
		&l.IsActive, &l.CreatedAt, &l.UpdatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("creating league: %w", err)
	}
	return &l, nil
}

// GetLeague returns a league with its teams.
func (r *FantasyRepo) GetLeague(ctx context.Context, id int) (*FantasyLeague, []FantasyTeam, error) {
	var l FantasyLeague
	err := r.pool.QueryRow(ctx, `
		SELECT id, name, platform, scoring_type, scoring_settings,
		       roster_positions, num_teams, season_id,
		       is_active, created_at, updated_at
		FROM fantasy_leagues
		WHERE id = $1`, id,
	).Scan(
		&l.ID, &l.Name, &l.Platform, &l.ScoringType, &l.ScoringSettings,
		&l.RosterPositions, &l.NumTeams, &l.SeasonID,
		&l.IsActive, &l.CreatedAt, &l.UpdatedAt,
	)
	if err != nil {
		return nil, nil, fmt.Errorf("getting league %d: %w", id, err)
	}

	rows, err := r.pool.Query(ctx, `
		SELECT id, league_id, name, owner_name, is_my_team,
		       standing_rank, wins, losses, ties, created_at
		FROM fantasy_teams
		WHERE league_id = $1
		ORDER BY COALESCE(standing_rank, 999), name`, id)
	if err != nil {
		return nil, nil, fmt.Errorf("getting teams for league %d: %w", id, err)
	}
	defer rows.Close()

	teams := make([]FantasyTeam, 0, 16)
	for rows.Next() {
		var t FantasyTeam
		if err := rows.Scan(
			&t.ID, &t.LeagueID, &t.Name, &t.OwnerName, &t.IsMyTeam,
			&t.StandingRank, &t.Wins, &t.Losses, &t.Ties, &t.CreatedAt,
		); err != nil {
			return nil, nil, fmt.Errorf("scanning team: %w", err)
		}
		teams = append(teams, t)
	}
	if err := rows.Err(); err != nil {
		return nil, nil, fmt.Errorf("iterating teams: %w", err)
	}

	return &l, teams, nil
}

// AddTeamToLeague inserts a new fantasy team into a league.
func (r *FantasyRepo) AddTeamToLeague(ctx context.Context, leagueID int, req AddTeamRequest) (*FantasyTeam, error) {
	var t FantasyTeam
	err := r.pool.QueryRow(ctx, `
		INSERT INTO fantasy_teams (league_id, name, owner_name, is_my_team)
		VALUES ($1, $2, $3, $4)
		RETURNING id, league_id, name, owner_name, is_my_team,
		          standing_rank, wins, losses, ties, created_at`,
		leagueID, req.Name, req.OwnerName, req.IsMyTeam,
	).Scan(
		&t.ID, &t.LeagueID, &t.Name, &t.OwnerName, &t.IsMyTeam,
		&t.StandingRank, &t.Wins, &t.Losses, &t.Ties, &t.CreatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("adding team to league %d: %w", leagueID, err)
	}
	return &t, nil
}

// GetTeamRoster returns all active players on a fantasy team.
func (r *FantasyRepo) GetTeamRoster(ctx context.Context, teamID int) ([]FantasyRoster, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT fr.id, fr.team_id, fr.player_id, fr.position_slot,
		       fr.acquired_date, fr.acquisition_type, fr.is_active,
		       pl.name, pl.position, t.abbreviation
		FROM fantasy_rosters fr
		JOIN players pl ON pl.id = fr.player_id
		LEFT JOIN teams t ON t.id = pl.current_team_id
		WHERE fr.team_id = $1 AND fr.is_active = true
		ORDER BY fr.position_slot, pl.name`, teamID)
	if err != nil {
		return nil, fmt.Errorf("querying roster for team %d: %w", teamID, err)
	}
	defer rows.Close()

	roster := make([]FantasyRoster, 0, 20)
	for rows.Next() {
		var entry FantasyRoster
		if err := rows.Scan(
			&entry.ID, &entry.TeamID, &entry.PlayerID, &entry.PositionSlot,
			&entry.AcquiredDate, &entry.AcquisitionType, &entry.IsActive,
			&entry.PlayerName, &entry.PlayerPosition, &entry.TeamAbbrev,
		); err != nil {
			return nil, fmt.Errorf("scanning roster entry: %w", err)
		}
		roster = append(roster, entry)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterating roster: %w", err)
	}

	return roster, nil
}

// AddPlayerToRoster adds a player to a fantasy team's roster.
func (r *FantasyRepo) AddPlayerToRoster(ctx context.Context, teamID int, req AddPlayerToRosterRequest) (*FantasyRoster, error) {
	acqType := "add"
	if req.AcquisitionType != nil {
		acqType = *req.AcquisitionType
	}

	var fr FantasyRoster
	err := r.pool.QueryRow(ctx, `
		INSERT INTO fantasy_rosters (team_id, player_id, position_slot, acquisition_type)
		VALUES ($1, $2, $3, $4)
		RETURNING id, team_id, player_id, position_slot,
		          acquired_date, acquisition_type, is_active`,
		teamID, req.PlayerID, req.PositionSlot, acqType,
	).Scan(
		&fr.ID, &fr.TeamID, &fr.PlayerID, &fr.PositionSlot,
		&fr.AcquiredDate, &fr.AcquisitionType, &fr.IsActive,
	)
	if err != nil {
		return nil, fmt.Errorf("adding player %d to team %d: %w", req.PlayerID, teamID, err)
	}

	// Fetch player name for response.
	_ = r.pool.QueryRow(ctx, `
		SELECT pl.name, pl.position, t.abbreviation
		FROM players pl
		LEFT JOIN teams t ON t.id = pl.current_team_id
		WHERE pl.id = $1`, req.PlayerID,
	).Scan(&fr.PlayerName, &fr.PlayerPosition, &fr.TeamAbbrev)

	return &fr, nil
}

// RemovePlayerFromRoster soft-deletes a player from a fantasy team's roster.
func (r *FantasyRepo) RemovePlayerFromRoster(ctx context.Context, teamID, playerID int) error {
	tag, err := r.pool.Exec(ctx, `
		UPDATE fantasy_rosters
		SET is_active = false, dropped_date = CURRENT_DATE, updated_at = NOW()
		WHERE team_id = $1 AND player_id = $2 AND is_active = true`,
		teamID, playerID)
	if err != nil {
		return fmt.Errorf("removing player %d from team %d: %w", playerID, teamID, err)
	}
	if tag.RowsAffected() == 0 {
		return fmt.Errorf("player %d not found on team %d roster", playerID, teamID)
	}
	return nil
}
