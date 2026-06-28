# Event Bus Architecture Design

## Overview

The event bus provides decoupled communication between application services. Services publish domain events without knowing who consumes them; subscribers react independently. This eliminates circular dependencies between services (e.g. `ConfigurationService` → `AdapterService` cache invalidation) and enables cross-cutting concerns like WebSocket broadcasting without polluting business logic.

The bus is fully async and supports two delivery modes per subscriber: **blocking** (publisher waits) and **fire-and-forget** (publisher continues immediately). This models the real-world distinction between critical operations that must complete before the flow continues and best-effort side effects that can happen in the background.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  Publishers                                                      │
│                                                                  │
│  ┌───────────────────────────┐  ┌─────────────────────┐          │
│  │ ConfigurationService      │  │ OptimizationService │          │
│  │                           │  │                     │          │
│  │ publish(ConfigurationUpd) │  │ publish(            │          │
│  │                           │  │  EnergyStateUpd)    │          │
│  └────────┬──────────────────┘  │  DecisionalCtxUpd)  │          │
│           │                     │  RuleEngagedEvent)  │          │
│           │                     │  MinerStateChanged) │          │
│           │                     └────────┬────────────┘          │
│           │                              │                       │
│           │  ┌───────────────────────────┘                       │
│           │  │  ┌──────────────────┐                             │
│           │  │  │MinerActionService│                             │
│           │  │  │ publish(         │                             │
│           │  │  │  MinerStateChgd) │                             │
│           │  │  └───────┬──────────┘                             │
└───────────┼──┼──────────┼────────────────────────────────────────┘
            │  │          │
            ▼  ▼          ▼
┌──────────────────────────────────────────────────────────────────┐
│  InMemoryEventBus                                                │
│                                                                  │
│  1. Execute blocking handlers sequentially (await each)          │
│  2. Dispatch fire-and-forget handlers via asyncio.create_task()  │
│                                                                  │
└───────────┬──────────────────────────────┬───────────────────────┘
            │                              │
            ▼                              ▼
   ┌──────────────────────┐     ┌─────────────────────────┐
   │ blocking=True        │     │ blocking=False          │
   │                      │     │                         │
   │ AdapterService       │     │ WebSocketManager        │
   │ .on_configuration_   │     │  (broadcasts to clients │
   │  updated()           │     │   via /ws/events)       │
   │ (cache invalidation) │     │                         │
   └──────────────────────┘     └─────────────────────────┘
```

## Key Components

### `DomainEvent` (base dataclass)

Located in `edge_mining/domain/common.py`.

Base class for all events in the system. Provides automatic ID generation, timestamp, and a serialization helper:

```python
@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_type(self) -> str:
        return self.__class__.__name__
```

### `EventBusInterface` (ABC)

Located in `edge_mining/application/interfaces.py`.

The application-layer port that services depend on. Defines two operations:

```python
class EventBusInterface(ABC):
    @abstractmethod
    async def publish(self, event: DomainEvent) -> None: ...

    @abstractmethod
    def subscribe(
        self,
        event_type: Type[DomainEvent],
        handler: Callable,
        blocking: bool = True,
    ) -> None: ...
```

The `blocking` parameter controls delivery semantics per subscriber.

### `InMemoryEventBus` (adapter)

Located in `edge_mining/adapters/infrastructure/event_bus/in_memory_event_bus.py`.

The single concrete implementation. On `publish()`:

1. **Blocking handlers** are awaited sequentially — exceptions propagate to the publisher.
2. **Fire-and-forget handlers** are dispatched via `asyncio.create_task()` — exceptions are caught and logged as warnings.

```python
async def publish(self, event: DomainEvent) -> None:
    handlers = self._handlers.get(type(event), [])

    # 1. Blocking — publisher WAITS, exceptions propagate
    for handler, is_blocking in handlers:
        if is_blocking:
            await handler(event)

    # 2. Fire-and-forget — publisher CONTINUES, exceptions caught
    for handler, is_blocking in handlers:
        if not is_blocking:
            asyncio.create_task(self._safe_execute(handler, event))
