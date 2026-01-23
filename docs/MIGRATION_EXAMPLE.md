# Practical Example: Adding a "Temperature" Field to Miners

This example shows the complete workflow for adding a new field to the domain while maintaining DDD and hexagonal architecture.

## Step 1: Modify the Domain Entity

**File**: `edge_mining/domain/miner/entities.py`

```python
@dataclass
class Miner(Entity):
    """Entity for a miner."""

    name: str = ""
    model: Optional[str] = None
    status: MinerStatus = MinerStatus.UNKNOWN
    hash_rate: Optional[HashRate] = None
    hash_rate_max: Optional[HashRate] = None
    power_consumption: Optional[Watts] = None  # Watts, non float!
    power_consumption_max: Optional[Watts] = None
    active: bool = True  # Default True
    controller_id: Optional[EntityId] = None

    temperature: Optional[float] = None  # NEW FIELD
```

## Step 2: Update the Table Definition

**File**: `edge_mining/adapters/domain/miner/tables.py`

```python
from sqlalchemy import Boolean, Column, Float, ForeignKey, String, Table

from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import metadata

miners_table = Table(
    "miners",
    metadata,
    # Primary Key
    Column("id", String, primary_key=True, index=True),
    # Basic attributes
    Column("name", String, nullable=False),
    Column("model", String, nullable=True),
    Column("status", MinerStatusType, nullable=False, default="UNKNOWN"),  # Custom type!
    Column("active", Boolean, nullable=False, default=True),
    # Hash Rate Value Object - stored as JSON in single String column
    Column("hash_rate", String, nullable=True),  # JSON, non separate value/unit
    Column("hash_rate_max", String, nullable=True),
    # Power Consumption (Watts Value Object stored as float)
    Column("power_consumption", Float, nullable=True),
    Column("power_consumption_max", Float, nullable=True),
    # Foreign Key to MinerController
    Column("controller_id", String, ForeignKey("miner_controllers.id"), nullable=True),
    # NEW COLUMN
    Column("temperature", Float, nullable=True),
)
```

**Important notes**:
- `HashRate` is serialized as **JSON in a single String column**, not in separate `value`/`unit` columns
- `status` uses custom `MinerStatusType` for enum ↔ string conversion
- `controller_id` is a **Foreign Key** to `miner_controllers.id`

## Step 3: Verify Imperative Mapping and Event Listeners

**File**: `edge_mining/adapters/domain/miner/tables.py`

The imperative mapping is already configured and **requires no changes** for simple fields like `temperature`:

```python
# Map Miner (child in the relationship)
mapper_registry.map_imperatively(
    Miner,
    miners_table,
    properties={
        # Relationship to controller
        "controller": relationship(
            "MinerController",
            foreign_keys=[miners_table.c.controller_id],
            lazy="joined",
        ),
    },
)
```

**Note**: No need to explicitly map every field! SQLAlchemy automatically maps columns with the same name as entity attributes. The `properties` dictionary contains only **relationships** and special configurations.

**Event Listeners**: For simple fields like `float`, no changes are needed. Event listeners `_receive_miner_load` and `_flatten_miner_value_objects` only handle conversions for **complex value objects** (HashRate, Watts).

## Step 4: SQLAlchemy Repository

**File**: `edge_mining/adapters/domain/miner/repositories.py`

**IMPORTANT**: With imperative mapping, the `SqlAlchemyMinerRepository` works **directly with mapped domain entities**.

SQLAlchemy and event listeners automatically handle all conversions between domain and database.

**How the repository works**:

```python
class SqlAlchemyMinerRepository(MinerRepository):
    def add(self, miner: Miner) -> None:
        """Add a new miner to the repository."""
        session = self._db.get_session()
        try:
            session.add(miner)  # Directly the domain entity!
            session.commit()
        finally:
            session.close()

    def get_by_id(self, miner_id: EntityId) -> Optional[Miner]:
        """Retrieve a miner by its ID."""
        session = self._db.get_session()
        try:
            stmt = select(Miner).where(Miner.id == miner_id)
            return session.execute(stmt).scalar_one_or_none()  # Returns the entity!
        finally:
            session.close()
```

**For the new `temperature` field**: being a simple `float`, SQLAlchemy handles it automatically. No repository changes needed!

**If the field were a complex value object**: you would need to add conversions in event listeners `_receive_miner_load` (reconstruction after loading) and `_flatten_miner_value_objects` (flattening before saving).

## Step 5: Generate the Migration

```bash
# Automatically generate the migration
python scripts/migrate.py create "Add temperature field to miners"
```

This will create a file like:
`alembic/versions/xxx_add_temperature_field_to_miners.py`

```python
"""Add temperature field to miners

Revision ID: abc123def456
Revises: cde387d5834c
Create Date: 2026-01-22 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, None] = 'cde387d5834c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('miners', sa.Column('temperature', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('miners', 'temperature')
```

## Step 6: Verify the Migration

