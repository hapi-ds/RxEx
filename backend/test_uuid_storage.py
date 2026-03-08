import asyncio
from uuid import uuid4
from src.services.mind_service import MindService
from src.schemas.minds import MindCreate
from neontology import GraphConnection

async def test():
    service = MindService()
    
    # Create a node
    mind_data = MindCreate(
        mind_type="project",
        title="Test",
        creator="test@example.com",
        type_specific_attributes={
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        },
    )
    
    created = await service.create_mind(mind_data)
    print(f"Created UUID: {created.uuid}")
    print(f"UUID type: {type(created.uuid)}")
    
    # Query the database directly
    gc = GraphConnection()
    
    # Try different UUID formats
    queries = [
        ("String UUID", "MATCH (n:Mind) WHERE n.uuid = $uuid RETURN n", str(created.uuid)),
        ("UUID object", "MATCH (n:Mind) WHERE n.uuid = $uuid RETURN n", created.uuid),
        ("All nodes", "MATCH (n:Mind) RETURN n.uuid, n.title LIMIT 5", None),
    ]
    
    for name, cypher, param in queries:
        print(f"\n{name}:")
        try:
            if param is None:
                result = gc.engine.evaluate_query(cypher)
            else:
                result = gc.engine.evaluate_query_single(cypher, {"uuid": param})
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")

asyncio.run(test())