```

### `Services` (dataclass)

Located in `edge_mining/shared/infrastructure.py`.

The DI container carries the `event_bus` instance alongside all application services:

```python
@dataclass(frozen=True)
class Services:
    adapter_service: AdapterServiceInterface
    optimization_service: OptimizationServiceInterface
    miner_action_service: MinerActionServiceInterface
    configuration_service: ConfigurationServiceInterface
    event_bus: EventBusInterface
```

## File Structure

```
edge_mining/
├── domain/
│   ├── common.py                              # DomainEvent base class
│   ├── energy/events.py                       # EnergyStateSnapshotUpdatedEvent
│   ├── miner/events.py                        # MinerStateChangedEvent
│   ├── optimization_unit/events.py            # RuleEngagedEvent
│   └── policy/events.py                       # DecisionalContextUpdatedEvent
│
├── application/
│   ├── interfaces.py                          # EventBusInterface (port)
│   ├── events/
│   │   ├── common.py                          # ConfigurationAction, ConfigurationUpdatedEventType enums
│   │   └── configuration_events.py            # ConfigurationUpdatedEvent
│   └── services/
│       ├── configuration_service.py           # publishes ConfigurationUpdatedEvent
│       ├── optimization_service.py            # publishes Energy/DecisionalContext/RuleEngaged/MinerStateChanged
│       ├── miner_action_service.py            # publishes MinerStateChangedEvent
│       └── adapter_service.py                 # subscribes to ConfigurationUpdatedEvent (blocking)
│
├── adapters/infrastructure/
│   └── event_bus/
│       └── in_memory_event_bus.py             # InMemoryEventBus implementation
│
├── shared/
│   └── infrastructure.py                      # Services dataclass (holds event_bus)
│
└── bootstrap.py                               # Wires event bus, services, and subscriptions
```

## Registered Events

### Domain Events

| Event | Subdomain | Publisher(s) | Description |
|---|---|---|---|
| `EnergyStateSnapshotUpdatedEvent` | energy | `OptimizationService` | New energy state snapshot read from a source |
| `MinerStateChangedEvent` | miner | `OptimizationService`, `MinerActionService` | Miner operational status changed (on/off) |
| `RuleEngagedEvent` | optimization_unit | `OptimizationService` | Policy rule produced a mining decision |
| `DecisionalContextUpdatedEvent` | policy | `OptimizationService` | Decisional context composed for an optimization unit |

### Application Events

| Event | Layer | Publisher | Description |
|---|---|---|---|
| `ConfigurationUpdatedEvent` | application | `ConfigurationService` | Entity created, updated, or removed |

`ConfigurationUpdatedEvent` uses typed enums instead of raw strings:

- `ConfigurationUpdatedEventType`: `ENERGY_MONITOR`, `MINER_CONTROLLER`, `NOTIFIER`, `EXTERNAL_SERVICE`
- `ConfigurationAction`: `CREATED`, `UPDATED`, `REMOVED`

## Registered Subscribers

| Event | Subscriber | Blocking | Purpose |
|---|---|---|---|
| `ConfigurationUpdatedEvent` | `AdapterService.on_configuration_updated` | **Yes** | Invalidate adapter instance cache |
| `EnergyStateSnapshotUpdatedEvent` | `WebSocketManager` (via handler) | No | Broadcast to frontend |
| `MinerStateChangedEvent` | `WebSocketManager` (via handler) | No | Broadcast to frontend |
| `RuleEngagedEvent` | `WebSocketManager` (via handler) | No | Broadcast to frontend |
| `DecisionalContextUpdatedEvent` | `WebSocketManager` (via handler) | No | Broadcast to frontend |
| `ConfigurationUpdatedEvent` | `WebSocketManager` (via handler) | No | Broadcast to frontend |

## Subscription Wiring

Subscriptions are established in two ways, both during application startup:

**Self-registering services** — `AdapterService` subscribes itself in its constructor:

```python
class AdapterService:
    def __init__(self, ..., event_bus: EventBusInterface, ...):
        self._subscribe_events(event_bus)

    def _subscribe_events(self, event_bus: EventBusInterface) -> None:
        event_bus.subscribe(
            ConfigurationUpdatedEvent,
            self.on_configuration_updated,
            blocking=True,
        )
