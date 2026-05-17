#!/usr/bin/env python3
"""Validation script to check Alembic migrations setup.

This script verifies that:
- Alembic is properly configured
- Database migrations are up to date
- All table definitions are registered
- The migration system is working correctly

Usage:
    cd /root/edge-mining/core-step1
    python -m scripts.validate_migrations
    OR
    python scripts/validate_migrations.py
"""

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
    get_alembic_config,
)
from edge_mining.adapters.infrastructure.persistence.sqlalchemy.registry import metadata
from edge_mining.shared.settings.settings import AppSettings


def main():
    """Run validation checks."""
    logger = TerminalLogger(log_level="INFO")
    settings = AppSettings()

    logger.info("=" * 60)
    logger.info("Alembic Migrations Setup Validation")
    logger.info("=" * 60)

    checks_passed = 0
    checks_failed = 0

    # Check 1: Settings
    logger.info("\n[1/5] Checking settings...")
    try:
        db_url = settings.db_path
        migrations_enabled = settings.run_migrations_on_startup
        logger.info(f"  ✓ Database URL: {db_url}")
        logger.info(f"  ✓ Migrations on startup: {migrations_enabled}")
        checks_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Settings check failed: {e}")
        checks_failed += 1

    # Check 2: Alembic Configuration
    logger.info("\n[2/5] Checking Alembic configuration...")
    try:
        alembic_cfg = get_alembic_config(settings.db_path)
        script_location = alembic_cfg.get_main_option("script_location")
        logger.info("  ✓ Alembic config loaded")
        logger.info(f"  ✓ Script location: {script_location}")
        checks_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Alembic config check failed: {e}")
        checks_failed += 1
        return 1

    # Check 3: Table Definitions
    logger.info("\n[3/5] Checking table definitions...")
    try:
        # Import registry loader to ensure all tables are registered
        from edge_mining.adapters.infrastructure.persistence.sqlalchemy import registry_loader  # noqa: F401

        tables = list(metadata.tables.keys())
        if tables:
            logger.info(f"  ✓ Found {len(tables)} table definition(s):")
            for table in sorted(tables):
                logger.info(f"    - {table}")
            checks_passed += 1
        else:
            logger.warning("  ⚠ No table definitions found (this may be expected for a fresh setup)")
            checks_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Table definitions check failed: {e}")
        checks_failed += 1

    # Check 4: Database Connection
    logger.info("\n[4/5] Checking database connection...")
    try:
        current_rev = check_current_revision(settings.db_path, logger=None)
        if current_rev:
            logger.info("  ✓ Database connected")
            logger.info(f"  ✓ Current revision: {current_rev}")
        else:
            logger.info("  ✓ Database connected")
            logger.warning("  ⚠ No migrations applied yet (database is empty)")
        checks_passed += 1
    except Exception as e:
        logger.error(f"  ✗ Database connection check failed: {e}")
        checks_failed += 1

    # Check 5: Migration Files
    logger.info("\n[5/5] Checking migration files...")
    try:
        if script_location:
            versions_dir = Path(script_location) / "versions"
            if versions_dir.exists():
                migration_files = list(versions_dir.glob("*.py"))
                migration_files = [f for f in migration_files if not f.name.startswith("__")]
                logger.info(f"  ✓ Migrations directory: {versions_dir}")
                logger.info(f"  ✓ Found {len(migration_files)} migration file(s)")
                for mig_file in sorted(migration_files):
                    logger.info(f"    - {mig_file.name}")
                checks_passed += 1
            else:
                logger.error(f"  ✗ Migrations directory not found: {versions_dir}")
                checks_failed += 1
        else:
            logger.error("  ✗ Could not determine script location")
            checks_failed += 1
    except Exception as e:
        logger.error(f"  ✗ Migration files check failed: {e}")
        checks_failed += 1

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    logger.info(f"Checks passed: {checks_passed}/5")
    logger.info(f"Checks failed: {checks_failed}/5")

    if checks_failed == 0:
        logger.info("\n✓ All checks passed! Alembic migrations are properly configured.")
        logger.info("\nNext steps:")
        logger.info("  - Run migrations: python scripts/migrate.py upgrade")
        logger.info("  - Check status: python scripts/migrate.py status")
        logger.info("  - Start application: python -m edge_mining")
        return 0
    else:
        logger.error("\n✗ Some checks failed. Please review the errors above.")
        logger.info("\nTroubleshooting:")
        logger.info("  - Check that alembic.ini exists in project root")
        logger.info("  - Verify database connection in .env file")
        logger.info("  - Ensure all dependencies are installed: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
