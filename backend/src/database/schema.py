"""Neo4j database schema setup for Mind-based data model system.

This module creates indexes and constraints for Mind nodes to ensure
data integrity and query performance.
"""

from typing import Optional

from neo4j import Driver


def create_mind_schema(driver: Optional[Driver] = None) -> None:
    """Create Neo4j indexes and constraints for Mind nodes.

    Args:
        driver: Neo4j driver instance. If None, will get from neontology.

    Creates:
    - Unique constraint on Mind.uuid
    - Index on Mind.status for filtering
    - Index on Mind.creator for filtering
    - Index on Mind.updated_at for sorting and range queries
    - Composite index on Mind type labels and status
    """
    if driver is None:
        from neontology import Neo4jConfig, init_neontology

        from src.config.config import settings

        config = Neo4jConfig(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )
        init_neontology(config)
    else:
        with driver.session() as session:
            # Unique constraint on UUID
            session.run("""
                CREATE CONSTRAINT mind_uuid_unique IF NOT EXISTS
                FOR (m:Mind) REQUIRE m.uuid IS UNIQUE
            """)

            # Index on status for filtering
            session.run("""
                CREATE INDEX mind_status_idx IF NOT EXISTS
                FOR (m:Mind) ON (m.status)
            """)

            # Index on creator for filtering
            session.run("""
                CREATE INDEX mind_creator_idx IF NOT EXISTS
                FOR (m:Mind) ON (m.creator)
            """)

            # Index on updated_at for sorting and range queries
            session.run("""
                CREATE INDEX mind_updated_at_idx IF NOT EXISTS
                FOR (m:Mind) ON (m.updated_at)
            """)

        print("✓ Neo4j schema created successfully")
        print("  - Unique constraint: mind_uuid_unique")
        print("  - Index: mind_status_idx")
        print("  - Index: mind_creator_idx")
        print("  - Index: mind_updated_at_idx")


def drop_mind_schema(driver: Optional[Driver] = None) -> None:
    """Drop all Mind-related indexes and constraints.

    Args:
        driver: Neo4j driver instance. If None, will get from neontology.

    Used for testing and development to reset the database schema.
    """
    if driver is None:
        from neontology import Neo4jConfig, init_neontology

        from src.config.config import settings

        config = Neo4jConfig(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password,
        )
        init_neontology(config)
    else:
        with driver.session() as session:
            # Drop indexes
            session.run("DROP INDEX mind_status_idx IF EXISTS")
            session.run("DROP INDEX mind_creator_idx IF EXISTS")
            session.run("DROP INDEX mind_updated_at_idx IF EXISTS")

            # Drop constraints
            session.run("DROP CONSTRAINT mind_uuid_unique IF EXISTS")

        print("✓ Neo4j schema dropped successfully")


if __name__ == "__main__":
    # Initialize database connection first
    from src.database.database import initiate_database

    initiate_database()
    create_mind_schema()
