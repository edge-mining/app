"""WebSocket event handler for Configuration application events."""

from typing import Any, List, Tuple

from edge_mining.adapters.infrastructure.websocket.utils import (
    WebSocketEventHandler,
    WebSocketEventRegistration,
)
from edge_mining.adapters.application.services.configuration.websocket.schemas import ConfigurationUpdatedSchema
from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent
from edge_mining.domain.common import DomainEvent


class ConfigurationWebSocketHandler(WebSocketEventHandler):
    """Serializes Configuration events for WebSocket broadcasting."""

    @property
    def registrations(self) -> List[WebSocketEventRegistration]:
        return [
            WebSocketEventRegistration(
                event_type=ConfigurationUpdatedEvent,
                serialize=self._serialize_configuration_updated,
            ),
        ]

    def _serialize_configuration_updated(self, event: DomainEvent) -> Tuple[str, dict[str, Any]]:
        assert isinstance(event, ConfigurationUpdatedEvent)
        payload = ConfigurationUpdatedSchema(
            entity_type=event.entity_type.value if event.entity_type else "",
            entity_id=str(event.entity_id) if event.entity_id else None,
            action=event.action.value if event.action else "",
        )
        return "config.updated", payload.model_dump(mode="json")
