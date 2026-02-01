"""Transform player data from NHL API format to database format."""

from datetime import date
from typing import Any


def transform_player(data: dict[str, Any]) -> dict[str, Any]:
    """Transform NHL API player landing data to database format."""
    return {
        "nhl_id": data.get("playerId"),
        "name": f"{data.get('firstName', {}).get('default', '')} {data.get('lastName', {}).get('default', '')}".strip(),
        "first_name": data.get("firstName", {}).get("default"),
        "last_name": data.get("lastName", {}).get("default"),
        "position": data.get("position"),
        "position_type": _get_position_type(data.get("position")),
        "birth_date": data.get("birthDate"),
        "birth_city": data.get("birthCity", {}).get("default"),
        "birth_country": data.get("birthCountry"),
        "nationality": data.get("nationality"),
        "height_cm": _inches_to_cm(data.get("heightInInches")),
        "weight_kg": _pounds_to_kg(data.get("weightInPounds")),
        "shoots": data.get("shootsCatches"),
        "is_active": data.get("isActive", True),
        "headshot_url": data.get("headshot"),
    }


def transform_player_bio(data: dict[str, Any]) -> dict[str, Any]:
    """Transform NHL Stats API player bio data to database format."""
    return {
        "nhl_id": data.get("playerId"),
        "name": data.get("skaterFullName") or data.get("goalieFullName"),
        "first_name": data.get("firstName"),
        "last_name": data.get("lastName"),
        "position": data.get("positionCode"),
        "position_type": _get_position_type(data.get("positionCode")),
        "birth_date": data.get("birthDate"),
        "birth_city": data.get("birthCity"),
        "birth_country": data.get("birthCountryCode"),
        "nationality": data.get("nationalityCode"),
        "height_cm": _height_str_to_cm(data.get("height")),
        "weight_kg": _pounds_to_kg(data.get("weight")),
        "shoots": data.get("shootsCatches"),
        "is_active": data.get("isActive", True),
    }


def _get_position_type(position: str | None) -> str | None:
    """Map position code to position type."""
    if not position:
        return None
    position = position.upper()
    if position == "G":
        return "Goalie"
    elif position == "D":
        return "Defenseman"
    elif position in ("C", "L", "R", "LW", "RW", "W", "F"):
        return "Forward"
    return None


def _inches_to_cm(inches: int | None) -> int | None:
    """Convert inches to centimeters."""
    if inches is None:
        return None
    return round(inches * 2.54)


def _pounds_to_kg(pounds: int | None) -> int | None:
    """Convert pounds to kilograms."""
    if pounds is None:
        return None
    return round(pounds * 0.453592)


def _height_str_to_cm(height_str: str | None) -> int | None:
    """Convert height string like 6'2\" to centimeters."""
    if not height_str:
        return None
    try:
        # Handle format like "6' 2\""
        parts = height_str.replace('"', '').replace("'", " ").split()
        if len(parts) >= 2:
            feet = int(parts[0])
            inches = int(parts[1])
            total_inches = feet * 12 + inches
            return round(total_inches * 2.54)
        elif len(parts) == 1:
            # Just inches
            return round(int(parts[0]) * 2.54)
    except (ValueError, IndexError):
        pass
    return None
