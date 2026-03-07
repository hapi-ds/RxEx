#!/usr/bin/env python3
"""Verify StatusEnum has correct values per Requirement 1.6"""

from src.models.enums import StatusEnum

print("Verifying StatusEnum per Requirement 1.6...")
print(f"Number of values: {len(StatusEnum)}")
print("Expected: 7 values (draft, frozen, accepted, ready, done, archived, obsolet)")
print()

required_values = ["draft", "frozen", "accepted", "ready", "done", "archived", "obsolet"]
actual_values = [e.value for e in StatusEnum]

print("Required values:", required_values)
print("Actual values:  ", actual_values)
print()

if set(required_values) == set(actual_values):
    print("✓ StatusEnum is CORRECT per Requirement 1.6")
else:
    print("✗ StatusEnum is INCORRECT")
    missing = set(required_values) - set(actual_values)
    extra = set(actual_values) - set(required_values)
    if missing:
        print(f"  Missing: {missing}")
    if extra:
        print(f"  Extra: {extra}")
