# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-rev3]

### Added
- **Mining Performance Analysis Domain** (`edge_mining/domain/performance/`):
  - Value objects: `MiningReward`, `PoolWorkerStats`, `PoolStats`, `PayoutSchedule` in `value_objects.py` (renamed from misspelled `values_objects.py`)
  - Entity `MiningSession` for tracking aggregated mining activity (`entities.py`)
  - Common types: `PayoutFrequency` enum, `Satoshi` NewType (`common.py`)
  - Domain exceptions: `MiningPoolUnreachableError`, `MiningPoolAuthError`, `MiningPoolResponseError`
  - Domain events: `RewardReceivedEvent`, `HashrateDropDetectedEvent` (`events.py`)
  - Async `MiningPerformanceTrackerPort` contract for live pool data (stats, rewards history, payout schedule, workers)

- **Pool Tracker Adapters** (`edge_mining/adapters/domain/performance/trackers/`):
  - `OceanMiningPerformanceTracker` — public Ocean pool API integration (no authentication, Bitcoin address based)
  - `BraiinsPoolMiningPerformanceTracker` — Braiins Pool v1 API integration using `Pool-Auth-Token` header
  - Corresponding adapter factories (`OceanMiningPerformanceTrackerFactory`, `BraiinsPoolMiningPerformanceTrackerFactory`)
  - Abstract `MiningPerformanceTrackerAdapterFactory` in `shared/interfaces/factories.py`

- **REST API** (`edge_mining/adapters/domain/performance/fast_api/router.py`):
  - 13 endpoints under `/api/v1` covering tracker CRUD, type discovery, config schema inspection, external service listing, connectivity test, live stats, workers, rewards history, payout schedule
  - Error mapping: `MiningPoolAuthError` → 401, `MiningPoolUnreachableError` → 503, `MiningPoolResponseError` → 502, `NotFoundError` → 404, `ConfigurationError` → 400

- **Pydantic Schemas** (`edge_mining/adapters/domain/performance/schemas.py`):
  - Tracker CRUD schemas with `to_model`/`from_model` converters
  - Per-adapter config schemas (Dummy, Ocean requires `bitcoin_address`, Braiins Pool requires `api_token`) + `MINING_PERFORMANCE_TRACKER_CONFIG_SCHEMA_MAP`
  - Response schemas: `HashRateSchema`, `PoolWorkerStatsSchema`, `PoolStatsSchema`, `MiningRewardSchema`, `PayoutScheduleSchema`, `MiningPerformanceSnapshotSchema` (all with both `from_model` and `to_model`)

- **MiningPerformanceSnapshot Value Object** (`edge_mining/domain/performance/value_objects.py`):
  - Consolidated snapshot grouping `current_hashrate` + `pool_stats` + `payout_schedule` under a single `timestamp`, following the same pattern as `EnergyStateSnapshot` and `MinerStateSnapshot`
  - Exposed to the rule engine via the new `DecisionalContext.mining_performance` field — enables rules on aggregated metrics (24h/7d average hashrate, unpaid balance, estimated next payout, payout frequency/threshold)

- **Interactive CLI** (`edge_mining/adapters/domain/performance/cli/commands.py`):
  - New main menu option "Manage Mining Performance Trackers" (list, create, update, delete, test, show stats/workers/rewards/payout)
  - Adapter-aware configuration wizard with dict-dispatch handler map
  - Async-to-sync bridging via `run_async_func` helper

- **Configuration & Wiring**:
  - `MINING_PERFORMANCE_TRACKER_CONFIG_TYPE_MAP` and `MINING_PERFORMANCE_TRACKER_EXTERNAL_SERVICE_MAP` in `shared/adapter_maps/performance.py`
  - New adapter configs (`DummyMiningPerformanceTrackerConfig`, `OceanMiningPerformanceTrackerConfig`, `BraiinsPoolMiningPerformanceTrackerConfig`)
  - Nine new `ConfigurationService` methods for tracker lifecycle management
  - `ConfigurationUpdatedEventType.MINING_PERFORMANCE_TRACKER` event type
  - `adapter_service.py` registers the three tracker factories

- **Shared Helper** (`edge_mining/domain/common.py`):
  - `utc_now_timestamp()` function to produce fresh `Timestamp` values for dataclass `default_factory` usage

