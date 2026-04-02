# WebSocket Architecture Design

## Overview

The WebSocket layer provides real-time push notifications to connected clients whenever domain events occur in the system. It follows the same DDD and hexagonal architecture principles used throughout the codebase, with each subdomain owning its own serialization logic while a central manager handles connection management and message delivery.

The design mirrors the pattern used by `main_api.py`, which aggregates FastAPI routers from each subdomain: the `WebSocketManager` aggregates `WebSocketEventHandler` instances from each subdomain and wires them to the event bus automatically.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  Domain Layer                                                    │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ EnergyState      │  │ MinerState       │  │ RuleEngaged    │  │
│  │ SnapshotUpdated  │  │ ChangedEvent     │  │ Event          │  │
│  │ Event            │  │                  │  │                │  │
│  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                     │                    │           │
│  ┌────────┴──────────┐  ┌───────┴──────────┐                     │
│  │ DecisionalContext │  │ Configuration    │                     │
│  │ UpdatedEvent      │  │ UpdatedEvent     │  (application)      │
│  └────────┬──────────┘  └───────┬──────────┘                     │
└───────────┼─────────────────────┼────────────────────────────────┘
            │                     │
            ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│  Event Bus                                                       │
│  (subscribes with blocking=False for fire-and-forget delivery)   │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  WebSocketManager (infrastructure adapter)                       │
│                                                                  │
│  - Collects all WebSocketEventHandler instances                  │
│  - Iterates their registrations (event_type + topic + serialize) │
│  - Subscribes callbacks on event bus                             │
│  - Broadcasts serialized payloads to matching clients            │
│  - Exposes available_topics for client discovery                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI WebSocket Endpoint  /ws/events                          │
│  (accepts connections, delegates to WebSocketManager)            │
└──────────────────────────────────────────────────────────────────┘
```

## Key Components

### `WebSocketEventRegistration` (dataclass)

Located in `edge_mining/adapters/infrastructure/websocket/utils.py`.

A frozen dataclass that binds a domain event to a WebSocket topic and a serialization function:

```python
@dataclass(frozen=True)
class WebSocketEventRegistration:
    event_type: Type[DomainEvent]                        # domain event class to subscribe to
    topic: str                                           # topic string for client subscriptions
    serialize: Callable[[DomainEvent], dict[str, Any]]   # converts event → payload dict
```

The `topic` field is declared alongside the event binding, making it inspectable and discoverable without executing the serialize function.

### `WebSocketMessage` (NamedTuple)

Located in `edge_mining/adapters/infrastructure/websocket/utils.py`.

A typed container used internally by the manager to pair a topic with its serialized payload:

```python
class WebSocketMessage(NamedTuple):
    topic: str
    payload: dict[str, Any]
```

### `WebSocketEventHandler` (ABC)

Located in `edge_mining/adapters/infrastructure/websocket/utils.py`.

Abstract base class that each subdomain handler must extend. It declares a single abstract property:

```python
class WebSocketEventHandler(ABC):
    @property
    @abstractmethod
    def registrations(self) -> List[WebSocketEventRegistration]:
        ...
```

The handler knows nothing about the event bus or the WebSocket manager. It is a pure serializer: given a domain event, it returns a payload dict. The manager is responsible for wiring everything together.

### `WebSocketManager`

Located in `edge_mining/adapters/infrastructure/websocket/manager.py`.

The central aggregator. On construction it:

1. Instantiates all subdomain handlers.
2. Iterates each handler's `registrations`.
3. Collects all declared topics into `_available_topics`.
4. Subscribes an async callback on the event bus for each registration (with `blocking=False`).

When a domain event fires, the corresponding callback serializes it via the handler's `serialize` function, wraps the result in a `WebSocketMessage`, and broadcasts it to all connected clients whose subscription patterns match the topic.

The manager also supports a `get_topics` client command to return the full list of available topics.

### WebSocket Router

Located in `edge_mining/adapters/infrastructure/websocket/router.py`.

Exposes the `/ws/events` FastAPI WebSocket endpoint. The `WebSocketManager` instance is injected via the `init_websocket_manager()` function during application startup.

### Initialization

Located in `edge_mining/adapters/infrastructure/websocket/setup.py`.

Called from `__main__.py` during application boot:

```python
def init_websocket_dependencies(services: Services, logger: LoggerPort) -> None:
    ws_manager = WebSocketManager(event_bus=services.event_bus, logger=logger)
    init_websocket_manager(ws_manager)
```

## File Structure

```
edge_mining/
├── adapters/
│   ├── infrastructure/websocket/          # Core WebSocket infrastructure
│   │   ├── utils.py                       # WebSocketMessage, WebSocketEventRegistration, WebSocketEventHandler ABC
│   │   ├── manager.py                     # WebSocketManager (aggregator)
│   │   ├── router.py                      # FastAPI /ws/events endpoint
│   │   └── setup.py                       # Dependency initialization
│   │
│   ├── domain/                            # Domain subdomain handlers
│   │   ├── energy/websocket/
│   │   │   ├── handlers.py                # EnergyWebSocketHandler
│   │   │   └── schemas.py                 # EnergyStateSnapshotUpdatedSchema
│   │   ├── miner/websocket/
│   │   │   ├── handlers.py                # MinerWebSocketHandler
│   │   │   └── schemas.py                 # MinerStateChangedSchema
│   │   ├── optimization_unit/websocket/
│   │   │   ├── handlers.py                # OptimizationUnitWebSocketHandler
│   │   │   └── schemas.py                 # RuleEngagedSchema
│   │   └── policy/websocket/
│   │       ├── handlers.py                # PolicyWebSocketHandler
│   │       └── schemas.py                 # DecisionalContextUpdatedSchema
│   │
│   └── application/services/configuration/websocket/  # Application-layer handler
│       ├── handlers.py                    # ConfigurationWebSocketHandler
│       └── schemas.py                     # ConfigurationUpdatedSchema
│
├── domain/                                # Domain events (source of truth)
│   ├── energy/events.py                   # EnergyStateSnapshotUpdatedEvent
│   ├── miner/events.py                    # MinerStateChangedEvent
│   ├── optimization_unit/events.py        # RuleEngagedEvent
│   └── policy/events.py                   # DecisionalContextUpdatedEvent
│
└── application/events/
    ├── common.py                          # ConfigurationAction, ConfigurationUpdatedEventType enums
    └── configuration_events.py            # ConfigurationUpdatedEvent
