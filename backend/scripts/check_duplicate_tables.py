#!/usr/bin/env python3
"""
Check for duplicate SQLModel table definitions.

This script scans all Python files in the domains directory and checks for
duplicate __tablename__ definitions. This prevents SQLAlchemy errors when
the same table is defined multiple times.

Usage:
    python scripts/check_duplicate_tables.py

Exit codes:
    0 - No duplicates found
    1 - Duplicates found
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


def find_table_definitions(root_dir: str = "domains") -> Dict[str, List[Tuple[str, int]]]:
    """
    Find all __tablename__ definitions in Python files.
    
    Returns:
        Dict mapping table names to list of (file_path, line_number) tuples
    """
    table_definitions = defaultdict(list)
    
    # Pattern to match __tablename__ = "table_name"
    pattern = re.compile(r'__tablename__\s*=\s*["\']([a-zA-Z_][a-zA-Z0-9_]*)["\']')
    
    root_path = Path(root_dir)
    if not root_path.exists():
        print(f"Warning: Directory '{root_dir}' not found")
        return table_definitions
    
    # Walk through all Python files
    for py_file in root_path.rglob("*.py"):
        # Skip __pycache__ and test files (tests can have fixtures)
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue
        
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    match = pattern.search(line)
                    if match:
                        table_name = match.group(1)
                        # Use string path with forward slashes for consistency
                        rel_path = str(py_file.relative_to(root_path.parent)).replace("\\", "/")
                        table_definitions[table_name].append((rel_path, line_num))
        except Exception as e:
            # Silently skip files we can't read
            pass
    
    return table_definitions


def check_for_duplicates(table_definitions: Dict[str, List[Tuple[str, int]]]) -> bool:
    """
    Check for duplicate table definitions.
    
    Returns:
        True if duplicates found, False otherwise
    """
    has_duplicates = False
    
    for table_name, locations in sorted(table_definitions.items()):
        if len(locations) > 1:
            has_duplicates = True
            print(f"\nERROR: Duplicate table definition found: '{table_name}'")
            print(f"   Found in {len(locations)} locations:")
            for file_path, line_num in locations:
                print(f"   - {file_path}:{line_num}")
            print(f"\n   SOLUTION: Keep only ONE definition of this table.")
            print(f"   If multiple models need it, import from a single source.")
    
    return has_duplicates


def main():
    """Main entry point."""
    print("Checking for duplicate SQLModel table definitions...")
    print()
    
    # Find all table definitions
    table_definitions = find_table_definitions()
    
    if not table_definitions:
        print("WARNING: No table definitions found. Is this correct?")
        return 0
    
    # Report summary
    total_tables = len(table_definitions)
    total_definitions = sum(len(locs) for locs in table_definitions.values())
    print(f"Found {total_definitions} table definitions across {total_tables} unique tables")
    print()
    
    # Check for duplicates
    has_duplicates = check_for_duplicates(table_definitions)
    
    if has_duplicates:
        print()
        print("FAILED: Duplicate table definitions detected!")
        print()
        print("To fix this issue:")
        print("1. Decide which file should own each table definition")
        print("2. Remove duplicate definitions from other files")
        print("3. Import the table from the owning file where needed")
        print()
        print("Example:")
        print("  # In file A (owner):")
        print("  class MyTable(SQLModel, table=True):")
        print("      __tablename__ = 'my_table'")
        print()
        print("  # In file B (user):")
        print("  from .file_a import MyTable  # Import, don't redefine")
        print()
        return 1
    else:
        print("SUCCESS: No duplicate table definitions found!")
        print()
        # List all unique tables for reference
        print("Unique tables defined:")
        for table_name in sorted(table_definitions.keys()):
            file_path, line_num = table_definitions[table_name][0]
            print(f"   - {table_name:30} -> {file_path}:{line_num}")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())

