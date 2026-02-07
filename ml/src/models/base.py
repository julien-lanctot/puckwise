"""Base model interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import joblib


class BaseModel(ABC):
    """Abstract base class for projection models."""

    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.model = None
        self.feature_columns: list[str] = []
        self.is_fitted = False

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> "BaseModel":
        """Fit the model to training data."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions on new data."""
        pass

    def predict_with_intervals(
        self, X: pd.DataFrame, confidence: float = 0.8
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Predict with confidence intervals.

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        preds = self.predict(X)
        # Default: estimate intervals from prediction variance
        # Subclasses can override with proper quantile regression
        std_estimate = np.std(preds) * 0.5
        lower = preds - std_estimate * 1.28  # ~80% CI
        upper = preds + std_estimate * 1.28
        return preds, lower, upper

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
        """Evaluate model performance."""
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

        preds = self.predict(X)
        return {
            "mae": mean_absolute_error(y, preds),
            "rmse": np.sqrt(mean_squared_error(y, preds)),
            "r2": r2_score(y, preds),
            "mape": np.mean(np.abs((y - preds) / y.clip(lower=1))) * 100,
        }

    def save(self, path: Path) -> None:
        """Save model to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        model_data = {
            "name": self.name,
            "version": self.version,
            "model": self.model,
            "feature_columns": self.feature_columns,
        }
        joblib.dump(model_data, path)

    @classmethod
    def load(cls, path: Path) -> "BaseModel":
        """Load model from disk."""
        data = joblib.load(path)
        instance = cls.__new__(cls)
        instance.name = data["name"]
        instance.version = data["version"]
        instance.model = data["model"]
        instance.feature_columns = data["feature_columns"]
        instance.is_fitted = True
        return instance

    def _prepare_features(self, X: pd.DataFrame) -> np.ndarray:
        """Prepare features for model input."""
        # Use only configured feature columns
        missing = set(self.feature_columns) - set(X.columns)
        if missing:
            raise ValueError(f"Missing features: {missing}")

        X_subset = X[self.feature_columns].copy()

        # Fill NaN with 0 (models handle this)
        X_subset = X_subset.fillna(0)

        return X_subset.values
