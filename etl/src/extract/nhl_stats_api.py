"""NHL Stats API client for aggregated statistics."""

import time
from typing import Any, Iterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import config


class NHLStatsApiClient:
    """Client for the NHL Stats API (api.nhle.com/stats)."""

    def __init__(self):
        self.base_url = config.nhl_stats_api_base_url
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
    def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        """Make a GET request with rate limiting and retry."""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        response = self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_skater_stats(
        self,
        season: str,
        game_type: int = 2,
        limit: int = 100,
        start: int = 0,
    ) -> dict[str, Any]:
        """
        Get skater summary statistics.

        Args:
            season: Season string like "20232024"
            game_type: 2 for regular season, 3 for playoffs
            limit: Number of results per page
            start: Starting index for pagination
        """
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "sort": '[{"property":"points","direction":"DESC"}]',
            "start": start,
            "limit": limit,
            "factCayenneExp": f"gamesPlayed>=1",
            "cayenneExp": f"gameTypeId={game_type} and seasonId<={season} and seasonId>={season}",
        }
        return self._get("/skater/summary", params)

    def get_goalie_stats(
        self,
        season: str,
        game_type: int = 2,
        limit: int = 100,
        start: int = 0,
    ) -> dict[str, Any]:
        """Get goalie summary statistics."""
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "sort": '[{"property":"wins","direction":"DESC"}]',
            "start": start,
            "limit": limit,
            "factCayenneExp": f"gamesPlayed>=1",
            "cayenneExp": f"gameTypeId={game_type} and seasonId<={season} and seasonId>={season}",
        }
        return self._get("/goalie/summary", params)

    def iter_all_skaters(self, season: str, game_type: int = 2) -> Iterator[dict[str, Any]]:
        """Iterate through all skaters for a season with pagination."""
        start = 0
        limit = 100
        while True:
            data = self.get_skater_stats(season, game_type, limit, start)
            players = data.get("data", [])
            if not players:
                break
            yield from players
            if len(players) < limit:
                break
            start += limit

    def iter_all_goalies(self, season: str, game_type: int = 2) -> Iterator[dict[str, Any]]:
        """Iterate through all goalies for a season with pagination."""
        start = 0
        limit = 100
        while True:
            data = self.get_goalie_stats(season, game_type, limit, start)
            players = data.get("data", [])
            if not players:
                break
            yield from players
            if len(players) < limit:
                break
            start += limit

    def get_skater_bios(self, season: str, limit: int = 100, start: int = 0) -> dict[str, Any]:
        """Get skater biographical information."""
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "sort": '[{"property":"playerId","direction":"ASC"}]',
            "start": start,
            "limit": limit,
            "cayenneExp": f"seasonId={season}",
        }
        return self._get("/skater/bios", params)

    def get_goalie_bios(self, season: str, limit: int = 100, start: int = 0) -> dict[str, Any]:
        """Get goalie biographical information."""
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "sort": '[{"property":"playerId","direction":"ASC"}]',
            "start": start,
            "limit": limit,
            "cayenneExp": f"seasonId={season}",
        }
        return self._get("/goalie/bios", params)

    def iter_all_skater_bios(self, season: str) -> Iterator[dict[str, Any]]:
        """Iterate through all skater bios for a season."""
        start = 0
        limit = 100
        while True:
            data = self.get_skater_bios(season, limit, start)
            players = data.get("data", [])
            if not players:
                break
            yield from players
            if len(players) < limit:
                break
            start += limit

    def iter_all_goalie_bios(self, season: str) -> Iterator[dict[str, Any]]:
        """Iterate through all goalie bios for a season."""
        start = 0
        limit = 100
        while True:
            data = self.get_goalie_bios(season, limit, start)
            players = data.get("data", [])
            if not players:
                break
            yield from players
            if len(players) < limit:
                break
            start += limit

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
