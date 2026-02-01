"""Initial load job - loads all historical data from 2008 to present."""

import sys
from datetime import datetime

from ..extract import NHLApiClient, NHLStatsApiClient, MoneyPuckClient
from ..transform import transform_player_bio, transform_skater_game_log, transform_goalie_game_log
from ..transform.advanced_stats import transform_moneypuck_skater
from ..load.loader import (
    upsert_player,
    upsert_skater_season_stats,
    upsert_goalie_season_stats,
    upsert_advanced_stats,
    get_season_id,
    get_team_id_by_abbrev,
    get_player_id,
    log_etl_run,
    update_etl_run,
    clear_caches,
)
from ..db import close_pool


def run_initial_load(start_year: int = 2008, end_year: int | None = None):
    """
    Run the initial historical data load.

    Args:
        start_year: First season start year (default 2008 for 2008-09 season)
        end_year: Last season start year (default: current year)
    """
    if end_year is None:
        end_year = datetime.now().year

    run_id = log_etl_run("initial_load", "running", job_type="initial_load")
    total_records = 0

    print(f"Starting initial load for seasons {start_year}-{start_year+1} to {end_year}-{end_year+1}")

    try:
        # Load players and season stats from NHL Stats API
        total_records += load_players_and_stats(start_year, end_year)

        # Load advanced stats from MoneyPuck
        total_records += load_moneypuck_stats(start_year, end_year)

        update_etl_run(run_id, "completed", total_records)
        print(f"\nInitial load completed! Total records: {total_records}")

    except Exception as e:
        update_etl_run(run_id, "failed", total_records, str(e))
        print(f"\nInitial load failed: {e}")
        raise
    finally:
        close_pool()


def load_players_and_stats(start_year: int, end_year: int) -> int:
    """Load players and season stats from NHL Stats API."""
    total = 0

    with NHLStatsApiClient() as client:
        for year in range(start_year, end_year + 1):
            season_str = f"{year}{year+1}"
            season_id = get_season_id(season_str)

            if not season_id:
                print(f"  Season {year}-{year+1} not found in database, skipping")
                continue

            print(f"\nLoading season {year}-{year+1}...")

            # Load skaters
            skater_count = 0
            for player_data in client.iter_all_skaters(season_str):
                try:
                    player = _transform_stats_api_player(player_data)
                    player_id = upsert_player(player)

                    if player_id:
                        stats = _transform_skater_stats(player_data, player_id, season_id)
                        upsert_skater_season_stats(stats)
                        skater_count += 1
                except Exception as e:
                    print(f"    Error loading skater {player_data.get('playerId')}: {e}")
                    continue

            print(f"  Loaded {skater_count} skaters")
            total += skater_count

            # Load goalies
            goalie_count = 0
            for player_data in client.iter_all_goalies(season_str):
                try:
                    player = _transform_stats_api_goalie(player_data)
                    player_id = upsert_player(player)

                    if player_id:
                        stats = _transform_goalie_stats(player_data, player_id, season_id)
                        upsert_goalie_season_stats(stats)
                        goalie_count += 1
                except Exception as e:
                    print(f"    Error loading goalie {player_data.get('playerId')}: {e}")
                    continue

            print(f"  Loaded {goalie_count} goalies")
            total += goalie_count

    return total


def load_moneypuck_stats(start_year: int, end_year: int) -> int:
    """Load advanced stats from MoneyPuck."""
    total = 0

    print("\nLoading MoneyPuck advanced stats...")

    with MoneyPuckClient() as client:
        for year, df in client.iter_seasons(start_year, end_year):
            season_str = f"{year}{year+1}"
            season_id = get_season_id(season_str)

            if not season_id:
                continue

            # Filter to 'all' situation for primary stats
            df_all = df[df["situation"] == "all"] if "situation" in df.columns else df

            count = 0
            errors = 0
            for _, row in df_all.iterrows():
                try:
                    stats = transform_moneypuck_skater(row, season_id)
                    if upsert_advanced_stats(stats):
                        count += 1
                except Exception as e:
                    errors += 1
                    if errors <= 3:  # Print first 3 errors
                        print(f"    MoneyPuck error: {e}")
                    continue
            if errors > 3:
                print(f"    ... and {errors - 3} more errors")

            print(f"  {year}-{year+1}: {count} advanced stat records")
            total += count

    return total


