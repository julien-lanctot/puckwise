"""Daily update job - loads recent games and updates stats."""

from datetime import datetime, timedelta
from typing import Any

from ..extract import NHLApiClient, NHLStatsApiClient
from ..transform.game_logs import transform_boxscore_skater
from ..load.loader import (
    upsert_player,
    upsert_game,
    upsert_skater_game_log,
    upsert_goalie_game_log,
    get_season_id,
    get_team_id_by_abbrev,
    get_team_id_by_nhl_id,
    get_player_id,
    get_game_id,
    log_etl_run,
    update_etl_run,
)
from ..db import close_pool, get_connection


def run_daily_update(date: str | None = None):
    """
    Run daily update for a specific date.

    Args:
        date: Date string YYYY-MM-DD (default: yesterday)
    """
    if date is None:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    run_id = log_etl_run("daily_update", "running")
    total_records = 0

    print(f"Running daily update for {date}")

    try:
        with NHLApiClient() as client:
            # Get schedule for the date
            schedule = client.get_schedule(date)
            games = schedule.get("gameWeek", [{}])[0].get("games", [])

            if not games:
                print(f"No games found for {date}")
                update_etl_run(run_id, "completed", 0)
                return

            print(f"Found {len(games)} games")

            for game_data in games:
                game_id = game_data.get("id")
                game_state = game_data.get("gameState")

                # Only process completed games
                if game_state not in ("FINAL", "OFF"):
                    print(f"  Game {game_id} not final (state: {game_state}), skipping")
                    continue

                try:
                    records = process_game(client, game_data, date)
                    total_records += records
                    print(f"  Game {game_id}: {records} records")
                except Exception as e:
                    print(f"  Error processing game {game_id}: {e}")
                    continue

        update_etl_run(run_id, "completed", total_records)
        print(f"\nDaily update completed! Total records: {total_records}")

    except Exception as e:
        update_etl_run(run_id, "failed", total_records, str(e))
        print(f"\nDaily update failed: {e}")
        raise
    finally:
        close_pool()


def process_game(client: NHLApiClient, game_data: dict, date: str) -> int:
    """Process a single game, loading game and player stats."""
    records = 0
    nhl_game_id = game_data.get("id")

    # Get detailed boxscore
    boxscore = client.get_game_boxscore(nhl_game_id)

    # Determine season
    season_str = str(game_data.get("season", ""))
    season_id = get_season_id(season_str)

    if not season_id:
        print(f"    Season {season_str} not found")
        return 0

    # Get team IDs
    home_team = boxscore.get("homeTeam", {})
    away_team = boxscore.get("awayTeam", {})

    home_team_id = get_team_id_by_abbrev(home_team.get("abbrev", ""))
    away_team_id = get_team_id_by_abbrev(away_team.get("abbrev", ""))

    # Insert/update game
    game = {
        "nhl_game_id": nhl_game_id,
        "season_id": season_id,
        "game_date": date,
        "game_type": game_data.get("gameType", 2),
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "home_score": home_team.get("score", 0),
        "away_score": away_team.get("score", 0),
        "status": "FINAL",
        "venue": game_data.get("venue", {}).get("default"),
    }

    db_game_id = upsert_game(game)
    if not db_game_id:
        print(f"    Failed to insert game {nhl_game_id}")
        return 0
    records += 1

    # Process player stats from boxscore
    player_stats = boxscore.get("playerByGameStats", {})

    # Home team players
    records += process_team_players(
        player_stats.get("homeTeam", {}),
        db_game_id,
        date,
        home_team_id,
        is_home=True,
    )

    # Away team players
    records += process_team_players(
        player_stats.get("awayTeam", {}),
        db_game_id,
        date,
        away_team_id,
        is_home=False,
    )

    return records


def process_team_players(
    team_stats: dict,
    game_id: int,
    game_date: str,
    team_id: int,
    is_home: bool,
) -> int:
    """Process all players for a team in a game."""
    records = 0

    # Process forwards
    for player in team_stats.get("forwards", []):
        if process_skater(player, game_id, game_date, team_id, is_home):
            records += 1

    # Process defense
    for player in team_stats.get("defense", []):
        if process_skater(player, game_id, game_date, team_id, is_home):
            records += 1

    # Process goalies
    for player in team_stats.get("goalies", []):
        if process_goalie(player, game_id, game_date, team_id, is_home):
            records += 1

    return records


