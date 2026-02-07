"""XGBoost model for projections."""

import numpy as np
import pandas as pd
import xgboost as xgb

from .base import BaseModel


class XGBoostModel(BaseModel):
    """XGBoost gradient boosting model for point projections.

    Handles non-linear relationships and feature interactions.
    Generally outperforms linear models on hockey data.
    """

    def __init__(
        self,
        n_estimators: int = 200,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        subsample: float = 0.8,
        colsample_bytree: float = 0.8,
        version: str = "1.0",
    ):
        super().__init__(name="xgboost", version=version)
        self.params = {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "subsample": subsample,
            "colsample_bytree": colsample_bytree,
            "objective": "reg:squarederror",
            "random_state": 42,
        }

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: tuple[pd.DataFrame, pd.Series] | None = None,
    ) -> "XGBoostModel":
        """Fit XGBoost model.

        Args:
            X: Feature DataFrame
            y: Target variable (points)
            eval_set: Optional validation set for early stopping
        """
        self.feature_columns = list(X.columns)

        X_array = self._prepare_features(X)

        self.model = xgb.XGBRegressor(**self.params)

        fit_params = {}
        if eval_set is not None:
            X_val, y_val = eval_set
            X_val_array = self._prepare_features(X_val)
            fit_params["eval_set"] = [(X_val_array, y_val)]
            fit_params["verbose"] = False

        self.model.fit(X_array, y, **fit_params)

        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict points for given features."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X_array = self._prepare_features(X)
        preds = self.model.predict(X_array)

        # Clip to reasonable bounds
        return np.clip(preds, 0, 150)

    def get_feature_importance(self) -> dict[str, float]:
        """Get XGBoost feature importance scores."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")

        importance = self.model.feature_importances_
        return dict(zip(self.feature_columns, importance))

    def predict_with_intervals(
        self, X: pd.DataFrame, confidence: float = 0.8
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with confidence intervals using quantile estimation."""
        preds = self.predict(X)

        # Use feature-based uncertainty estimation
        # Higher uncertainty for edge cases (young players, regression candidates)
        X_array = self._prepare_features(X)

        # Base uncertainty from prediction magnitude
        base_se = np.abs(preds) * 0.12

        # Adjust for specific features if available
        if "years_from_peak" in self.feature_columns:
            idx = self.feature_columns.index("years_from_peak")
            years_from_peak = np.abs(X_array[:, idx])
            base_se = base_se * (1 + 0.05 * years_from_peak)

        if "regression_score" in self.feature_columns:
            idx = self.feature_columns.index("regression_score")
            regression_score = np.abs(X_array[:, idx])
            base_se = base_se * (1 + 0.02 * regression_score)

        z = 1.28 if confidence == 0.8 else 1.96
        lower = np.clip(preds - z * base_se, 0, 150)
        upper = np.clip(preds + z * base_se, 0, 150)

        return preds, lower, upper