def _transform_stats_api_player(data: dict) -> dict:
    """Transform NHL Stats API skater data to player format."""
    team_abbrev = data.get("teamAbbrevs", "").split(",")[0] if data.get("teamAbbrevs") else None
    team_id = get_team_id_by_abbrev(team_abbrev) if team_abbrev else None

    return {
        "nhl_id": data.get("playerId"),
        "name": data.get("skaterFullName"),
        "first_name": data.get("firstName"),
        "last_name": data.get("lastName"),
        "position": data.get("positionCode"),
        "position_type": _get_position_type(data.get("positionCode")),
        "birth_date": data.get("birthDate"),
        "birth_city": data.get("birthCity"),
        "birth_country": data.get("birthCountryCode"),
        "nationality": data.get("nationalityCode"),
        "height_cm": None,
        "weight_kg": None,
        "shoots": data.get("shootsCatches"),
        "current_team_id": team_id,
        "is_active": True,
        "headshot_url": None,
    }


def _transform_stats_api_goalie(data: dict) -> dict:
    """Transform NHL Stats API goalie data to player format."""
    team_abbrev = data.get("teamAbbrevs", "").split(",")[0] if data.get("teamAbbrevs") else None
    team_id = get_team_id_by_abbrev(team_abbrev) if team_abbrev else None

    return {
        "nhl_id": data.get("playerId"),
        "name": data.get("goalieFullName"),
        "first_name": data.get("firstName"),
        "last_name": data.get("lastName"),
        "position": "G",
        "position_type": "Goalie",
        "birth_date": data.get("birthDate"),
        "birth_city": data.get("birthCity"),
        "birth_country": data.get("birthCountryCode"),
        "nationality": data.get("nationalityCode"),
        "height_cm": None,
        "weight_kg": None,
        "shoots": data.get("shootsCatches"),
        "current_team_id": team_id,
        "is_active": True,
        "headshot_url": None,
    }


def _transform_skater_stats(data: dict, player_id: int, season_id: int) -> dict:
    """Transform NHL Stats API skater stats to season stats format."""
    team_abbrev = data.get("teamAbbrevs", "").split(",")[0] if data.get("teamAbbrevs") else None
    team_id = get_team_id_by_abbrev(team_abbrev) if team_abbrev else None

    gp = data.get("gamesPlayed", 0)
    toi_total = data.get("timeOnIcePerGame", 0)  # Already in seconds per game

    return {
        "player_id": player_id,
        "season_id": season_id,
        "team_id": team_id,
        "games_played": gp,
        "goals": data.get("goals", 0),
        "assists": data.get("assists", 0),
        "points": data.get("points", 0),
        "plus_minus": data.get("plusMinus", 0),
        "pim": data.get("penaltyMinutes", 0),
        "pp_goals": data.get("ppGoals", 0),
        "pp_assists": data.get("ppPoints", 0) - data.get("ppGoals", 0) if data.get("ppPoints") else 0,
        "pp_points": data.get("ppPoints", 0),
        "sh_goals": data.get("shGoals", 0),
        "sh_assists": data.get("shPoints", 0) - data.get("shGoals", 0) if data.get("shPoints") else 0,
        "shots": data.get("shots", 0),
        "shooting_pct": data.get("shootingPct"),
        "toi_per_game_seconds": int(toi_total) if toi_total else 0,
        "hits": data.get("hits", 0),
        "blocks": data.get("blockedShots", 0),
        "faceoff_pct": data.get("faceoffWinPct"),
    }


def _transform_goalie_stats(data: dict, player_id: int, season_id: int) -> dict:
    """Transform NHL Stats API goalie stats to season stats format."""
    team_abbrev = data.get("teamAbbrevs", "").split(",")[0] if data.get("teamAbbrevs") else None
    team_id = get_team_id_by_abbrev(team_abbrev) if team_abbrev else None

    return {
        "player_id": player_id,
        "season_id": season_id,
        "team_id": team_id,
        "games_played": data.get("gamesPlayed", 0),
        "games_started": data.get("gamesStarted", 0),
        "wins": data.get("wins", 0),
        "losses": data.get("losses", 0),
        "ot_losses": data.get("otLosses", 0),
        "goals_against": data.get("goalsAgainst", 0),
        "goals_against_avg": data.get("goalsAgainstAverage"),
        "saves": data.get("saves", 0),
        "shots_against": data.get("shotsAgainst", 0),
        "save_pct": data.get("savePercentage"),
        "shutouts": data.get("shutouts", 0),
        "toi_total_seconds": data.get("timeOnIce", 0),
    }


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

    parser = argparse.ArgumentParser(description="Run initial ETL load")
    parser.add_argument("--start-year", type=int, default=2008, help="Start year (default: 2008)")
    parser.add_argument("--end-year", type=int, default=None, help="End year (default: current)")
    args = parser.parse_args()

    run_initial_load(args.start_year, args.end_year)
