#!/bin/bash
# Simple test runner script
cd "$(dirname "$0")"
uv run pytest tests/unit/test_enums.py -v --tb=short