- **Rate-limit / caching layer for pool trackers** (`edge_mining/adapters/domain/performance/trackers/_base.py`):
  - New shared base class `CachedRateLimitedTrackerBase` providing per-method TTL caching and exponential backoff (5s / 10s / 20s / 40s / 80s with ±20% jitter) around HTTP 429 responses
  - `MiningPoolRateLimitedError` domain exception (with optional `retry_after` hint) raised when the pool signals throttling; mapped to HTTP 429 by the REST router (including `Retry-After` response header) and displayed with hint in the CLI
  - Stale-while-error fallback: when all retries are exhausted a cached value — even if past its TTL — is served in preference to propagating the error; the error is only re-raised when no cached value exists
  - In-memory cache keyed by `(method_name, args_tuple)` so methods with arguments (e.g. `get_recent_rewards(limit)`) get separate cache slots
  - TTL tables (`TTL_MAP`) tuned per pool: hashrate 60s, pool/worker stats 300s (worker data updates every ~5 min upstream), recent rewards 600s, payout schedule 3600s
  - Applied transparently to both `OceanMiningPerformanceTracker` and `BraiinsPoolMiningPerformanceTracker`; `_get()` detects 429 before any auth/5xx mapping and extracts `Retry-After`

- **Tests** — 107 new unit tests across tracker adapters, configuration service, REST router, and CLI commands
- **Tests** — 15 new unit tests for `CachedRateLimitedTrackerBase` (cache hit/miss, TTL expiry, backoff progression, stale-while-error, retry-after handling, cache invalidation) plus 429-detection tests for the Ocean and Braiins adapters

### Changed
- `MiningPerformanceTrackerPort` methods are now `async`; the dummy tracker adapter has been adapted accordingly
- `OptimizationService` now awaits `get_current_hashrate` calls to match the async port contract, and consolidates the three tracker calls behind a new private helper `_build_mining_performance_snapshot` that returns a single `MiningPerformanceSnapshot`
- Replaced `DecisionalContext.tracker_current_hashrate: Optional[HashRate]` with `mining_performance: Optional[MiningPerformanceSnapshot]`; `DecisionalContextSchema` and the rule engine `OPERATOR_EXAMPLES[LTE]` example updated accordingly (new field path: `mining_performance.current_hashrate.value`)
- Interactive CLI main menu: "Run all optimization units" shifted from option 8 to 9 to accommodate the new tracker menu at option 8
- Replaced per-module `_utc_now_timestamp()` helpers in `domain/performance/entities.py` and `domain/performance/value_objects.py` with the shared `utc_now_timestamp()` from `domain/common.py`

### Fixed
- Replaced latent `default_factory=Timestamp(datetime.now())` bugs (which froze a single timestamp at class-definition time) with the proper callable `utc_now_timestamp`, producing a fresh timestamp per instance
- **Braiins Pool adapter aligned to post-FPPS API schema** (`edge_mining/adapters/domain/performance/trackers/braiins_pool.py`): the adapter was reading pre-FPPS field names that were removed in the November 2023 migration, so `unpaid_balance`, worker `valid_shares`, `payout_schedule.threshold` and `payout_schedule.next_payout_at` were always `None` in the `DecisionalContext`. Mapping now follows the current schema:
  - `unpaid_balance` reads `current_balance` (previously `unconfirmed_reward`, removed upstream)
  - current-hashrate fallback chain uses `hash_rate_60m` (previously `hash_rate_1h`, which never existed)
  - `average_hashrate_7d` is left `None` (Braiins exposes only 24h/yesterday aggregates)
  - `PayoutSchedule` is now `DAILY` with `threshold=None` and `next_payout_at=None` (FPPS pays daily, threshold is no longer configurable)
  - Worker `valid_shares` maps to `shares_24h` (the only cumulative share metric exposed); `stale_shares`/`rejected_shares` stay `None` as Braiins doesn't surface them

## [0.1.0-rev2]

### Added
- **Miner Aggregate Root** (`edge_mining/domain/miner/aggregate_roots.py`):
  - Promotes `Miner` to a full aggregate root with feature management capabilities
  - Feature CRUD: `add_feature()`, `remove_feature()`, `remove_features_by_controller()`
  - Feature queries: `get_active_feature()`, `get_features_by_controller()`, `get_features_by_type()`, `get_controller_ids()`, `has_feature()`
  - Feature configuration: `enable_feature()`, `disable_feature()`, `set_feature_priority()`

