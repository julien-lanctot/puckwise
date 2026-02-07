"""Training pipeline for projection models."""

import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
from sklearn.model_selection import train_test_split

from ..config import config
from ..features import SkaterFeatureBuilder
from ..models import RidgeModel, XGBoostModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Trainer:
    """Training pipeline for projection models."""

    def __init__(self, target_season: str):
        """Initialize trainer.

        Args:
            target_season: Season to predict (e.g., "20242025")
        """
        self.target_season = target_season
        self.feature_builder = SkaterFeatureBuilder(target_season)
        self.models: dict = {}
        self.metrics: dict = {}

    def run(self, save_models: bool = True) -> dict:
        """Run full training pipeline.

        Returns:
            Dict with model metrics and paths
        """
        logger.info(f"Starting training for target season: {self.target_season}")

        # Build training data
        logger.info("Building training features...")
        df = self.feature_builder.build_training_data(min_seasons=2)

        if df.empty:
            raise ValueError("No training data available")

        logger.info(f"Training data: {len(df)} player-seasons")

        # Encode position
        df = self.feature_builder.encode_position(df)

        # Get feature columns
        feature_cols = self.feature_builder.get_feature_columns()

        # Filter to available columns
        available_cols = [c for c in feature_cols if c in df.columns]
        missing_cols = set(feature_cols) - set(available_cols)
        if missing_cols:
            logger.warning(f"Missing features (will use zeros): {missing_cols}")
            for col in missing_cols:
                df[col] = 0
            available_cols = feature_cols

        X = df[available_cols]
        y = df["target_points"]

        logger.info(f"Features: {len(available_cols)}, Samples: {len(X)}")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, random_state=config.random_state
        )

        logger.info(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

        # Train Ridge baseline
        logger.info("Training Ridge baseline...")
        ridge = RidgeModel(alpha=1.0, version="1.0")
        ridge.fit(X_train, y_train)
        ridge_metrics = ridge.evaluate(X_test, y_test)
        self.models["ridge"] = ridge
        self.metrics["ridge"] = ridge_metrics
        logger.info(f"Ridge - MAE: {ridge_metrics['mae']:.2f}, R²: {ridge_metrics['r2']:.3f}")

        # Train XGBoost
        logger.info("Training XGBoost...")
        xgb_model = XGBoostModel(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            version="1.0",
        )
        xgb_model.fit(X_train, y_train, eval_set=(X_test, y_test))
        xgb_metrics = xgb_model.evaluate(X_test, y_test)
        self.models["xgboost"] = xgb_model
        self.metrics["xgboost"] = xgb_metrics
        logger.info(f"XGBoost - MAE: {xgb_metrics['mae']:.2f}, R²: {xgb_metrics['r2']:.3f}")

        # Feature importance
        logger.info("\nTop 10 XGBoost feature importances:")
        importance = xgb_model.get_feature_importance()
        sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        for feat, imp in sorted_imp[:10]:
            logger.info(f"  {feat}: {imp:.4f}")

        # Save models
        if save_models:
            model_dir = config.model_dir
            model_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d")

            ridge_path = model_dir / f"ridge_{self.target_season}_{timestamp}.joblib"
            ridge.save(ridge_path)
            logger.info(f"Saved Ridge model to {ridge_path}")

            xgb_path = model_dir / f"xgboost_{self.target_season}_{timestamp}.joblib"
            xgb_model.save(xgb_path)
            logger.info(f"Saved XGBoost model to {xgb_path}")

            # Save a "latest" symlink/copy
            latest_ridge = model_dir / "ridge_latest.joblib"
            latest_xgb = model_dir / "xgboost_latest.joblib"
            ridge.save(latest_ridge)
            xgb_model.save(latest_xgb)

        return {
            "target_season": self.target_season,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "metrics": self.metrics,
            "feature_importance": sorted_imp[:10],
        }


def main():
    """Run training from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Train projection models")
    parser.add_argument(
        "--target-season",
        type=str,
        default="20242025",
        help="Target season to predict (e.g., 20242025)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save models to disk",
    )

    args = parser.parse_args()

    trainer = Trainer(args.target_season)
    results = trainer.run(save_models=not args.no_save)

    print("\n" + "=" * 50)
    print("TRAINING COMPLETE")
    print("=" * 50)
    print(f"Target Season: {results['target_season']}")
    print(f"Training Samples: {results['train_size']}")
    print(f"Test Samples: {results['test_size']}")
    print("\nModel Performance:")
    for model_name, metrics in results["metrics"].items():
        print(f"\n  {model_name.upper()}:")
        print(f"    MAE: {metrics['mae']:.2f} points")
        print(f"    RMSE: {metrics['rmse']:.2f} points")
        print(f"    R²: {metrics['r2']:.3f}")


if __name__ == "__main__":
    main()
