"""NHL Web API client for player data, game logs, and schedules."""

import time
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import config


class NHLApiClient:
    """Client for the NHL Web API (api-web.nhle.com)."""

    def __init__(self):
        self.base_url = config.nhl_api_base_url
        self.client = httpx.Client(timeout=30.0)
        self.last_request_time = 0.0
        self.min_request_interval = 1.0 / config.requests_per_second

    def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request with rate limiting and retry."""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        response = self.client.get(url)
        response.raise_for_status()
        return response.json()

    def get_player(self, player_id: int) -> dict[str, Any]:
        """Get player landing page data."""
        return self._get(f"/player/{player_id}/landing")

    def get_player_game_log(self, player_id: int, season: str, game_type: int = 2) -> dict[str, Any]:
        """
        Get player game log for a season.

        Args:
            player_id: NHL player ID
            season: Season string like "20232024"
            game_type: 2 for regular season, 3 for playoffs
        """
        return self._get(f"/player/{player_id}/game-log/{season}/{game_type}")

    def get_schedule(self, date: str) -> dict[str, Any]:
        """Get schedule for a specific date (YYYY-MM-DD)."""
        return self._get(f"/schedule/{date}")

    def get_schedule_week(self, date: str) -> dict[str, Any]:
        """Get schedule for the week containing the date."""
        return self._get(f"/schedule/{date}")

    def get_game_landing(self, game_id: int) -> dict[str, Any]:
        """Get game landing page with boxscore data."""
        return self._get(f"/gamecenter/{game_id}/landing")

    def get_game_boxscore(self, game_id: int) -> dict[str, Any]:
        """Get detailed boxscore for a game."""
        return self._get(f"/gamecenter/{game_id}/boxscore")

    def get_standings(self, date: str | None = None) -> dict[str, Any]:
        """Get current or historical standings."""
        if date:
            return self._get(f"/standings/{date}")
        return self._get("/standings/now")

    def get_roster(self, team_abbrev: str, season: str) -> dict[str, Any]:
        """Get team roster for a season."""
        return self._get(f"/roster/{team_abbrev}/{season}")

    def get_season_schedule(self, team_abbrev: str, season: str) -> dict[str, Any]:
        """Get full season schedule for a team."""
        return self._get(f"/club-schedule-season/{team_abbrev}/{season}")

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
