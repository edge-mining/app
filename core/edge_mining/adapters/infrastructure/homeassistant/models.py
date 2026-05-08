"""Collection of data models for Home Assistant integration."""

from dataclasses import dataclass
from typing import List, Optional

from edge_mining.domain.common import Timestamp


@dataclass
class HistoryDataPoint:
    """A single data point in the history of an entity."""

    timestamp: Timestamp
    value: str
    unit: Optional[str]


@dataclass
class EntityHistory:
    """Historical data for a specific entity."""

    entity_id: str
    history: List[HistoryDataPoint]

    def sort_by_timestamp(self) -> None:
        """Sorts the history data points by their timestamp."""
        self.history.sort(key=lambda point: point.timestamp)
