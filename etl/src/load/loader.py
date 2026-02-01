"""Database loader with upsert operations for all entities."""

from typing import Any
from datetime import date

from ..db import get_connection, fetch_one, fetch_all


# Cache for lookups
_team_cache: dict[str, int] = {}
_season_cache: dict[str, int] = {}
_player_cache: dict[int, int] = {}


def get_team_id_by_abbrev(abbrev: str) -> int | None:
    """Get team ID by abbreviation, with caching."""
    if abbrev in _team_cache:
        return _team_cache[abbrev]

    result = fetch_one(
        "SELECT id FROM teams WHERE abbreviation = %s",
        (abbrev.upper(),)
    )
    if result:
        _team_cache[abbrev] = result["id"]
        return result["id"]
    return None


def get_team_id_by_nhl_id(nhl_id: int) -> int | None:
    """Get team ID by NHL team ID."""
    result = fetch_one(
        "SELECT id FROM teams WHERE nhl_id = %s",
        (nhl_id,)
    )
    return result["id"] if result else None


def get_season_id(season_str: str) -> str | None:
    """
    Get season_id string by season input (e.g., '20232024', '2023-24', or '2023').

    Returns the season_id VARCHAR like '20232024'.
    """
    if season_str in _season_cache:
        return _season_cache[season_str]

    # Normalize season string
    if len(season_str) == 8:
        # Format: 20232024
        start_year = int(season_str[:4])
    elif "-" in season_str:
        # Format: 2023-24
        start_year = int(season_str.split("-")[0])
    else:
        # Format: 2023
        start_year = int(season_str)

    result = fetch_one(
        "SELECT season_id FROM seasons WHERE start_year = %s",
        (start_year,)
    )
    if result:
        _season_cache[season_str] = result["season_id"]
        return result["season_id"]
    return None


def get_player_id(nhl_id: int) -> int | None:
    """Get player database ID by NHL player ID, with caching."""
    if nhl_id in _player_cache:
        return _player_cache[nhl_id]

    result = fetch_one(
        "SELECT id FROM players WHERE nhl_id = %s",
        (nhl_id,)
    )
    if result:
        _player_cache[nhl_id] = result["id"]
        return result["id"]
    return None


def get_game_id(nhl_game_id: int) -> int | None:
    """Get game database ID by NHL game ID."""
    result = fetch_one(
        "SELECT id FROM games WHERE nhl_game_id = %s",
        (nhl_game_id,)
    )
    return result["id"] if result else None


def upsert_player(player: dict[str, Any]) -> int:
    """Insert or update a player, returning the player ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO players (
                    nhl_id, name, first_name, last_name, position, position_type,
                    birth_date, birth_city, birth_country, nationality,
                    height_cm, weight_kg, shoots, current_team_id, is_active, headshot_url
                ) VALUES (
                    %(nhl_id)s, %(name)s, %(first_name)s, %(last_name)s, %(position)s, %(position_type)s,
                    %(birth_date)s, %(birth_city)s, %(birth_country)s, %(nationality)s,
                    %(height_cm)s, %(weight_kg)s, %(shoots)s, %(current_team_id)s, %(is_active)s, %(headshot_url)s
                )
                ON CONFLICT (nhl_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    position = EXCLUDED.position,
                    position_type = EXCLUDED.position_type,
                    birth_date = COALESCE(EXCLUDED.birth_date, players.birth_date),
                    birth_city = COALESCE(EXCLUDED.birth_city, players.birth_city),
                    birth_country = COALESCE(EXCLUDED.birth_country, players.birth_country),
                    nationality = COALESCE(EXCLUDED.nationality, players.nationality),
                    height_cm = COALESCE(EXCLUDED.height_cm, players.height_cm),
                    weight_kg = COALESCE(EXCLUDED.weight_kg, players.weight_kg),
                    shoots = COALESCE(EXCLUDED.shoots, players.shoots),
                    current_team_id = COALESCE(EXCLUDED.current_team_id, players.current_team_id),
                    is_active = EXCLUDED.is_active,
                    headshot_url = COALESCE(EXCLUDED.headshot_url, players.headshot_url),
                    updated_at = NOW()
                RETURNING id
            """, player)
            result = cur.fetchone()
            conn.commit()

            # Update cache
            if result and player.get("nhl_id"):
                _player_cache[player["nhl_id"]] = result["id"]

            return result["id"] if result else None


def upsert_players(players: list[dict[str, Any]]) -> int:
    """Bulk upsert players, returning count inserted/updated."""
    count = 0
    for player in players:
        if upsert_player(player):
            count += 1
    return count


def upsert_game(game: dict[str, Any]) -> int:
    """Insert or update a game, returning the game ID."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO games (
                    nhl_game_id, season_id, game_date, game_type,
                    home_team_id, away_team_id, home_score, away_score,
                    status, venue
                ) VALUES (
                    %(nhl_game_id)s, %(season_id)s, %(game_date)s, %(game_type)s,
                    %(home_team_id)s, %(away_team_id)s, %(home_score)s, %(away_score)s,
                    %(status)s, %(venue)s
                )
                ON CONFLICT (nhl_game_id) DO UPDATE SET
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    status = EXCLUDED.status,
                    updated_at = NOW()
                RETURNING id
            """, game)
            result = cur.fetchone()
            conn.commit()
            return result["id"] if result else None


