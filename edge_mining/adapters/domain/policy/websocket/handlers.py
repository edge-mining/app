"""WebSocket event handler for the Policy domain."""

from typing import Any, List, Tuple

from edge_mining.adapters.domain.policy.schemas import DecisionalContextSchema
from edge_mining.adapters.domain.policy.websocket.schemas import DecisionalContextUpdatedSchema
from edge_mining.adapters.infrastructure.websocket.handler_protocol import (
    WebSocketEventHandler,
    WebSocketEventRegistration,
)
from edge_mining.domain.common import DomainEvent
from edge_mining.domain.policy.events import DecisionalContextUpdatedEvent


class PolicyWebSocketHandler(WebSocketEventHandler):
    """Serializes Policy domain events for WebSocket broadcasting."""

    @property
    def registrations(self) -> List[WebSocketEventRegistration]:
        return [
            WebSocketEventRegistration(
                event_type=DecisionalContextUpdatedEvent,
                serialize=self._serialize_decisional_context_updated,
            ),
        ]

    def _serialize_decisional_context_updated(self, event: DomainEvent) -> Tuple[str, dict[str, Any]]:
        assert isinstance(event, DecisionalContextUpdatedEvent)
        payload = DecisionalContextUpdatedSchema(
            optimization_unit_id=str(event.optimization_unit_id) if event.optimization_unit_id else None,
            optimization_unit_name=event.optimization_unit_name,
            context=(DecisionalContextSchema.from_model(event.context) if event.context else None),
            target_miner_ids=[str(mid) for mid in event.target_miner_ids],
        )
        return "policy.context", payload.model_dump(mode="json")
