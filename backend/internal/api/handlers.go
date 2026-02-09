package api

import (
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/puckwise/backend/internal/repository"
)

// Handlers holds all HTTP handler methods.
type Handlers struct {
	repos *repository.Repositories
}

// NewHandlers creates a Handlers with all dependencies.
func NewHandlers(repos *repository.Repositories) *Handlers {
	return &Handlers{repos: repos}
}

// --- Player handlers ---

func (h *Handlers) ListPlayers(w http.ResponseWriter, r *http.Request) {
	pg := parsePagination(r)
	q := r.URL.Query()

	position := q.Get("position")
	search := q.Get("search")
	teamID, _ := strconv.Atoi(q.Get("team_id"))
	activeOnly := q.Get("active") != "false"

	players, total, err := h.repos.Player.ListPlayers(r.Context(), pg, position, search, teamID, activeOnly)
	if err != nil {
		log.Printf("error listing players: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to list players")
		return
	}

	writeJSON(w, http.StatusOK, repository.NewPaginatedResponse(players, total, pg.Page, pg.PerPage))
}

func (h *Handlers) GetPlayer(w http.ResponseWriter, r *http.Request) {
	id, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	detail, err := h.repos.Player.GetPlayer(r.Context(), id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeError(w, http.StatusNotFound, "player not found")
			return
		}
		log.Printf("error getting player %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "failed to get player")
		return
	}

	writeJSON(w, http.StatusOK, detail)
}

func (h *Handlers) GetPlayerGameLog(w http.ResponseWriter, r *http.Request) {
	id, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	pg := parsePagination(r)
	seasonID := r.URL.Query().Get("season")

	logs, total, err := h.repos.Player.GetPlayerGameLog(r.Context(), id, pg, seasonID)
	if err != nil {
		log.Printf("error getting game log for player %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "failed to get game log")
		return
	}

	writeJSON(w, http.StatusOK, repository.NewPaginatedResponse(logs, total, pg.Page, pg.PerPage))
}

// --- Projection handlers ---

func (h *Handlers) GetRankings(w http.ResponseWriter, r *http.Request) {
	pg := parsePagination(r)
	q := r.URL.Query()

	position := q.Get("position")
	projType := q.Get("type")

	rankings, total, err := h.repos.Projection.GetRankings(r.Context(), pg, position, projType)
	if err != nil {
		log.Printf("error getting rankings: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to get rankings")
		return
	}

	writeJSON(w, http.StatusOK, repository.NewPaginatedResponse(rankings, total, pg.Page, pg.PerPage))
}

func (h *Handlers) GetRegressionCandidates(w http.ResponseWriter, r *http.Request) {
	flag := r.URL.Query().Get("flag")

	candidates, err := h.repos.Projection.GetRegressionCandidates(r.Context(), flag)
	if err != nil {
		log.Printf("error getting regression candidates: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to get regression candidates")
		return
	}

	writeJSON(w, http.StatusOK, candidates)
}

// --- Trade handler ---

func (h *Handlers) AnalyzeTrade(w http.ResponseWriter, r *http.Request) {
	var req repository.TradeAnalyzeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if len(req.Team1PlayerIDs) == 0 || len(req.Team2PlayerIDs) == 0 {
		writeError(w, http.StatusBadRequest, "both sides must have at least one player")
		return
	}

	// Fetch player values for both sides.
	allIDs := make([]int, 0, len(req.Team1PlayerIDs)+len(req.Team2PlayerIDs))
	allIDs = append(allIDs, req.Team1PlayerIDs...)
	allIDs = append(allIDs, req.Team2PlayerIDs...)

	values, err := h.repos.Projection.GetTradePlayerValues(r.Context(), allIDs)
	if err != nil {
		log.Printf("error getting trade values: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to get player values")
		return
	}

	// Fetch replacement levels for VORP.
	replacements, err := h.repos.Projection.GetReplacementLevel(r.Context())
	if err != nil {
		log.Printf("error getting replacement levels: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to get replacement levels")
		return
	}

	// Index values by player ID.
	valueMap := make(map[int]repository.TradePlayerValue, len(values))
	for _, v := range values {
		valueMap[v.PlayerID] = v
	}

	// Compute VORP for each player and split into sides.
	computeVORP := func(v *repository.TradePlayerValue) {
		fp := 0.0
		if v.FantasyPoints != nil {
			fp = *v.FantasyPoints
		}
		repl, ok := replacements[v.Position]
		if !ok {
			repl = 0
		}
		v.VORP = fp - repl
	}

	analysis := repository.TradeAnalysis{
		Team1Players: make([]repository.TradePlayerValue, 0, len(req.Team1PlayerIDs)),
		Team2Players: make([]repository.TradePlayerValue, 0, len(req.Team2PlayerIDs)),
	}

	for _, pid := range req.Team1PlayerIDs {
		v, ok := valueMap[pid]
		if !ok {
			writeError(w, http.StatusBadRequest, fmt.Sprintf("player %d not found", pid))
			return
		}
		computeVORP(&v)
		analysis.Team1Players = append(analysis.Team1Players, v)
		analysis.Team1TotalVORP += v.VORP
	}

	for _, pid := range req.Team2PlayerIDs {
		v, ok := valueMap[pid]
		if !ok {
			writeError(w, http.StatusBadRequest, fmt.Sprintf("player %d not found", pid))
			return
		}
		computeVORP(&v)
		analysis.Team2Players = append(analysis.Team2Players, v)
		analysis.Team2TotalVORP += v.VORP
	}

	analysis.VORPDifference = analysis.Team1TotalVORP - analysis.Team2TotalVORP

	switch {
	case analysis.VORPDifference > 5:
		analysis.Recommendation = "Team 1 wins this trade significantly"
	case analysis.VORPDifference > 1:
		analysis.Recommendation = "Slight edge to Team 1"
	case analysis.VORPDifference < -5:
		analysis.Recommendation = "Team 2 wins this trade significantly"
	case analysis.VORPDifference < -1:
		analysis.Recommendation = "Slight edge to Team 2"
	default:
		analysis.Recommendation = "Relatively fair trade"
	}

	writeJSON(w, http.StatusOK, analysis)
}

// --- Fantasy handlers ---

func (h *Handlers) ListLeagues(w http.ResponseWriter, r *http.Request) {
	leagues, err := h.repos.Fantasy.ListLeagues(r.Context())
	if err != nil {
		log.Printf("error listing leagues: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to list leagues")
		return
	}

	writeJSON(w, http.StatusOK, leagues)
}

func (h *Handlers) CreateLeague(w http.ResponseWriter, r *http.Request) {
	var req repository.CreateLeagueRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.Name == "" {
		writeError(w, http.StatusBadRequest, "name is required")
		return
	}
	if req.ScoringType == "" {
		req.ScoringType = "points"
	}
	if req.NumTeams < 1 {
		req.NumTeams = 12
	}

	league, err := h.repos.Fantasy.CreateLeague(r.Context(), req)
	if err != nil {
		log.Printf("error creating league: %v", err)
		writeError(w, http.StatusInternalServerError, "failed to create league")
		return
	}

	writeJSON(w, http.StatusCreated, league)
}

func (h *Handlers) GetLeague(w http.ResponseWriter, r *http.Request) {
	id, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	league, teams, err := h.repos.Fantasy.GetLeague(r.Context(), id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeError(w, http.StatusNotFound, "league not found")
			return
		}
		log.Printf("error getting league %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "failed to get league")
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"league": league,
		"teams":  teams,
	})
}

