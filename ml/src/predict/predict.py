"""Prediction pipeline for generating player projections."""

import logging
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import config
from ..db import get_connection, fetch_all
from ..features import SkaterFeatureBuilder
from ..models import XGBoostModel, RidgeModel, BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Predictor:
    """Generate and store player projections."""

    def __init__(
        self,
        target_season: str,
        model_type: str = "xgboost",
        model_path: Path | None = None,
    ):
        """Initialize predictor.

        Args:
            target_season: Season to predict (e.g., "20242025")
            model_type: Model to use ("xgboost" or "ridge")
            model_path: Path to trained model file
        """
        self.target_season = target_season
        self.model_type = model_type
        self.feature_builder = SkaterFeatureBuilder(target_season)

        # Load model
        if model_path is None:
            model_path = config.model_dir / f"{model_type}_latest.joblib"

        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        if model_type == "xgboost":
            self.model = XGBoostModel.load(model_path)
        else:
            self.model = RidgeModel.load(model_path)

        logger.info(f"Loaded {model_type} model from {model_path}")

    def run(
        self,
        projection_type: str = "season",
        save_to_db: bool = True,
    ) -> pd.DataFrame:
        """Generate projections for all active players.

        Args:
            projection_type: Type of projection (season, rolling_14d, rolling_30d)
            save_to_db: Whether to save projections to database

        Returns:
            DataFrame with projections
        """
        logger.info(f"Generating {projection_type} projections for {self.target_season}")

        # Build prediction features
        df = self.feature_builder.build_prediction_features()

        if df.empty:
            logger.warning("No players found for predictions")
            return pd.DataFrame()

        logger.info(f"Building projections for {len(df)} players")

        # Encode position
        df = self.feature_builder.encode_position(df)

        # Get features
        feature_cols = self.feature_builder.get_feature_columns()

        # Add missing columns
        for col in feature_cols:
            if col not in df.columns:
                df[col] = 0

        X = df[feature_cols].astype(float)

        # Generate predictions with intervals
        preds, lower, upper = self.model.predict_with_intervals(X)

        # Ensure numpy arrays
        preds = np.asarray(preds, dtype=float)
        lower = np.asarray(lower, dtype=float)
        upper = np.asarray(upper, dtype=float)

        # Build results DataFrame
        results = pd.DataFrame({
            "player_id": df["player_id"],
            "nhl_id": df["nhl_id"],
            "name": df["name"],
            "position": df["position"],
            "season_id": self.target_season,
            "projection_type": projection_type,
            "projection_date": date.today(),
            # Projected stats
            "projected_points": np.round(preds, 1),
            "confidence_low": np.round(lower, 1),
            "confidence_high": np.round(upper, 1),
            # Estimated breakdowns (based on historical ratios)
            "projected_goals": np.round(preds * 0.4, 1),  # ~40% goals
            "projected_assists": np.round(preds * 0.6, 1),  # ~60% assists
            "projected_games": 82,  # Full season default
            # Regression indicators from features
            "regression_score": df["regression_score"].values.astype(float) if "regression_score" in df else 0,
        })

        # Determine regression flags
        results["regression_flag"] = results["regression_score"].apply(
            lambda x: "sell_high" if x > 3 else ("buy_low" if x < -3 else None)
        )

        # Calculate regression reasons
        results["regression_reasons"] = results.apply(
            lambda row: self._get_regression_reasons(df, row.name), axis=1
        )

        # Add model info
        results["model_type"] = self.model_type
        results["model_version"] = self.model.version

        # Rank by projected points
        results["fantasy_rank"] = results["projected_points"].rank(
            ascending=False, method="min"
        ).astype(int)

        logger.info(f"Generated {len(results)} projections")
        logger.info(f"Top 5 projected:")
        for _, row in results.nsmallest(5, "fantasy_rank").iterrows():
            logger.info(f"  {row['fantasy_rank']}. {row['name']}: {row['projected_points']} pts")

        # Save to database
        if save_to_db:
            self._save_projections(results)

        return results

    def _get_regression_reasons(self, df: pd.DataFrame, idx: int) -> list[str]:
        """Generate regression reason explanations."""
        reasons = []

        if idx >= len(df):
            return reasons

        row = df.iloc[idx]

        if "sh_pct_zscore" in row and not pd.isna(row["sh_pct_zscore"]):
            zscore = row["sh_pct_zscore"]
            if zscore > 2:
                reasons.append(f"High shooting% (z={zscore:.1f})")
            elif zscore < -2:
                reasons.append(f"Low shooting% (z={zscore:.1f})")

        if "pdo_deviation" in row and not pd.isna(row["pdo_deviation"]):
            pdo_dev = row["pdo_deviation"]
            if pdo_dev > 0.02:
                reasons.append(f"High PDO ({1 + pdo_dev:.3f})")
            elif pdo_dev < -0.02:
                reasons.append(f"Low PDO ({1 + pdo_dev:.3f})")

        if "goals_above_xg" in row and not pd.isna(row["goals_above_xg"]):
            gax = row["goals_above_xg"]
            if gax > 5:
                reasons.append(f"Goals >> xG (+{gax:.1f})")
            elif gax < -5:
                reasons.append(f"Goals << xG ({gax:.1f})")

        return reasons

    def _save_projections(self, df: pd.DataFrame) -> None:
        """Save projections to database."""
        logger.info("Saving projections to database...")

        insert_query = """
            INSERT INTO player_projections (
                player_id, season_id, projection_date, projection_type,
                projected_games, projected_goals, projected_assists, projected_points,
                confidence_low, confidence_high,
                fantasy_rank, regression_flag, regression_score, regression_reasons,
                model_type, model_version
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (player_id, season_id, projection_date, projection_type)
            DO UPDATE SET
                projected_games = EXCLUDED.projected_games,
                projected_goals = EXCLUDED.projected_goals,
                projected_assists = EXCLUDED.projected_assists,
                projected_points = EXCLUDED.projected_points,
                confidence_low = EXCLUDED.confidence_low,
                confidence_high = EXCLUDED.confidence_high,
                fantasy_rank = EXCLUDED.fantasy_rank,
                regression_flag = EXCLUDED.regression_flag,
                regression_score = EXCLUDED.regression_score,
                regression_reasons = EXCLUDED.regression_reasons,
                model_type = EXCLUDED.model_type,
                model_version = EXCLUDED.model_version,
                updated_at = NOW()
        """

        import json

        with get_connection() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    reasons_json = json.dumps(row["regression_reasons"])
                    cur.execute(insert_query, (
                        row["player_id"],
                        row["season_id"],
                        row["projection_date"],
                        row["projection_type"],
                        row["projected_games"],
                        row["projected_goals"],
                        row["projected_assists"],
                        row["projected_points"],
                        row["confidence_low"],
                        row["confidence_high"],
                        row["fantasy_rank"],
                        row["regression_flag"],
                        row["regression_score"],
                        reasons_json,
                        row["model_type"],
                        row["model_version"],
                    ))
            conn.commit()

        logger.info(f"Saved {len(df)} projections to database")


