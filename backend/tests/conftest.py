"""Pytest configuration and fixtures for Mind-based data model system tests.

This module provides shared fixtures for unit, property-based, and integration tests.
"""

import os
from typing import Generator

import pytest
from neo4j import GraphDatabase
from neontology import Neo4jConfig, init_neontology

from src.config.config import Settings


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings with test database configuration.

    Returns:
        Settings: Test configuration with separate Neo4j test database.
    """
    # Override settings for testing
    test_settings = Settings(
        neo4j_uri=os.getenv("NEO4J_TEST_URI", "bolt://localhost:7687"),
        neo4j_username=os.getenv("NEO4J_TEST_USERNAME", "neo4j"),
        neo4j_password=os.getenv("NEO4J_TEST_PASSWORD", "password"),
        jwt_secret="test_secret_key_for_testing_only",
        jwt_algorithm="HS256",
        jwt_expiration_minutes=60,
    )
    return test_settings


@pytest.fixture(scope="session")
def neo4j_driver(test_settings: Settings) -> Generator:
    """Initialize Neo4j driver for testing.

    Args:
        test_settings: Test configuration settings.

    Yields:
        Neo4j driver instance.
    """
    # Initialize neontology with config
    config = Neo4jConfig(
        uri=test_settings.neo4j_uri,
        username=test_settings.neo4j_username,
        password=test_settings.neo4j_password,
    )
    init_neontology(config)

    # Create driver directly using neo4j package
    driver = GraphDatabase.driver(
        test_settings.neo4j_uri,
        auth=(test_settings.neo4j_username, test_settings.neo4j_password)
    )

    yield driver

    # Cleanup: close driver after all tests
    driver.close()


@pytest.fixture(scope="function")
def clean_database(neo4j_driver) -> Generator:
    """Clean the test database before each test.

    This fixture ensures each test starts with a clean database state.

    Args:
        neo4j_driver: Neo4j driver instance.

    Yields:
        None
    """
    # Clean database before test
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    yield

    # Clean database after test
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture(scope="session")
def setup_schema(neo4j_driver) -> Generator:
    """Set up Neo4j schema for testing.

    Creates indexes and constraints needed for Mind nodes.

    Args:
        neo4j_driver: Neo4j driver instance.

    Yields:
        None
    """
    from src.database.schema import create_mind_schema

    # Create schema before tests, passing the driver
    create_mind_schema(neo4j_driver)

    yield

    # Optionally drop schema after all tests (commented out to preserve schema)
    # drop_mind_schema(neo4j_driver)
