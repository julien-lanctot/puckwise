package repository

import (
	"encoding/json"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Repositories aggregates all repository types.
type Repositories struct {
	Player     *PlayerRepo
	Projection *ProjectionRepo
	Fantasy    *FantasyRepo
}

// NewRepositories creates all repositories from a shared connection pool.
func NewRepositories(pool *pgxpool.Pool) *Repositories {
	return &Repositories{
		Player:     &PlayerRepo{pool: pool},
		Projection: &ProjectionRepo{pool: pool},
		Fantasy:    &FantasyRepo{pool: pool},
	}
}

// --- Player-related models ---

type Player struct {
	HeadshotURL   *string    `json:"headshot_url,omitempty"`
	Name          string     `json:"name"`
	FirstName     *string    `json:"first_name,omitempty"`
	LastName      *string    `json:"last_name,omitempty"`
	Position      string     `json:"position"`
	PositionType  *string    `json:"position_type,omitempty"`
	BirthDate     *time.Time `json:"birth_date,omitempty"`
	BirthCountry  *string    `json:"birth_country,omitempty"`
	Shoots        *string    `json:"shoots,omitempty"`
	TeamName      *string    `json:"team_name,omitempty"`
	TeamAbbrev    *string    `json:"team_abbreviation,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`
	ID            int        `json:"id"`
	NhlID         int        `json:"nhl_id"`
	HeightCM      *int       `json:"height_cm,omitempty"`
	WeightKG      *int       `json:"weight_kg,omitempty"`
	CurrentTeamID *int       `json:"current_team_id,omitempty"`
	IsActive      bool       `json:"is_active"`
}

type PlayerDetail struct {
	Player        Player                `json:"player"`
	SeasonStats   []SkaterSeasonStats   `json:"season_stats"`
	AdvancedStats []SkaterAdvancedStats `json:"advanced_stats"`
	Projection    *PlayerProjection     `json:"projection,omitempty"`
}

// --- Game log models ---

type SkaterGameLog struct {
	GameDate       time.Time `json:"game_date"`
	TeamAbbrev     string    `json:"team_abbreviation"`
	OpponentAbbrev string    `json:"opponent_abbreviation"`
	ID             int64     `json:"id"`
	GameID         int       `json:"game_id"`
	Goals          int       `json:"goals"`
	Assists        int       `json:"assists"`
	Points         int       `json:"points"`
	PlusMinus      int       `json:"plus_minus"`
	PIM            int       `json:"pim"`
	Shots          int       `json:"shots"`
	TOISeconds     int       `json:"toi_seconds"`
	PPGoals        int       `json:"pp_goals"`
	PPAssists      int       `json:"pp_assists"`
	Hits           int       `json:"hits"`
	Blocks         int       `json:"blocks"`
	IsHome         bool      `json:"is_home"`
}

// --- Season stats models ---

type SkaterSeasonStats struct {
	SeasonID     string   `json:"season_id"`
	TeamAbbrev   *string  `json:"team_abbreviation,omitempty"`
	ID           int      `json:"id"`
	GamesPlayed  int      `json:"games_played"`
	Goals        int      `json:"goals"`
	Assists      int      `json:"assists"`
	Points       int      `json:"points"`
	PlusMinus    int      `json:"plus_minus"`
	PIM          int      `json:"pim"`
	Shots        int      `json:"shots"`
	PPPoints     int      `json:"pp_points"`
	Hits         int      `json:"hits"`
	Blocks       int      `json:"blocks"`
	TOIPerGameS  int      `json:"toi_per_game_seconds"`
	ShootingPct  *float64 `json:"shooting_pct,omitempty"`
	PointsPerGP  *float64 `json:"points_per_game,omitempty"`
}

// --- Advanced stats models ---

type SkaterAdvancedStats struct {
	SeasonID          string   `json:"season_id"`
	Situation         string   `json:"situation"`
	ID                int      `json:"id"`
	GamesPlayed       int      `json:"games_played"`
	XG                *float64 `json:"xg,omitempty"`
	GoalsAboveExpect  *float64 `json:"goals_above_expected,omitempty"`
	CFPct             *float64 `json:"cf_pct,omitempty"`
	FFPct             *float64 `json:"ff_pct,omitempty"`
	PDO               *float64 `json:"pdo,omitempty"`
	WAR               *float64 `json:"war,omitempty"`
	OffensiveWAR      *float64 `json:"offensive_war,omitempty"`
	DefensiveWAR      *float64 `json:"defensive_war,omitempty"`
	ShootingPct       *float64 `json:"shooting_pct,omitempty"`
	OnIceShootingPct  *float64 `json:"on_ice_shooting_pct,omitempty"`
	OnIceSavePct      *float64 `json:"on_ice_save_pct,omitempty"`
	GoalsP60          *float64 `json:"goals_per_60,omitempty"`
	AssistsP60        *float64 `json:"assists_per_60,omitempty"`
	PointsP60         *float64 `json:"points_per_60,omitempty"`
	OZStartPct        *float64 `json:"oz_start_pct,omitempty"`
}

// --- Projection models ---

type PlayerProjection struct {
	SeasonID         string           `json:"season_id"`
	ProjectionDate   time.Time        `json:"projection_date"`
	ProjectionType   string           `json:"projection_type"`
	RegressionFlag   *string          `json:"regression_flag,omitempty"`
	ModelVersion     *string          `json:"model_version,omitempty"`
	ModelType        *string          `json:"model_type,omitempty"`
	PlayerName       string           `json:"player_name,omitempty"`
	Position         string           `json:"position,omitempty"`
	TeamAbbrev       *string          `json:"team_abbreviation,omitempty"`
	RegressionReason json.RawMessage  `json:"regression_reasons,omitempty"`
	ID               int              `json:"id"`
	PlayerID         int              `json:"player_id"`
	ProjectedGames   *int             `json:"projected_games,omitempty"`
	FantasyRank      *int             `json:"fantasy_rank,omitempty"`
	ProjectedGoals   *float64         `json:"projected_goals,omitempty"`
	ProjectedAssists *float64         `json:"projected_assists,omitempty"`
	ProjectedPoints  *float64         `json:"projected_points,omitempty"`
	ProjectedPPP     *float64         `json:"projected_ppp,omitempty"`
	ProjectedShots   *float64         `json:"projected_shots,omitempty"`
	ConfidenceLow    *float64         `json:"confidence_low,omitempty"`
	ConfidenceHigh   *float64         `json:"confidence_high,omitempty"`
	FantasyPoints    *float64         `json:"fantasy_points,omitempty"`
	RegressionScore  *float64         `json:"regression_score,omitempty"`
}

type RegressionCandidate struct {
	PlayerName       string          `json:"player_name"`
	Position         string          `json:"position"`
	TeamAbbrev       *string         `json:"team_abbreviation,omitempty"`
	RegressionFlag   string          `json:"regression_flag"`
	RegressionReason json.RawMessage `json:"regression_reasons"`
	PlayerID         int             `json:"player_id"`
	ProjectedPoints  *float64        `json:"projected_points,omitempty"`
	RegressionScore  *float64        `json:"regression_score,omitempty"`
	FantasyPoints    *float64        `json:"fantasy_points,omitempty"`
	CurrentPoints    *int            `json:"current_points,omitempty"`
	CurrentGames     *int            `json:"current_games,omitempty"`
}

// --- Fantasy models ---

type FantasyLeague struct {
	Name             string          `json:"name"`
	Platform         *string         `json:"platform,omitempty"`
	ScoringType      string          `json:"scoring_type"`
	ScoringSettings  json.RawMessage `json:"scoring_settings,omitempty"`
	RosterPositions  json.RawMessage `json:"roster_positions,omitempty"`
	SeasonID         *string         `json:"season_id,omitempty"`
	CreatedAt        time.Time       `json:"created_at"`
	UpdatedAt        time.Time       `json:"updated_at"`
	ID               int             `json:"id"`
	NumTeams         int             `json:"num_teams"`
	IsActive         bool            `json:"is_active"`
}

type FantasyTeam struct {
	Name         string    `json:"name"`
	OwnerName    *string   `json:"owner_name,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
	ID           int       `json:"id"`
	LeagueID     int       `json:"league_id"`
	StandingRank *int      `json:"standing_rank,omitempty"`
	Wins         int       `json:"wins"`
	Losses       int       `json:"losses"`
	Ties         int       `json:"ties"`
	IsMyTeam     bool      `json:"is_my_team"`
}

type FantasyRoster struct {
	PositionSlot    *string    `json:"position_slot,omitempty"`
	AcquiredDate    *time.Time `json:"acquired_date,omitempty"`
	AcquisitionType *string    `json:"acquisition_type,omitempty"`
	PlayerName      string     `json:"player_name"`
	PlayerPosition  string     `json:"player_position"`
	TeamAbbrev      *string    `json:"team_abbreviation,omitempty"`
	ID              int        `json:"id"`
	TeamID          int        `json:"team_id"`
	PlayerID        int        `json:"player_id"`
	IsActive        bool       `json:"is_active"`
}

// --- Request models ---

type CreateLeagueRequest struct {
	Name            string          `json:"name"`
	Platform        *string         `json:"platform,omitempty"`
	ScoringType     string          `json:"scoring_type"`
	ScoringSettings json.RawMessage `json:"scoring_settings,omitempty"`
	RosterPositions json.RawMessage `json:"roster_positions,omitempty"`
	SeasonID        *string         `json:"season_id,omitempty"`
	NumTeams        int             `json:"num_teams"`
}

type AddTeamRequest struct {
	Name      string  `json:"name"`
	OwnerName *string `json:"owner_name,omitempty"`
	IsMyTeam  bool    `json:"is_my_team"`
}

type AddPlayerToRosterRequest struct {
	PositionSlot    *string `json:"position_slot,omitempty"`
	AcquisitionType *string `json:"acquisition_type,omitempty"`
	PlayerID        int     `json:"player_id"`
}

type TradeAnalyzeRequest struct {
	Team1PlayerIDs []int `json:"team_1_player_ids"`
	Team2PlayerIDs []int `json:"team_2_player_ids"`
}

type TradePlayerValue struct {
	PlayerName      string   `json:"player_name"`
	Position        string   `json:"position"`
	TeamAbbrev      *string  `json:"team_abbreviation,omitempty"`
	PlayerID        int      `json:"player_id"`
	ProjectedPoints *float64 `json:"projected_points,omitempty"`
	FantasyPoints   *float64 `json:"fantasy_points,omitempty"`
	VORP            float64  `json:"vorp"`
}

type TradeAnalysis struct {
	Team1Players    []TradePlayerValue `json:"team_1_players"`
	Team2Players    []TradePlayerValue `json:"team_2_players"`
	Team1TotalVORP  float64           `json:"team_1_total_vorp"`
	Team2TotalVORP  float64           `json:"team_2_total_vorp"`
	VORPDifference  float64           `json:"vorp_difference"`
	Recommendation  string            `json:"recommendation"`
}

// --- Pagination ---

type PaginatedResponse[T any] struct {
	Data       []T `json:"data"`
	TotalCount int `json:"total_count"`
	Page       int `json:"page"`
	PerPage    int `json:"per_page"`
	TotalPages int `json:"total_pages"`
}

type Pagination struct {
	Page    int
	PerPage int
}

func (p Pagination) Offset() int {
	return (p.Page - 1) * p.PerPage
}

func NewPaginatedResponse[T any](data []T, total, page, perPage int) PaginatedResponse[T] {
	totalPages := total / perPage
	if total%perPage != 0 {
		totalPages++
	}
	return PaginatedResponse[T]{
		Data:       data,
		TotalCount: total,
		Page:       page,
		PerPage:    perPage,
		TotalPages: totalPages,
	}
}

// ReplacementLevel holds average fantasy points by position for VORP calculation.
type ReplacementLevel struct {
	Position     string  `json:"position"`
	AvgFantasyPt float64 `json:"avg_fantasy_points"`
}
