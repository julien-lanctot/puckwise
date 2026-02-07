"""Ridge regression baseline model."""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from .base import BaseModel


class RidgeModel(BaseModel):
    """Ridge regression baseline for point projections.

    Simple, interpretable baseline model. Ridge regression handles
    multicollinearity well and provides regularization.
    """

    def __init__(self, alpha: float = 1.0, version: str = "1.0"):
        super().__init__(name="ridge", version=version)
        self.alpha = alpha
        self.scaler = StandardScaler()

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "RidgeModel":
        """Fit Ridge regression model.

        Args:
            X: Feature DataFrame
            y: Target variable (points)
        """
        self.feature_columns = list(X.columns)

        # Prepare and scale features
        X_array = self._prepare_features(X)
        X_scaled = self.scaler.fit_transform(X_array)

        # Fit Ridge model
        self.model = Ridge(alpha=self.alpha)
        self.model.fit(X_scaled, y)

        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict points for given features."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X_array = self._prepare_features(X)
        X_scaled = self.scaler.transform(X_array)

        preds = self.model.predict(X_scaled)

        # Clip to reasonable bounds (0 to 150 points)
        return np.clip(preds, 0, 150)

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature coefficients as importance scores."""
        if not self.is_fitted:
            raise RuntimeError("Model not fitted.")

        return dict(zip(self.feature_columns, self.model.coef_))

    def predict_with_intervals(
        self, X: pd.DataFrame, confidence: float = 0.8
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with confidence intervals based on model residuals."""
        preds = self.predict(X)

        # Estimate standard error (simplified)
        # In production, use bootstrap or cross-validation residuals
        se = np.abs(preds) * 0.15  # ~15% relative error

        z = 1.28 if confidence == 0.8 else 1.96  # 80% or 95% CI
        lower = np.clip(preds - z * se, 0, 150)
        upper = np.clip(preds + z * se, 0, 150)

        return preds, lower, upper
