# Managing Migrations with Alembic

## Overview

The automatic migration system integrates Alembic into the hexagonal architecture while maintaining separation between domain and infrastructure.

## DDD Principles and Hexagonal Architecture

### Separation of Concerns

- **Domain**: Domain entities remain pure and independent of persistence
- **Adapters**: SQLAlchemy repositories map entities to tables
- **Infrastructure**: Alembic manages database schema migrations

### Imperative Mapping

We use SQLAlchemy's imperative mapping to keep domain entities clean:

```python
# Domain entities don't know about SQLAlchemy
@dataclass
class Miner(Entity):
    """Entity for a miner."""

    name: str = ""
    model: Optional[str] = None
    status: MinerStatus = MinerStatus.UNKNOWN
    hash_rate: Optional[HashRate] = None  # Hash rate in GH/s or TH/s
    hash_rate_max: Optional[HashRate] = None  # Max hash rate for the miner
    power_consumption: Optional[Watts] = None  # Can be dynamic or fixed
    power_consumption_max: Optional[Watts] = None  # Max power consumption for the miner
    active: bool = True  # Is the miner active in the system?

# Mapping happens separately in the adapter
mapper_registry.map_imperatively(Miner, miners_table)
```

## Configuration

### Settings

In `edge_mining/shared/settings/settings.py`:

```python
class AppSettings(BaseSettings):
    persistence_adapter: str = "sqlalchemy"
    db_path: str = "sqlite:///edgemining.db"
    run_migrations_on_startup: bool = True  # Automatic migrations
    backup_before_migration: bool = True  # Database backup before migrations
```

### Environment Variables

You can configure migrations via `.env`:

```bash
# Enable/disable automatic migrations
RUN_MIGRATIONS_ON_STARTUP=true

# Create database backup before migrations (SQLite only)
BACKUP_BEFORE_MIGRATION=true

# Database URL
DB_PATH=sqlite:///edgemining.db
# DB_PATH=postgresql://user:pass@localhost/dbname
```

## Startup Workflow

### 1. Automatic Bootstrap

When the application starts with `persistence_adapter=sqlalchemy`:

```python
# In bootstrap.py - simplified code
sqlalchemy_db = BaseSQLAlchemyRepository(
    db_path=db_url,
    logger=logger,
    run_migrations=settings.run_migrations_on_startup,
    backup_before_migration=settings.backup_before_migration,
)

# Single method that handles all initialization
sqlalchemy_db.initialize_database()
```

### 2. Automatic Execution

The `initialize_database()` method in `BaseSQLAlchemyRepository`:

1. **Loads table definitions** via `registry_loader` (imported at module level)
2. **Runs Alembic migrations** (if `run_migrations=True`)
   - **Checks for pending migrations**
     - Compares current database revision with latest migration script
     - Skips migration process if database is already up to date
     - **Raises RuntimeError if no migration files exist** (enforces Alembic-only approach)
   - **Creates database backup** (if enabled and migrations are pending)
     - Only for SQLite databases
     - Backup file format: `dbname_backup_YYYYMMDD_HHMMSS.db`
   - **Applies all pending migrations** with `alembic upgrade head`
3. **Database schema is EXCLUSIVELY managed through Alembic migrations**
   - No fallback to `metadata.create_all()`
   - First run requires an initial migration (e.g., `alembic revision --autogenerate -m "Initial schema"`)
   - All subsequent schema changes must be done via migrations
   - If migrations fail, initialization fails (fail-fast)

## Initial Setup (New Projects)

For a completely new project or empty database:

1. **Generate Initial Migration**
   ```bash
   # This will auto-detect all tables defined in the codebase
   alembic revision --autogenerate -m "Initial schema with all tables"
   ```

2. **Review Generated Migration**
   ```python
   # In alembic/versions/xxx_initial_schema_with_all_tables.py
   # Verify that all tables are included
   # Check that custom types are properly imported
   ```

3. **Apply Migration**
   ```bash
   # Start the application (migrations run automatically)
   python -m edge_mining

   # Or run manually
   alembic upgrade head
   ```

**Note**: The migration template (`alembic/script.py.mako`) automatically includes imports for all custom types, so auto-generated migrations should work without manual import fixes.

## Creating New Migrations

### Development Workflow

1. **Modify Domain Entities**
    ```python
    # Add a new attribute
    @dataclass
    class Miner(Entity):
        """Entity for a miner."""

        name: str = ""
        model: Optional[str] = None
        status: MinerStatus = MinerStatus.UNKNOWN
        hash_rate: Optional[HashRate] = None  # Hash rate in GH/s or TH/s
        hash_rate_max: Optional[HashRate] = None  # Max hash rate for the miner
        power_consumption: Optional[Watts] = None  # Can be dynamic or fixed
        power_consumption_max: Optional[Watts] = None  # Max power consumption for the miner
        active: bool = True  # Is the miner active in the system?

        temperature: Optional[float] = None
    ```