```

## Currently Registered Topics

| Topic              | Domain Event                        | Handler Class                        |
|--------------------|-------------------------------------|--------------------------------------|
| `config.updated`   | `ConfigurationUpdatedEvent`         | `ConfigurationWebSocketHandler`      |
| `energy.state`     | `EnergyStateSnapshotUpdatedEvent`   | `EnergyWebSocketHandler`             |
| `miner.state`      | `MinerStateChangedEvent`            | `MinerWebSocketHandler`              |
| `rule.engaged`     | `RuleEngagedEvent`                  | `OptimizationUnitWebSocketHandler`   |
| `policy.context`   | `DecisionalContextUpdatedEvent`     | `PolicyWebSocketHandler`             |

## How to Add a New WebSocket Event

Follow these steps to expose a new domain event via WebSocket. The example below adds a hypothetical `MinerHashrateUpdatedEvent` from the miner subdomain.

### Step 1 — Define the domain event

Create or update the event dataclass in the relevant subdomain's `events.py`:

```python
# edge_mining/domain/miner/events.py

@dataclass
class MinerHashrateUpdatedEvent(DomainEvent):
    miner_id: Optional[EntityId] = None
    miner_name: str = ""
    hashrate: float = 0.0
```

### Step 2 — Create the WebSocket schema

Add a Pydantic schema in the subdomain's `websocket/schemas.py`:

```python
# edge_mining/adapters/domain/miner/websocket/schemas.py

class MinerHashrateUpdatedSchema(BaseModel):
    miner_id: Optional[str] = Field(None, description="ID of the miner")
    miner_name: str = Field(default="", description="Name of the miner")
    hashrate: float = Field(default=0.0, description="Current hashrate in TH/s")
```

### Step 3 — Register in the handler

Add a new `WebSocketEventRegistration` entry and its serialize method in the subdomain's handler:

```python
# edge_mining/adapters/domain/miner/websocket/handlers.py

class MinerWebSocketHandler(WebSocketEventHandler):

    @property
    def registrations(self) -> List[WebSocketEventRegistration]:
        return [
            WebSocketEventRegistration(
                event_type=MinerStateChangedEvent,
                topic="miner.state",
                serialize=self._serialize_miner_state_changed,
            ),
            # NEW registration
            WebSocketEventRegistration(
                event_type=MinerHashrateUpdatedEvent,
                topic="miner.hashrate",
                serialize=self._serialize_miner_hashrate_updated,
            ),
        ]

    def _serialize_miner_hashrate_updated(self, event: DomainEvent) -> dict[str, Any]:
        assert isinstance(event, MinerHashrateUpdatedEvent)
        payload = MinerHashrateUpdatedSchema(
            miner_id=str(event.miner_id) if event.miner_id else None,
            miner_name=event.miner_name,
            hashrate=event.hashrate,
        )
        return payload.model_dump(mode="json")
```

**That's it.** No changes to the `WebSocketManager` are needed. It discovers the new registration automatically via the handler's `registrations` property. The new topic `miner.hashrate` will appear in `available_topics` and clients subscribing to `miner.*` will receive it automatically.

### Step 4 (new subdomain only) — Create a new handler class

If the event belongs to a **new** subdomain that doesn't have a handler yet:

1. Create `adapters/domain/<subdomain>/websocket/handlers.py` with a class extending `WebSocketEventHandler`.
2. Create `adapters/domain/<subdomain>/websocket/schemas.py` with the Pydantic schema(s).
3. Import and instantiate the new handler in `WebSocketManager.__init__` (add it to the `handlers` list).

## Design Decisions

- **Handlers are pure serializers.** They have no dependency on the event bus or the WebSocket manager. This eliminates circular imports and makes handlers trivially testable.
- **Topics are declarative.** Each `WebSocketEventRegistration` declares its topic explicitly, making it inspectable without executing any code. The manager collects all topics for client discovery.
- **One handler per subdomain, N registrations per handler.** A subdomain with multiple events simply returns multiple entries in its `registrations` list. No new handler classes are needed.
- **`fnmatch` wildcard matching.** Clients can subscribe using glob patterns (`energy.*`, `*`), which is matched via Python's `fnmatch` module.
- **`blocking=False` for all subscriptions.** WebSocket broadcasting is fire-and-forget — it must never block the domain service that raised the event.
- **Configuration events live in the application layer.** Unlike domain events, configuration events (`ConfigurationUpdatedEvent`) are raised by application services and their handler is placed under `adapters/application/services/configuration/websocket/`.
