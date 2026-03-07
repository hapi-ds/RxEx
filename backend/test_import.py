#!/usr/bin/env python3
"""Quick import test."""

try:
    from src.schemas.minds import (
        ErrorResponse,
        MindResponse,
        QueryResult,
        RelationshipResponse,
    )
    print("SUCCESS: All response schemas imported successfully!")
    print(f"- MindResponse: {MindResponse.__name__}")
    print(f"- QueryResult: {QueryResult.__name__}")
    print(f"- ErrorResponse: {ErrorResponse.__name__}")
    print(f"- RelationshipResponse: {RelationshipResponse.__name__}")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
