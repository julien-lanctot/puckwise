"""ML models for hockey analytics."""

from .base import BaseModel
from .ridge import RidgeModel
from .xgboost_model import XGBoostModel

__all__ = ["BaseModel", "RidgeModel", "XGBoostModel"]
