#!/usr/bin/env python3
"""Simple test runner to check test status without terminal corruption."""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "--tb=short", "-q"],
    capture_output=True,
    text=True,
    cwd="."
)

print(result.stdout)
if result.stderr:
    print(result.stderr)

sys.exit(result.returncode)
