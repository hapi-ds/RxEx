#!/usr/bin/env python3
"""Initialize Neo4j database schema for Mind-based data model system.

This script creates the necessary indexes and constraints for Mind nodes.
Run this script after setting up the Neo4j database.

Usage:
    uv run python scripts/init_schema.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.database.database import initiate_database
from src.database.schema import create_mind_schema


def main() -> None:
    """Initialize database connection and create schema."""
    print("Initializing Neo4j database connection...")
    initiate_database()

    print("\nCreating Mind node schema...")
    create_mind_schema()

    print("\n✓ Database schema initialization complete!")


if __name__ == "__main__":
    main()
