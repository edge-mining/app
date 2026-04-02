"""WebSocket manager for broadcasting domain events to connected clients.

Acts as an aggregator: each subdomain provides a ``WebSocketEventHandler``
that declares which event it handles and how to serialize it.
The manager reads ``event_type`` and ``serialize`` from each handler,
subscribes on the event bus, and broadcasts pre-serialized payloads –
mirroring the pattern used by ``main_api.py`` which aggregates FastAPI
routers from each subdomain.
"""

import json
from fnmatch import fnmatch
from typing import List

from fastapi import WebSocket

from edge_mining.adapters.domain.energy.websocket.handlers import EnergyWebSocketHandler
from edge_mining.adapters.domain.miner.websocket.handlers import MinerWebSocketHandler
from edge_mining.adapters.domain.optimization_unit.websocket.handlers import OptimizationUnitWebSocketHandler
from edge_mining.adapters.domain.policy.websocket.handlers import PolicyWebSocketHandler
from edge_mining.adapters.application.services.configuration.websocket.handlers import ConfigurationWebSocketHandler
from edge_mining.adapters.infrastructure.websocket.utils import WebSocketEventHandler, WebSocketMessage
from edge_mining.application.interfaces import EventBusInterface
from edge_mining.domain.common import DomainEvent
from edge_mining.shared.logging.port import LoggerPort


class WebSocketManager:
    """Manages WebSocket connections and broadcasts domain events to subscribers.

    Each subdomain handler exposes a ``registrations`` property
    returning a list of ``WebSocketEventRegistration`` items.
    Each registration binds a domain event class to a serialization function.

    The manager iterates over all registrations, subscribes on the event bus,
    and broadcasts the serialized results.
    """

    def __init__(self, event_bus: EventBusInterface, logger: LoggerPort) -> None:
        self._logger = logger
        self._connections: dict[WebSocket, set[str]] = {}
        self._available_topics: List[str] = []

        # Collect all subdomain handlers
        handlers: List[WebSocketEventHandler] = [
            ConfigurationWebSocketHandler(),
            EnergyWebSocketHandler(),
            MinerWebSocketHandler(),
            OptimizationUnitWebSocketHandler(),
            PolicyWebSocketHandler(),
        ]

        # Subscribe to the event bus for every registration across all handlers
        for handler in handlers:
            for registration in handler.registrations:
                self._available_topics.append(registration.topic)
                event_bus.subscribe(
                    registration.event_type,
                    self._make_callback(registration.topic, registration.serialize),
                    blocking=False,
                )

    @property
    def available_topics(self) -> List[str]:
        """Return the list of all topics that clients can subscribe to."""
        return list(self._available_topics)

    def _make_callback(self, topic, serialize_fn):
        """Create an async callback that serializes the event and broadcasts it."""

        async def _callback(event: DomainEvent) -> None:
            payload = serialize_fn(event)
            await self.broadcast_message(WebSocketMessage(topic, payload))

        return _callback

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

    async def broadcast_message(self, message: WebSocketMessage) -> None:
        """Broadcast a pre-serialized payload to all clients subscribed to the topic.

        Called by subdomain handlers after they have serialized their events.
        """
        raw = json.dumps({"topic": message.topic, "payload": message.payload})

        disconnected: list[WebSocket] = []

        for ws, subscriptions in self._connections.items():
            if not subscriptions:
                continue
            if self._matches(subscriptions, message.topic):
                try:
                    await ws.send_text(raw)
                except Exception:
                    disconnected.append(ws)

        # Clean up dead connections
        for ws in disconnected:
            self.disconnect(ws)

    def _matches(self, subscriptions: set[str], topic: str) -> bool:
        """Check if any subscription pattern matches the topic."""
        return any(fnmatch(topic, pattern) for pattern in subscriptions)

    async def handle_client_messages(self, websocket: WebSocket) -> None:
        """Listen for messages from a connected client.

        Expected message format:
            {"subscribe": ["energy.*", "miner.state"]}
            {"unsubscribe": ["energy.*"]}
            {"get_topics": true}
        """
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("get_topics"):
                    await websocket.send_json(
                        {
                            "type": "available_topics",
                            "topics": sorted(self._available_topics),
                        }
                    )
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