def process_skater(
    player: dict,
    game_id: int,
    game_date: str,
    team_id: int,
    is_home: bool,
) -> bool:
    """Process a single skater's game log."""
    nhl_player_id = player.get("playerId")
    if not nhl_player_id:
        return False

    player_id = get_player_id(nhl_player_id)
    if not player_id:
        # Player doesn't exist, create minimal record
        new_player = {
            "nhl_id": nhl_player_id,
            "name": f"{player.get('firstName', {}).get('default', '')} {player.get('lastName', {}).get('default', '')}".strip(),
            "first_name": player.get("firstName", {}).get("default"),
            "last_name": player.get("lastName", {}).get("default"),
            "position": player.get("position"),
            "position_type": _get_position_type(player.get("position")),
            "birth_date": None,
            "birth_city": None,
            "birth_country": None,
            "nationality": None,
            "height_cm": None,
            "weight_kg": None,
            "shoots": None,
            "current_team_id": team_id,
            "is_active": True,
            "headshot_url": None,
        }
        player_id = upsert_player(new_player)

    if not player_id:
        return False

    # Transform and load game log
    toi_str = player.get("toi", "0:00")
    toi_seconds = _toi_to_seconds(toi_str)

    log = {
        "player_id": player_id,
        "game_id": game_id,
        "game_date": game_date,
        "team_id": team_id,
        "goals": player.get("goals", 0),
        "assists": player.get("assists", 0),
        "points": player.get("goals", 0) + player.get("assists", 0),
        "plus_minus": player.get("plusMinus", 0),
        "pim": player.get("pim", 0),
        "shots": player.get("sog", 0) or player.get("shots", 0),
        "shooting_pct": None,
        "toi_seconds": toi_seconds,
        "toi_even_seconds": 0,
        "toi_pp_seconds": 0,
        "toi_sh_seconds": 0,
        "pp_goals": 0,
        "pp_assists": 0,
        "sh_goals": 0,
        "sh_assists": 0,
        "hits": player.get("hits", 0),
        "blocks": player.get("blockedShots", 0),
        "giveaways": player.get("giveaways", 0),
        "takeaways": player.get("takeaways", 0),
        "faceoff_wins": player.get("faceoffWins", 0),
        "faceoff_losses": player.get("faceoffLosses", 0),
        "is_home": is_home,
    }

    return upsert_skater_game_log(log)


def process_goalie(
    player: dict,
    game_id: int,
    game_date: str,
    team_id: int,
    is_home: bool,
) -> bool:
    """Process a single goalie's game log."""
    nhl_player_id = player.get("playerId")
    if not nhl_player_id:
        return False

    player_id = get_player_id(nhl_player_id)
    if not player_id:
        # Create minimal record
        new_player = {
            "nhl_id": nhl_player_id,
            "name": f"{player.get('firstName', {}).get('default', '')} {player.get('lastName', {}).get('default', '')}".strip(),
            "first_name": player.get("firstName", {}).get("default"),
            "last_name": player.get("lastName", {}).get("default"),
            "position": "G",
            "position_type": "Goalie",
            "birth_date": None,
            "birth_city": None,
            "birth_country": None,
            "nationality": None,
            "height_cm": None,
            "weight_kg": None,
            "shoots": None,
            "current_team_id": team_id,
            "is_active": True,
            "headshot_url": None,
        }
        player_id = upsert_player(new_player)

    if not player_id:
        return False

    # Transform and load game log
    saves = player.get("saves", 0) or player.get("saveShotsAgainst", "0").split("/")[0] if player.get("saveShotsAgainst") else 0
    shots_against = player.get("shotsAgainst", 0)

    if isinstance(saves, str):
        try:
            saves = int(saves)
        except ValueError:
            saves = 0

    log = {
        "player_id": player_id,
        "game_id": game_id,
        "game_date": game_date,
        "team_id": team_id,
        "decision": player.get("decision"),
        "goals_against": player.get("goalsAgainst", 0),
        "saves": saves,
        "shots_against": shots_against,
        "save_pct": player.get("savePercentage") or player.get("savePctg"),
        "toi_seconds": _toi_to_seconds(player.get("toi", "0:00")),
        "shutout": player.get("goalsAgainst", 0) == 0,
        "goals": 0,
        "assists": 0,
        "pim": player.get("pim", 0),
        "is_home": is_home,
        "is_starter": player.get("starter", False),
    }

    return upsert_goalie_game_log(log)


def _toi_to_seconds(toi: str | int | None) -> int:
    """Convert time on ice string (MM:SS) to seconds."""
    if toi is None:
        return 0
    if isinstance(toi, (int, float)):
        return int(toi)
    try:
        parts = str(toi).split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(float(toi) * 60)
    except (ValueError, TypeError):
        return 0


def _get_position_type(position: str | None) -> str | None:
    """Map position code to position type."""
    if not position:
        return None
    position = position.upper()
    if position == "G":
        return "Goalie"
    elif position == "D":
        return "Defenseman"
    elif position in ("C", "L", "R", "LW", "RW", "W", "F"):
        return "Forward"
    return None


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run daily ETL update")
    parser.add_argument("--date", type=str, default=None, help="Date YYYY-MM-DD (default: yesterday)")
    args = parser.parse_args()

    run_daily_update(args.date)
