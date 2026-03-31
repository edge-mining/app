"""WebSocket manager for broadcasting domain events to connected clients."""

import json
from fnmatch import fnmatch
from typing import Any

from fastapi import WebSocket

from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent
from edge_mining.application.events.energy_events import EnergyStateSnapshotUpdatedEvent
from edge_mining.application.events.miner_events import MinerStateChangedEvent
from edge_mining.application.events.optimization_events import RuleEngagedEvent
from edge_mining.application.events.policy_events import DecisionalContextUpdatedEvent
from edge_mining.application.interfaces import EventBusInterface
from edge_mining.domain.common import DomainEvent
from edge_mining.shared.logging.port import LoggerPort


# Event class name → WebSocket topic
EVENT_TOPIC_MAP: dict[str, str] = {
    "ConfigurationUpdatedEvent": "config.updated",
    "RuleEngagedEvent": "rule.engaged",
    "MinerStateChangedEvent": "miner.state",
    "EnergyStateSnapshotUpdatedEvent": "energy.state",
    "DecisionalContextUpdatedEvent": "policy.context",
}


class WebSocketManager:
    """Manages WebSocket connections and broadcasts domain events to subscribers."""

    def __init__(self, event_bus: EventBusInterface, logger: LoggerPort) -> None:
        self._logger = logger
        # WebSocket → set of topic patterns the client subscribed to
        self._connections: dict[WebSocket, set[str]] = {}

        self._subscribe_events(event_bus)

    def _subscribe_events(self, event_bus: EventBusInterface) -> None:
        """Register all event subscriptions for WebSocket broadcasting."""
        event_bus.subscribe(ConfigurationUpdatedEvent, self.broadcast, blocking=False)
        event_bus.subscribe(RuleEngagedEvent, self.broadcast, blocking=False)
        event_bus.subscribe(MinerStateChangedEvent, self.broadcast, blocking=False)
        event_bus.subscribe(EnergyStateSnapshotUpdatedEvent, self.broadcast, blocking=False)
        event_bus.subscribe(DecisionalContextUpdatedEvent, self.broadcast, blocking=False)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection. No subscriptions by default."""
        await websocket.accept()
        self._connections[websocket] = set()
        self._logger.debug(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self._connections.pop(websocket, None)
        self._logger.debug(f"WebSocket disconnected: {websocket.client}")

    def subscribe(self, websocket: WebSocket, topics: list[str]) -> None:
        """Add topic subscriptions for a connected client."""
        if websocket in self._connections:
            self._connections[websocket].update(topics)
            self._logger.debug(f"WebSocket {websocket.client} subscribed to: {topics}")

    def unsubscribe(self, websocket: WebSocket, topics: list[str]) -> None:
        """Remove topic subscriptions for a connected client."""
        if websocket in self._connections:
            self._connections[websocket] -= set(topics)

    async def broadcast(self, event: DomainEvent) -> None:
        """Broadcast a domain event to all clients subscribed to its topic.

        This method is designed to be used as a fire-and-forget event bus handler.
        """
        topic = EVENT_TOPIC_MAP.get(event.event_type)
        if topic is None:
            return

        message = json.dumps(
            {
                "topic": topic,
                "payload": self._serialize_event(event),
            }
        )

        disconnected: list[WebSocket] = []

        for ws, subscriptions in self._connections.items():
            if not subscriptions:
                continue
            if self._matches(subscriptions, topic):
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(ws)

        # Clean up dead connections
        for ws in disconnected:
            self.disconnect(ws)

    def _matches(self, subscriptions: set[str], topic: str) -> bool:
        """Check if any subscription pattern matches the topic."""
        return any(fnmatch(topic, pattern) for pattern in subscriptions)

    def _serialize_event(self, event: DomainEvent) -> dict[str, Any]:
        """Serialize event for WebSocket transmission."""
        import uuid
        from datetime import datetime
        from enum import Enum

        data = event.to_dict()
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, uuid.UUID):
                sanitized[key] = str(value)
            elif isinstance(value, Enum):
                sanitized[key] = value.value
            elif isinstance(value, datetime):
                sanitized[key] = value.isoformat()
            else:
                sanitized[key] = value
        return sanitized

    async def handle_client_messages(self, websocket: WebSocket) -> None:
        """Listen for subscription messages from a connected client.

        Expected message format:
            {"subscribe": ["energy.*", "miner.state"]}
            {"unsubscribe": ["energy.*"]}
        """
        try:
            while True:
                data = await websocket.receive_json()
                if "subscribe" in data and isinstance(data["subscribe"], list):
                    self.subscribe(websocket, data["subscribe"])
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "topics": sorted(self._connections[websocket]),
                        }
                    )
                if "unsubscribe" in data and isinstance(data["unsubscribe"], list):
                    self.unsubscribe(websocket, data["unsubscribe"])
                    await websocket.send_json(
                        {
                            "type": "subscribed",
                            "topics": sorted(self._connections[websocket]),
                        }
                    )
        except Exception:
            self.disconnect(websocket)
