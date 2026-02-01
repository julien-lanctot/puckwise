"""ETL Configuration loaded from environment variables."""

import os
from dataclasses import dataclass
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

    # NHL API
    nhl_api_base_url: str = os.getenv("NHL_API_BASE_URL", "https://api-web.nhle.com/v1")
    nhl_stats_api_base_url: str = os.getenv("NHL_STATS_API_BASE_URL", "https://api.nhle.com/stats/rest/en")

    # MoneyPuck
    moneypuck_base_url: str = os.getenv("MONEYPUCK_BASE_URL", "https://moneypuck.com/moneypuck/playerData")

    # Rate limiting
    requests_per_second: float = 1.0

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


config = Config()
