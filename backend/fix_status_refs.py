#!/usr/bin/env python3
"""Fix all StatusEnum.ACTIVE references to StatusEnum.DONE"""

import os


def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content
    content = content.replace('StatusEnum.ACTIVE', 'StatusEnum.DONE')

    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

# Fix test files
test_dirs = ['tests/unit', 'tests/properties']
fixed_count = 0

for test_dir in test_dirs:
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1

print(f"\nTotal files fixed: {fixed_count}")
