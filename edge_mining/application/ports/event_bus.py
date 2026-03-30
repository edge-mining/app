"""Application port for the domain event bus."""

from abc import ABC, abstractmethod
from typing import Callable, Type

from edge_mining.domain.common import DomainEvent


class EventBus(ABC):
    """Application port for the domain event bus."""

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event. Blocking handlers are executed before returning."""
        ...

    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable,
        blocking: bool = True,
    ) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: The class of the event to listen for.
            handler: Async coroutine that receives the event.
            blocking: If True, the publisher waits for the handler to complete.
                      If False, the handler is executed in fire-and-forget mode.
        """
        ...