def upsert_skater_game_log(log: dict[str, Any]) -> bool:
    """Insert or update a skater game log entry."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO skater_game_logs (
                    player_id, game_id, game_date, team_id,
                    goals, assists, points, plus_minus, pim,
                    shots, shooting_pct, toi_seconds, toi_even_seconds, toi_pp_seconds, toi_sh_seconds,
                    pp_goals, pp_assists, sh_goals, sh_assists,
                    hits, blocks, giveaways, takeaways, faceoff_wins, faceoff_losses,
                    is_home
                ) VALUES (
                    %(player_id)s, %(game_id)s, %(game_date)s, %(team_id)s,
                    %(goals)s, %(assists)s, %(points)s, %(plus_minus)s, %(pim)s,
                    %(shots)s, %(shooting_pct)s, %(toi_seconds)s, %(toi_even_seconds)s, %(toi_pp_seconds)s, %(toi_sh_seconds)s,
                    %(pp_goals)s, %(pp_assists)s, %(sh_goals)s, %(sh_assists)s,
                    %(hits)s, %(blocks)s, %(giveaways)s, %(takeaways)s, %(faceoff_wins)s, %(faceoff_losses)s,
                    %(is_home)s
                )
                ON CONFLICT (player_id, game_id, game_date) DO UPDATE SET
                    goals = EXCLUDED.goals,
                    assists = EXCLUDED.assists,
                    points = EXCLUDED.points,
                    plus_minus = EXCLUDED.plus_minus,
                    pim = EXCLUDED.pim,
                    shots = EXCLUDED.shots,
                    shooting_pct = EXCLUDED.shooting_pct,
                    toi_seconds = EXCLUDED.toi_seconds,
                    hits = EXCLUDED.hits,
                    blocks = EXCLUDED.blocks
            """, log)
            conn.commit()
            return True


def upsert_goalie_game_log(log: dict[str, Any]) -> bool:
    """Insert or update a goalie game log entry."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO goalie_game_logs (
                    player_id, game_id, game_date, team_id,
                    decision, goals_against, saves, shots_against, save_pct,
                    toi_seconds, shutout, goals, assists, pim,
                    is_home, is_starter
                ) VALUES (
                    %(player_id)s, %(game_id)s, %(game_date)s, %(team_id)s,
                    %(decision)s, %(goals_against)s, %(saves)s, %(shots_against)s, %(save_pct)s,
                    %(toi_seconds)s, %(shutout)s, %(goals)s, %(assists)s, %(pim)s,
                    %(is_home)s, %(is_starter)s
                )
                ON CONFLICT (player_id, game_id, game_date) DO UPDATE SET
                    decision = EXCLUDED.decision,
                    goals_against = EXCLUDED.goals_against,
                    saves = EXCLUDED.saves,
                    shots_against = EXCLUDED.shots_against,
                    save_pct = EXCLUDED.save_pct,
                    toi_seconds = EXCLUDED.toi_seconds,
                    shutout = EXCLUDED.shutout
            """, log)
            conn.commit()
            return True


def upsert_skater_season_stats(stats: dict[str, Any]) -> bool:
    """Insert or update skater season stats."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO skater_season_stats (
                    player_id, season_id, team_id,
                    games_played, goals, assists, points, plus_minus, pim,
                    pp_goals, pp_assists, pp_points, sh_goals, sh_assists,
                    shots, shooting_pct, toi_per_game_seconds,
                    hits, blocks, faceoff_pct
                ) VALUES (
                    %(player_id)s, %(season_id)s, %(team_id)s,
                    %(games_played)s, %(goals)s, %(assists)s, %(points)s, %(plus_minus)s, %(pim)s,
                    %(pp_goals)s, %(pp_assists)s, %(pp_points)s, %(sh_goals)s, %(sh_assists)s,
                    %(shots)s, %(shooting_pct)s, %(toi_per_game_seconds)s,
                    %(hits)s, %(blocks)s, %(faceoff_pct)s
                )
                ON CONFLICT (player_id, season_id) DO UPDATE SET
                    games_played = EXCLUDED.games_played,
                    goals = EXCLUDED.goals,
                    assists = EXCLUDED.assists,
                    points = EXCLUDED.points,
                    plus_minus = EXCLUDED.plus_minus,
                    pim = EXCLUDED.pim,
                    pp_goals = EXCLUDED.pp_goals,
                    pp_assists = EXCLUDED.pp_assists,
                    pp_points = EXCLUDED.pp_points,
                    shots = EXCLUDED.shots,
                    shooting_pct = EXCLUDED.shooting_pct,
                    toi_per_game_seconds = EXCLUDED.toi_per_game_seconds,
                    hits = EXCLUDED.hits,
                    blocks = EXCLUDED.blocks,
                    faceoff_pct = EXCLUDED.faceoff_pct,
                    updated_at = NOW()
            """, stats)
            conn.commit()
            return True