def get_regression_candidates(
    target_season: str,
    limit: int = 20,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Get buy-low and sell-high candidates.

    Returns:
        Tuple of (buy_low_df, sell_high_df)
    """
    buy_low_query = """
        SELECT
            p.name,
            p.position,
            pp.projected_points,
            pp.regression_score,
            pp.regression_reasons,
            pp.fantasy_rank
        FROM player_projections pp
        JOIN players p ON pp.player_id = p.id
        WHERE pp.season_id = %s
          AND pp.regression_flag = 'buy_low'
          AND pp.projection_date = (
              SELECT MAX(projection_date)
              FROM player_projections
              WHERE season_id = %s AND projection_type = 'season'
          )
        ORDER BY pp.regression_score ASC
        LIMIT %s
    """

    sell_high_query = """
        SELECT
            p.name,
            p.position,
            pp.projected_points,
            pp.regression_score,
            pp.regression_reasons,
            pp.fantasy_rank
        FROM player_projections pp
        JOIN players p ON pp.player_id = p.id
        WHERE pp.season_id = %s
          AND pp.regression_flag = 'sell_high'
          AND pp.projection_date = (
              SELECT MAX(projection_date)
              FROM player_projections
              WHERE season_id = %s AND projection_type = 'season'
          )
        ORDER BY pp.regression_score DESC
        LIMIT %s
    """

    buy_low = fetch_all(buy_low_query, (target_season, target_season, limit))
    sell_high = fetch_all(sell_high_query, (target_season, target_season, limit))

    return pd.DataFrame(buy_low), pd.DataFrame(sell_high)


def main():
    """Run predictions from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate player projections")
    parser.add_argument(
        "--target-season",
        type=str,
        default="20242025",
        help="Target season to predict (e.g., 20242025)",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="xgboost",
        choices=["xgboost", "ridge"],
        help="Model to use for predictions",
    )
    parser.add_argument(
        "--projection-type",
        type=str,
        default="season",
        choices=["season", "rolling_14d", "rolling_30d"],
        help="Type of projection",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save projections to database",
    )
    parser.add_argument(
        "--show-regression",
        action="store_true",
        help="Show regression candidates after prediction",
    )

    args = parser.parse_args()

    predictor = Predictor(args.target_season, args.model_type)
    results = predictor.run(
        projection_type=args.projection_type,
        save_to_db=not args.no_save,
    )

    if args.show_regression and not args.no_save:
        print("\n" + "=" * 50)
        print("REGRESSION CANDIDATES")
        print("=" * 50)

        buy_low, sell_high = get_regression_candidates(args.target_season)

        if not buy_low.empty:
            print("\nBUY LOW (underperforming luck metrics):")
            for _, row in buy_low.iterrows():
                print(f"  {row['name']} ({row['position']}): {row['projected_points']} pts")
                print(f"    Reasons: {row['regression_reasons']}")

        if not sell_high.empty:
            print("\nSELL HIGH (overperforming luck metrics):")
            for _, row in sell_high.iterrows():
                print(f"  {row['name']} ({row['position']}): {row['projected_points']} pts")
                print(f"    Reasons: {row['regression_reasons']}")


if __name__ == "__main__":
    main()