- **Miner Feature System** (`edge_mining/domain/miner/ports.py`):
  - `MinerFeature` value object with identity based on `(feature_type, controller_id)` pair and configurable priority/enabled state
  - `MinerFeatureType` enum with 17 values across 4 categories: monitoring (9), control (4), detection (3)
  - `MinerFeaturePort` abstract base with MRO-based introspection via `get_supported_features()` class method
  - **Monitoring Ports**: `HashrateMonitorPort`, `PowerMonitorPort`, `StatusMonitorPort`, `HashboardMonitorPort`, `InletTemperatureMonitorPort`, `OutletTemperatureMonitorPort`, `InternalFanSpeedMonitorPort`, `ExternalFanSpeedMonitorPort`, `OperationalMonitorPort`
  - **Control Ports**: `MiningControlPort`, `PowerControlPort`, `InternalFanControlPort`, `ExternalFanControlPort`
  - **Detection Ports**: `MaxPowerDetectionPort`, `MaxHashrateDetectionPort`, `DeviceInfoPort`

- **New Value Objects** (`edge_mining/domain/miner/value_objects.py`):
  - Measurement types: `Temperature`, `FanSpeed`, `Voltage`, `Frequency` frozen dataclasses with value and unit
  - `MinerInfo`: Device information with model, serial number, firmware type (Stock, BOS+, VNish, etc.), firmware version, MAC address, hostname, hashboard/chip/fan count
  - `MinerLimit`: Miner limits with optional `max_power` (Watts) and `max_hash_rate` (HashRate)
  - `HashboardSnapshot`: Per-board metrics (chip/board temperature, voltage, frequency, hash rate, nominal hash rate, hash rate error)
  - Extended `MinerStateSnapshot` with: `inlet_temperature`, `outlet_temperature`, `internal_fan_speed` (list), `hashboards` (list), and convenience properties (`max_chip_temperature`, `avg_board_temperature`, etc.)

- **New Pydantic Schemas** (`edge_mining/adapters/domain/miner/schemas.py`):
  - `TemperatureSchema`, `FanSpeedSchema`, `VoltageSchema`, `FrequencySchema` with unit validation
  - `HashboardSnapshotSchema`, `MinerInfoSchema`, `MinerFeatureSchema`, `FeaturePrioritySchema`
  - `MinerLimitSchema` with validation, `from_model()`/`to_model()` conversion for `MinerLimit` value object

- **`miner_features` Database Table** (`edge_mining/adapters/domain/miner/tables.py`):
  - Columns: `id`, `miner_id` (FK), `controller_id` (FK), `feature_type`, `priority` (default 50), `enabled` (default True)
  - Helper functions: `load_features_for_miner()`, `save_features_for_miner()`

- **New API Endpoints** (`edge_mining/adapters/domain/miner/fast_api/router.py`):
  - `GET /miners/{miner_id}/info` — Get miner device information (model, serial number, firmware version, etc.)
  - `GET /miners/{miner_id}/limits` — Get miner limits (max power, max hash rate) via `MaxPowerDetectionPort` and `MaxHashrateDetectionPort`
  - `GET /miners/{miner_id}/features` — List miner features
  - `POST /miners/{miner_id}/features/{controller_id}/{feature_type}/enable` — Enable a feature
  - `POST /miners/{miner_id}/features/{controller_id}/{feature_type}/disable` — Disable a feature
  - `PUT /miners/{miner_id}/features/{controller_id}/{feature_type}/priority` — Set feature priority
  - `POST /miners/{miner_id}/link-controller/{controller_id}` — Link controller and auto-create features
  - `POST /miners/{miner_id}/unlink-controller` — Remove all features from a controller

### Changed
- **Full Async Refactoring**:
  - All `MinerActionServiceInterface` methods are now `async`: `start_miner()`, `stop_miner()`, `get_miner_status()`, `get_miner_consumption()`, `get_miner_hashrate()`, `get_miner_info()`, `sync_all_miners()`
  - All `ConfigurationServiceInterface` miner management methods are now `async`: `add_miner()`, `update_miner()`, `remove_miner()`, `activate_miner()`, `deactivate_miner()`, `add_miner_controller()`, `update_miner_controller()`, `remove_miner_controller()`
  - Miner controller adapters, energy providers, forecast providers, and external services refactored to support asynchronous operations
  - Miner feature port methods updated to `async`
  - `OptimizationService` methods `get_decisional_context()` and `test_rules()` are now `async`

- **`AdapterService`** (`edge_mining/application/services/adapter_service.py`):
  - New methods: `get_miner_controller_adapter()`, `get_miner_feature_port()` for dynamic port-based adapter resolution
  - `sync_miner_features()` method for reconciling stored vs. actual controller features
  - Async initialization of external services with instance caching

