"""WebSocket event handler for the Miner domain."""

from typing import Any, List

from edge_mining.adapters.domain.miner.websocket.schemas import MinerStateChangedSchema
from edge_mining.adapters.infrastructure.websocket.utils import (
    WebSocketEventHandler,
    WebSocketEventRegistration,
)
from edge_mining.domain.common import DomainEvent
from edge_mining.domain.miner.events import MinerStateChangedEvent


class MinerWebSocketHandler(WebSocketEventHandler):
    """Serializes Miner domain events for WebSocket broadcasting."""

    @property
    def registrations(self) -> List[WebSocketEventRegistration]:
        return [
            WebSocketEventRegistration(
                event_type=MinerStateChangedEvent,
                topic="miner.state",
                serialize=self._serialize_miner_state_changed,
            ),
        ]

    def _serialize_miner_state_changed(self, event: DomainEvent) -> dict[str, Any]:
        assert isinstance(event, MinerStateChangedEvent)
        payload = MinerStateChangedSchema(
            miner_id=str(event.miner_id) if event.miner_id else None,
            miner_name=event.miner_name,
            old_status=event.old_status.value if event.old_status else None,
            new_status=event.new_status.value if event.new_status else None,
        )
        return payload.model_dump(mode="json")