func (h *Handlers) AddTeamToLeague(w http.ResponseWriter, r *http.Request) {
	id, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	var req repository.AddTeamRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.Name == "" {
		writeError(w, http.StatusBadRequest, "name is required")
		return
	}

	team, err := h.repos.Fantasy.AddTeamToLeague(r.Context(), id, req)
	if err != nil {
		if strings.Contains(err.Error(), "duplicate key") {
			writeError(w, http.StatusConflict, "team name already exists in this league")
			return
		}
		log.Printf("error adding team to league %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "failed to add team")
		return
	}

	writeJSON(w, http.StatusCreated, team)
}

func (h *Handlers) GetTeamRoster(w http.ResponseWriter, r *http.Request) {
	id, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	roster, err := h.repos.Fantasy.GetTeamRoster(r.Context(), id)
	if err != nil {
		log.Printf("error getting roster for team %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "failed to get roster")
		return
	}

	writeJSON(w, http.StatusOK, roster)
}

func (h *Handlers) AddPlayerToRoster(w http.ResponseWriter, r *http.Request) {
	id, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	var req repository.AddPlayerToRosterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body")
		return
	}

	if req.PlayerID == 0 {
		writeError(w, http.StatusBadRequest, "player_id is required")
		return
	}

	entry, err := h.repos.Fantasy.AddPlayerToRoster(r.Context(), id, req)
	if err != nil {
		if strings.Contains(err.Error(), "duplicate key") {
			writeError(w, http.StatusConflict, "player already on this roster")
			return
		}
		log.Printf("error adding player to roster for team %d: %v", id, err)
		writeError(w, http.StatusInternalServerError, "failed to add player to roster")
		return
	}

	writeJSON(w, http.StatusCreated, entry)
}

func (h *Handlers) RemovePlayerFromRoster(w http.ResponseWriter, r *http.Request) {
	teamID, err := parseID(r, "id")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	playerID, err := parseID(r, "playerId")
	if err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	if err := h.repos.Fantasy.RemovePlayerFromRoster(r.Context(), teamID, playerID); err != nil {
		if strings.Contains(err.Error(), "not found on team") {
			writeError(w, http.StatusNotFound, err.Error())
			return
		}
		log.Printf("error removing player %d from team %d: %v", playerID, teamID, err)
		writeError(w, http.StatusInternalServerError, "failed to remove player from roster")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "removed"})
}