- **`ConfigurationService`** (`edge_mining/application/services/configuration_service.py`):
  - New methods: `set_miner_controller()`, `unlink_controller_from_miner()`, `unlink_miner_controller()`, `enable_miner_feature()`, `disable_miner_feature()`, `set_miner_feature_priority()`

- **`MinerActionService`** (`edge_mining/application/services/miner_action_service.py`):
  - Uses `AdapterService` to dynamically resolve feature ports instead of direct controller access
  - New `get_miner_info()` method using `DeviceInfoPort`
  - New `get_miner_limits()` method using `MaxPowerDetectionPort` and `MaxHashrateDetectionPort`

- **CLI Commands** (`edge_mining/adapters/domain/miner/cli/commands.py`):
  - Refactored miner controller handling to support linking after creation
  - New `unlink_controller_from_miner()` command
  - Uses `run_async_func()` for async service calls

- **Dependencies**: Updated `pyasic` to version `0.78.10`

### Fixed
- Fixed data integrity validation and cleanup for unknown miner features in database

## [0.1.0-rev1]

### Added
- **Event-Driven Architecture**:
  - `InMemoryEventBus` (`edge_mining/adapters/infrastructure/event_bus/in_memory_event_bus.py`): Dual delivery mode event bus supporting blocking and fire-and-forget handlers via `asyncio.create_task()`
  - `ConfigurationUpdatedEvent` (`edge_mining/application/events/configuration_events.py`): Application-level event for cache invalidation with `ConfigurationUpdatedEventType` and `ConfigurationAction` enums
  - `MinerStateChangedEvent` (`edge_mining/domain/miner/events.py`): Emitted on miner start/stop with old and new status
  - `EnergyStateSnapshotUpdatedEvent` (`edge_mining/domain/energy/events.py`): Emitted when energy state is read
  - `RuleEngagedEvent` (`edge_mining/domain/optimization_unit/events.py`): Emitted when a policy rule produces a mining decision
  - `DecisionalContextUpdatedEvent` (`edge_mining/domain/policy/events.py`): Emitted when decisional context is composed

- **WebSocket Infrastructure**:
  - `WebSocketManager` (`edge_mining/adapters/infrastructure/websocket/manager.py`): Real-time event broadcasting to connected clients with wildcard topic subscriptions (e.g. `energy.*`, `miner.state`)
  - `WebSocketEventHandler` base class and 5 domain handlers: `MinerWebSocketHandler`, `EnergyWebSocketHandler`, `PolicyWebSocketHandler`, `OptimizationUnitWebSocketHandler`, `ConfigurationWebSocketHandler`
  - Available topics: `config.updated`, `energy.state`, `miner.state`, `policy.context`, `rule.engaged`
  - `WebSocketMessage` NamedTuple and `WebSocketEventRegistration` dataclass for type-safe event routing

- **Testing**:
  - Unit tests for all 5 domain events (`tests/unit/application/events/`)
  - Unit tests for `DomainEvent` base class (`tests/unit/domain/test_events.py`)
  - Unit tests for `WebSocketManager` (`tests/unit/adapters/infrastructure/websocket/test_websocket_manager.py`): lifecycle, subscriptions, wildcard matching, broadcast
  - Unit tests for `InMemoryEventBus` (`tests/unit/adapters/infrastructure/test_in_memory_event_bus.py`)
  - Integration tests for configuration event flow (`tests/unit/application/services/test_configuration_event_flow.py`)

- **Documentation**:
  - `docs/architecture/event_bus.md` — Event Bus architecture design
  - `docs/WEBSOCKET.md` — WebSocket client guide and architecture

- **`MinerStateSnapshot` Value Object** (`edge_mining/domain/miner/value_objects.py`):
  - New frozen dataclass representing the runtime operational state of a miner
  - Fields: `status` (MinerStatus), `hash_rate` (Optional[HashRate]), `power_consumption` (Optional[Watts])
  - Follows the Single Responsibility Principle: separates real-time state from static configuration

- **`MinerStateSnapshotSchema`** (`edge_mining/adapters/domain/miner/schemas.py`):
  - Pydantic schema for serialization/deserialization of `MinerStateSnapshot`
  - Methods: `from_model()`, `to_model()` for domain ↔ schema conversion

### Changed
- **`Miner` Entity** (`edge_mining/domain/miner/entities.py`):
  - **BREAKING**: Removed runtime state fields: `status`, `hash_rate`, `power_consumption`
  - **BREAKING**: Removed methods: `turn_on()`, `turn_off()`, `update_status()`
  - Simplified `deactivate()` to only set `self.active = False`
  - Entity now represents only static configuration: `name`, `model`, `hash_rate_max`, `power_consumption_max`, `active`, `controller_id`

