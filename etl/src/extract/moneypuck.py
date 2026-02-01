"""MoneyPuck data downloader for advanced statistics."""

import io
from typing import Iterator

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import config


class MoneyPuckClient:
    """Client for downloading MoneyPuck CSV data."""

    def __init__(self):
        self.base_url = config.moneypuck_base_url
        self.client = httpx.Client(timeout=60.0)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _download_csv(self, url: str) -> pd.DataFrame:
        """Download and parse a CSV file."""
        response = self.client.get(url)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))

    def get_skater_stats(self, season: int, situation: str = "all") -> pd.DataFrame:
        """
        Get skater advanced stats for a season.

        Args:
            season: Start year of season (e.g., 2023 for 2023-24)
            situation: 'all', '5on5', '5on4', '4on5', etc.
        """
        url = f"{self.base_url}/seasonSummary/{season}/regular/skaters.csv"
        df = self._download_csv(url)
        if situation != "all":
            df = df[df["situation"] == situation]
        return df

    def get_goalie_stats(self, season: int, situation: str = "all") -> pd.DataFrame:
        """Get goalie advanced stats for a season."""
        url = f"{self.base_url}/seasonSummary/{season}/regular/goalies.csv"
        df = self._download_csv(url)
        if situation != "all":
            df = df[df["situation"] == situation]
        return df

    def get_team_stats(self, season: int, situation: str = "all") -> pd.DataFrame:
        """Get team advanced stats for a season."""
        url = f"{self.base_url}/seasonSummary/{season}/regular/teams.csv"
        df = self._download_csv(url)
        if situation != "all":
            df = df[df["situation"] == situation]
        return df

    def iter_seasons(
        self,
        start_year: int = 2007,
        end_year: int = 2024,
    ) -> Iterator[tuple[int, pd.DataFrame]]:
        """
        Iterate through seasons, yielding skater stats.

        Args:
            start_year: First season start year (2007 = 2007-08 season)
            end_year: Last season start year
        """
        for year in range(start_year, end_year + 1):
            try:
                df = self.get_skater_stats(year)
                yield year, df
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    print(f"MoneyPuck data not available for {year}-{year+1}")
                    continue
                raise

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def map_moneypuck_to_nhl_id(mp_player_id: int) -> int | None:
    """
    Map MoneyPuck player ID to NHL player ID.

    MoneyPuck uses NHL player IDs directly, so this is usually a passthrough.
    Some older records may need manual mapping.
    """
    # MoneyPuck uses NHL IDs directly
    return mp_player_id
