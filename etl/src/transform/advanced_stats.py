"""Transform MoneyPuck advanced stats to database format."""

from typing import Any
import pandas as pd


def transform_moneypuck_skater(row: pd.Series, season_id: str) -> dict[str, Any]:
    """
    Transform a MoneyPuck skater row to database format.

    Args:
        row: A pandas Series from MoneyPuck CSV
        season_id: The database season_id string (e.g., '20232024')
    """
    on_ice_xg_for = _safe_float(row.get("OnIce_F_xGoals"))
    on_ice_xg_against = _safe_float(row.get("OnIce_A_xGoals"))

    return {
        "nhl_player_id": int(row.get("playerId", 0)),
        "season_id": season_id,
        "situation": row.get("situation", "all"),
        # Games and TOI
        "games_played": _safe_int(row.get("games_played")),
        "toi_minutes": _calc_toi_minutes(row),
        # Individual expected goals
        "xg": _safe_float(row.get("I_F_xGoals")),
        "goals_above_expected": _calc_goals_above_xg(row),
        # On-ice expected goals
        "on_ice_xg_for": on_ice_xg_for,
        "on_ice_xg_against": on_ice_xg_against,
        "xg_diff": _calc_xg_diff(on_ice_xg_for, on_ice_xg_against),
        # Corsi (shot attempts)
        "cf": _safe_int(row.get("OnIce_F_shotAttempts")),
        "ca": _safe_int(row.get("OnIce_A_shotAttempts")),
        "cf_pct": _safe_float(row.get("onIce_corsiPercentage")),
        # Fenwick (unblocked shot attempts)
        "ff": _safe_int(row.get("OnIce_F_unblockedShotAttempts")),
        "fa": _safe_int(row.get("OnIce_A_unblockedShotAttempts")),
        "ff_pct": _safe_float(row.get("onIce_fenwickPercentage")),
        # On-ice shooting/save percentage
        "on_ice_shooting_pct": _calc_on_ice_sh_pct(row),
        "on_ice_save_pct": _calc_on_ice_sv_pct(row),
        "pdo": _calc_pdo(row),
        # Zone starts
        "oz_start_pct": _calc_oz_start_pct(row),
    }


def transform_moneypuck_goalie(row: pd.Series, season_id: int) -> dict[str, Any]:
    """Transform a MoneyPuck goalie row to database format."""
    return {
        "nhl_player_id": int(row.get("playerId", 0)),
        "season_id": season_id,
        "situation": row.get("situation", "all"),
        "xga": _safe_float(row.get("xGoalsAgainst")),
        "goals_saved_above_expected": _safe_float(row.get("goalsSavedAboveExpected")),
        "low_danger_sv_pct": _safe_float(row.get("lowDangerSavePercentage")),
        "medium_danger_sv_pct": _safe_float(row.get("mediumDangerSavePercentage")),
        "high_danger_sv_pct": _safe_float(row.get("highDangerSavePercentage")),
    }


def _safe_int(val: Any) -> int | None:
    """Safely convert to int."""
    if pd.isna(val) or val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> float | None:
    """Safely convert to float."""
    if pd.isna(val) or val is None:
        return None
    try:
        return round(float(val), 4)
    except (ValueError, TypeError):
        return None


def _calc_goals_above_xg(row: pd.Series) -> float | None:
    """Calculate goals above expected goals."""
    goals = _safe_float(row.get("I_F_goals"))
    xg = _safe_float(row.get("I_F_xGoals"))
    if goals is not None and xg is not None:
        return round(goals - xg, 2)
    return None


def _calc_toi_minutes(row: pd.Series) -> float | None:
    """Convert icetime (seconds) to minutes."""
    icetime = _safe_float(row.get("icetime"))
    if icetime is not None:
        return round(icetime / 60, 2)
    return None


def _calc_xg_diff(xg_for: float | None, xg_against: float | None) -> float | None:
    """Calculate xG differential."""
    if xg_for is not None and xg_against is not None:
        return round(xg_for - xg_against, 2)
    return None


def _calc_on_ice_sh_pct(row: pd.Series) -> float | None:
    """Calculate on-ice shooting percentage (goals for / shots on goal for)."""
    goals = _safe_float(row.get("OnIce_F_goals"))
    shots = _safe_float(row.get("OnIce_F_shotsOnGoal"))
    if goals is not None and shots and shots > 0:
        return round(goals / shots * 100, 2)  # Percentage format (10.5)
    return None


def _calc_on_ice_sv_pct(row: pd.Series) -> float | None:
    """Calculate on-ice save percentage as decimal (0.920 not 92.0)."""
    goals_against = _safe_float(row.get("OnIce_A_goals"))
    shots_against = _safe_float(row.get("OnIce_A_shotsOnGoal"))
    if goals_against is not None and shots_against and shots_against > 0:
        return round(1 - goals_against / shots_against, 3)  # Decimal format (0.920)
    return None


def _calc_pdo(row: pd.Series) -> float | None:
    """Calculate PDO (on-ice sh% + on-ice sv%). Expected ~1.000."""
    goals = _safe_float(row.get("OnIce_F_goals"))
    shots = _safe_float(row.get("OnIce_F_shotsOnGoal"))
    goals_against = _safe_float(row.get("OnIce_A_goals"))
    shots_against = _safe_float(row.get("OnIce_A_shotsOnGoal"))

    if all(v is not None for v in [goals, shots, goals_against, shots_against]):
        if shots > 0 and shots_against > 0:
            sh_pct = goals / shots  # Decimal (0.10)
            sv_pct = 1 - goals_against / shots_against  # Decimal (0.92)
            return round(sh_pct + sv_pct, 3)  # ~1.000
    return None


def _calc_oz_start_pct(row: pd.Series) -> float | None:
    """Calculate offensive zone start percentage."""
    oz = _safe_float(row.get("I_F_oZoneShiftStarts"))
    dz = _safe_float(row.get("I_F_dZoneShiftStarts"))
    nz = _safe_float(row.get("I_F_neutralZoneShiftStarts"))
    if oz is not None and dz is not None:
        total = (oz or 0) + (dz or 0) + (nz or 0)
        if total > 0:
            return round(oz / total * 100, 2)
    return None


def _calc_dz_start_pct(row: pd.Series) -> float | None:
    """Calculate defensive zone start percentage."""
    oz = _safe_float(row.get("I_F_oZoneShiftStarts"))
    dz = _safe_float(row.get("I_F_dZoneShiftStarts"))
    nz = _safe_float(row.get("I_F_neutralZoneShiftStarts"))
    if oz is not None and dz is not None:
        total = (oz or 0) + (dz or 0) + (nz or 0)
        if total > 0:
            return round(dz / total * 100, 2)
    return None