- **`DecisionalContext`** (`edge_mining/domain/policy/value_objects.py`):
  - Added `miner_state: Optional[MinerStateSnapshot]` field for runtime state access
  - Existing `miner: Optional[Miner]` field retained for static configuration access

- **`OptimizationPolicy`** (`edge_mining/domain/policy/aggregate_roots.py`):
  - Updated `decide_next_action()` to read status from `decisional_context.miner_state.status` instead of `decisional_context.miner.status`

- **Repositories** (`edge_mining/adapters/domain/miner/repositories.py`):
  - `SqliteMinerRepository`: Removed `status`, `hash_rate`, `power_consumption` from schema, SQL queries, and row mapping
  - `SqlAlchemyMinerRepository`: Removed runtime state fields from `update()` method

- **SQLAlchemy Tables** (`edge_mining/adapters/domain/miner/tables.py`):
  - Removed `MinerStatusType` custom type class
  - Removed `status`, `hash_rate`, `power_consumption` columns from `miners_table`
  - Simplified event listeners to only handle `hash_rate_max` and `power_consumption_max`

- **Pydantic Schemas**:
  - `MinerSchema` (`edge_mining/adapters/domain/miner/schemas.py`): Removed `status`, `hash_rate`, `power_consumption` fields
  - `MinerCreateSchema`: Removed state fields from creation payload
  - `DecisionalContextSchema` (`edge_mining/adapters/domain/policy/schemas.py`): Added `miner_state` field with `MinerStateSnapshotSchema`

- **API Router** (`edge_mining/adapters/domain/miner/fast_api/router.py`):
  - `GET /miners/{miner_id}/status`: Now returns `MinerStateSnapshotSchema` instead of `MinerSchema`
  - `GET /miner-controllers/{controller_id}/miner-details`: Now returns `MinerStateSnapshotSchema`

- **`AdapterService`** (`edge_mining/application/services/adapter_service.py`):
  - Event subscription for `ConfigurationUpdatedEvent` to invalidate service caches

- **`ConfigurationService`** (`edge_mining/application/services/configuration_service.py`):
  - Publishes `ConfigurationUpdatedEvent` on all configuration changes

- **`MinerActionService`** (`edge_mining/application/services/miner_action_service.py`):
  - `start_miner()`/`stop_miner()` now publish `MinerStateChangedEvent` via event bus

- **`bootstrap.py`**: Instantiates `InMemoryEventBus` and injects it into all services; adds `init_websocket_dependencies()` call at startup; runs `sync_all_miners()` on application start

- **CLI Commands** (`edge_mining/adapters/domain/miner/cli/commands.py`):
  - Removed status display from `list_miners()` and `print_miner_details()`

- **Application Interfaces** (`edge_mining/application/interfaces.py`):
  - New `get_miner_limits()` abstract method in `MinerActionServiceInterface`
  - `get_miner_status()`: Return type changed from `Optional[MinerStatus]` to `Optional[MinerStateSnapshot]`
  - `get_miner_details_from_controller()`: Return type changed from `Optional[Miner]` to `Optional[MinerStateSnapshot]`
  - `add_miner()`: Removed `status` parameter

- **Application Services**:
  - `MinerActionService` (`edge_mining/application/services/miner_action_service.py`): Refactored all methods to build and return `MinerStateSnapshot` instead of mutating/persisting the `Miner` entity state
  - `ConfigurationService` (`edge_mining/application/services/configuration_service.py`): Removed `status` from `add_miner()`
  - `OptimizationService` (`edge_mining/application/services/optimization_service.py`): Updated context building to create `MinerStateSnapshot` objects; removed `miner.turn_on()`/`miner.turn_off()` calls and state persistence after decisions

- **Rule Engine** (`edge_mining/adapters/infrastructure/rule_engine/schemas.py`):
  - Updated operator examples from `miner.status` to `miner_state.status`

- **YAML Rule Files** (`data/examples/rules/stop/`):
  - Updated `advanced_stop_rules.yaml` and `basic_stop_rules.yaml`: Changed field references from `miner.status` to `miner_state.status`

- **Alembic Migration** (`alembic/versions/4e55fe6113c7_initial_schema_with_all_tables.py`):
  - Removed columns `status`, `hash_rate`, `power_consumption` from `miners` table definition
  - Removed `MinerStatusType()` reference (custom type no longer exists)

