"""FastAPI WebSocket endpoint for real-time domain events."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from edge_mining.adapters.infrastructure.websocket.manager import WebSocketManager

router = APIRouter()

# WebSocketManager instance — will be set from outside during initialization
_ws_manager: WebSocketManager | None = None


def init_websocket_manager(manager: WebSocketManager) -> None:
    """Initialize the WebSocket manager for the router."""
    global _ws_manager
    _ws_manager = manager


def get_ws_manager() -> WebSocketManager:
    """Get the WebSocket manager instance."""
    if _ws_manager is None:
        raise RuntimeError("WebSocketManager not initialized")
    return _ws_manager


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time domain events.

    After connecting, the client sends subscription messages:
        {"subscribe": ["energy.*", "miner.state"]}

    The server pushes events matching the subscribed topics:
        {"topic": "energy.state", "payload": {...}}
    """
    manager = get_ws_manager()
    await manager.connect(websocket)
    try:
        await manager.handle_client_messages(websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
