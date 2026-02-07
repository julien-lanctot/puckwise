"""Feature engineering for skater projections."""

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from ..db import fetch_all
from ..config import config


class SkaterFeatureBuilder:
    """Build features for skater projection models.

    Key features:
    - Historical production (1yr, 3yr, 5yr rolling PPG)
    - Age (peak 24-28, decline curve)
    - Games played % (durability)
    - Team context (projected team GF)
    - xG vs actual goals (regression signal)
    - Shooting % z-score (regression signal)
    - PDO deviation from 1.0 (luck indicator)
    """

    # Age curve parameters (peak production age range)
    PEAK_AGE_START = 24
    PEAK_AGE_END = 28

    # Season constants
    FULL_SEASON_GAMES = 82

    def __init__(self, target_season: str):
        """Initialize with target season for predictions.

        Args:
            target_season: Season ID to predict (e.g., "20242025")
        """
        self.target_season = target_season
        self.target_year = int(target_season[:4])

    def build_training_data(self, min_seasons: int = 2) -> pd.DataFrame:
        """Build training dataset from historical data.

        Returns DataFrame with features and target (next season points).
        Each row is a player-season with features from that season
        and target = their points in the following season.
        """
        # Get all season stats with player info
        query = """
            SELECT
                s.player_id,
                s.season_id,
                s.games_played,
                s.goals,
                s.assists,
                s.points,
                s.plus_minus,
                s.shots,
                s.shooting_pct,
                s.toi_per_game_seconds,
                s.pp_points,
                s.hits,
                s.blocks,
                p.position,
                p.birth_date,
                p.nhl_id
            FROM skater_season_stats s
            JOIN players p ON s.player_id = p.id
            WHERE s.games_played >= %s
            ORDER BY s.player_id, s.season_id
        """
        rows = fetch_all(query, (config.min_games_threshold,))

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = self._convert_decimals(df)

        # Get advanced stats
        adv_query = """
            SELECT
                player_id,
                season_id,
                xg,
                goals_above_expected,
                cf_pct,
                pdo,
                war,
                oz_start_pct
            FROM skater_advanced_stats
            WHERE situation = 'all'
        """
        adv_rows = fetch_all(adv_query)

        if adv_rows:
            adv_df = pd.DataFrame(adv_rows)
            adv_df = self._convert_decimals(adv_df)
            df = df.merge(adv_df, on=["player_id", "season_id"], how="left")

        # Calculate features
        df = self._add_age_features(df)
        df = self._add_rolling_features(df)
        df = self._add_regression_features(df)
        df = self._add_durability_features(df)
        df = self._add_target_variable(df)

        # Filter to players with enough history
        season_counts = df.groupby("player_id")["season_id"].transform("count")
        df = df[season_counts >= min_seasons]

        # Drop rows without target (last season for each player)
        df = df.dropna(subset=["target_points"])

        return df

    def build_prediction_features(self) -> pd.DataFrame:
        """Build features for current players to make predictions.

        Uses most recent available season data to predict target_season.
        """
        # Get most recent season before target
        prev_season = self._get_previous_season(self.target_season)

        query = """
            SELECT
                s.player_id,
                s.season_id,
                s.games_played,
                s.goals,
                s.assists,
                s.points,
                s.plus_minus,
                s.shots,
                s.shooting_pct,
                s.toi_per_game_seconds,
                s.pp_points,
                s.hits,
                s.blocks,
                p.position,
                p.birth_date,
                p.nhl_id,
                p.name
            FROM skater_season_stats s
            JOIN players p ON s.player_id = p.id
            WHERE s.season_id = %s
              AND s.games_played >= %s
              AND p.is_active = true
        """
        rows = fetch_all(query, (prev_season, config.min_games_threshold))

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = self._convert_decimals(df)

        # Get advanced stats
        adv_query = """
            SELECT
                player_id,
                season_id,
                xg,
                goals_above_expected,
                cf_pct,
                pdo,
                war,
                oz_start_pct
            FROM skater_advanced_stats
            WHERE situation = 'all' AND season_id = %s
        """
        adv_rows = fetch_all(adv_query, (prev_season,))

        if adv_rows:
            adv_df = pd.DataFrame(adv_rows)
            adv_df = self._convert_decimals(adv_df)
            df = df.merge(adv_df, on=["player_id", "season_id"], how="left")

        # Get historical data for rolling features
        hist_query = """
            SELECT
                s.player_id,
                s.season_id,
                s.games_played,
                s.points
            FROM skater_season_stats s
            WHERE s.player_id = ANY(%s)
              AND s.games_played >= %s
            ORDER BY s.player_id, s.season_id
        """
        player_ids = list(df["player_id"].unique())
        hist_rows = fetch_all(hist_query, (player_ids, config.min_games_threshold))

        if hist_rows:
            hist_df = pd.DataFrame(hist_rows)
            hist_df = self._convert_decimals(hist_df)
            df = self._add_rolling_features_from_history(df, hist_df)

        # Calculate features
        df = self._add_age_features(df, prediction_year=self.target_year)
        df = self._add_regression_features(df)
        df = self._add_durability_features(df)

        return df

    def _add_age_features(self, df: pd.DataFrame, prediction_year: int | None = None) -> pd.DataFrame:
        """Add age-related features."""
        df = df.copy()

        def calc_age(row):
            if pd.isna(row["birth_date"]):
                return None
            birth = row["birth_date"]
            if prediction_year:
                # Age at start of prediction season
                return prediction_year - birth.year
            else:
                # Age at start of the season in the row
                season_year = int(row["season_id"][:4])
                return season_year - birth.year

        df["age"] = df.apply(calc_age, axis=1)

        # Age curve features
        df["age_peak"] = df["age"].apply(
            lambda a: 1.0 if pd.isna(a) else (
                1.0 if self.PEAK_AGE_START <= a <= self.PEAK_AGE_END else 0.0
            )
        )

        # Years from peak (negative = pre-peak, positive = post-peak)
        def years_from_peak(age):
            if pd.isna(age):
                return 0
            if age < self.PEAK_AGE_START:
                return age - self.PEAK_AGE_START
            elif age > self.PEAK_AGE_END:
                return age - self.PEAK_AGE_END
            return 0

        df["years_from_peak"] = df["age"].apply(years_from_peak)

        # Decline factor (exponential decay after peak)
        df["age_decline_factor"] = df["years_from_peak"].apply(
            lambda y: np.exp(-0.05 * max(0, y))  # 5% decline per year after peak
        )

        return df

    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling average features (1yr, 3yr, 5yr PPG)."""
        df = df.copy()
        df = df.sort_values(["player_id", "season_id"])

        # Points per game
        df["ppg"] = df["points"] / df["games_played"].clip(lower=1)

        # Rolling averages by player
        for window in [1, 3, 5]:
            col_name = f"ppg_{window}yr"
            df[col_name] = df.groupby("player_id")["ppg"].transform(
                lambda x: x.rolling(window=window, min_periods=1).mean()
            )

        # Goals per game rolling
        df["gpg"] = df["goals"] / df["games_played"].clip(lower=1)
        df["gpg_3yr"] = df.groupby("player_id")["gpg"].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean()
        )

        return df

    def _add_rolling_features_from_history(
        self, df: pd.DataFrame, hist_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Add rolling features using separate history DataFrame."""
        df = df.copy()

        hist_df = hist_df.sort_values(["player_id", "season_id"])
        hist_df["ppg"] = hist_df["points"] / hist_df["games_played"].clip(lower=1)

        # Calculate rolling stats per player
        rolling_stats = []
        for player_id in df["player_id"].unique():
            player_hist = hist_df[hist_df["player_id"] == player_id].copy()

            ppg_values = player_hist["ppg"].values

            stats = {
                "player_id": player_id,
                "ppg_1yr": ppg_values[-1] if len(ppg_values) >= 1 else None,
                "ppg_3yr": np.mean(ppg_values[-3:]) if len(ppg_values) >= 1 else None,
                "ppg_5yr": np.mean(ppg_values[-5:]) if len(ppg_values) >= 1 else None,
            }
            rolling_stats.append(stats)

        rolling_df = pd.DataFrame(rolling_stats)
        df = df.merge(rolling_df, on="player_id", how="left")

        # Current PPG
        df["ppg"] = df["points"] / df["games_played"].clip(lower=1)
        df["gpg"] = df["goals"] / df["games_played"].clip(lower=1)
        df["gpg_3yr"] = df["ppg_3yr"]  # Approximation

        return df

    def _add_regression_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add regression-to-mean indicators."""
        df = df.copy()

        # Shooting percentage z-score (league average ~10%)
        league_sh_pct = df["shooting_pct"].mean() or 10.0
        league_sh_std = df["shooting_pct"].std() or 3.0
        df["sh_pct_zscore"] = (df["shooting_pct"] - league_sh_pct) / league_sh_std

        # PDO deviation from 1.0 (luck indicator)
        if "pdo" in df.columns:
            df["pdo_deviation"] = df["pdo"].fillna(1.0) - 1.0
        else:
            df["pdo_deviation"] = 0.0

        # Goals above expected (xG regression signal)
        if "goals_above_expected" in df.columns:
            df["goals_above_xg"] = df["goals_above_expected"].fillna(0)
        else:
            df["goals_above_xg"] = 0.0

        # Regression score (-10 to +10)
        # Positive = sell high (lucky), Negative = buy low (unlucky)
        df["regression_score"] = (
            df["sh_pct_zscore"] * 2 +
            df["pdo_deviation"] * 50 +
            df["goals_above_xg"] * 0.5
        ).clip(-10, 10)

        return df

    def _add_durability_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add games played / durability features."""
        df = df.copy()

        df["games_pct"] = df["games_played"] / self.FULL_SEASON_GAMES
        df["games_pct"] = df["games_pct"].clip(upper=1.0)

        return df

    def _add_target_variable(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add next season points as target variable."""
        df = df.copy()
        df = df.sort_values(["player_id", "season_id"])

        # Shift points to get next season
        df["target_points"] = df.groupby("player_id")["points"].shift(-1)
        df["target_games"] = df.groupby("player_id")["games_played"].shift(-1)
        df["target_ppg"] = df["target_points"] / df["target_games"].clip(lower=1)

        return df

    def _get_previous_season(self, season_id: str) -> str:
        """Get the season before the given one."""
        start_year = int(season_id[:4])
        end_year = int(season_id[4:])
        return f"{start_year - 1}{end_year - 1}"

    def get_feature_columns(self) -> list[str]:
        """Get list of feature column names for model training."""
        return [
            # Historical production
            "ppg_1yr",
            "ppg_3yr",
            "ppg_5yr",
            "gpg_3yr",
            # Age
            "age",
            "age_peak",
            "years_from_peak",
            "age_decline_factor",
            # Durability
            "games_pct",
            # Regression signals
            "sh_pct_zscore",
            "pdo_deviation",
            "goals_above_xg",
            # Ice time
            "toi_per_game_seconds",
            # Position encoded
            "is_center",
            "is_winger",
            "is_defenseman",
        ]

    def encode_position(self, df: pd.DataFrame) -> pd.DataFrame:
        """One-hot encode position."""
        df = df.copy()
        df["is_center"] = (df["position"] == "C").astype(int)
        df["is_winger"] = df["position"].isin(["LW", "RW"]).astype(int)
        df["is_defenseman"] = (df["position"] == "D").astype(int)
        return df

    def _convert_decimals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Decimal columns to float for numpy compatibility."""
        from decimal import Decimal

        df = df.copy()
        for col in df.columns:
            if df[col].dtype == object:
                # Check if column contains Decimals
                sample = df[col].dropna().head(1)
                if len(sample) > 0 and isinstance(sample.iloc[0], Decimal):
                    df[col] = df[col].astype(float)
        return df
