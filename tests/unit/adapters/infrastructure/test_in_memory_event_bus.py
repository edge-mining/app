"""Unit tests for InMemoryEventBus."""

import asyncio
import unittest
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from edge_mining.adapters.infrastructure.event_bus.in_memory_event_bus import InMemoryEventBus
from edge_mining.domain.common import DomainEvent


@dataclass
class EventA(DomainEvent):
    value: str = ""


@dataclass
class EventB(DomainEvent):
    value: int = 0


@pytest.fixture
def logger():
    mock = MagicMock()
    mock.debug = MagicMock()
    mock.warning = MagicMock()
    return mock


@pytest.fixture
def bus(logger):
    return InMemoryEventBus(logger)


@pytest.mark.asyncio
async def test_subscribe_and_publish(bus):
    handler = AsyncMock(__qualname__="test_handler")
    bus.subscribe(EventA, handler, blocking=True)

    event = EventA(value="hello")
    await bus.publish(event)

    handler.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_publish_no_handlers(bus):
    """Publishing an event with no subscribers should not fail."""
    await bus.publish(EventA(value="ignored"))


@pytest.mark.asyncio
async def test_blocking_handler_awaited(bus):
    """Blocking handler is awaited before publish returns."""
    call_order = []

    async def handler(event):
        call_order.append("handler")

    bus.subscribe(EventA, handler, blocking=True)
    await bus.publish(EventA(value="test"))
    call_order.append("after_publish")

    assert call_order == ["handler", "after_publish"]


@pytest.mark.asyncio
async def test_fire_and_forget_handler(bus):
    """Fire-and-forget handler runs after publish returns."""
    completed = asyncio.Event()

    async def handler(event):
        completed.set()

    bus.subscribe(EventA, handler, blocking=False)
    await bus.publish(EventA(value="test"))

    # Give the fire-and-forget task a chance to run
    await asyncio.wait_for(completed.wait(), timeout=1.0)
    assert completed.is_set()


@pytest.mark.asyncio
async def test_blocking_before_fire_and_forget(bus):
    """Blocking handlers execute before fire-and-forget handlers."""
    order = []

    async def blocking_handler(event):
        order.append("blocking")

    async def ff_handler(event):
        order.append("fire_and_forget")

    bus.subscribe(EventA, blocking_handler, blocking=True)
    bus.subscribe(EventA, ff_handler, blocking=False)

    await bus.publish(EventA(value="test"))
    # Let fire-and-forget tasks complete
    await asyncio.sleep(0.05)

    assert order == ["blocking", "fire_and_forget"]


@pytest.mark.asyncio
async def test_blocking_handler_exception_propagates(bus):
    """Exceptions from blocking handlers propagate to the publisher."""

    async def failing_handler(event):
        raise ValueError("handler failed")

    bus.subscribe(EventA, failing_handler, blocking=True)

    with pytest.raises(ValueError, match="handler failed"):
        await bus.publish(EventA(value="test"))


@pytest.mark.asyncio
async def test_fire_and_forget_handler_exception_caught(bus, logger):
    """Exceptions from fire-and-forget handlers are caught and logged."""
    completed = asyncio.Event()

    async def failing_handler(event):
        completed.set()
        raise ValueError("ff handler failed")

    bus.subscribe(EventA, failing_handler, blocking=False)
    await bus.publish(EventA(value="test"))

    await asyncio.wait_for(completed.wait(), timeout=1.0)
    await asyncio.sleep(0.05)  # Let _safe_execute finish

    logger.warning.assert_called_once()
    assert "ff handler failed" in logger.warning.call_args[0][0]


@pytest.mark.asyncio
async def test_multiple_handlers(bus):
    """Multiple handlers for the same event type are all invoked."""
    handler1 = AsyncMock(__qualname__="handler1")
    handler2 = AsyncMock(__qualname__="handler2")

    bus.subscribe(EventA, handler1, blocking=True)
    bus.subscribe(EventA, handler2, blocking=True)

    event = EventA(value="multi")
    await bus.publish(event)

    handler1.assert_awaited_once_with(event)
    handler2.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_handler_receives_only_subscribed_type(bus):
    """Handlers only receive events of the type they subscribed to."""
    handler_a = AsyncMock(__qualname__="handler_a")
    handler_b = AsyncMock(__qualname__="handler_b")

    bus.subscribe(EventA, handler_a, blocking=True)
    bus.subscribe(EventB, handler_b, blocking=True)

    await bus.publish(EventA(value="a"))

    handler_a.assert_awaited_once()
    handler_b.assert_not_awaited()
