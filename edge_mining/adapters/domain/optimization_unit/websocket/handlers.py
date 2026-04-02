"""WebSocket event handler for the Optimization Unit domain."""

from typing import List

from edge_mining.adapters.domain.optimization_unit.websocket.schemas import RuleEngagedSchema
from edge_mining.adapters.infrastructure.websocket.utils import (
    WebSocketEventHandler,
    WebSocketEventRegistration,
    WebSocketMessage,
)
from edge_mining.domain.common import DomainEvent
from edge_mining.domain.optimization_unit.events import RuleEngagedEvent


class OptimizationUnitWebSocketHandler(WebSocketEventHandler):
    """Serializes Optimization Unit domain events for WebSocket broadcasting."""

    @property
    def registrations(self) -> List[WebSocketEventRegistration]:
        return [
            WebSocketEventRegistration(
                event_type=RuleEngagedEvent,
                serialize=self._serialize_rule_engaged,
            ),
        ]

    def _serialize_rule_engaged(self, event: DomainEvent) -> WebSocketMessage:
        assert isinstance(event, RuleEngagedEvent)
        payload = RuleEngagedSchema(
            optimization_unit_id=str(event.optimization_unit_id) if event.optimization_unit_id else None,
            optimization_unit_name=event.optimization_unit_name,
            policy_id=str(event.policy_id) if event.policy_id else None,
            policy_name=event.policy_name,
            miner_id=str(event.miner_id) if event.miner_id else None,
            decision=event.decision.value if event.decision else None,
            miner_status=event.miner_status,
        )
        return WebSocketMessage("rule.engaged", payload.model_dump(mode="json"))
