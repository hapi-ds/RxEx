# Mind-Based Data Model System Setup

This guide covers the setup process for the Mind-based data model system.

## Prerequisites

- Python 3.13+
- Neo4j database (running via Docker Compose or standalone)
- UV package manager

## Installation Steps

### 1. Install Dependencies

The required packages are already configured in `pyproject.toml`:
- `neontology>=2.1.0` - Neo4j ORM for Python
- `hypothesis>=6.0.0` - Property-based testing framework (dev dependency)

To install all dependencies:

```bash
cd backend
uv sync
```

### 2. Configure Database Connection

Ensure your `.env` file has the correct Neo4j connection settings:

```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
```

For local development (backend running outside Docker):
```env
NEO4J_URI=bolt://localhost:7687
```

### 3. Start Neo4j Database

Using Docker Compose:

```bash
docker compose up neo4j -d
```

Verify Neo4j is running:
```bash
docker compose ps neo4j
```

### 4. Initialize Database Schema

Run the schema initialization script to create indexes and constraints:

```bash
cd backend
uv run python scripts/init_schema.py
```

This creates:
- Unique constraint on `Mind.uuid`
- Index on `Mind.status` for filtering
- Index on `Mind.creator` for filtering  
- Index on `Mind.updated_at` for sorting and range queries

### 5. Verify Setup

Run the database setup tests:

```bash
cd backend
uv run pytest tests/test_database_setup.py -v
```

Expected output:
```
tests/test_database_setup.py::test_database_connection PASSED
tests/test_database_setup.py::test_schema_creation PASSED
tests/test_database_setup.py::test_clean_database_fixture PASSED
```

## Test Database Configuration

For running tests, you can use a separate test database by setting environment variables:

```bash
export NEO4J_TEST_URI="bolt://localhost:7687"
export NEO4J_TEST_USERNAME="neo4j"
export NEO4J_TEST_PASSWORD="password"
```

Or create a `.env.test` file in the backend directory.

## Database Schema Details

### Constraints

**mind_uuid_unique**: Ensures UUID uniqueness across all Mind nodes
```cypher
CREATE CONSTRAINT mind_uuid_unique IF NOT EXISTS
FOR (m:Mind) REQUIRE m.uuid IS UNIQUE
```

### Indexes

**mind_status_idx**: Optimizes filtering by status
```cypher
CREATE INDEX mind_status_idx IF NOT EXISTS
FOR (m:Mind) ON (m.status)
```

**mind_creator_idx**: Optimizes filtering by creator
```cypher
CREATE INDEX mind_creator_idx IF NOT EXISTS
FOR (m:Mind) ON (m.creator)
```

**mind_updated_at_idx**: Optimizes sorting and date range queries
```cypher
CREATE INDEX mind_updated_at_idx IF NOT EXISTS
FOR (m:Mind) ON (m.updated_at)
```

## Troubleshooting

### Connection Issues

If you get connection errors:

1. **Check Neo4j is running**:
   ```bash
   docker compose ps neo4j
   ```

2. **Check Neo4j logs**:
   ```bash
   docker compose logs neo4j
   ```

3. **Verify connection settings** in `.env` file

4. **Test connection manually**:
   ```bash
   uv run python -c "from src.database.database import initiate_database; initiate_database(); print('Connected!')"
   ```

### Schema Creation Issues

If schema creation fails:

1. **Check Neo4j version** (requires Neo4j 4.0+):
   ```bash
   docker compose exec neo4j neo4j --version
   ```

2. **Manually verify schema**:
   ```cypher
   // In Neo4j Browser (http://localhost:7474)
   SHOW CONSTRAINTS;
   SHOW INDEXES;
   ```

3. **Drop and recreate schema**:
   ```python
   from src.database.database import initiate_database
   from src.database.schema import drop_mind_schema, create_mind_schema
   
   initiate_database()
   drop_mind_schema()
   create_mind_schema()
   ```

### Permission Issues

If you get permission errors:

1. **Verify Neo4j user has admin privileges**
2. **Check Neo4j authentication** is enabled
3. **Ensure password is correct** in `.env` file

## Next Steps

After completing setup:

1. **Run all tests** to verify everything works:
   ```bash
   uv run pytest -q
   ```

2. **Proceed to Task 2**: Implement base Mind model and enumerations

3. **Review the design document**: `.kiro/specs/mind-based-data-model-system/design.md`

## Additional Resources

- [Neontology Documentation](https://github.com/ontolocy/neontology)
- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