def upsert_goalie_season_stats(stats: dict[str, Any]) -> bool:
    """Insert or update goalie season stats."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO goalie_season_stats (
                    player_id, season_id, team_id,
                    games_played, games_started, wins, losses, ot_losses,
                    goals_against, goals_against_avg, saves, shots_against, save_pct,
                    shutouts, toi_total_seconds
                ) VALUES (
                    %(player_id)s, %(season_id)s, %(team_id)s,
                    %(games_played)s, %(games_started)s, %(wins)s, %(losses)s, %(ot_losses)s,
                    %(goals_against)s, %(goals_against_avg)s, %(saves)s, %(shots_against)s, %(save_pct)s,
                    %(shutouts)s, %(toi_total_seconds)s
                )
                ON CONFLICT (player_id, season_id) DO UPDATE SET
                    games_played = EXCLUDED.games_played,
                    games_started = EXCLUDED.games_started,
                    wins = EXCLUDED.wins,
                    losses = EXCLUDED.losses,
                    ot_losses = EXCLUDED.ot_losses,
                    goals_against = EXCLUDED.goals_against,
                    goals_against_avg = EXCLUDED.goals_against_avg,
                    saves = EXCLUDED.saves,
                    shots_against = EXCLUDED.shots_against,
                    save_pct = EXCLUDED.save_pct,
                    shutouts = EXCLUDED.shutouts,
                    toi_total_seconds = EXCLUDED.toi_total_seconds,
                    updated_at = NOW()
            """, stats)
            conn.commit()
            return True


def upsert_advanced_stats(stats: dict[str, Any]) -> bool:
    """Insert or update skater advanced stats from MoneyPuck."""
    player_id = get_player_id(stats.pop("nhl_player_id"))
    if not player_id:
        return False

    stats["player_id"] = player_id

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO skater_advanced_stats (
                    player_id, season_id, situation,
                    games_played, toi_minutes,
                    xg, goals_above_expected, on_ice_xg_for, on_ice_xg_against, xg_diff,
                    cf, ca, cf_pct, ff, fa, ff_pct,
                    on_ice_shooting_pct, on_ice_save_pct, pdo,
                    oz_start_pct
                ) VALUES (
                    %(player_id)s, %(season_id)s, %(situation)s,
                    %(games_played)s, %(toi_minutes)s,
                    %(xg)s, %(goals_above_expected)s, %(on_ice_xg_for)s, %(on_ice_xg_against)s, %(xg_diff)s,
                    %(cf)s, %(ca)s, %(cf_pct)s, %(ff)s, %(fa)s, %(ff_pct)s,
                    %(on_ice_shooting_pct)s, %(on_ice_save_pct)s, %(pdo)s,
                    %(oz_start_pct)s
                )
                ON CONFLICT (player_id, season_id, situation) DO UPDATE SET
                    games_played = EXCLUDED.games_played,
                    toi_minutes = EXCLUDED.toi_minutes,
                    xg = EXCLUDED.xg,
                    goals_above_expected = EXCLUDED.goals_above_expected,
                    on_ice_xg_for = EXCLUDED.on_ice_xg_for,
                    on_ice_xg_against = EXCLUDED.on_ice_xg_against,
                    xg_diff = EXCLUDED.xg_diff,
                    cf = EXCLUDED.cf,
                    ca = EXCLUDED.ca,
                    cf_pct = EXCLUDED.cf_pct,
                    ff = EXCLUDED.ff,
                    fa = EXCLUDED.fa,
                    ff_pct = EXCLUDED.ff_pct,
                    on_ice_shooting_pct = EXCLUDED.on_ice_shooting_pct,
                    on_ice_save_pct = EXCLUDED.on_ice_save_pct,
                    pdo = EXCLUDED.pdo,
                    oz_start_pct = EXCLUDED.oz_start_pct,
                    updated_at = NOW()
            """, stats)
            conn.commit()
            return True


def log_etl_run(
    job_name: str,
    status: str,
    job_type: str = "manual",
    records_processed: int = 0,
    error_message: str | None = None,
) -> int:
    """Log an ETL run to the database."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO etl_runs (job_name, job_type, status, records_processed, error_message)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (job_name, job_type, status, records_processed, error_message))
            result = cur.fetchone()
            conn.commit()
            return result["id"] if result else None


def update_etl_run(
    run_id: int,
    status: str,
    records_processed: int = 0,
    error_message: str | None = None,
) -> None:
    """Update an ETL run status."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE etl_runs
                SET status = %s, records_processed = %s, error_message = %s, completed_at = NOW()
                WHERE id = %s
            """, (status, records_processed, error_message, run_id))
            conn.commit()


def clear_caches() -> None:
    """Clear all lookup caches."""
    global _team_cache, _season_cache, _player_cache
    _team_cache = {}
    _season_cache = {}
    _player_cache = {}
