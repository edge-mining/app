"""WebSocket event handler for the Energy domain."""

from typing import Any, List, Tuple

from edge_mining.adapters.domain.energy.schemas import EnergyStateSnapshotSchema
from edge_mining.adapters.domain.energy.websocket.schemas import EnergyStateSnapshotUpdatedSchema
from edge_mining.adapters.infrastructure.websocket.utils import (
    WebSocketEventHandler,
    WebSocketEventRegistration,
)
from edge_mining.domain.common import DomainEvent
from edge_mining.domain.energy.events import EnergyStateSnapshotUpdatedEvent


class EnergyWebSocketHandler(WebSocketEventHandler):
    """Serializes Energy domain events for WebSocket broadcasting."""

    @property
    def registrations(self) -> List[WebSocketEventRegistration]:
        return [
            WebSocketEventRegistration(
                event_type=EnergyStateSnapshotUpdatedEvent,
                serialize=self._serialize_energy_state_snapshot_updated,
            ),
        ]

    def _serialize_energy_state_snapshot_updated(self, event: DomainEvent) -> Tuple[str, dict[str, Any]]:
        assert isinstance(event, EnergyStateSnapshotUpdatedEvent)
        payload = EnergyStateSnapshotUpdatedSchema(
            optimization_unit_id=str(event.optimization_unit_id) if event.optimization_unit_id else None,
            optimization_unit_name=event.optimization_unit_name,
            energy_source_id=str(event.energy_source_id) if event.energy_source_id else None,
            energy_state_snapshot=(
                EnergyStateSnapshotSchema.from_model(event.energy_state_snapshot)
                if event.energy_state_snapshot
                else None
            ),
        )
        return "energy.state", payload.model_dump(mode="json")
