"""Pytest configuration for property-based tests.

Property-based tests for BaseMind model validation don't require database access
since they test Pydantic model validation directly.
"""

# No fixtures needed for property tests that only test Pydantic validation
# These tests create BaseMind instances in memory without persisting to Neo4j
