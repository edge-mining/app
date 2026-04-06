# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-rev1]

### Added
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

- **CLI Commands** (`edge_mining/adapters/domain/miner/cli/commands.py`):
  - Removed status display from `list_miners()` and `print_miner_details()`

- **Application Interfaces** (`edge_mining/application/interfaces.py`):
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

### Fixed
- Fixed unterminated string literal in `MinerActionServiceInterface` docstring

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
