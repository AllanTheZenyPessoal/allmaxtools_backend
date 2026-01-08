#!/usr/bin/env python
"""
Script to run Alembic migrations programmatically.
Useful for Docker containers and CI/CD pipelines.

Usage:
    python run_migrations.py upgrade head     # Apply all migrations
    python run_migrations.py downgrade -1     # Rollback one migration
    python run_migrations.py current          # Show current revision
    python run_migrations.py stamp head       # Mark current state as head (for existing DBs)
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command


def get_alembic_config():
    """Get Alembic config pointing to our alembic.ini."""
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    return alembic_cfg


def run_upgrade(revision="head"):
    """Run upgrade to specified revision."""
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, revision)
    print(f"✅ Successfully upgraded to: {revision}")


def run_downgrade(revision="-1"):
    """Run downgrade to specified revision."""
    alembic_cfg = get_alembic_config()
    command.downgrade(alembic_cfg, revision)
    print(f"✅ Successfully downgraded to: {revision}")


def show_current():
    """Show current revision."""
    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg)


def stamp_revision(revision="head"):
    """Stamp the database with a revision without running migrations."""
    alembic_cfg = get_alembic_config()
    command.stamp(alembic_cfg, revision)
    print(f"✅ Database stamped with revision: {revision}")


def show_history():
    """Show migration history."""
    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        run_upgrade(revision)
    elif action == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "-1"
        run_downgrade(revision)
    elif action == "current":
        show_current()
    elif action == "stamp":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        stamp_revision(revision)
    elif action == "history":
        show_history()
    else:
        print(f"Unknown action: {action}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
