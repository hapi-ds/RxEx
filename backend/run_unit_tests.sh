#!/bin/bash
# Run only unit and property tests (skip websocket and database tests)
cd "$(dirname "$0")"
uv run pytest tests/unit/ tests/properties/ -v --tb=short