2. **Update Table Definition**
   ```python
   # In edge_mining/adapters/domain/miner/tables.py
   miners_table = Table(
       "miners",
       metadata,
       Column("temperature", Float, nullable=True),
       ...
   )
   ```

3. **Generate Migration**
   ```bash
   python scripts/migrate.py create "Add temperature field to miners"
   ```

4. **Verify Generated Migration**
   ```python
   # In alembic/versions/xxx_add_temperature_field.py
   def upgrade() -> None:
       op.add_column('miners', sa.Column('temperature', sa.Float(), nullable=True))

   def downgrade() -> None:
       op.drop_column('miners', 'temperature')
   ```

5. **Apply Migration**
   ```bash
   # Manually
   python scripts/migrate.py upgrade

   # Or restart the application (if run_migrations_on_startup=true)
   python -m edge_mining
   ```

## Alembic Commands

### Check Migration Status

```bash
# Show current revision
python scripts/migrate.py status

# Show migration history
python scripts/migrate.py history

# Or use Alembic directly
alembic current
alembic history --verbose
```

### Managing Migrations

```bash
# Create new migration (autogenerate)
python scripts/migrate.py create "Description"

# Create empty migration
python scripts/migrate.py create "Description" --no-autogenerate

# Apply all migrations
python scripts/migrate.py upgrade

# Rollback migrations
python scripts/migrate.py downgrade [n]

# Or use Alembic directly
alembic revision --autogenerate -m "Description"
alembic revision -m "Description"
alembic upgrade head
alembic upgrade <revision_id>
alembic downgrade -1
alembic downgrade <revision_id>
```

### SQL Visualization

```bash
# Show SQL without executing
alembic upgrade head --sql

# Generate SQL for offline migration
alembic upgrade head --sql > migration.sql
```

## Best Practices

### Development

1. **Always verify autogenerated migrations**: Alembic may not detect all changes
2. **Test upgrade and downgrade**: Make sure both work
3. **Use descriptive names**: `add_temperature_to_miners` instead of `update_table`
4. **Commit migrations with code**: Migrations are part of the code
5. **Never delete the initial migration**: It's required for creating new databases
6. **Custom types are auto-imported**: The template (`script.py.mako`) includes all custom type imports

### Production

1. **Disable autogenerate**: Use only tested migrations
2. **Backup before migrations**: Always! (automatically done if `backup_before_migration=true`)
3. **Test on staging environment**: Before production
4. **Monitor execution**: Log all migration steps

### Multi-Database

For databases other than SQLite, configure the appropriate connection URL:

```python
# PostgreSQL
DB_PATH=postgresql://user:password@localhost:5432/edgemining

# MySQL
DB_PATH=mysql+pymysql://user:password@localhost:3306/edgemining

# SQL Server
DB_PATH=mssql+pyodbc://user:password@localhost/edgemining?driver=ODBC+Driver+17+for+SQL+Server
```

## Troubleshooting

### Failed Migration

If a migration fails midway:

```bash
# Check status
alembic current

# If necessary, manually force the revision
alembic stamp <last_good_revision>

# Manually repair the database if needed
# Then retry migration
alembic upgrade head
```

### Merge Conflicts

If two developers create migrations in parallel:

```bash
# Create a merge migration
alembic merge -m "Merge revisions" <rev1> <rev2>

# Apply the merge
alembic upgrade head
```

### Complete Reset (Development Only!)

```bash
# WARNING: Deletes all data!
rm edgemining.db

# Option 1: Run the application (migrations apply automatically)
python -m edge_mining

# Option 2: Run migrations manually
alembic upgrade head
```

### Missing Initial Migration

If you encounter an error like "No Alembic migrations found":

```bash
# Generate the initial migration
alembic revision --autogenerate -m "Initial schema with all tables"

# Review the generated file in alembic/versions/
# Then apply it
alembic upgrade head
```

## CI/CD Integration

### Pre-deploy Check

```bash
#!/bin/bash
# check_migrations.sh

# Verify all migrations are applied
alembic current | grep "head" || {
    echo "Pending migrations found!"
    alembic history --verbose
    exit 1
}
```

### Automated Testing

```python
# tests/unit/adapters/persistence/test_migrations.py
def test_migrations_apply_cleanly():
    """Test that all migrations can be applied from scratch."""
    # Drop database
    # Run migrations
    # Verify schema

def test_migrations_reversible():
    """Test that migrations can be downgraded and reapplied."""
    # Apply all migrations
    # Downgrade one step
    # Upgrade again
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Imperative Mapping](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#imperative-mapping)
- See also: `docs/SQLALCHEMY_ALEMBIC_GUIDE.md` for implementation details
