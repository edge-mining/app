# Scripts Directory

Utility scripts for Edge Mining development and maintenance.

## Available Scripts

### migrate.py

Database migration management tool using Alembic.

**Usage:**
```bash
# Check current database version
python scripts/migrate.py status

# Apply all pending migrations
python scripts/migrate.py upgrade

# Rollback last migration
python scripts/migrate.py downgrade

# Rollback multiple migrations
python scripts/migrate.py downgrade 3

# Create new migration
python scripts/migrate.py create "Description of changes"

# Create empty migration (no autogenerate)
python scripts/migrate.py create "Custom migration" --no-autogenerate

# View migration history
python scripts/migrate.py history
```

**Configuration:**

The script automatically loads configuration from `.env` file:
- `DB_PATH`: Database connection URL
- `LOG_LEVEL`: Logging verbosity

**See Also:**
- [Alembic Migrations Guide](../../docs/ALEMBIC_MIGRATIONS.md)
- [Migration Example](../../docs/MIGRATION_EXAMPLE.md)

## Adding New Scripts

When adding new utility scripts to this directory:

1. Make them executable: `chmod +x scripts/your_script.py`
2. Add a shebang: `#!/usr/bin/env python3`
3. Document usage in this README
4. Use the project's settings and logger where appropriate

Example template:

```python
#!/usr/bin/env python3
"""Short description of the script."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from edge_mining.shared.settings.settings import AppSettings
from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Script description")
    # Add arguments
    args = parser.parse_args()

    # Load settings
    settings = AppSettings()
    logger = TerminalLogger(log_level=settings.log_level)

    # Script logic here
    logger.info("Script starting...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
```
