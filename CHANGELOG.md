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
  - `ALEMBIC_INTEGRATION_SUMMARY.md` - Implementation summary

- **Testing**:
  - `tests/unit/adapters/persistence/test_migrations.py` - Test suite for migration functionality
  - `tests/unit/adapters/persistence/test_sqlalchemy_base.py` - Test suite for BaseSQLAlchemyRepository

### Changed
- **`BaseSQLAlchemyRepository`**:
  - Added `initialize_database()` method that encapsulates all database setup logic
  - Added `run_migrations` parameter to constructor
  - Improved separation of concerns by moving migration logic from bootstrap to repository
  - **BREAKING**: Removed `create_all_tables()` method - all schema changes must now go through Alembic migrations
  - Fail-fast approach: initialization fails clearly if migrations fail (no silent fallback)
- **`bootstrap.py`**: Simplified database initialization using `initialize_database()`
- **`alembic/env.py`**: Updated to use shared metadata registry from SQLAlchemy imperative mapping
- **`.env.example`**: Added migration configuration examples and multi-database support
- **`README.md`**: Added database migrations section with usage instructions
- **Settings**: Added `run_migrations_on_startup` configuration option

### Fixed
- Migration path calculation now correctly resolves project root
- Better error handling for migration failures with graceful fallback
- Improved encapsulation: database initialization logic moved to appropriate layer

## [Previous Versions]
