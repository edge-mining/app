"""Setup for WebSocket infrastructure with Dependency Injection."""

from edge_mining.adapters.infrastructure.websocket.manager import WebSocketManager
from edge_mining.adapters.infrastructure.websocket.router import init_websocket_manager
from edge_mining.shared.infrastructure import Services
from edge_mining.shared.logging.port import LoggerPort


def init_websocket_dependencies(services: Services, logger: LoggerPort) -> None:
    """Initialize WebSocket dependencies - call this during app startup."""
    ws_manager = WebSocketManager(event_bus=services.event_bus, logger=logger)
    init_websocket_manager(ws_manager)
