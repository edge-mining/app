"""Timezone utility for the Edge Mining application."""

from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo


class TimezoneProvider:
    """Holds the application-wide timezone and caches the resolved ZoneInfo.

    Seeded at startup from the persisted system configuration and updated at
    runtime when the configuration changes.
    """

    def __init__(self, timezone: str = "Europe/Rome") -> None:
        self._timezone_name = timezone
        self._cached_zone: Optional[ZoneInfo] = None

    def set_timezone(self, timezone: str) -> None:
        """Set the timezone and invalidate the cached zone."""
        self._timezone_name = timezone
        self._cached_zone = None

    def get_timezone(self) -> ZoneInfo:
        """Get the configured timezone, resolving and caching it on first use."""
        if self._cached_zone is None:
            self._cached_zone = ZoneInfo(self._timezone_name)
        return self._cached_zone


_provider = TimezoneProvider()


def set_timezone(timezone: str) -> None:
    """Set the application's timezone."""
    _provider.set_timezone(timezone)


def get_timezone() -> ZoneInfo:
    """Get the application's configured timezone."""
    return _provider.get_timezone()


def now() -> datetime:
    """Get current datetime in the application's configured timezone."""
    return datetime.now(tz=get_timezone())
