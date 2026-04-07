"""In-memory implementation of the event bus."""

import asyncio
from collections import defaultdict
from typing import Callable, Type

from edge_mining.application.interfaces import EventBusInterface
from edge_mining.domain.common import DomainEvent
from edge_mining.shared.logging.port import LoggerPort


class InMemoryEventBus(EventBusInterface):
    """In-memory implementation of the event bus with blocking/fire-and-forget support."""

    def __init__(self, logger: LoggerPort) -> None:
        self._logger = logger
        # dict[Type[DomainEvent], list[tuple[Callable, bool]]]
        # bool = is_blocking
        self._handlers: dict[Type[DomainEvent], list[tuple[Callable, bool]]] = defaultdict(list)

    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable,
        blocking: bool = True,
    ) -> None:
        self._handlers[event_type].append((handler, blocking))
        self._logger.debug(
            f"EventBus: subscribed {handler.__qualname__} to {event_type.__name__} (blocking={blocking})"
        )

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])

        if not handlers:
            return

        self._logger.debug(
            f"EventBus: publishing {event.event_type} (id={event.event_id[:8]}..., handlers={len(handlers)})"
        )

        # 1. Blocking handlers — the publisher WAITS, exceptions are propagated
        for handler, is_blocking in handlers:
            if is_blocking:
                await handler(event)

        # 2. Fire-and-forget handlers — the publisher DOES NOT wait, exceptions are caught
        for handler, is_blocking in handlers:
            if not is_blocking:
                asyncio.create_task(self._safe_execute(handler, event))

    async def _safe_execute(self, handler: Callable, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception as e:
            self._logger.warning(
                f"EventBus: fire-and-forget handler {handler.__qualname__} failed for {event.event_type}: {e}"
            )
