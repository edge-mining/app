"""User Settings domain events."""

from dataclasses import dataclass
from typing import Optional

from edge_mining.domain.common import DomainEvent
from edge_mining.domain.user.value_objects import SystemConfiguration


@dataclass
class SystemConfigurationUpdated(DomainEvent):
    """Event emitted when the user-editable system configuration is updated."""

    configuration: Optional[SystemConfiguration] = None
