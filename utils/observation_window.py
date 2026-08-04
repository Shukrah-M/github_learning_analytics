"""Shared fixed observation-window configuration."""

from datetime import datetime, timezone
import os

from dotenv import load_dotenv


load_dotenv()


def parse_datetime(value: str | datetime | None) -> datetime | None:
    """Convert a GitHub ISO timestamp or datetime to UTC."""
    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def read_required_datetime(variable_name: str) -> datetime:
    """Read and validate a required datetime environment variable."""
    value = os.getenv(variable_name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {variable_name}"
        )

    parsed = parse_datetime(value)

    if parsed is None:
        raise RuntimeError(
            f"Invalid datetime for {variable_name}: {value}"
        )

    return parsed


OBSERVATION_START = read_required_datetime(
    "OBSERVATION_START"
)
OBSERVATION_END = read_required_datetime(
    "OBSERVATION_END"
)

if OBSERVATION_END <= OBSERVATION_START:
    raise RuntimeError(
        "OBSERVATION_END must be later than OBSERVATION_START."
    )


OBSERVATION_DAYS = (
    OBSERVATION_END - OBSERVATION_START
).days


def is_within_observation_window(
    value: str | datetime | None,
) -> bool:
    """Return True when a timestamp is inside the fixed window."""
    parsed = parse_datetime(value)

    if parsed is None:
        return False

    return OBSERVATION_START <= parsed < OBSERVATION_END


def to_github_timestamp(value: datetime) -> str:
    """Convert a UTC datetime to GitHub's ISO timestamp format."""
    utc_value = value.astimezone(timezone.utc)

    return utc_value.strftime("%Y-%m-%dT%H:%M:%SZ")