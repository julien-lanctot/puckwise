"""Transform game log data from NHL API format to database format."""

from datetime import date
from typing import Any


def transform_skater_game_log(
    game: dict[str, Any],
    player_id: int,
    team_id: int,
) -> dict[str, Any]:
    """Transform a single skater game log entry."""
    return {
        "player_id": player_id,
        "game_id": game.get("gameId"),
        "game_date": game.get("gameDate"),
        "team_id": team_id,
        "goals": game.get("goals", 0),
        "assists": game.get("assists", 0),
        "points": game.get("points", 0),
        "plus_minus": game.get("plusMinus", 0),
        "pim": game.get("pim", 0),
        "shots": game.get("shots", 0),
        "shooting_pct": _calc_shooting_pct(game.get("goals", 0), game.get("shots", 0)),
        "toi_seconds": _toi_to_seconds(game.get("toi")),
        "toi_even_seconds": _toi_to_seconds(game.get("evenTimeOnIce")),
        "toi_pp_seconds": _toi_to_seconds(game.get("powerPlayTimeOnIce")),
        "toi_sh_seconds": _toi_to_seconds(game.get("shorthandedTimeOnIce")),
        "pp_goals": game.get("powerPlayGoals", 0),
        "pp_assists": game.get("powerPlayAssists", 0) if "powerPlayAssists" in game else _calc_pp_assists(game),
        "sh_goals": game.get("shorthandedGoals", 0),
        "sh_assists": game.get("shorthandedAssists", 0) if "shorthandedAssists" in game else 0,
        "hits": game.get("hits", 0),
        "blocks": game.get("blockedShots", 0) or game.get("blocks", 0),
        "giveaways": game.get("giveaways", 0),
        "takeaways": game.get("takeaways", 0),
        "faceoff_wins": game.get("faceoffWins", 0) or game.get("faceoffWinningPctg", 0),
        "faceoff_losses": _calc_faceoff_losses(game),
        "is_home": game.get("homeRoadFlag") == "H",
    }


def transform_goalie_game_log(
    game: dict[str, Any],
    player_id: int,
    team_id: int,
) -> dict[str, Any]:
    """Transform a single goalie game log entry."""
    saves = game.get("savePctg", 0) * game.get("shotsAgainst", 0) if game.get("savePctg") else game.get("saves", 0)
    shots_against = game.get("shotsAgainst", 0)

    return {
        "player_id": player_id,
        "game_id": game.get("gameId"),
        "game_date": game.get("gameDate"),
        "team_id": team_id,
        "decision": game.get("decision"),
        "goals_against": game.get("goalsAgainst", 0),
        "saves": int(saves) if saves else 0,
        "shots_against": shots_against,
        "save_pct": game.get("savePctg"),
        "toi_seconds": _toi_to_seconds(game.get("toi")),
        "shutout": game.get("shutouts", 0) > 0 or game.get("goalsAgainst", 0) == 0,
        "goals": game.get("goals", 0),
        "assists": game.get("assists", 0),
        "pim": game.get("pim", 0),
        "is_home": game.get("homeRoadFlag") == "H",
        "is_starter": game.get("gamesStarted", 0) > 0 if "gamesStarted" in game else True,
    }


def transform_boxscore_skater(
    player: dict[str, Any],
    game_id: int,
    game_date: str,
    team_id: int,
    is_home: bool,
) -> dict[str, Any]:
    """Transform boxscore player stats to game log format."""
    return {
        "nhl_player_id": player.get("playerId"),
        "game_id": game_id,
        "game_date": game_date,
        "team_id": team_id,
        "goals": player.get("goals", 0),
        "assists": player.get("assists", 0),
        "points": player.get("goals", 0) + player.get("assists", 0),
        "plus_minus": player.get("plusMinus", 0),
        "pim": player.get("pim", 0),
        "shots": player.get("sog", 0) or player.get("shots", 0),
        "toi_seconds": _toi_to_seconds(player.get("toi")),
        "hits": player.get("hits", 0),
        "blocks": player.get("blockedShots", 0) or player.get("blocks", 0),
        "giveaways": player.get("giveaways", 0),
        "takeaways": player.get("takeaways", 0),
        "faceoff_wins": player.get("faceoffWins", 0),
        "faceoff_losses": player.get("faceoffLosses", 0),
        "is_home": is_home,
    }


def _toi_to_seconds(toi: str | int | None) -> int:
    """Convert time on ice string (MM:SS) or minutes to seconds."""
    if toi is None:
        return 0
    if isinstance(toi, (int, float)):
        # Assume it's already in seconds or minutes
        return int(toi) if toi > 100 else int(toi * 60)
    try:
        parts = str(toi).split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(float(toi) * 60)
    except (ValueError, TypeError):
        return 0


def _calc_shooting_pct(goals: int, shots: int) -> float | None:
    """Calculate shooting percentage."""
    if shots == 0:
        return None
    return round(goals / shots * 100, 2)


def _calc_pp_assists(game: dict[str, Any]) -> int:
    """Calculate PP assists from PP points minus PP goals."""
    pp_points = game.get("powerPlayPoints", 0)
    pp_goals = game.get("powerPlayGoals", 0)
    return max(0, pp_points - pp_goals)


def _calc_faceoff_losses(game: dict[str, Any]) -> int:
    """Calculate faceoff losses from total and wins."""
    wins = game.get("faceoffWins", 0) or 0
    total = game.get("faceoffs", 0) or game.get("faceoffsTaken", 0) or 0
    if total > 0:
        return total - wins
    return 0
