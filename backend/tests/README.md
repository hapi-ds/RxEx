# Mind-Based Data Model System Tests

This directory contains tests for the Mind-based data model system.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures and configuration
├── unit/                    # Unit tests for specific components
├── properties/              # Property-based tests using Hypothesis
├── integration/             # Integration tests with real Neo4j database
└── README.md               # This file
```

## Test Database Configuration

Tests use a separate Neo4j database instance to avoid interfering with development data.

### Environment Variables

Set these environment variables to configure the test database:

```bash
export NEO4J_TEST_URI="bolt://localhost:7687"
export NEO4J_TEST_USERNAME="neo4j"
export NEO4J_TEST_PASSWORD="password"
```

Or create a `.env.test` file in the backend directory:

```
NEO4J_TEST_URI=bolt://localhost:7687
NEO4J_TEST_USERNAME=neo4j
NEO4J_TEST_PASSWORD=password
```

### Database Setup

The test suite automatically:
1. Connects to the test database
2. Creates necessary indexes and constraints
3. Cleans the database before and after each test

**Important**: Use a separate Neo4j database for testing to avoid data loss.

## Running Tests

### Run All Tests

```bash
uv run pytest -q
```

### Run Unit Tests Only

```bash
uv run pytest tests/unit/ -q
```

### Run Property-Based Tests Only

```bash
uv run pytest tests/properties/ -q
```

### Run Integration Tests Only

```bash
uv run pytest tests/integration/ -q
```

### Run with Coverage

```bash
uv run pytest --cov=src --cov-report=html
```

## Test Types

### Unit Tests

Unit tests validate specific examples, edge cases, and error conditions:
- Model validation
- Schema validation
- Service layer methods
- API endpoint behavior
- Error handling

### Property-Based Tests

Property-based tests use Hypothesis to verify universal properties across randomized inputs:
- UUID uniqueness
- Version number incrementing
- Timestamp accuracy
- Attribute preservation
- Relationship integrity

Each property test runs 100 iterations by default to ensure adequate coverage.

### Integration Tests

Integration tests validate end-to-end workflows with a real Neo4j database:
- Full CRUD lifecycle
- Version history traversal
- Complex relationship graphs
- Bulk operations
- Concurrent updates

## Writing Tests

### Property Test Template

```python
from hypothesis import given, settings
from hypothesis.strategies import composite

# Feature: mind-based-data-model-system, Property N: Property Name
@given(mind_data=mind_creation_strategy())
@settings(max_examples=100)
def test_property_name(mind_data):
    """For any valid input, the property should hold."""
    # Test implementation
    pass
```

### Unit Test Template

```python
def test_specific_behavior():
    """Test description.
    
    Validates Requirement X.Y.
    """
    # Test implementation
    pass
```

## Test Coverage Requirements

- Minimum 80% code coverage across all modules
- 100% coverage of service layer CRUD operations
- All 42 correctness properties must have corresponding property tests

## Troubleshooting

### Database Connection Issues

If tests fail with connection errors:
1. Ensure Neo4j is running: `docker compose up neo4j -d`
2. Verify connection settings in environment variables
3. Check Neo4j logs: `docker compose logs neo4j`

### Test Database Cleanup

If tests leave data in the database:
```bash
# Connect to Neo4j and run:
MATCH (n) DETACH DELETE n
```

### Hypothesis Test Failures

When a property test fails, Hypothesis provides a minimal counterexample.
The test will automatically shrink the failing input to the simplest case.

To reproduce a specific failure:
```python
@reproduce_failure('6.0.0', b'...')  # Hypothesis provides this
@given(...)
def test_property():
    pass
```