- **WebSocket event handlers**: Refactored to use topic strings and return `WebSocketMessage` payloads; `broadcast_message()` updated to use `WebSocketMessage` type

- **`FORECAST_PROVIDER`** added to `ConfigurationUpdatedEventType` enum

### Fixed
- Fixed unterminated string literal in `MinerActionServiceInterface` docstring
- Fixed connection error handling for Home Assistant API with client reset and improved logging
- Fixed external service update logic to handle missing configuration classes
- Fixed database directory creation for SQLite connections when using SQLAlchemy persistence adapter
- Fixed critical error handling replaced with warnings for missing energy values in Home Assistant monitors
- Fixed missing import for sqlalchemy in migration script

## [0.1.0]

### Added
- **Automatic Alembic Migrations**: Database migrations now run automatically on application startup
  - New module `edge_mining/adapters/infrastructure/persistence/sqlalchemy/migrations.py`
  - CLI tool `scripts/migrate.py` for manual migration management
  - Configuration option `RUN_MIGRATIONS_ON_STARTUP` in settings (default: true)
  - Commands: `status`, `upgrade`, `downgrade`, `create`, `history`
  - Method `initialize_database()` in `BaseSQLAlchemyRepository` that handles complete DB initialization

- **Documentation**:
  - `docs/ALEMBIC_MIGRATIONS.md` - Complete guide to migration system
  - `docs/MIGRATION_EXAMPLE.md` - Practical example of adding a field

- **Testing Infrastructure**:
  - **Unit Tests** (42 tests):
    - `tests/unit/adapters/domain/energy/test_tables_event_listeners.py` - Complete test suite for SQLAlchemy event listeners
    - Tests for `load` event listeners (EntityId, enum, and value object conversions from database)
    - Tests for `before_insert/update` event listeners (flattening composites before persistence)
    - Tests for `after_insert/update` event listeners (restoring composites after persistence)
    - Tests for configuration deserialization and value object round-trip conversion
  - **Integration Tests** (34 tests):
    - `tests/integration/adapters/persistence/test_sqlalchemy_energy_repositories.py` (21 tests) - Full CRUD operations with real database
    - `tests/integration/adapters/persistence/test_alembic_migrations.py` (9 tests) - Alembic migration system validation
    - `tests/integration/adapters/persistence/test_e2e_persistence.py` (8 tests) - End-to-end persistence workflows

### Changed
- **`BaseSQLAlchemyRepository`**:
  - Added `initialize_database()` method that encapsulates all database setup logic
  - Added `run_migrations` parameter to constructor
  - Improved separation of concerns by moving migration logic from bootstrap to repository
  - **BREAKING**: Removed `create_all_tables()` method - all schema changes must now go through Alembic migrations
  - Fail-fast approach: initialization fails clearly if migrations fail (no silent fallback)
- **SQLAlchemy Event Listeners** (`edge_mining/adapters/domain/energy/tables.py`):
  - Enhanced 4-phase conversion system for domain entities ↔ database mapping
  - `load` listeners: Convert database strings to EntityId, enums, and value objects
  - `before_insert/update` listeners: Flatten value objects to primitives before persistence
  - `after_insert/update` listeners: Restore EntityId, enums, and value objects after persistence
  - Added type ignore comments with explanatory notes for runtime type conversions
  - Fixed foreign key conversions (energy_monitor_id, forecast_provider_id, external_service_id)
- **`bootstrap.py`**: Simplified database initialization using `initialize_database()`
- **`alembic/env.py`**: Updated to use shared metadata registry from SQLAlchemy imperative mapping
- **`.env.example`**: Added migration configuration examples and multi-database support
- **`README.md`**: Added database migrations section with usage instructions
- **Settings**: Added `run_migrations_on_startup` configuration option

### Fixed
- Migration path calculation now correctly resolves project root
- Better error handling for migration failures with graceful fallback
- Improved encapsulation: database initialization logic moved to appropriate layer
- Fixed import error in `tests/unit/adapters/infrastructure/rule_engine/test_rule_evaluator.py` (OperatorType import path)
- SQLAlchemy event listeners now correctly handle all type conversions between domain and database layers
- EntityId conversions for primary keys and foreign keys (energy_monitor_id, forecast_provider_id, external_service_id)
- Enum conversions (EnergySourceType, EnergyMonitorAdapter) in both directions
- Value object conversions (Watts, Battery, Grid) with proper serialization/deserialization

## [Previous Versions]
