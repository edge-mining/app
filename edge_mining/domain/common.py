"""Collection of Common Objects for the Edge Mining application domain."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, NewType, Tuple

# Example Value Objects using NewType for stronger typing
Watts = NewType("Watts", float)
WattHours = NewType("WattHours", float)
Percentage = NewType("Percentage", float)  # 0.0 to 100.0
Timestamp = NewType("Timestamp", datetime)
EntityId = NewType("EntityId", uuid.UUID)

TimePeriod = Tuple[datetime, datetime]


@dataclass(frozen=True)
class ValueObject:
    """Base class for value objects."""

    pass  # Base class for value objects if needed


@dataclass
class Entity:
    """Base class for entities."""

    id: EntityId = field(default_factory=lambda: EntityId(uuid.uuid4()))


@dataclass
class AggregateRoot:
    """Base class for aggregate roots."""

    id: EntityId = field(default_factory=lambda: EntityId(uuid.uuid4()))


class AdapterType(Enum):
    """Base class for adapter types."""

    pass  # Base class for adapter types if needed


@dataclass
class DomainEvent:
    """Base class for all domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialization for WebSocket/logging. Override in subtypes if needed."""
        from dataclasses import asdict

        result = asdict(self)
        result["occurred_at"] = self.occurred_at.isoformat()
        result["event_type"] = self.event_type
        return result

    @property
    def event_type(self) -> str:
        """Event type derived from class name. Useful for serialization."""
        return self.__class__.__name__