```

**WebSocketManager** — subscribes all its handlers' registrations in its constructor (see `docs/architecture/websocket-design.md` for details).

Both are instantiated in `bootstrap.py` → `configure_dependencies()`, where the same `InMemoryEventBus` instance is injected into all services.

## Delivery Semantics

### Blocking (`blocking=True`)

The publisher awaits the handler. If it raises, the exception propagates to the publisher. Used for operations that **must** complete before the business flow continues.

Current blocking handlers are in-memory operations (cache invalidation via `dict.pop()`), so failure probability is near zero. If a blocking handler were to perform real I/O in the future, the error handling strategy should be revisited.

### Fire-and-forget (`blocking=False`)

The handler runs as a detached `asyncio.Task`. Exceptions are caught by `_safe_execute()` and logged as warnings. The publisher never knows if it succeeded or failed.

No retry mechanism is implemented. If a WebSocket broadcast fails because a client disconnected, retrying would be pointless. If transient failures become a real concern, a retry/backpressure layer can be added at the bus level without changing any publisher or subscriber.

## How to Add a New Event

### Step 1 — Define the event

Create a dataclass extending `DomainEvent` in the relevant subdomain:

```python
# edge_mining/domain/miner/events.py

@dataclass
class MinerHashrateUpdatedEvent(DomainEvent):
    miner_id: Optional[EntityId] = None
    hashrate: float = 0.0
```

### Step 2 — Publish from a service

Call `event_bus.publish()` after the business operation:

```python
# In the application service
if self._event_bus:
    await self._event_bus.publish(
        MinerHashrateUpdatedEvent(
            miner_id=miner.id,
            hashrate=current_hashrate,
        )
    )
```

The `if self._event_bus` guard allows services to work without an event bus in testing or standalone modes.

### Step 3 — Subscribe (if needed)

For a blocking subscriber in another service:

```python
event_bus.subscribe(MinerHashrateUpdatedEvent, some_service.on_hashrate_updated, blocking=True)
```

For WebSocket broadcasting, add a registration to the relevant subdomain handler (see `docs/architecture/websocket-design.md`).

## Design Decisions

- **Single bus, two delivery modes.** A single `InMemoryEventBus` serves both internal (cache invalidation) and external (WebSocket) subscribers. The `blocking` flag provides the necessary semantic distinction without the complexity of separate bus instances.
- **Async-first.** All handlers are async coroutines. The bus uses `await` for blocking and `asyncio.create_task()` for fire-and-forget, matching the async nature of the application services (Home Assistant API, PyASIC sockets, Telegram API).
- **Exception propagation for blocking handlers.** Blocking handlers today are in-memory operations that should never fail. If they do, it's a bug, and the exception should surface to the caller rather than being silently swallowed.
- **Application-level configuration event.** `ConfigurationUpdatedEvent` uses a generic structure with typed enums (`ConfigurationUpdatedEventType`, `ConfigurationAction`) rather than per-entity event classes. The primary use case is cache invalidation, where the subscriber only needs to know *which cache entry* is stale, not the full entity data. This avoids class proliferation (3 actions × N entity types) while retaining type safety through enums.
- **Domain events in subdomains.** Domain events (`EnergyStateSnapshotUpdatedEvent`, `MinerStateChangedEvent`, etc.) live in their respective subdomain's `events.py`, following DDD ownership principles. If a subdomain were extracted into a separate bounded context, its events would travel with it.
- **Optional event bus injection.** Services accept `event_bus: Optional[EventBusInterface] = None` and guard publishes with `if self._event_bus`. This keeps services testable without requiring a bus mock in every unit test.
