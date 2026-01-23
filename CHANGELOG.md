# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