```bash
# Display the SQL that will be executed
alembic upgrade head --sql
```

**Note**: The `python scripts/migrate.py` script **does not support** the `--sql` flag. To view the generated SQL, use Alembic directly.

## Step 7: Apply the Migration

### Option A: Automatic (on startup)

```bash
# With RUN_MIGRATIONS_ON_STARTUP=true and BACKUP_BEFORE_MIGRATION=true
python -m edge_mining
```

**The system automatically**:
1. ✅ Checks if there are pending migrations
2. ✅ Creates a database backup (if enabled and there are migrations to apply)
   - Backup format: `edgemining_backup_YYYYMMDD_HHMMSS.db`
3. ✅ Applies **only** the necessary migrations
4. ✅ Skips completely if the database is already up to date

**Configuration** (`.env`):
```bash
RUN_MIGRATIONS_ON_STARTUP=true
BACKUP_BEFORE_MIGRATION=true  # Automatic backup (SQLite only)
```

### Option B: Manual

```bash
# Apply pending migrations
python scripts/migrate.py upgrade

# Verify current status
python scripts/migrate.py status

# Display history
python scripts/migrate.py history
```

## Step 8: Test

```python
# test_miner_temperature.py
def test_miner_with_temperature():
    """Test that miner can store and retrieve temperature."""
    # Create miner with dataclass syntax
    miner = Miner(
        id=EntityId.generate(),
        name="Test Miner",
        temperature=65.5,
    )

    # Save to repository
    miner_repo.add(miner)

    # Retrieve from repository
    retrieved = miner_repo.get_by_id(miner.id)

    # Verify
    assert retrieved is not None
    assert retrieved.temperature == 65.5
    assert retrieved.name == "Test Miner"
```

**Note**: The `Miner` class is a `@dataclass`, so it is instantiated directly by passing parameters. SQLAlchemy handles persistence automatically through imperative mapping.

## Rollback (If Necessary)

If something goes wrong:

```bash
# Rollback one migration
python scripts/migrate.py downgrade 1

# Or return to a specific revision
alembic downgrade cde387d5834c
```

## Best Practices

### ✅ DO

1. **Always add optional fields initially** (`nullable=True`)
2. **Test on test database first**
3. **Verify the autogenerated migration** (it might not be perfect)
4. **Add appropriate default values** for NOT NULL fields
5. **Document the reason for the change** in the migration message

### ❌ DON'T

1. **Don't modify migrations already applied** in production
2. **Don't remove fields without a data migration plan**
3. **Don't make breaking changes without deployment strategy**
4. **Don't ignore migration errors**
5. **Don't apply migrations without backup**

## Complex Migrations

### Rename a Column

```python
def upgrade() -> None:
    op.alter_column('miners', 'old_name', new_column_name='new_name')

def downgrade() -> None:
    op.alter_column('miners', 'new_name', new_column_name='old_name')
```

### Add NOT NULL Field with Default

```python
def upgrade() -> None:
    # First add as nullable with default
    op.add_column('miners', sa.Column('required_field', sa.String(), nullable=True))

    # Populate existing values
    op.execute("UPDATE miners SET required_field = 'default_value' WHERE required_field IS NULL")

    # Make NOT NULL
    op.alter_column('miners', 'required_field', nullable=False)

def downgrade() -> None:
    op.drop_column('miners', 'required_field')
```

### Create Index

```python
def upgrade() -> None:
    op.create_index('idx_miners_temperature', 'miners', ['temperature'])

def downgrade() -> None:
    op.drop_index('idx_miners_temperature', 'miners')
```

## Complete Workflow Summary

```bash
# 1. Modify the code (domain, tables, repository)

# 2. Generate migration
python scripts/migrate.py create "Description of changes"

# 3. Verify the generated file
cat alembic/versions/xxx_descrizione_modifiche.py

# 4. Test on development database
python scripts/migrate.py upgrade

# 5. Verify it works
python -m edge_mining

# 6. Commit everything together
git add edge_mining/ alembic/versions/
git commit -m "feat: add temperature field to miners"
```

## Common Troubleshooting

### Migration Not Detected

```bash
# Make sure registry_loader is imported
# Verify the table is in metadata
python -c "from edge_mining.adapters.infrastructure.persistence.sqlalchemy import registry_loader; \
           from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import metadata; \
           print(list(metadata.tables.keys()))"
```

### Migration Conflict

If two developers create migrations in parallel:

```bash
# Create a merge migration
alembic merge -m "Merge migrations" rev1 rev2
alembic upgrade head
```

### Database Out of Sync

```bash
# Force the current revision
alembic stamp head

# Or return to a specific revision
alembic stamp <revision_id>
```

## Conclusion

This workflow maintains:
- ✅ **DDD**: Domain entities always pure
- ✅ **Hexagonal Architecture**: Separate adapters
- ✅ **Version Control**: Traceable migrations
- ✅ **Safety**: Rollback supported
- ✅ **Automation**: Automatic migrations on startup
