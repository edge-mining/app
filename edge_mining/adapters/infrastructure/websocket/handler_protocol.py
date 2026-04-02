"""Base class for domain-specific WebSocket event handlers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple, Type

from edge_mining.domain.common import DomainEvent


@dataclass(frozen=True)
class WebSocketEventRegistration:
    """A single event-to-topic binding.

    *event_type* is the domain event class to subscribe to.
    *serialize* converts a domain event into a ``(topic, payload)`` pair.
    """

    event_type: Type[DomainEvent]
    serialize: Callable[[DomainEvent], Tuple[str, dict[str, Any]]]


class WebSocketEventHandler(ABC):
    """Each subdomain implements this to declare which events it handles
    and how to serialize them for WebSocket clients.

    The handler knows nothing about the event bus or the WebSocket manager.
    It only provides a list of ``WebSocketEventRegistration`` items,
    each mapping a domain event class to a serialization function.

    A subdomain with one event returns one registration;
    a subdomain with *N* events returns *N* registrations.
    The ``WebSocketManager`` iterates over all registrations,
    subscribes on the event bus, and broadcasts the results.
    """

    @property
    @abstractmethod
    def registrations(self) -> List[WebSocketEventRegistration]:
        """Return the event registrations handled by this subdomain."""
        ...
