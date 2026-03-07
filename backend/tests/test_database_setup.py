"""Test database setup and schema creation.

This test verifies that the database connection and schema setup work correctly.
"""



def test_database_connection(neo4j_driver):
    """Test that we can connect to the Neo4j database.

    Args:
        neo4j_driver: Neo4j driver fixture from conftest.
    """
    assert neo4j_driver is not None

    # Verify we can execute a simple query
    with neo4j_driver.session() as session:
        result = session.run("RETURN 1 as num")
        record = result.single()
        assert record["num"] == 1


def test_schema_creation(neo4j_driver, setup_schema):
    """Test that schema indexes and constraints are created.

    Args:
        neo4j_driver: Neo4j driver fixture from conftest.
        setup_schema: Schema setup fixture from conftest.
    """
    with neo4j_driver.session() as session:
        # Check that the unique constraint exists
        constraints = session.run("SHOW CONSTRAINTS").data()
        constraint_names = [c.get("name") for c in constraints]
        assert "mind_uuid_unique" in constraint_names

        # Check that indexes exist
        indexes = session.run("SHOW INDEXES").data()
        index_names = [i.get("name") for i in indexes]
        assert "mind_status_idx" in index_names
        assert "mind_creator_idx" in index_names
        assert "mind_updated_at_idx" in index_names


def test_clean_database_fixture(neo4j_driver, clean_database):
    """Test that the clean_database fixture works correctly.

    Args:
        neo4j_driver: Neo4j driver fixture from conftest.
        clean_database: Clean database fixture from conftest.
    """
    # Create a test node
    with neo4j_driver.session() as session:
        session.run("CREATE (n:TestNode {name: 'test'})")

        # Verify node exists
        result = session.run("MATCH (n:TestNode) RETURN count(n) as count")
        assert result.single()["count"] == 1

    # After test, the fixture should clean up
    # (This is verified by the fixture itself in conftest.py)
