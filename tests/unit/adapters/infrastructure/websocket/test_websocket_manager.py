"""Unit tests for WebSocketManager."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from edge_mining.adapters.infrastructure.websocket.manager import WebSocketManager
from edge_mining.adapters.infrastructure.websocket.utils import WebSocketMessage
from edge_mining.application.events.configuration_events import ConfigurationUpdatedEvent
from edge_mining.domain.energy.events import EnergyStateSnapshotUpdatedEvent
from edge_mining.domain.miner.events import MinerStateChangedEvent
from edge_mining.domain.optimization_unit.events import RuleEngagedEvent
from edge_mining.domain.policy.events import DecisionalContextUpdatedEvent
from edge_mining.application.interfaces import EventBusInterface
from edge_mining.domain.common import EntityId, Watts
from edge_mining.domain.miner.common import MinerStatus
from edge_mining.domain.policy.common import MiningDecision


@pytest.fixture
def logger():
    mock = MagicMock()
    mock.debug = MagicMock()
    mock.info = MagicMock()
    mock.warning = MagicMock()
    mock.error = MagicMock()
    return mock


@pytest.fixture
def mock_event_bus():
    bus = MagicMock(spec=EventBusInterface)
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def manager(mock_event_bus, logger):
    return WebSocketManager(event_bus=mock_event_bus, logger=logger)


def make_ws():
    """Create a mock WebSocket."""
    ws = AsyncMock()
    ws.client = ("127.0.0.1", 8000)
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_json = AsyncMock()
    return ws


# --- Event bus subscription ---


def test_subscribe_events_registers_all_handlers(mock_event_bus, logger):
    """WebSocketManager should subscribe to all event types on construction."""
    manager = WebSocketManager(event_bus=mock_event_bus, logger=logger)
    assert mock_event_bus.subscribe.call_count == 5
    subscribed_types = {call.args[0] for call in mock_event_bus.subscribe.call_args_list}
    assert subscribed_types == {
        ConfigurationUpdatedEvent,
        RuleEngagedEvent,
        MinerStateChangedEvent,
        EnergyStateSnapshotUpdatedEvent,
        DecisionalContextUpdatedEvent,
    }
    # All should be fire-and-forget
    for call in mock_event_bus.subscribe.call_args_list:
        assert call.kwargs.get("blocking") is False or call.args[2] is False


def test_available_topics_returns_all_registered_topics(mock_event_bus, logger):
    """available_topics should list every topic declared by subdomain handlers."""
    manager = WebSocketManager(event_bus=mock_event_bus, logger=logger)
    assert sorted(manager.available_topics) == [
        "config.updated",
        "energy.state",
        "miner.state",
        "policy.context",
        "rule.engaged",
    ]


# --- Connection management ---


@pytest.mark.asyncio
async def test_connect(manager):
    ws = make_ws()
    await manager.connect(ws)
    assert ws in manager._connections
    ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.disconnect(ws)
    assert ws not in manager._connections


def test_disconnect_unknown_ws(manager):
    ws = make_ws()
    manager.disconnect(ws)  # Should not raise


# --- Subscription ---


@pytest.mark.asyncio
async def test_subscribe(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["energy.*", "miner.state"])
    assert manager._connections[ws] == {"energy.*", "miner.state"}


@pytest.mark.asyncio
async def test_unsubscribe(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["energy.*", "miner.state"])
    manager.unsubscribe(ws, ["energy.*"])
    assert manager._connections[ws] == {"miner.state"}


@pytest.mark.asyncio
async def test_subscribe_not_connected(manager):
    ws = make_ws()
    manager.subscribe(ws, ["energy.*"])  # Should not raise
    assert ws not in manager._connections


# --- Topic matching ---


def test_matches_exact(manager):
    assert manager._matches({"energy.state"}, "energy.state") is True
    assert manager._matches({"energy.state"}, "miner.state") is False


def test_matches_wildcard(manager):
    assert manager._matches({"energy.*"}, "energy.state") is True
    assert manager._matches({"energy.*"}, "miner.state") is False


def test_matches_star_all(manager):
    assert manager._matches({"*"}, "energy.state") is True
    assert manager._matches({"*"}, "miner.state") is True
    assert manager._matches({"*"}, "config.updated") is True


# --- Broadcasting ---


@pytest.mark.asyncio
async def test_broadcast_sends_to_matching_subscriber(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["energy.*"])

    await manager.broadcast_message(
        WebSocketMessage(
            topic="energy.state",
            payload={"optimization_unit_name": "Unit 1"},
        )
    )

    ws.send_text.assert_awaited_once()
    sent = json.loads(ws.send_text.call_args[0][0])
    assert sent["topic"] == "energy.state"
    assert sent["payload"]["optimization_unit_name"] == "Unit 1"


@pytest.mark.asyncio
async def test_broadcast_skips_non_matching_subscriber(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["miner.*"])

    await manager.broadcast_message(
        WebSocketMessage(
            topic="energy.state",
            payload={"optimization_unit_name": "Unit 1"},
        )
    )

    ws.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_skips_client_with_no_subscriptions(manager):
    ws = make_ws()
    await manager.connect(ws)
    # No subscribe call

    await manager.broadcast_message(WebSocketMessage(topic="energy.state", payload={}))

    ws.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_cleans_dead_connections(manager):
    ws = make_ws()
    ws.send_text.side_effect = Exception("Connection closed")
    await manager.connect(ws)
    manager.subscribe(ws, ["energy.*"])

    await manager.broadcast_message(WebSocketMessage(topic="energy.state", payload={}))

    assert ws not in manager._connections


@pytest.mark.asyncio
async def test_broadcast_multiple_clients(manager):
    ws1 = make_ws()
    ws2 = make_ws()
    ws3 = make_ws()

    await manager.connect(ws1)
    await manager.connect(ws2)
    await manager.connect(ws3)

    manager.subscribe(ws1, ["energy.*"])
    manager.subscribe(ws2, ["miner.*"])
    manager.subscribe(ws3, ["*"])

    await manager.broadcast_message(WebSocketMessage(topic="energy.state", payload={}))

    ws1.send_text.assert_awaited_once()
    ws2.send_text.assert_not_awaited()
    ws3.send_text.assert_awaited_once()


# --- Subdomain handler broadcasting ---


@pytest.mark.asyncio
async def test_broadcast_rule_engaged_event(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["rule.*"])

    await manager.broadcast_message(
        WebSocketMessage(
            topic="rule.engaged",
            payload={
                "optimization_unit_name": "Unit 1",
                "policy_name": "Solar Policy",
                "decision": "start_mining",
                "miner_status": "OFF",
            },
        )
    )

    ws.send_text.assert_awaited_once()
    sent = json.loads(ws.send_text.call_args[0][0])
    assert sent["topic"] == "rule.engaged"


@pytest.mark.asyncio
async def test_broadcast_miner_state_event(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["miner.state"])

    await manager.broadcast_message(
        WebSocketMessage(
            topic="miner.state",
            payload={
                "miner_name": "Antminer",
                "old_status": "off",
                "new_status": "on",
            },
        )
    )

    ws.send_text.assert_awaited_once()
    sent = json.loads(ws.send_text.call_args[0][0])
    assert sent["topic"] == "miner.state"


@pytest.mark.asyncio
async def test_broadcast_config_updated_event(manager):
    ws = make_ws()
    await manager.connect(ws)
    manager.subscribe(ws, ["config.*"])

    await manager.broadcast_message(
        WebSocketMessage(
            topic="config.updated",
            payload={"entity_type": "", "entity_id": None, "action": ""},
        )
    )

    ws.send_text.assert_awaited_once()
    sent = json.loads(ws.send_text.call_args[0][0])
    assert sent["topic"] == "config.updated"
