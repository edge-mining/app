#!/usr/bin/env python3
"""CLI utility for managing Alembic migrations.

This script provides convenient commands for managing database migrations
while respecting the application's settings and configuration.

Usage:
    cd app/core
    python -m scripts.migrate status          # Check current revision
    python -m scripts.migrate upgrade         # Apply all pending migrations
    python -m scripts.migrate downgrade [n]   # Rollback n migrations (default: 1)
    python -m scripts.migrate create "msg"    # Create new migration
    python -m scripts.migrate history         # Show migration history

    OR use directly:
    python scripts/migrate.py status
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for direct script execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from edge_mining.adapters.infrastructure.logging.terminal_logging import TerminalLogger
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.migrations import (
    check_current_revision,
    create_migration,
    downgrade_migration,
    get_alembic_config,
    run_migrations,
)
from edge_mining.shared.settings.settings import AppSettings


def main():
    """Main entry point for migration CLI."""
    parser = argparse.ArgumentParser(
        description="Manage Alembic database migrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Status command
    subparsers.add_parser("status", help="Show current database revision")

    # Upgrade command
    subparsers.add_parser("upgrade", help="Apply all pending migrations")

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Rollback migrations")
    downgrade_parser.add_argument(
        "steps",
        nargs="?",
        default="1",
        help="Number of migrations to rollback (default: 1)",
    )

    # Create command
    create_parser = subparsers.add_parser("create", help="Create new migration")
    create_parser.add_argument("message", help="Migration message/description")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Create empty migration (no autogenerate)",
    )

    # History command
    subparsers.add_parser("history", help="Show migration history")

    args = parser.parse_args()

    # Load settings
    settings = AppSettings()
    logger = TerminalLogger(log_level=settings.log_level)

    db_url = settings.db_path

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "status":
            current_rev = check_current_revision(db_url, logger)
            if current_rev:
                logger.info(f"Current database revision: {current_rev}")
            else:
                logger.warning("No migrations have been applied yet")

        elif args.command == "upgrade":
            logger.info("Applying pending migrations...")
            run_migrations(db_url, logger)
            logger.info("✓ Migrations applied successfully")

        elif args.command == "downgrade":
            steps = args.steps
            if steps.isdigit():
                revision = f"-{steps}"
            else:
                revision = steps

            logger.warning(f"Rolling back {steps} migration(s)...")
            downgrade_migration(db_url, revision, logger)
            logger.info("✓ Rollback completed")

        elif args.command == "create":
            autogenerate = not args.no_autogenerate
            logger.info(f"Creating migration: {args.message}")
            create_migration(
                db_url,
                args.message,
                logger,
                autogenerate=autogenerate,
            )
            logger.info("✓ Migration created successfully")

        elif args.command == "history":
            from alembic import command

            alembic_cfg = get_alembic_config(db_url)
            command.history(alembic_cfg, verbose=True)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
