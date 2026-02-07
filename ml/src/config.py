"""ML Configuration loaded from environment variables."""

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "puckwise")
    db_password: str = os.getenv("DB_PASSWORD", "puckwise_dev")
    db_name: str = os.getenv("DB_NAME", "hockey_analytics")

    # Model paths
    model_dir: Path = Path(os.getenv("MODEL_DIR", "ml/models"))

    # Training params
    test_size: float = 0.2
    random_state: int = 42
    min_games_threshold: int = 20  # Minimum games to include in training

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


config = Config()
