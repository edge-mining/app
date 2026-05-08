"""Timezone utility for the Edge Mining application."""

from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from edge_mining.shared.settings.settings import AppSettings


@lru_cache(maxsize=1)
def get_timezone() -> ZoneInfo:
    """Get the application's configured timezone."""
    return ZoneInfo(AppSettings().timezone)


def now() -> datetime:
    """Get current datetime in the application's configured timezone."""
    return datetime.now(tz=get_timezone())
